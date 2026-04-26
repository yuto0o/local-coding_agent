from typing import TypedDict

class AgentState(TypedDict):
    task: str
    messages: list[dict]
    current_actions: list[dict]
    last_error: str
    error_count: int
    require_approval: bool
