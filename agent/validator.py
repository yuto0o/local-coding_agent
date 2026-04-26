import json

def validate_json(output: str):
    try:
        data = json.loads(output)
    except:
        raise Exception("JSON形式エラー")

    required = ["action", "reason"]

    for r in required:
        if r not in data:
            raise Exception("キー不足")

    return data