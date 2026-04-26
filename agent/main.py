import argparse
from agent.planner import plan
from agent.graph import build_graph, save_graph_image, update_progress

def run():
    parser = argparse.ArgumentParser(description="AI Coding Agent")
    parser.add_argument('--require-approval', action='store_true', help="Require human approval before writing files")
    args = parser.parse_args()

    task = input(">> ")
    messages = plan(task)

    graph = build_graph()
    save_graph_image(graph, "graph.md")

    initial_state = {
        "task": task,
        "messages": messages,
        "current_actions": [],
        "last_error": "",
        "error_count": 0,
        "require_approval": args.require_approval
    }

    current_state = initial_state.copy()
    try:
        for output in graph.stream(initial_state, config={"recursion_limit": 100}):
            for node_name, update in output.items():
                if update:
                    current_state.update(update)
                update_progress(current_state, node_name, "graph.md")
    except Exception as e:
        print(f"Agent stopped: {e}")

if __name__ == "__main__":
    run()