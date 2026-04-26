from langgraph.graph import StateGraph, START, END
from agent.state import AgentState
from agent.llm_client import call_llm
from agent.validator import validate_json
from agent.executor import execute
from agent.planner import get_workspace_context
from pathlib import Path
import subprocess
import os
import glob

def llm_node(state: AgentState):
    print("\n[Node] llm_node 実行開始...")
    messages = state["messages"].copy()
    try:
        output = call_llm(messages)
        print("[Node] llm_node: LLMからの応答を取得しました。")
        messages.append({"role": "assistant", "content": output})
        actions = validate_json(output)
        return {"messages": messages, "current_actions": actions}
    except Exception as e:
        error_msg = str(e)
        print(f"[Node] llm_node: エラー発生 - {error_msg}")
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
    print("\n[Node] review_node 実行...")
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
    print("\n[Node] execute_node 実行開始...")
    actions = state.get("current_actions", [])
    if not actions:
        print("[Node] execute_node: 実行するアクションがありません。")
        return {}
        
    messages = state["messages"].copy()
    results = []
    has_error = False
    last_error = state.get("last_error", "")
    error_count = state.get("error_count", 0)
    
    for action in actions:
        try:
            print(f"[Node] execute_node: 実行中 -> {action.get('action')} {action.get('path', '')}")
            result = execute(action)
            results.append(f"[{action.get('action')} {action.get('path', '')} 実行結果]:\n{result}")
            print(f"       -> Success")
        except Exception as e:
            error_msg = str(e)
            results.append(f"[{action.get('action')} {action.get('path', '')} エラー発生]:\n{error_msg}")
            print(f"       -> Error: {e}")
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
    print("\n[Node] human_help_node 実行...")
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

def lint_node(state: AgentState):
    print("\n[Node] lint_node 実行開始...")
    actions = state.get("current_actions", [])
    if not any(a.get("action") == "write" for a in actions):
        print("[Node] lint_node: ファイルの書き込みがないためスキップします。")
        return {}

    messages = state["messages"].copy()
    error_count = state.get("error_count", 0)
    last_error = state.get("last_error", "")

    print("[Node] lint_node: Ruffフォーマット・自動修正を実行します。")
    subprocess.run(["uv", "run", "ruff", "format", "."], cwd="workspace", capture_output=True)
    subprocess.run(["uv", "run", "ruff", "check", "--fix", "."], cwd="workspace", capture_output=True)
    
    result = subprocess.run(["uv", "run", "ruff", "check", "."], cwd="workspace", capture_output=True, text=True)
    
    if result.returncode != 0:
        error_msg = f"Lintエラーが残っています:\n{result.stdout}\n修正してください。"
        print("[Node] lint_node: Lint Error を検出しました。")
        
        if error_msg == last_error:
            error_count += 1
        else:
            error_count = 1
            last_error = error_msg
            
        messages.append({"role": "user", "content": error_msg})
        return {
            "messages": messages,
            "last_error": last_error,
            "error_count": error_count
        }

    print("[Node] lint_node: Lintチェック合格！")
    return {}

