import os
import requests
from dotenv import load_dotenv

load_dotenv()

LLM_URL = os.environ.get("LLM_URL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

def call_llm(messages):
    print(f"Sending {len(messages)} messages to LLM...")
    res = requests.post(
        LLM_URL,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}"
        },
        json={
            "messages": messages
        },
        timeout=360
    )
    if res.status_code != 200:
        print(f"Error: {res.status_code} {res.text}")
        raise Exception(f"{res.status_code} {res.text}")
    
    return res.json()["choices"][0]["message"]["content"]
