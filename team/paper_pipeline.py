"""Run paper -> metric names -> initialized JSON without needing an agent server."""
import argparse
import json
from pathlib import Path

from team.eval_metrics_tool.eval_metrics import extract_paper, select_metrics, PDFReadError
from team.initialize_metrics_record_tool import initialize_metrics_record
from team.insert_into_record_tool import MetricsRecord


def run_pipeline(paper, output, *, metrics=None, model=None, use_llm=True,
                 top_k=5, row_label=None, overwrite=False):
    """Persist one record and return provenance separately from numeric values."""
    if metrics is None:
        content = extract_paper(str(paper))
        if not any(section.text.strip() for section in content.sections):
            raise ValueError("No extractable PDF text; OCR or a text PDF is required")
        selection = select_metrics(content, top_k=top_k, model=model, use_llm=use_llm)
        metrics, source, note = selection.names, selection.source, selection.reason
    else:
        source, note = 'supplied', None
    if not metrics:
        raise ValueError("No metric names found; supply --metric names or review PDF extraction")
    record = initialize_metrics_record(str(paper), metrics=metrics, row_label=row_label)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    MetricsRecord(record).save_json(output, overwrite=overwrite)
    return {'record': str(output), 'source': source, 'note': note, 'metrics': record,
            'unresolved': [name for name, value in record.items() if value is None]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paper', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--metric', action='append', dest='metrics')
    parser.add_argument('--model')
    parser.add_argument('--no-llm', action='store_true')
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--row-label')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = run_pipeline(args.paper, args.output, metrics=args.metrics, model=args.model,
                              use_llm=not args.no_llm, top_k=args.top_k,
                              row_label=args.row_label, overwrite=args.overwrite)
    except (OSError, ValueError, TypeError, PDFReadError) as exc:
        parser.exit(1, f'error: {exc}\n')
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
