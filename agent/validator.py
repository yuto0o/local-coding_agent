import json
from pydantic import BaseModel, ValidationError
from typing import Literal, Optional, List

class AgentAction(BaseModel):
    action: Literal["read", "write", "done"]
    path: Optional[str] = ""
    content: Optional[str] = ""
    reason: Optional[str] = ""

def validate_json(output: str) -> List[dict]:
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

    validated_data = []
    for i, item in enumerate(data):
        try:
            action = AgentAction(**item)
            validated_data.append(action.model_dump())
        except ValidationError as e:
            raise Exception(f"アクション形式エラー:\n{e}")

    return validated_data