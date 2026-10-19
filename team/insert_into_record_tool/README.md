
# Insert Into Record Tool

## Overview

This tool is part of the Fair Fairness Benchmark (FFB) VIP team's evaluation-metrics workflow.

It provides a Python interface for updating, validating, saving, and loading evaluation metric records created by the team's `initialize_metrics_record_tool`.

The tool also integrates with the team's LangChain/Ollama agent, allowing a local Qwen model to request updates to an active evaluation metrics record.

The tool does not calculate evaluation metrics or train machine-learning models. It manages existing metric values.

## Features

- Update values of previously initialized metrics
- Validate metric names and numerical values
- Reject unknown metrics and invalid values
- Save metric records to JSON files
- Load and validate previously saved records
- Prevent accidental overwriting of existing JSON files
- Integrate with the team's existing metric record initializer
- Expose metric updates through a LangChain-compatible tool
- Support agent-initiated updates with local Ollama/Qwen

## Project Structure

```text
team/
├── agent/
│   └── basic_agent.py
└── insert_into_record_tool/
    ├── __init__.py
    ├── insert_into_record.py
    ├── langchain_tool.py
    ├── README.md
    └── tests/
        ├── test_insert_into_record.py
        └── test_langchain_tool.py
```

The repository root also contains a local `metrics_record.json` file when a sample or active metrics record has been created. This file is ignored by Git.

## Requirements

- Python 3.10 or newer for the record-management implementation
- Python 3.12 for the current agent environment
- Dependencies from the existing evaluation-metrics tool
- LangChain tool dependencies
- Ollama and the `qwen3:4b` model for live agent execution

Install the existing project dependencies from the repository root:

```bash
python -m pip install -r team/eval_metrics_tool/requirements.txt
python -m pip install -r team/agent/requirements.txt
```

Activate the agent virtual environment if it already exists:

```bash
source .venv-agent/bin/activate
```

## Core Python Usage

All examples should be executed from the repository root.

### 1. Create a metrics record

```python
from team.insert_into_record_tool import MetricsRecord

record = MetricsRecord({
    "Accuracy": 92.0,
    "F1": None,
    "Demographic Parity": 10.5
})
```

The record contains metric names as keys and numerical values as values.

`None` indicates that a metric does not yet have an assigned value.

The numbers shown in these examples are illustrative and are not verified FFB research results.

### 2. Update an existing metric

```python
record.insert_into_record("F1", 0.87)

print(record.record)
```

Expected output:

```python
{
    "Accuracy": 92.0,
    "F1": 0.87,
    "Demographic Parity": 10.5
}
```

Updates modify the record held in memory.

Only previously initialized metric names can be updated.

### 3. Save the record to JSON

```python
record.save_json("metrics.json")
```

This creates a JSON file containing the current metric values.

By default, the tool does not overwrite an existing file.

To intentionally overwrite an existing file:

```python
record.save_json("metrics.json", overwrite=True)
```

### 4. Load an existing record

```python
loaded = MetricsRecord.load_json("metrics.json")

print(loaded.record)
```

The loaded record is validated before it can be used.

### 5. Integration with the existing initializer

The tool works with records returned by Team 2's `initialize_metrics_record_tool`.

```python
from team.initialize_metrics_record_tool import initialize_metrics_record
from team.insert_into_record_tool import MetricsRecord

initialized = initialize_metrics_record(
    "paper.pdf",
    ["Accuracy", "F1"]
)

record = MetricsRecord(initialized)

record.insert_into_record("F1", 0.90)

record.save_json("updated_metrics.json")
```

This demonstrates how an initialized paper-metrics record can be updated and saved.

The initializer uses heuristic extraction, so its reported values may require manual verification against the paper.

## Validation and Error Handling

The tool validates metric names and numerical values before updating records.

| Situation | Behavior |
| --- | --- |
| Existing metric with valid numeric value | Updates the record |
| Unknown metric name | Raises `KeyError` |
| Empty or whitespace-only metric name | Raises `ValueError` |
| Non-numeric value | Raises `TypeError` |
| Boolean value | Raises `TypeError` |
| NaN or infinity | Raises `ValueError` |
| Missing JSON file | Raises `FileNotFoundError` |
| Malformed JSON file | Raises `JSONDecodeError` |
| Invalid values in loaded record | Raises `TypeError` or `ValueError` |
| Saving to an existing file without overwrite permission | Raises `FileExistsError` |

Only initialized metric names can be updated. The tool does not automatically introduce new metrics into a record.

## LangChain Agent Integration

The metrics record updater is exposed to LangChain through:

`team/insert_into_record_tool/langchain_tool.py`

The `update_metric_record` tool accepts two arguments:

- `metric`: the name of an existing evaluation metric
- `value`: the new numerical value

When invoked, the tool:

1. Checks whether an active metrics record exists.
2. Loads the record from `metrics_record.json` in the repository root.
3. Validates the metric name and numerical value.
4. Calls the existing `MetricsRecord.insert_into_record()` implementation.
5. Saves the updated record to JSON.
6. Returns a success message or an error message.

