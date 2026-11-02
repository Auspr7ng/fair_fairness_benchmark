"""Run the local FFB agent with paper-metric and optional metric-record tools."""

import argparse
import os
import httpx
from ollama import ResponseError
import sys
from pathlib import Path

from deepagents import create_deep_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from team.agent.paper_tools import find_eval_metrics
from team.agent.initialization_tool import create_initialization_tool
from team.insert_into_record_tool.langchain_tool import create_record_tools


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
    tools = [list_reproduction_scripts, find_eval_metrics]
    if record_path is not None:
        record_path = Path(record_path).expanduser().resolve(strict=True)
        tools.extend(create_record_tools(record_path))
        tools.append(create_initialization_tool(record_path.resolve()))
    if model is None:
        model = ChatOllama(model=os.environ.get("FFB_AGENT_MODEL", "qwen3:4b"),
                           base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"), temperature=0)
    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=(
            "You are an assistant for the Fair Fairness Benchmark repository. "
            "Call list_reproduction_scripts before answering questions about available experiments. "
            "When asked which evaluation metrics a paper reports, call find_eval_metrics with the PDF path "
            "and say whether the names came from the LLM or the dictionary fallback. "
            "When a metric record is selected, use show_current_record to inspect it. "
            "When explicitly asked to initialize the selected record from a paper, call "
            "initialize_current_record with the discovered metric names. "
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

    try:
        agent = build_agent(args.record)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"error: agent setup failed: {exc}\n")
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": args.prompt}]})
    except (ConnectionError, OSError, httpx.HTTPError, ResponseError) as exc:
        parser.exit(1, f"error: agent model unavailable: {exc}. Start Ollama or configure "
                       "OLLAMA_HOST/FFB_AGENT_MODEL. For extraction without an agent, run "
                       "python -m team.paper_pipeline PAPER --output RECORD --no-llm.\n")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()

