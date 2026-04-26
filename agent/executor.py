from agent.tools.file_tool import read_file, write_file
from agent.tools.ast_guard import validate_code

def execute(action):
    if action["action"] == "read":
        return read_file(action["path"])

    elif action["action"] == "write":
        validate_code(action["content"])
        write_file(action["path"], action["content"])
        return "ok"

    else:
        raise Exception("不明なaction")