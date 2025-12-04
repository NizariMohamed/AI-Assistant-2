import speech_recognition as sr
import pyttsx3
from groq import Groq
import time
import os
from pathlib import Path
import threading
import queue
import webbrowser
import re
from pynput.keyboard import Key, Controller
import subprocess
import platform

# ------------------------
# Configuration
# ------------------------
MAX_HISTORY = 20
AUDIO_FILE = "audio.wav"
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2

LISTENING_MODES = {
    "quick": {"timeout": 10,"phrase_time_limit": 8,"pause_threshold": 0.8,"energy_threshold": 400},
    "normal": {"timeout": 30,"phrase_time_limit": 15,"pause_threshold": 1.2,"energy_threshold": 300},
    "patient": {"timeout": 60,"phrase_time_limit": 30,"pause_threshold": 2.0,"energy_threshold": 250}
}

CURRENT_MODE = "normal"
VOICE_PROFILES = {
    "professional": {"rate": 170, "volume": 0.9},
    "casual": {"rate": 180, "volume": 1.0},
    "slow": {"rate": 140, "volume": 1.0},
    "fast": {"rate": 200, "volume": 0.95}
}
CURRENT_VOICE_PROFILE = "casual"

assistant_awake = True

try:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        api_key = "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"
        print("⚠️  Warning: Using hardcoded API key. Set GROQ_API_KEY environment variable!")
    client = Groq(api_key=api_key)
except Exception as e:
    print(f"❌ Failed to initialize Groq client: {e}")
    exit(1)

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.phrase_threshold = 0.1
recognizer.non_speaking_duration = 0.3

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    elif len(voices) > 0:
        engine.setProperty('voice', voices[0].id)
    print("✅ TTS engine initialized")
except Exception as e:
    print(f"❌ Failed to initialize TTS: {e}")
    exit(1)

conversation_history = [
    {"role": "system", "content": "You are Neez, a friendly AI assistant. Answer briefly like a human in 1-3 sentences unless asked for detail."}
]

speech_queue = queue.Queue()
is_speaking = False
stop_speaking = threading.Event()

# ------------------------
# Helper Functions
# ------------------------

def apply_listening_mode(mode="normal"):
    global CURRENT_MODE
    if mode not in LISTENING_MODES:
        mode = "normal"
    CURRENT_MODE = mode
    settings = LISTENING_MODES[mode]
    recognizer.energy_threshold = settings["energy_threshold"]
    recognizer.pause_threshold = settings["pause_threshold"]
    print(f"🎚️  Listening mode: {mode.upper()}")

def apply_voice_profile(profile="casual"):
    global CURRENT_VOICE_PROFILE
    if profile not in VOICE_PROFILES:
        profile = "casual"
    CURRENT_VOICE_PROFILE = profile
    settings = VOICE_PROFILES[profile]
    engine.setProperty('rate', settings["rate"])
    engine.setProperty('volume', settings["volume"])
    print(f"🎤 Voice profile: {profile.upper()}")

def speak(text):
    global engine
    try:
        engine = pyttsx3.init()
        settings = VOICE_PROFILES[CURRENT_VOICE_PROFILE]
        engine.setProperty('rate', settings["rate"])
        engine.setProperty('volume', settings["volume"])
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        del engine
        time.sleep(0.1)
        engine = pyttsx3.init()
    except Exception as e:
        print(f"⚠️  TTS error: {e}")
        try:
            engine = pyttsx3.init()
        except:
            pass

def listen_with_visual_feedback():
    with sr.Microphone() as source:
        print("\n👂 Listening", end="", flush=True)
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        settings = LISTENING_MODES[CURRENT_MODE]
        try:
            audio = recognizer.listen(
                source,
                timeout=settings["timeout"],
                phrase_time_limit=settings["phrase_time_limit"]
            )
            print("\r👂 Listening... ✓")
            return audio
        except sr.WaitTimeoutError:
            print("\r⏱️  Timeout - no speech detected")
            return None

def transcribe_audio(audio_data):
    for attempt in range(RETRY_ATTEMPTS):
        try:
            with open(AUDIO_FILE, "wb") as f:
                f.write(audio_data.get_wav_data())
            with open(AUDIO_FILE, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                    language="en"
                )
            return transcription.text.strip()
        except:
            time.sleep(1)
    return None

