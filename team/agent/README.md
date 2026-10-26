# Local LangChain Agent

This is a basic LangChain Deep Agent for the Fair Fairness Benchmark (FFB) repository. It uses a local Qwen model through Ollama. It can list reproduction scripts, list the evaluation metrics a paper PDF reports, and, when given a JSON metric record, read and update that selected record.

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

## Find a paper's evaluation metrics

```bash
python team/agent/basic_agent.py --prompt "Which evaluation metrics does /path/to/paper.pdf report?"
```

The agent calls `find_eval_metrics` (in `paper_tools.py`), which runs the extractor in `team/eval_metrics_tool/`. The reply is JSON with the metric names and a `source` of `llm` or `dictionary`. A dictionary reply also has a `note` that explains why the LLM was not used. A missing or unreadable PDF returns an `error` instead.

The extractor's LLM is separate from the agent's Qwen model. It comes from `EVAL_METRICS_MODEL` and your provider's API key, set in your shell or a `.env` file; see the [extractor README](../eval_metrics_tool/README.md#choosing-a-model). Without them, the tool uses the dictionary ranking.

## Work with a metric record

Create a record with the initializer, or use an existing JSON record whose keys are metric names:

```bash
python -m team.initialize_metrics_record_tool paper.pdf --metric F1 --metric Accuracy > metrics.json
python team/agent/basic_agent.py --record metrics.json --prompt "Show the current metric record"
python team/agent/basic_agent.py --record metrics.json --prompt "Update F1 to 0.90"
```

`team/agent/requirements.txt` includes the extractor's dependencies, which the paper initializer also needs. Reading or updating an existing JSON record uses the updater under `team/insert_into_record_tool/`.

The `--record` path is chosen when the agent starts. Its `show_current_record` and `update_metric` tools are bound to that file; the model cannot supply a different path to either tool. Unknown metrics and invalid values return an error without changing the file. The agent instructions tell it to update only when the user provides both a metric and a value.

## Tests

Run the paper-tool and record-tool tests without starting Ollama:

```bash
python -m unittest discover -s team/agent/tests -v
```

These tests also run the real DeepAgents graph with a scripted model. In one test it calls `find_eval_metrics`; in another it reads the record, updates it, and reads back the persisted value. They verify failed updates, preservation of another record, and that the paper tool reports errors and fallbacks instead of raising. The paper-tool tests never read your `.env`. This checks integration, not Qwen’s ability to choose the right tool. A live model run still requires Ollama and `qwen3:4b`.
