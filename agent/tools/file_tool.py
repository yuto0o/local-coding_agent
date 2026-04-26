from pathlib import Path

BASE = Path("workspace")

def _clean_path(path):
    path_str = str(path)
    if path_str.startswith("workspace/"):
        return path_str[len("workspace/"):]
    return path_str

def read_file(path):
    return (BASE / _clean_path(path)).read_text()

def write_file(path, content):
    target_path = BASE / _clean_path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)