def get_ai_response(messages, detailed=False):
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.7,
                max_tokens=250 if detailed else 150
            )
            return response.choices[0].message.content
        except:
            time.sleep(1)
    return "I'm having trouble thinking right now."

def trim_conversation_history():
    global conversation_history
    if len(conversation_history) > MAX_HISTORY:
        conversation_history = [conversation_history[0]] + conversation_history[-(MAX_HISTORY - 1):]

def check_microphone():
    try:
        mics = sr.Microphone.list_microphone_names()
        return len(mics) > 0
    except:
        return False

# -------------------------
# NEW: Music Controls
# -------------------------
keyboard = Controller()

def get_system_type():
    """Detect operating system"""
    return platform.system()

def control_music(action):
    """Control music playback using keyboard media keys"""
    system = get_system_type()
    
    try:
        if action == "play" or action == "pause":
            # Play/Pause toggle
            if system == "Darwin":  # macOS
                keyboard.press(Key.media_play_pause)
                keyboard.release(Key.media_play_pause)
            elif system == "Windows":
                keyboard.press(Key.media_play_pause)
                keyboard.release(Key.media_play_pause)
            elif system == "Linux":
                subprocess.run(["playerctl", "play-pause"], check=False)
            return True, "play/pause"
            
        elif action == "next" or action == "skip":
            # Next track
            if system == "Darwin":
                keyboard.press(Key.media_next)
                keyboard.release(Key.media_next)
            elif system == "Windows":
                keyboard.press(Key.media_next)
                keyboard.release(Key.media_next)
            elif system == "Linux":
                subprocess.run(["playerctl", "next"], check=False)
            return True, "next"
            
        elif action == "previous" or action == "back":
            # Previous track
            if system == "Darwin":
                keyboard.press(Key.media_previous)
                keyboard.release(Key.media_previous)
            elif system == "Windows":
                keyboard.press(Key.media_previous)
                keyboard.release(Key.media_previous)
            elif system == "Linux":
                subprocess.run(["playerctl", "previous"], check=False)
            return True, "previous"
            
        elif action == "volume up" or action == "louder":
            # Volume up
            for _ in range(5):  # Increase by 5 steps
                keyboard.press(Key.media_volume_up)
                keyboard.release(Key.media_volume_up)
                time.sleep(0.05)
            return True, "volume up"
            
        elif action == "volume down" or action == "quieter":
            # Volume down
            for _ in range(5):
                keyboard.press(Key.media_volume_down)
                keyboard.release(Key.media_volume_down)
                time.sleep(0.05)
            return True, "volume down"
            
        elif action == "mute":
            # Mute
            keyboard.press(Key.media_volume_mute)
            keyboard.release(Key.media_volume_mute)
            return True, "mute"
            
    except Exception as e:
        print(f"⚠️  Music control error: {e}")
        return False, None
    
    return False, None

def play_music_on_youtube(query):
    """Search and play music on YouTube - directly plays first video"""
    try:
        # Use youtube-search-python or similar to get video ID
        # For now, we'll use a workaround with invidious or direct search
        
        # Method 1: Try to use pywhatkit if available
        try:
            import pywhatkit as kit
            speak("Starting YouTube playback")
            kit.playonyt(query)
            return True
        except ImportError:
            pass
        
        # Method 2: Use direct video URL format (opens and auto-plays)
        # This uses YouTube's search redirect which plays first result
        search_query = query.replace(' ', '+')
        
        # YouTube Music with autoplay
        yt_music_url = f"https://music.youtube.com/search?q={search_query}"
        webbrowser.open(yt_music_url)
        
        # Wait and simulate Enter to play first result
        time.sleep(1.5)
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        # Ultimate fallback
        search_query = query.replace(' ', '+')
        url = f"https://www.youtube.com/results?search_query={search_query}"
        webbrowser.open(url)
        return True

def play_music_on_spotify(query):
    """Open Spotify with search query"""
    search_query = query.replace(' ', '%20')
    url = f"spotify:search:{search_query}"
    try:
        webbrowser.open(url)
        return True
    except:
        # Fallback to web version
        web_url = f"https://open.spotify.com/search/{search_query}"
        webbrowser.open(web_url)
        return True

