import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

def get_workspace_context(base_path: Path, include_contents: bool = True) -> str:
    if not base_path.exists() or not base_path.is_dir():
        return "ワークスペースがありません"
    
    tree_lines = []
    file_contents = []
    allowed_exts = {'.py', '.txt', '.md', '.json'}
    
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        rel_root = Path(root).relative_to(base_path.parent)
        level = len(rel_root.parts) - 1
        indent = '  ' * level
        tree_lines.append(f"{indent}{rel_root.name}/")
        subindent = '  ' * (level + 1)
        for f in files:
            if not f.startswith('.'):
                tree_lines.append(f"{subindent}{f}")
                
                if include_contents and Path(f).suffix in allowed_exts:
                    f_path = Path(root) / f
                    try:
                        content = f_path.read_text(encoding='utf-8')
                        file_contents.append(f"\n--- {rel_root / f} ---\n{content}\n")
                    except Exception:
                        pass
    
    context = "\n".join(tree_lines)
    if include_contents and file_contents:
        context += "\n\n【ファイル内容】\n" + "".join(file_contents)
        
    return context

def plan(task: str, include_file_contents: bool = True) -> list[dict]:
    system_path = BASE_DIR / "agent" / "prompts" / "system.txt"
    coding_path = BASE_DIR / "agent" / "prompts" / "coding.txt"
    workspace_path = BASE_DIR / "workspace"
    
    system_prompt = system_path.read_text(encoding="utf-8") if system_path.exists() else "JSON配列で出力してください。"
    coding_prompt = coding_path.read_text(encoding="utf-8") if coding_path.exists() else ""
    
    workspace_context = get_workspace_context(workspace_path, include_file_contents)
    
    user_prompt = f"{coding_prompt}\n\n【現在のワークスペース状況】\n{workspace_context}\n\n【タスク】\n{task}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]