def test_node(state: AgentState):
    print("\n[Node] test_node 実行開始...")
    test_files = glob.glob("workspace/**/test_*.py", recursive=True) + glob.glob("workspace/**/*_test.py", recursive=True)
    if not test_files:
        print("[Node] test_node: テストファイルが見つからないためスキップします。")
        return {}
        
    print("[Node] test_node: Dockerサンドボックス内でテストを実行中...")
    
    workspace_dir = os.path.abspath("workspace")
    
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{workspace_dir}:/workspace",
        "-w", "/workspace",
        "ghcr.io/astral-sh/uv:python3.12-bookworm-slim",
        "bash", "-c",
        "uv pip install --system pytest && if [ -f requirements.txt ]; then uv pip install --system -r requirements.txt; fi && pytest ."
    ]
    
    result = subprocess.run(docker_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        full_output = result.stdout + "\n" + result.stderr
        stdout = full_output[:1000] + "\n...(省略)" if len(full_output) > 1000 else full_output
        error_msg = f"テストが失敗しました:\n{stdout}\n修正してください。"
        print("[Node] test_node: テスト失敗！エラーをフィードバックします。")
        
        messages = state["messages"].copy()
        error_count = state.get("error_count", 0)
        last_error = state.get("last_error", "")
        
        if error_msg == last_error:
            error_count += 1
        else:
            error_count = 1
            last_error = error_msg
            
        messages.append({"role": "user", "content": error_msg})
        return {
            "messages": messages,
            "last_error": last_error,
            "error_count": error_count
        }
        
    print("[Node] test_node: テスト合格！")
    return {}

def summarize_node(state: AgentState):
    print("\n[Node] summarize_node 実行開始...")
    messages = state["messages"].copy()
    
    if len(messages) <= 2:
        return {}
        
    history_messages = messages[2:]
    
    summary_prompt = [
        {"role": "system", "content": "あなたはAIコーディングアシスタントの履歴要約エージェントです。以下のやり取りを読み、「どのようなコード変更を試みたか」「どのようなエラーが発生したか」「どう対処しようとしたか」を簡潔に（500文字程度で）要約してください。"},
        {"role": "user", "content": f"【これまでの履歴】\n" + "\n".join([f"{m.get('role', '')}: {m.get('content', '')}" for m in history_messages])}
    ]
    
    print("[Node] summarize_node: LLMに要約を依頼中...")
    try:
        summary_text = call_llm(summary_prompt)
    except Exception as e:
        print(f"[Node] summarize_node: 要約に失敗しました - {e}")
        summary_text = "要約の生成に失敗しました。"
    
    workspace_path = Path(os.path.abspath("workspace"))
    current_workspace = get_workspace_context(workspace_path, include_contents=True)
    
    new_user_content = (
        "【これまでの試行錯誤の要約】\n"
        f"{summary_text}\n\n"
        "【最新のワークスペース状況】\n"
        f"{current_workspace}\n\n"
        "上記を踏まえ、引き続きタスクを解決してください。"
    )
    
    new_messages = [
        messages[0],
        messages[1],
        {"role": "user", "content": new_user_content}
    ]
    
    print("[Node] summarize_node: コンテキストを圧縮・リフレッシュしました！")
    return {"messages": new_messages}

def route_after_llm(state: AgentState):
    print("[Route] route_after_llm 判定中...")
    if state.get("error_count", 0) >= 3:
        print("  -> エラー3回連続のため human_help へ")
        return "human_help"
        
    actions = state.get("current_actions", [])
    
    # 書き込みアクションがある場合は review または execute へ
    if any(a.get("action") in ["write", "read"] for a in actions):
        if state.get("require_approval", False) and any(a.get("action") == "write" for a in actions):
            print("  -> 承認必須のため review へ")
            return "review"
        print("  -> 実行のため execute へ")
        return "execute"
        
    # 実行対象がなく done のみの場合
    if any(a.get("action") == "done" for a in actions):
        print("  -> 完了フラグのため END へ")
        return END
        
    print("  -> フォールバック: execute へ")
    return "execute"
    
def route_after_review(state: AgentState):
    print("[Route] route_after_review 判定中...")
    actions = state.get("current_actions", [])
    if not actions:
        print("  -> アクションが空になったため llm へ")
        return "llm"
    print("  -> 承認されたため execute へ")
    return "execute"

def route_after_execute(state: AgentState):
    print("[Route] route_after_execute 判定中...")
    print("  -> lint へ")
    return "lint"

def route_after_lint(state: AgentState):
    print("[Route] route_after_lint 判定中...")
    if state.get("error_count", 0) > 0 and state.get("last_error", "").startswith("Lintエラー"):
        if state.get("error_count", 0) >= 3:
            print("  -> Lintエラー3回連続のため human_help へ")
            return "human_help"
        print("  -> Lintエラーがあるため差し戻し")
        if len(state.get("messages", [])) >= 10:
            return "summarize"
        return "llm"
    print("  -> test へ")
    return "test"

def route_after_test(state: AgentState):
    print("[Route] route_after_test 判定中...")
    if state.get("error_count", 0) >= 3:
        print("  -> エラー3回連続のため human_help へ")
        return "human_help"
        
    # エラーが無く、LLMが done を宣言していたら終了
    if state.get("error_count", 0) == 0:
        actions = state.get("current_actions", [])
        if any(a.get("action") == "done" for a in actions):
            print("  -> テスト合格・完了フラグありのため END へ！")
            return END
            
    print("  -> エラー修正 または 次のステップのため差し戻し")
    if len(state.get("messages", [])) >= 10:
        return "summarize"
    return "llm"

def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("llm", llm_node)
    builder.add_node("review", review_node)
    builder.add_node("execute", execute_node)
    builder.add_node("lint", lint_node)
    builder.add_node("test", test_node)
    builder.add_node("summarize", summarize_node)
    builder.add_node("human_help", human_help_node)
    
    builder.add_edge(START, "llm")
    builder.add_conditional_edges("llm", route_after_llm)
    builder.add_conditional_edges("review", route_after_review)
    builder.add_conditional_edges("execute", route_after_execute)
    builder.add_conditional_edges("lint", route_after_lint)
    builder.add_conditional_edges("test", route_after_test)
    builder.add_edge("summarize", "llm")
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

def update_progress(state: AgentState, node_name: str, path="graph.md"):
    try:
        with open(path, "r") as f:
            content = f.read()
        
        parts = content.split("```\n", 1)
        if len(parts) > 0:
            mermaid_part = parts[0] + "```\n"
        else:
            mermaid_part = ""

        task = state.get("task", "")
        error_count = state.get("error_count", 0)
        messages = state.get("messages", [])
        
        log_text = "\n---\n## 🔄 現在のステータス\n"
        log_text += f"- **タスク**: {task}\n"
        log_text += f"- **最後に完了したノード**: `{node_name}`\n"
        log_text += f"- **連続エラー回数**: {error_count}\n\n"
        log_text += "### 📝 最新のログ\n"
        
        for msg in messages[-3:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if len(content) > 300:
                content = content[:300] + "\n...(省略)"
            
            icon = "🤖" if role == "assistant" else "👤"
            log_text += f"**{icon} {role}**:\n```\n{content}\n```\n\n"

        with open(path, "w") as f:
            f.write(mermaid_part + log_text)

    except Exception as e:
        print(f"進捗更新エラー: {e}")
