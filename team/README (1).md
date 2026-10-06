# eval_metrics

Rule-based (no LLMs, no network) extraction of the most important evaluation
metrics a research paper PDF reports. Output is deterministic.

## Install

```bash
pip install -r requirements.txt        # runtime: pdfplumber (MIT)
pip install -r requirements-dev.txt    # optional test dependencies
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

Run both from `team/eval_metrics_tool/`.

## Metric records: weighted text crawling

```python
from eval_metrics import create_eval_metrics_record, insert_eval_metric

# Crawl the paper and initialize the most important metric values.
record = create_eval_metrics_record("paper.pdf", top_k=5)

# Or pass extract_eval_metrics' output / your own metric list.
record = create_eval_metrics_record("paper.pdf", ["F1", "Accuracy"])
insert_eval_metric(record, "F1", 0.91)

# Optionally tune weights and selection thresholds.
record = create_eval_metrics_record(
    "paper.pdf", ["F1", "Accuracy"],
    weights={"our_method": 3.0, "repeat_support": 2.5},
    min_score=4.0, min_margin=1.0,
)
```

The initializer accepts PDFs and UTF-8 `.txt` papers. It crawls every section,
joins wrapped lines, recognizes metric aliases, and gathers numeric candidates
within a configurable character window (default 140). It does not require
standard headings or direct statements such as `F1 = 0.87`. Headings supply
optional context weights; unknown sections remain eligible.

Candidate values are associated with the nearest recognized metric mention.
Simple table headers and metric row labels provide additional alignment
signals. Numbers embedded in metric names, such as `F1` and `Recall@10`, and
uncertainty terms following `±` are excluded from candidate values.

### Default evidence weights

| Feature | Contribution |
|---|---:|
| Proximity to metric | `4 * exp(-distance / 40)` |
| Direct metric/value statement | +3 |
| Result wording (achieved, measured, reported, etc.) | +3 |
| Our/proposed method wording | +2 |
| Table header/row alignment | +5 |
| Results section hint | +1 |
| Abstract/conclusion hint | +0.5 |
| Baseline/prior method wording | −3 |
| Related-work section hint | −3 |
| References section hint | −6 |
| Citation number | −6 |
| Likely year/sample count | −5 |
| Improvement amount / percentage points | −5 |

For each metric/value pair, duplicate contexts are collapsed. Aggregate score
is the strongest evidence score plus `2 * log(1 + support)`, where `support`
sums the relative strengths of other positive evidence contexts, each capped
at 1. Repetition therefore contributes sublinearly. `repeat_support` controls
the multiplier. All feature weights are defined in `records.py:VALUE_WEIGHTS`
and may be overridden through `weights`.

The highest-scoring value initializes each metric when its score meets
`min_score` and its lead over the next candidate meets `min_margin`.
Missing, weak, or closely competing values remain `None`. A comparison paper
can therefore initialize the proposed model's value without rejecting all
competing results. Optional `row_label="Our model"` explicitly restricts
extraction to table rows with that exact case-insensitive cell label.

This combines evidence frequency statistics with hand-selected weights; it is
not a trained statistical model, and scores are not calibrated probabilities.
Weights need validation against annotated papers from the target domain.
Percentages retain the paper's scale (`92%` becomes `92.0`); uncertainty is not
stored. Multiple datasets, metric variants, complex tables, severely scrambled
PDF text, and scanned pages can still require manual review. No OCR is used.

The insert function updates the dictionary in place and returns it. Repeated
inserts overwrite the previous value; unknown metric names raise `KeyError`.

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

When adding tests, include an alias case for the new pattern. A test suite is
not yet committed in this repository.

## Tests

Record extraction tests generate PDFs with prose and ruled tables. Run from
`team/eval_metrics_tool/` after installing the development requirements:

```bash
python -m unittest discover -s tests -v
```

Tests cover heading-free PDFs, indirect wording, repeated evidence, distractor
numbers, baseline comparisons, table row selection, adjustable weights, missing
values, plain-text input, and record updates.

## Known limitations

- Scanned / image-only PDFs are not supported (no OCR); they yield `[]`.
- Two-column layouts may scramble text order, which can break heading and caption detection.
- Only ruled tables are detected (pdfplumber's default). Borderless
  "booktabs"-style tables are missed as tables, though their text still counts as prose.
- Table text also appears in the page text, so table mentions are partly counted twice.
- Metrics referred to only by symbols or nonstandard names are missed.
- Words like "precision" or "recall" in a non-metric sense can still slip through despite basic filters.
- Section detection is heading-regex based and imperfect; a missed "Related Work" heading means its metrics count.