The tool uses the original record-management implementation rather than duplicating its validation and insertion logic.

### LangChain tool registration

The tool is registered in `team/agent/basic_agent.py` alongside the existing reproduction-script listing tool.

```python
agent = create_deep_agent(
    model=model,
    tools=[
        list_reproduction_scripts,
        update_metric_record
    ],
    system_prompt=(
        "You are an assistant for the Fair Fairness Benchmark repository. "
        "Use list_reproduction_scripts to answer questions about reproduction scripts. "
        "Use update_metric_record when explicitly asked to update a metric in "
        "the active evaluation record. Never invent metric values or update "
        "records without a user request."
    ),
)
```

The agent uses the local `qwen3:4b` model through Ollama.

The model chooses an appropriate registered tool based on the user's request. The Python tool performs the actual record update and persistence.

### Create a sample active record

From the repository root:

```bash
python -c 'from team.insert_into_record_tool import MetricsRecord; MetricsRecord({"Accuracy": 92.0, "F1": None}).save_json("metrics_record.json")'
```

This creates an example record.

If the file already exists, `save_json()` raises a `FileExistsError` to prevent accidental overwriting.

### Direct LangChain invocation

The tool can be tested without running Ollama:

```python
from team.insert_into_record_tool.langchain_tool import update_metric_record

result = update_metric_record.invoke({
    "metric": "F1",
    "value": 0.87
})

print(result)
```

Expected response:

```text
Successfully updated F1 to 0.87.
```

### Running the Qwen agent

Start the Ollama server:

```bash
ollama serve
```

In a separate terminal, run:

```bash
ollama list
```

Make sure the `qwen3:4b` model is installed.

If necessary:

```bash
ollama pull qwen3:4b
```

Run the existing agent from the repository root:

```bash
python -m team.agent.basic_agent
```

The demonstration in `basic_agent.py` currently asks the agent to list available reproduction scripts.

To manually test a metric update through Qwen, the demonstration user message can be changed to:

```python
"Use update_metric_record to update F1 to 0.91 in the active metrics record."
```

After execution, inspect the saved record:

```bash
cat metrics_record.json
```

A successful local demonstration updated the sample F1 value from `0.87` to `0.91`, and the new value was confirmed in the JSON file.

The demonstration uses sample values, not actual experimental results.

## Testing

The project includes automated tests for both the original record-management implementation and the new LangChain integration.

Run the tests from the repository root:

```bash
python -m unittest discover -s team/insert_into_record_tool/tests -v
```

The test suite contains 18 tests:

### Core record-management tests (14)

- Updating an existing metric
- Rejecting unknown metrics
- Rejecting string values
- Rejecting NaN values
- Saving and loading JSON records
- Rejecting infinity
- Rejecting Boolean values
- Rejecting empty metric names
- Preserving unrelated metric values
- Handling missing JSON files
- Handling corrupted JSON files
- Rejecting invalid values in loaded records
- Preventing accidental overwrites
- Integrating with the existing metric initializer

### LangChain integration tests (4)

- Successfully updating and persisting a metric through the LangChain wrapper
- Handling a missing active record
- Rejecting updates to unknown metrics
- Rejecting invalid numerical values without modifying the saved record

The integration tests use temporary directories and mocked record paths.

They do not require a running Ollama server.

Separate manual testing is used to confirm that Qwen can select and invoke the tool through the LangChain agent.

## Current Limitations

- Only existing metric names can be updated.
- The active record must already exist before the LangChain update tool is invoked.
- The agent currently uses one fixed JSON record path.
- Updates are stored in memory until saved.
- The tool validates numerical values but does not independently verify their scientific accuracy.
- JSON storage does not support concurrent updates or atomic file replacement.
- The live agent requires Ollama and an available local Qwen model.
- The demonstration is not yet an interactive user interface.
- The current workflow does not automatically reproduce ML experiments.

## Remaining Work

The core record updater and initial LangChain integration have been implemented.

Potential future improvements include:

1. Supporting multiple evaluation records and selecting an active record.
2. Connecting the paper-metric initializer directly to the agent workflow.
3. Tracking metric provenance, including the source paper, table, method, and experiment.
4. Adding automated tests for the complete model-driven agent workflow.
5. Improving persistence safety with atomic file writes and concurrency handling.
6. Supporting interactive user requests without editing the agent demonstration code.

## Team Workflow

This tool builds on the existing `insert_eval_metric()` helper in `initialize_metrics_record_tool`.

The helper performs dictionary updates, while `MetricsRecord` adds validation, record management, JSON persistence, and a tested interface.

The LangChain wrapper exposes that interface to the local Qwen agent, which can invoke the updater when explicitly requested.

This provides a foundation for integrating research-paper metric extraction, record initialization, record updating, and future experiment reproduction workflows.
