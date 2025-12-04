# mapper.py
import os
import shutil
import subprocess
import webbrowser
import platform
import psutil
import requests


# ---------------------------
# FILE SYSTEM ACTIONS
# ---------------------------

def action_list_dir(path):
    try:
        return os.listdir(path)
    except Exception as e:
        return f"Error: {e}"

def action_show_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

def action_create_file(path):
    try:
        open(path, "w").close()
        return "File created"
    except Exception as e:
        return f"Error: {e}"

def action_write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return "Written successfully"
    except Exception as e:
        return f"Error: {e}"

def action_append_file(path, content):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return "Appended successfully"
    except Exception as e:
        return f"Error: {e}"

def action_remove_file(path):
    try:
        os.remove(path)
        return "File removed"
    except Exception as e:
        return f"Error: {e}"

def action_move_file(src, dest):
    try:
        shutil.move(src, dest)
        return "File moved"
    except Exception as e:
        return f"Error: {e}"

def action_copy_file(src, dest):
    try:
        shutil.copy(src, dest)
        return "File copied"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------
# SYSTEM INFORMATION
# ---------------------------

def action_get_system_info():
    return {
        "os": platform.system(),
        "version": platform.version(),
        "machine": platform.machine()
    }

def action_get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def action_get_memory_usage():
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "available": mem.available,
        "percent": mem.percent
    }

def action_get_disk_usage(path):
    usage = shutil.disk_usage(path)
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free
    }


# ---------------------------
# NETWORK ACTIONS
# ---------------------------

def action_ping_host(host):
    try:
        result = subprocess.run(["ping", "-n", "1", host], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def action_download_file(url, save_path):
    try:
        data = requests.get(url).content
        with open(save_path, "wb") as f:
            f.write(data)
        return "Downloaded successfully"
    except Exception as e:
        return f"Error: {e}"

def action_open_url(url):
    webbrowser.open(url)
    return f"Opening URL: {url}"


# ---------------------------
# PROCESS / APPLICATION
# ---------------------------

def action_run_program(command, args):
    try:
        cmd = [command] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def action_kill_process(pid):
    try:
        p = psutil.Process(pid)
        p.terminate()
        return f"Process {pid} terminated"
    except Exception as e:
        return f"Error: {e}"

def action_start_service(service):
    try:
        subprocess.run(["sc", "start", service], capture_output=True, text=True)
        return "Service started"
    except Exception as e:
        return f"Error: {e}"

def action_stop_service(service):
    try:
        subprocess.run(["sc", "stop", service], capture_output=True, text=True)
        return "Service stopped"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------
# AI/TEXT UTILITIES
# ---------------------------

def action_summarize_text(text):
    return text[:200] + "..." if len(text) > 200 else text

def action_extract_entities(text):
    words = text.split()
    return [w for w in words if w.istitle()]

def action_classify_text(text, labels):
    return {label: (label.lower() in text.lower()) for label in labels}

def action_plan_task(goal):
    return [
        "Understand the goal",
        "Break into steps",
        "Execute step by step",
        f"Goal: {goal}"
    ]


# ---------------------------
# MULTI ACTION
# ---------------------------

def action_multi_action_plan(execute_action, steps):
    results = []
    for step in steps:
        act = step["action"]
        params = step["params"]
        results.append({
            "action": act,
            "result": execute_action(act, params)
        })
    return results
