from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.llm_client import call_llm
from agent.validator import validate_json
from agent.executor import execute

def llm_node(state: AgentState):
    messages = state["messages"].copy()
    try:
        output = call_llm(messages)
        messages.append({"role": "assistant", "content": output})
        actions = validate_json(output)
        return {"messages": messages, "current_actions": actions}
    except Exception as e:
        error_msg = str(e)
        error_count = state.get("error_count", 0)
        last_error = state.get("last_error", "")
        
        if error_msg == last_error:
            error_count += 1
        else:
            error_count = 1
            
        messages.append({"role": "user", "content": f"エラー発生:\n{error_msg}"})
        return {
            "messages": messages,
            "current_actions": [],
            "last_error": error_msg,
            "error_count": error_count
        }

def review_node(state: AgentState):
    actions = state.get("current_actions", [])
    print("\n" + "="*40)
    print("【人間の承認が必要です】以下の操作を実行しますか？")
    for a in actions:
        if a.get("action") == "write":
            print(f"- [WRITE] {a.get('path', '')}")
    print("="*40)
    
    while True:
        ans = input("実行を承認しますか？ (y/n): ").strip().lower()
        if ans in ['y', 'yes']:
            return {}
        elif ans in ['n', 'no']:
            msg = "ユーザーによって操作が拒否されました。別のアプローチを提案してください。"
            messages = state["messages"].copy()
            messages.append({"role": "user", "content": msg})
            return {"messages": messages, "current_actions": []}

def execute_node(state: AgentState):
    actions = state.get("current_actions", [])
    if not actions:
        return {}
        
    messages = state["messages"].copy()
    results = []
    has_error = False
    last_error = state.get("last_error", "")
    error_count = state.get("error_count", 0)
    
    for action in actions:
        try:
            result = execute(action)
            results.append(f"[{action.get('action')} {action.get('path', '')} 実行結果]:\n{result}")
            print(f"Action: {action.get('action')} -> Success")
        except Exception as e:
            error_msg = str(e)
            results.append(f"[{action.get('action')} {action.get('path', '')} エラー発生]:\n{error_msg}")
            print(f"Action: {action.get('action')} -> Error: {e}")
            has_error = True
            
            if error_msg == last_error:
                error_count += 1
            else:
                error_count = 1
                last_error = error_msg

    messages.append({"role": "user", "content": "\n\n".join(results)})
    
    if not has_error:
        error_count = 0
        last_error = ""
        
    return {
        "messages": messages,
        "last_error": last_error,
        "error_count": error_count
    }

def human_help_node(state: AgentState):
    print("\n" + "!"*40)
    print(f"【エスカレーション】同じエラーが {state.get('error_count')} 回連続で発生しました。")
    print(f"エラー内容: {state.get('last_error')}")
    print("!"*40)
    
    advice = input("エージェントへの助言を入力してください（空入力で終了）: ").strip()
    if not advice:
        return {"current_actions": [{"action": "done"}]}
        
    messages = state["messages"].copy()
    messages.append({"role": "user", "content": f"ユーザーからの助言:\n{advice}"})
    return {
        "messages": messages,
        "error_count": 0,
        "last_error": ""
    }

def route_after_llm(state: AgentState):
    if state.get("error_count", 0) >= 3:
        return "human_help"
        
    actions = state.get("current_actions", [])
    if any(a.get("action") == "done" for a in actions):
        return END
        
    if state.get("require_approval", False) and any(a.get("action") == "write" for a in actions):
        return "review"
        
    return "execute"
    
def route_after_review(state: AgentState):
    actions = state.get("current_actions", [])
    if not actions:
        return "llm"
    return "execute"

def route_after_execute(state: AgentState):
    if state.get("error_count", 0) >= 3:
        return "human_help"
    return "llm"

def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("llm", llm_node)
    builder.add_node("review", review_node)
    builder.add_node("execute", execute_node)
    builder.add_node("human_help", human_help_node)
    
    builder.add_edge(START, "llm")
    builder.add_conditional_edges("llm", route_after_llm)
    builder.add_conditional_edges("review", route_after_review)
    builder.add_conditional_edges("execute", route_after_execute)
    builder.add_edge("human_help", "llm")
    
    return builder.compile()

def save_graph_image(graph, path="graph.md"):
    try:
        mermaid_code = graph.get_graph().draw_mermaid()
        with open(path, "w") as f:
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n")
        print(f"グラフ構造を {path} に保存しました。")
    except Exception as e:
        print(f"グラフ保存エラー: {e}")
