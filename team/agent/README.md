# Local LangChain Agent

This is a basic LangChain Deep Agent for the Fair Fairness Benchmark (FFB) repository. It uses a local Qwen model through Ollama. It can list reproduction scripts and, when given a JSON metric record, read and update that selected record.

## Requirements

- Python 3.12
- Ollama
- The `qwen3:4b` Ollama model

## Setup

Run these commands from the main `fair_fairness_benchmark` folder:

```bash
ollama pull qwen3:4b
python3 -m venv .venv-agent
source .venv-agent/bin/activate
python -m pip install -r team/agent/requirements.txt
```

## Run

Make sure Ollama is open, then run:

```bash
python team/agent/basic_agent.py
```

This runs the original reproduction-script demonstration. The agent is constructed only when the command runs, so importing `basic_agent.py` does not start Ollama.

## Work with a metric record

Create a record with the initializer, or use an existing JSON record whose keys are metric names:

```bash
python -m team.initialize_metrics_record_tool paper.pdf --metric F1 --metric Accuracy > metrics.json
python team/agent/basic_agent.py --record metrics.json --prompt "Show the current metric record"
python team/agent/basic_agent.py --record metrics.json --prompt "Update F1 to 0.90"
```

The paper initializer needs the dependencies in `team/eval_metrics_tool/requirements.txt`. Reading or updating an existing JSON record uses the updater under `team/insert_into_record_tool/`.

The `--record` path is chosen when the agent starts. Its `show_current_record` and `update_metric` tools are bound to that file; the model cannot supply a different path to either tool. Unknown metrics and invalid values return an error without changing the file. The agent instructions tell it to update only when the user provides both a metric and a value.

## Tests

Run the record-tool tests without starting Ollama:

```bash
python -m unittest discover -s team/agent/tests -v
```

These tests also run the real DeepAgents graph with a scripted model: read the record, update it, and read back the persisted value. They verify failed updates and preservation of another record. This checks integration, not Qwen’s ability to choose the right tool. A live model run still requires Ollama and `qwen3:4b`.