def extract_music_query(text):
    """Extract song/artist name from play command"""
    text_lower = text.lower()
    
    patterns = [
        r'play (.+?) on youtube',
        r'play (.+?) on spotify',
        r'play (.+)',
        r'music (.+)',
        r'song (.+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            query = match.group(1).strip()
            # Remove common filler words
            query = query.replace('the song', '').replace('song', '').strip()
            return query
    
    return None
def extract_search_query(text):
    """Extract search query from various command formats"""
    text_lower = text.lower()
    
    # Patterns to extract search terms
    patterns = [
        r'search (?:for |about )?(.+)',
        r'google (.+)',
        r'look up (.+)',
        r'find (?:me )?(?:information on |about )?(.+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1).strip()
    
    return None

def extract_website(text):
    """Extract website name from command"""
    text_lower = text.lower()
    
    patterns = [
        r'open (.+)',
        r'go to (.+)',
        r'visit (.+)',
        r'launch (.+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            site = match.group(1).strip()
            # Removing common words
            site = site.replace('website', '').replace('site', '').strip()
            return site
    
    return None

def open_website(site_name):
    """Open a website based on name or URL"""
    site_name = site_name.lower().strip()
    
    site_map = {
        'youtube': 'https://www.youtube.com',
        'google': 'https://www.google.com',
        'facebook': 'https://www.facebook.com',
        'twitter': 'https://www.twitter.com',
        'instagram': 'https://www.instagram.com',
        'linkedin': 'https://www.linkedin.com',
        'amazon': 'https://www.amazon.com',
        'netflix': 'https://www.netflix.com',
        'reddit': 'https://www.reddit.com',
        'wikipedia': 'https://www.wikipedia.org',
        'github': 'https://www.github.com',
        'stackoverflow': 'https://stackoverflow.com',
        'stack overflow': 'https://stackoverflow.com',
        'gmail': 'https://mail.google.com',
        'twitter': 'https://twitter.com',
        'x': 'https://x.com',
    }
    
    if site_name in site_map:
        url = site_map[site_name]
        webbrowser.open(url)
        return True, site_name
     
    if site_name.startswith('http://') or site_name.startswith('https://'):
        webbrowser.open(site_name)
        return True, site_name
    
    if not site_name.startswith('www.'):
        url = f"https://www.{site_name}"
        if not url.endswith('.com') and '.' not in site_name:
            url += '.com'
        webbrowser.open(url)
        return True, site_name
    
    # If all else fails, open with https://
    url = f"https://{site_name}"
    webbrowser.open(url)
    return True, site_name

def perform_web_search(query):
    """Perform a Google search"""
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(search_url)
    return True

# -------------------------
# Management Commands
# -------------------------
def process_management_commands(text):
    global assistant_awake

    t = text.lower()

    if "wake up" in t or "start listening" in t or "come back" in t:
        assistant_awake = True
        speak("I am awake and listening again.")
        return True

    if "sleep mode" in t or "stop listening" in t or "go to sleep" in t:
        assistant_awake = False
        speak("Okay, I will stop listening. Say 'wake up' when you need me.")
        return True

    if "shutdown" in t or "exit now" in t or "terminate" in t:
        speak("Shutting down now. Goodbye!")
        os._exit(0)

    return False

def process_voice_commands(text):
    text_lower = text.lower()

    # Check management commands first
    if process_management_commands(text):
        return True, ""

    # MUSIC CONTROLS - Check for music commands
    if any(keyword in text_lower for keyword in ['pause music', 'resume music', 'play music', 'stop music']):
        success, action = control_music("pause")
        if success:
            speak("Done")
            return True, ""
    
    if any(keyword in text_lower for keyword in ['next song', 'skip song', 'next track', 'skip']):
        success, action = control_music("next")
        if success:
            speak("Skipping")
            return True, ""
    
    if any(keyword in text_lower for keyword in ['previous song', 'last song', 'go back', 'previous track']):
        success, action = control_music("previous")
        if success:
            speak("Going back")
            return True, ""
    
    if any(keyword in text_lower for keyword in ['volume up', 'louder', 'increase volume']):
        success, action = control_music("volume up")
        if success:
            speak("Volume up")
            return True, ""
    
    if any(keyword in text_lower for keyword in ['volume down', 'quieter', 'decrease volume', 'lower volume']):
        success, action = control_music("volume down")
        if success:
            speak("Volume down")
            return True, ""
    
    if 'mute' in text_lower:
        success, action = control_music("mute")
        if success:
            speak("Muted")
            return True, ""
    
    # PLAY SPECIFIC MUSIC
    if text_lower.startswith('play ') and 'on youtube' in text_lower:
        query = extract_music_query(text)
        if query:
            speak(f"Playing {query} on YouTube")
            play_music_on_youtube(query)
            return True, ""
    
    if text_lower.startswith('play ') and 'on spotify' in text_lower:
        query = extract_music_query(text)
        if query:
            speak(f"Playing {query} on Spotify")
            play_music_on_spotify(query)
            return True, ""
    
    if text_lower.startswith('play ') and 'on youtube' not in text_lower and 'on spotify' not in text_lower:
        query = extract_music_query(text)
        if query:
            speak(f"Playing {query} on YouTube")
            play_music_on_youtube(query)
            return True, ""

    # WEB SEARCH - Check for search commands
    if any(keyword in text_lower for keyword in ['search', 'google', 'look up', 'find information']):
        search_query = extract_search_query(text)
        if search_query:
            speak(f"Searching for {search_query}")
            perform_web_search(search_query)
            return True, f"Opening search results for {search_query}"
        else:
            speak("What should I search for?")
            return True, ""

    # WEBSITE OPENING - Check for open/visit/go to commands
    if any(keyword in text_lower for keyword in ['open', 'go to', 'visit', 'launch']):
        website = extract_website(text)
        if website:
            success, site = open_website(website)
            if success:
                speak(f"Opening {site}")
                return True, f"Opened {site}"
        else:
            speak("Which website should I open?")
            return True, ""

    # Listening mode commands
    if "quick mode" in text_lower:
        apply_listening_mode("quick")
        return True, "Switched to quick mode"

    if "patient mode" in text_lower:
        apply_listening_mode("patient")
        return True, "Switched to patient mode"

    if "normal mode" in text_lower:
        apply_listening_mode("normal")
        return True, "Back to normal mode"

    # Voice profile commands
    if "speak faster" in text_lower:
        apply_voice_profile("fast")
        return True, "Speaking faster"

    if "speak slower" in text_lower:
        apply_voice_profile("slow")
        return True, "Speaking slower"

    if "professional voice" in text_lower:
        apply_voice_profile("professional")
        return True, "Professional voice activated"

    if "casual voice" in text_lower:
        apply_voice_profile("casual")
        return True, "Casual voice activated"

    if "clear history" in text_lower:
        conversation_history.clear()
        conversation_history.append({"role": "system", "content": "You are Neez... brief answers."})
        return True, "History cleared"

    return False, None

# ------------------------
# Main loop
# ------------------------
def main():
    global assistant_awake

    print("\n=== Neez Voice Assistant ===")
    print("🌐 Web commands enabled!")
    print("   - 'search for [query]' or 'google [query]'")
    print("   - 'open [website]' or 'go to [website]'")
    print("🎵 Music controls enabled!")
    print("   - 'play [song name]' - plays on YouTube")
    print("   - 'play [song] on spotify' - plays on Spotify")
    print("   - 'pause music', 'next song', 'previous song'")
    print("   - 'volume up', 'volume down', 'mute'\n")

    if not check_microphone():
        print("No microphone detected!")
        return

    apply_listening_mode(CURRENT_MODE)
    apply_voice_profile(CURRENT_VOICE_PROFILE)

    while True:
        try:
            # If assistant is in sleep mode
            if not assistant_awake:
                print("💤 Assistant sleeping... waiting for wake word.")
                audio = listen_with_visual_feedback()
                if audio:
                    text = transcribe_audio(audio)
                    if text:
                        process_management_commands(text)
                continue

            audio = listen_with_visual_feedback()
            if not audio:
                continue

            user_text = transcribe_audio(audio)
            if not user_text:
                continue

            print("You:", user_text)

            # Handle management commands
            if process_management_commands(user_text):
                continue

            # Handle voice commands (including web search and opening)
            is_command, cmd_response = process_voice_commands(user_text)
            if is_command:
                if cmd_response:
                    speak(cmd_response)
                continue

            # Normal conversation
            conversation_history.append({"role": "user", "content": user_text})
            reply = get_ai_response(conversation_history)
            conversation_history.append({"role": "assistant", "content": reply})

            print("Neez:", reply)
            speak(reply)
            trim_conversation_history()

        except KeyboardInterrupt:
            speak("Goodbye!")
            break

if __name__ == "__main__":
    main()