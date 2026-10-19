"""Run the local FFB agent with optional metric-record tools."""

import argparse
import sys
from pathlib import Path

from deepagents import create_deep_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from team.agent.record_tools import create_record_tools


@tool
def list_reproduction_scripts() -> str:
    """List the available Python reproduction scripts in the FFB repository."""
    reproduce_folder = REPO_ROOT / "ffb" / "reproduce"
    scripts = sorted(file.name for file in reproduce_folder.glob("*.py"))
    if not scripts:
        return "No reproduction scripts were found."
    return "\n".join(scripts)


def build_agent(record_path: Path | None = None, model=None):
    """Create an agent whose record tools are bound to one selected JSON file."""
    tools = [list_reproduction_scripts]
    if record_path is not None:
        tools.extend(create_record_tools(record_path))
    if model is None:
        model = ChatOllama(model="qwen3:4b", temperature=0)
    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=(
            "You are an assistant for the Fair Fairness Benchmark repository. "
            "Call list_reproduction_scripts before answering questions about available experiments. "
            "When a metric record is selected, use show_current_record to inspect it. "
            "Call update_metric only when the user explicitly supplies both a metric name and a value. "
            "Never invent a metric value, and report tool errors instead of claiming an update succeeded."
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, help="JSON record to expose to the agent")
    parser.add_argument(
        "--prompt",
        default="Use the repository tool and tell me which reproduction experiments are available.",
        help="Question or instruction for the agent",
    )
    args = parser.parse_args()

    agent = build_agent(args.record)
    result = agent.invoke({"messages": [{"role": "user", "content": args.prompt}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
