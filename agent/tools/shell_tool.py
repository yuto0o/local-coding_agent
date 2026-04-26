import subprocess

def run_command(cmd):
    if "rm" in cmd or "sudo" in cmd:
        raise Exception("危険コマンド")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout