import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

LLM_URL = os.environ.get("LLM_URL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

def save_debug_log(prefix, data):
    os.makedirs("debug", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 連番などの代わりにマイクロ秒をつけてファイル名被りを防ぐ
    microsec = datetime.now().strftime("%f")[:3]
    filename = f"debug/{timestamp}_{microsec}_{prefix}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def call_llm(messages):
    print(f"Sending {len(messages)} messages to LLM...")
    save_debug_log("request", {"messages": messages})
    
    res = requests.post(
        LLM_URL,
        headers={"Authorization": f"Bearer {LLM_API_KEY}"},
        json={"messages": messages},
        timeout=900,
    )
    if res.status_code != 200:
        print(f"Error: {res.status_code} {res.text}")
        save_debug_log("error", {"status_code": res.status_code, "text": res.text})
        raise Exception(f"{res.status_code} {res.text}")

    output_content = res.json()["choices"][0]["message"]["content"]
    save_debug_log("response", {"content": output_content})
    return output_content
