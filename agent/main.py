import json
from agent.planner import plan
from agent.executor import execute
from agent.validator import validate_json

# def fake_llm(prompt):
#     # 実際はOpenAI / ローカルLLM
#     return json.dumps({
#         "action": "done",
#         "reason": "完了"
#     })

import requests

LLM_URL = "http://100.108.194.117:8081/v1/chat/completions"

def call_llm(prompt):
    print(prompt)
    res = requests.post(
        LLM_URL,
        headers = {
            "Authorization": "Bearer iso3rotor2026"
        },
        json={
            "messages": [
                {"role": "system", "content": "必ずJSONで出力"},
                {"role": "user", "content": prompt}
            ]
        },
        timeout=60
    )
    print(res)

    return res.json()["choices"][0]["message"]["content"]

def run():
    task = input(">> ")

    plan_text = plan(task)

    for step in range(5):
        output = call_llm(plan_text)

        action = validate_json(output)

        if action["action"] == "done":
            print("DONE")
            break

        result = execute(action)
        print(result)

if __name__ == "__main__":
    run()