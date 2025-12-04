# decision.py

WHITELIST_ACTIONS = {
    "list_dir": "safe",
    "show_file": "safe",
    "create_file": "safe",
    "write_file": "safe",
    "append_file": "safe",
    "remove_file": "dangerous",
    "move_file": "safe",
    "copy_file": "safe",
    "open_url": "safe",
    "system_shutdown": "dangerous",
    "play_media": "safe",
    "open_app": "safe",
}

def build_plan(ai_response: dict, confidence_threshold=0.5):
    candidates = ai_response.get("candidates", [])
    plan = []

    for c in candidates:
        action = c.get("action")
        score = c.get("score", 0.0)

        if action not in WHITELIST_ACTIONS:
            continue

        if WHITELIST_ACTIONS[action] == "dangerous":
            score *= 0.5

        if score >= confidence_threshold:
            plan.append({
                "action": action,
                "params": c.get("params", {}),
                "score": score,
                "explanation": c.get("explanation", "")
            })

    plan.sort(key=lambda x: x["score"], reverse=True)
    return plan
