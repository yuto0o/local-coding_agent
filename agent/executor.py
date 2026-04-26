from agent.tools.file_tool import read_file, write_file

def execute(action):
    if action["action"] == "read":
        return read_file(action["path"])

    elif action["action"] == "write":
        path = action.get("path", "")
        write_file(path, action["content"])
        return "ok"

    else:
        raise Exception("不明なaction")