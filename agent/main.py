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

import os
from dotenv import load_dotenv

load_dotenv()

LLM_URL = os.environ.get("LLM_URL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

def call_llm(messages):
    print(messages)
    print(f"Sending {len(messages)} messages to LLM...")
    res = requests.post(
        LLM_URL,
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}"
        },
        json={
            "messages": messages
        },
        timeout=900
    )
    if res.status_code != 200:
        print(f"Error: {res.status_code} {res.text}")
        
    return res.json()["choices"][0]["message"]["content"]

def run():
    task = input(">> ")

    messages = plan(task)

    for step in range(10):
        print(f"\n--- Step {step + 1} ---")
        try:
            output = call_llm(messages)
        except Exception as e:
            print(f"LLM API Error: {e}")
            break
            
        print("LLM Output:", output)
        messages.append({"role": "assistant", "content": output})

        try:
            actions = validate_json(output)
            
            if any(a.get("action") == "done" for a in actions):
                print("DONE")
                break

            results = []
            for action in actions:
                try:
                    result = execute(action)
                    results.append(f"[{action['action']} {action.get('path', '')} 実行結果]:\n{result}")
                    print(f"Action: {action['action']} -> Success")
                except Exception as e:
                    results.append(f"[{action['action']} {action.get('path', '')} エラー発生]:\n{str(e)}")
                    print(f"Action: {action['action']} -> Error: {e}")
                    
            messages.append({"role": "user", "content": "\n\n".join(results)})
            
        except Exception as e:
            messages.append({"role": "user", "content": f"エラー発生:\n{str(e)}"})
            print(f"Error: {e}")

if __name__ == "__main__":
    run()