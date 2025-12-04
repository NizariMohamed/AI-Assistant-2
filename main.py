# main.py

from planner import ai_generate_actions
from decision import build_plan
from mapperCore import execute_action


def execute_plan(plan: list):
    results = []

    for step in plan:
        action = step["action"]
        params = step.get("params", {})

        result = execute_action(action, params)
        results.append({
            "action": action,
            "params": params,
            "result": result
        })

    return results


if __name__ == "__main__":
    user_input = input("Enter command: ")

    ai_response = ai_generate_actions(user_input)
    plan = build_plan(ai_response)

    print("\n--- GENERATED PLAN ---")
    for step in plan:
        print(step)

    print("\n--- EXECUTION RESULTS ---")
    results = execute_plan(plan)
    for item in results:
        print(item)
