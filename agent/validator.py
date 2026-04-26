import json

def validate_json(output: str):
    cleaned = output.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except Exception as e:
        raise Exception(f"JSON形式エラー: {e}")

    if isinstance(data, dict):
        data = [data]
        
    if not isinstance(data, list):
        raise Exception("ルートが配列またはオブジェクトではありません")

    required = ["action", "reason"]

    for item in data:
        for r in required:
            if r not in item:
                raise Exception(f"キー不足: {r}")

    return data