#planner.py
from groq import Groq
import json

#Initialize the Cliant
cliant = Groq(api_key = "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")


def ai_generate_actions(user_input: str) -> dict:
    #load system instruction prompts
    system_prompt = open("planner_prompt.txt").read()
    #sending to groq
    completion = cliant.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content":system_prompt},
            {"role":"user", "content":user_input}
        ],
        temperature=0.2,
        max_tokens=400
    )
    #Extract text
    row_output = completion.choices[0].message.content.strip()

    #Parse JSON safely
    try:
        data = json.loads(row_output)
        return data
    except json.JSONDecodeError:
        print("AI returned invalid JSON. Raw output: ")
        print(row_output)
        return {}

#Example test
if __name__ == "__main__":
    result = ai_generate_actions("open facebook")
    print("AI Responce: ")
    print(json.dumps(result, indent=4))
