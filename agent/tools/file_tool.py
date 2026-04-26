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
    (BASE / _clean_path(path)).write_text(content)