from pathlib import Path

BASE = Path("workspace")

def read_file(path):
    return (BASE / path).read_text()

def write_file(path, content):
    (BASE / path).write_text(content)