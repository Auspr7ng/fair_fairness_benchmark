# eval_metrics

Extracts the most important evaluation metrics a research paper PDF reports.
The tool sends the paper's Experiments section to an LLM, or the whole paper
body (minus References) when no Experiments heading is found. Any provider works through [LiteLLM](https://docs.litellm.ai/docs/providers),
including local models via Ollama. No API key ships with this project; bring
your own, or use a local model. If no model is set or the call fails, it falls
back to a deterministic, rule-based dictionary ranking.

## Install

```bash
pip install -r requirements.txt        # runtime: pdfplumber (MIT), litellm (MIT), python-dotenv (BSD)
pip install -r requirements-dev.txt    # adds pytest, reportlab for tests
```

## Choosing a model

`model` / `--model` is a LiteLLM model string. It defaults to the
`EVAL_METRICS_MODEL` environment variable. LiteLLM reads keys from each
provider's usual environment variable.

| Provider | Model string | Setup |
|---|---|---|
| Ollama (local) | `ollama/qwen3:4b` | `ollama pull qwen3:4b`; no key. Remote host: `--api-base http://host:11434` |
| OpenAI | `gpt-4o-mini` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-haiku-5-5` | `ANTHROPIC_API_KEY` |
| Any OpenAI-compatible server (LM Studio, vLLM, ...) | `openai/<model>` | `--api-base http://host:port/v1` |

`--api-base` also defaults to `EVAL_METRICS_API_BASE`. You can pass `--api-key`,
but environment variables keep keys out of your shell history.

### Settings in a `.env` file

All of these variables (`EVAL_METRICS_MODEL`, `EVAL_METRICS_API_BASE`, provider
keys) can go in a `.env` file instead of your shell:

```bash
cp .env.example ../../.env     # repo root; already git-ignored
```

The tool loads the nearest `.env` found by walking up from the current
directory, then from the package folder. Precedence, highest first: the
`--model` / `--api-base` / `--api-key` flags (or Python arguments), then
variables already set in your shell, then `.env`. Never commit `.env`; commit
changes to `.env.example` instead.

## Usage

```python
from eval_metrics import extract_eval_metrics
extract_eval_metrics("paper.pdf", top_k=5, model="ollama/qwen3:4b")  # ["F1 score", "Accuracy"]
extract_eval_metrics("paper.pdf", use_llm=False)                     # dictionary only
```

Returns metric names, most important first, or `[]` if none are found. LLM
results use the paper's own wording (they are not normalized). The dictionary
fallback returns canonical names. When the tool falls back, it issues a
`UserWarning` that says why. Raises `FileNotFoundError` for a missing file and
`eval_metrics.PDFReadError` for a file that is not a readable PDF.

```bash
python -m eval_metrics paper.pdf --model ollama/qwen3:4b   # one metric per line
python -m eval_metrics paper.pdf --show-section            # print the text sent to the LLM
python -m eval_metrics paper.pdf --no-llm --verbose        # dictionary: + score and where found
```

Run both from `team/eval_metrics_tool/`.

## How it works

LLM path:

1. pdfplumber extraction and section splitting (below).
2. Choose the text to send (`llm_text`). This is the Experiments section: the
   text under headings that `sections.py` classifies as Experiments / Results /
   Evaluation (several such headings are joined). Many papers title their
   experiments by topic instead ("5 Benchmarking Current Fairness Methods").
   Without such a heading, every section except References is sent. If the
   PDF has no text at all, the dictionary fallback is used.
3. `llm.py` asks the model for a JSON array of the metrics the paper reports
   and parses it, ignoring `<think>` blocks from reasoning models. It asks for
   temperature 0. Models that reject that setting (Claude 5, OpenAI reasoning
   models) run at their default instead of failing.

Dictionary fallback:

1. `extraction.py` reads page text and tables with pdfplumber
   (`page.extract_text()`, `page.extract_tables()`). The word gap is set
   relative to font size (`X_TOLERANCE_RATIO`), because pdfplumber's fixed
   default glues words together in tightly set papers. It then splits the text into
   sections by heading heuristics (`sections.py`: Abstract, Introduction,
   Related Work, Method, Experiments/Results/Evaluation, Conclusion,
   References), and tags each table with the section its page mostly belongs to.
   Unrecognised text falls into an "other" section.
2. `matcher.py` finds metric mentions using `metrics_dictionary.py`. Matches use
   word boundaries; when patterns overlap the longest wins ("Top-1 accuracy" is
   not also "Accuracy"). Short ambiguous acronyms (EM, IS, R2, AP, ...) are
   case-sensitive and count in running text only when a number follows
   ("EM = 85.2"), or anywhere in a table.
3. `scoring.py` sums weights per canonical metric, sorts by score and breaks
   ties alphabetically. Weights live in the `WEIGHTS` dict at the top of that
   file (heuristic, meant to be tuned):

   | Where | Weight |
   |---|---|
   | Table header / column (or row) label | 5 |
   | Table cell, caption ("Table 1: ...") | 3 |
   | Abstract | 3 |
   | Experiments / Results / Evaluation | 2 |
   | Anywhere else | 1 |
   | References, Related Work (text and tables) | 0 |

Extraction and scoring are separate: `rank_metrics(PaperContent(...))` and
`experiments_section(PaperContent(...))` work on plain strings and lists, so most
tests need no PDFs. LLM tests use a fake `litellm` module (`tests/conftest.py`),
so they need no network or key.

## Adding a metric

Append a `MetricSpec` to `METRICS` in `eval_metrics/metrics_dictionary.py`.
Patterns are regexes without word boundaries (added automatically):

- `patterns`: case-insensitive, for full names ("mean squared error").
- `cs_patterns`: case-sensitive, for distinctive acronyms ("BLEU").
- `context_patterns`: case-sensitive and context-gated, for short or ambiguous acronyms.

When adding a metric, add an alias case for the new pattern to `tests/test_matcher.py`.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest          # from team/eval_metrics_tool/
```

The tests build small PDFs with reportlab and replace `litellm` with a fake, so
they need no network, API key or local model. They also never read your `.env`.

## Known limitations

- The LLM path is only as good as the model. Small local models may miss
  metrics or list ones from other papers. Use `--show-section` to check what it saw.
- When a paper has an Experiments heading, the LLM sees only that section.
  Metrics reported only in the abstract, or in a separately titled results
  section, are missed.
- Without an Experiments heading, the LLM sees the whole body, Related Work
  included. Small models may then list metrics from other papers.
- Text is sent with no length limit. A whole-body fallback is often 50–90k
  characters, which exceeds a small local model's context window (Ollama
  defaults to a few thousand tokens).
- Models that reject temperature 0 (Claude 5, OpenAI reasoning models) can
  return slightly different lists on different runs.

- Scanned / image-only PDFs are not supported (no OCR); they yield `[]`.
- Two-column layouts may scramble text order, which can break heading and caption detection.
- Only ruled tables are detected (pdfplumber's default). Borderless
  "booktabs"-style tables are missed as tables, though their text still counts as prose.
- Table text also appears in the page text, so table mentions are partly counted twice.
- Metrics referred to only by symbols or nonstandard names are missed.
- Words like "precision" or "recall" in a non-metric sense can still slip through despite basic filters.
- Section detection is heading-regex based and imperfect; a missed "Related Work" heading means its metrics count.

### Shared extraction decision

`select_metrics(content, ...)` owns the LLM-or-dictionary choice for the Python
API, CLI, and paper agent tool. Its result includes names, source, fallback
reason, and dictionary scores (for verbose CLI output). An empty successful LLM
result stays empty; only an unavailable or failed model triggers fallback.
