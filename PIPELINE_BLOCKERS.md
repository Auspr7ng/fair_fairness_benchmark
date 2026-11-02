# Pipeline continuation fixes

These changes target execution/handoff blockers; paper-extraction accuracy is a separate concern.

## Paper -> persisted record without an agent

From the repository root, after installing `team/eval_metrics_tool/requirements.txt`:

```bash
python -m team.paper_pipeline paper.pdf --output results/paper-record.json --no-llm
python -m team.paper_pipeline paper.txt --output results/custom-record.json --metric 'mean flip rate (mFR)'
```

The response identifies dictionary/model/supplied provenance and lists unresolved values. The saved file retains the existing flat metric-to-value format, so record readers/updaters can use it unchanged. Parent directories are created; an existing record is protected unless `--overwrite` is supplied. Empty/scanned PDFs with no extractable text fail before creating a misleading empty record. No OCR is added.

## Optional agent step

```bash
python team/agent/basic_agent.py --record results/paper-record.json --prompt 'Show the selected record'
```

`OLLAMA_HOST` selects the reachable server; `FFB_AGENT_MODEL` selects the agent model (default `qwen3:4b`). Extractor model configuration remains separate (`EVAL_METRICS_MODEL`). Connection/model errors produce a short diagnostic and point to the deterministic paper pipeline. This does not provide a missing server or download model weights.

When explicitly requested, the new `initialize_current_record` tool can replace the already selected record using a paper and supplied metric names. Its output lists unresolved fields. The record must exist and validate at agent startup; create it with the paper pipeline first. No experiment execution tool is added.

## Evaluation and persistence

`metric_evaluation` now returns `None` for unsupported/undefined scores instead of crashing or emitting NaN. Remaining scores can still be saved. Consumers must support nullable values; `print_metrics` renders them as `NA`. Invalid/misaligned input still raises a descriptive ValueError. Raw individual metric helpers retain their legacy behavior; use the aggregate evaluation entry point for this handling.

Metric records are serialized to a temporary file, flushed and atomically installed. Failed writes preserve the last complete record. Concurrent writers are not serialized; locking/version checks remain future work.

## Training entry points

```bash
python ffb/benchmark/benchmark_tabular.py --dataset_path /data/adult --method diffdp --dry-run --num_training_steps 2
```

The former legacy stub dispatches to the existing `ffb_tabular_erm.py` or `ffb_tabular_diffdp.py`, forwarding data/attribute arguments and extra trainer options. Both target trainers now honor the supplied data path rather than ignoring it in favor of hardcoded directories. Run without `--dry-run` only with the trainer's dependencies, dataset and logging configuration prepared. `--num_epochs`, `--mlp_arch`, dropout and weight-decay options from the old incomplete helper are not translated to unrelated trainer concepts; use options supported by the selected trainer (such as `--num_training_steps` and `--mlp_layers`).

CelebA runners now reject empty data and nonpositive/nonfinite training settings, and consistently stratify on target/group. Single-group DiffDP batches train only the classifier and increment `skipped_fairness_batches` in the output; no group contrast is invented. Rare strata can still make a requested split infeasible; supply adequate data. Missing datasets/dependencies remain external prerequisites.

## Tests

```bash
python -m pytest -q
```

Root configuration resolves both package import paths and runs `team/` plus `ffb/tests/`. FFB metric regressions require statsmodels/NumPy/sklearn/SciPy; when unavailable they skip explicitly. Training/GPU tests and live-model inference require additional setup. The single-group torch training branch has not been executed in the audit environment because torch is unavailable.

Not addressed in this patch: inequality-to-exact-value mistakes, unit/context metadata, broad PDF layout recovery, parser strictness, model quality, training-to-paper comparison and concurrent record-update arbitration.
