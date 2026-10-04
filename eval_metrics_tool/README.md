# eval_metrics

Rule-based (no LLMs, no network) extraction of the most important evaluation
metrics a research paper PDF reports. Output is deterministic.

## Install

```bash
pip install -r requirements.txt        # runtime: pdfplumber (MIT)
pip install -r requirements-dev.txt    # adds pytest, reportlab for tests
```

## Usage

```python
from eval_metrics import extract_eval_metrics
extract_eval_metrics("paper.pdf", top_k=5)   # ["F1", "Accuracy", "BLEU"]
```

Returns canonical names only, most important first, or `[]` if none are found.
Raises `FileNotFoundError` for a missing file and `eval_metrics.PDFReadError`
for a file that is not a readable PDF.

```bash
python -m eval_metrics paper.pdf --top-k 5     # one metric per line
python -m eval_metrics paper.pdf --verbose     # + score and where it was found
```

Run both from this directory (`eval_metrics_tool/`).

## How it works

1. `extraction.py` reads page text and tables with pdfplumber
   (`page.extract_text()`, `page.extract_tables()`), splits the text into
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

Extraction and scoring are separate: `rank_metrics(PaperContent(...))` works on
plain strings and lists, so most tests need no PDFs.

## Adding a metric

Append a `MetricSpec` to `METRICS` in `eval_metrics/metrics_dictionary.py`.
Patterns are regexes without word boundaries (added automatically):

- `patterns`: case-insensitive, for full names ("mean squared error").
- `cs_patterns`: case-sensitive, for distinctive acronyms ("BLEU").
- `context_patterns`: case-sensitive and context-gated, for short or ambiguous acronyms.

Then add an alias test in `tests/test_matcher.py`.

## Tests

```bash
python -m pytest
```

## Known limitations

- Scanned / image-only PDFs are not supported (no OCR); they yield `[]`.
- Two-column layouts may scramble text order, which can break heading and caption detection.
- Only ruled tables are detected (pdfplumber's default). Borderless
  "booktabs"-style tables are missed as tables, though their text still counts as prose.
- Table text also appears in the page text, so table mentions are partly counted twice.
- Metrics referred to only by symbols or nonstandard names are missed.
- Words like "precision" or "recall" in a non-metric sense can still slip through despite basic filters.
- Section detection is heading-regex based and imperfect; a missed "Related Work" heading means its metrics count.
