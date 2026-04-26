openclaw-coding-agent/
├── docker/
│   └── Dockerfile
├── agent/
│   ├── main.py
│   ├── planner.py
│   ├── executor.py
│   ├── validator.py
│   ├── tools/
│   │   ├── file_tool.py
│   │   ├── shell_tool.py
│   │   └── ast_guard.py
│   └── prompts/
│       ├── system.txt
│       └── coding.txt
├── config/
│   └── config.yaml
├── workspace/
│   └── (編集対象コード)
├── requirements.txt
└── run.sh

```
# ローカルの時
run.sh
# dockerの時
docker build -t claw-agent .
docker run -it claw-agent
``` 