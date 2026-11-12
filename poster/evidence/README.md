# Four-PDF execution check — November 12, 2026

The JSON records a deterministic extraction check using current repository code, `select_metrics(..., top_k=5, use_llm=False)`. Inputs are the four local course PDFs; SHA-256 checksums identify their exact versions.

All four returned extractable text and nonempty metric-name candidates. Counts are capped by top_k and do not measure precision, recall, value correctness, or whole-paper consistency. Candidate names can include false positives or omit unfamiliar measures. No live LLM calls or full agent tasks were run.

The earlier user-reported four-paper agreement statement is superseded in the poster by this bounded, reproducible check. The historical comparison ZIP targets another code branch and is not a current-version accuracy result.

To reproduce from the repository root with extractor dependencies installed:

```python
from pathlib import Path
from team.eval_metrics_tool.eval_metrics import extract_paper, select_metrics

for pdf in sorted(Path("../paper").glob("*.pdf")):
    paper = extract_paper(str(pdf))
    selection = select_metrics(paper, top_k=5, use_llm=False)
    print(pdf.name, any(section.text.strip() for section in paper.sections), selection.names)
```
