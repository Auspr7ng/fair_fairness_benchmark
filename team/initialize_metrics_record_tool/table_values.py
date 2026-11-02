"""Find reported metric values in ruled tables and selected plain-text rows."""

import math
import re

from team.eval_metrics_tool.eval_metrics.matcher import find_metrics, find_requested_metrics, normalize_metric
from .evidence import _NUMBER, _Evidence, _context_features, _section_features

_CELL = re.compile(rf'^\s*({_NUMBER})\s*%?(?:\s*(?:±|\+/-)\s*{_NUMBER}\s*%?)?\s*[*†‡]*\s*$')
_TABLE_VALUE = re.compile(
    rf'(?<![\w.])(?P<value>{_NUMBER})(?:\s*(?:±|\+/-)\s*{_NUMBER})?\s*%?(?!\w)'
)
# Common compact headers in ML result tables, including FFB Table 4. The
# teammate's matcher deliberately treats short acronyms more conservatively in
# prose, so table header aliases are handled here without changing that rule.
_TABLE_HEADERS = {
    'acc': 'Accuracy', 'auc': 'AUC', 'ap': 'mAP', 'f1': 'F1',
    'dp': 'Demographic Parity', 'abcc': 'ABCC', 'prule': 'p%-rule',
    'eodd': 'Equalized Odds', 'eopp': 'Equal Opportunity',
}



def _crawl_tables(paper, wanted, weights, row_label):
    evidence = []
    found = False
    for table in paper.tables:
        headers = {}
        for row in table.rows:
            labels = {}
            values = {}
            for col, cell in enumerate(row):
                matches = find_requested_metrics(cell, wanted)
                if len(matches) == 1:
                    labels[col] = matches[0].metric
                number = _CELL.fullmatch(cell)
                if number and math.isfinite(value := float(number.group(1))):
                    values[col] = value
            selected = row_label is None or any(
                cell.strip().casefold() == row_label.strip().casefold() for cell in row)
            found |= selected and row_label is not None
            if selected:
                context = ' | '.join(row)
                features = ['table_alignment'] + _section_features(table.section) + _context_features(context)
                score = sum(weights[f] for f in features)
                pairs = [(headers[col], value) for col, value in values.items() if col in headers]
                if len(labels) == 1 and len(values) == 1:
                    label_col, metric = next(iter(labels.items()))
                    value_col, value = next(iter(values.items()))
                    if value_col > label_col:
                        pairs.append((metric, value))
                for metric, value in pairs:
                    if metric in wanted:
                        evidence.append(_Evidence(metric, value, score, context, tuple(features)))
            if labels and not values:
                # A repeated header starts a new block, not a stale merge.
                headers = labels
    return evidence, found


def _crawl_unruled_table_row(paper, wanted, weights, row_label):
    """Read a selected row when PDF extraction leaves a table as plain text.

    A preceding whitespace-separated metric header supplies the column order.
    The caller must specify the row label: guessing a row from a paper with
    several datasets or methods would produce an arbitrary baseline.
    """
    evidence = []
    label = re.compile(
        r'^\s*' + r'\s+'.join(map(re.escape, row_label.split())) + r'\s+(?=[-+]?\d)',
        re.I,
    )
    for section in paper.sections:
        if section.kind == 'references':
            continue
        headers = []
        header_line = -100
        for line_number, line in enumerate(section.text.splitlines()):
            tokens = line.strip().split()
            recognized = [(_TABLE_HEADERS.get(token.lower()) or normalize_metric(token))
                          for token in tokens]
            recognized = [name for name in recognized if name]
            if recognized and len(recognized) >= len(tokens) - 2:
                headers = recognized
                header_line = line_number
                continue
            match = label.match(line)
            if not match or not headers or line_number - header_line > 40:
                continue
            values = [float(m.group('value')) for m in _TABLE_VALUE.finditer(line[match.end():])]
            if len(values) < len(headers):
                continue
            context = line.strip()
            features = ['table_alignment'] + _section_features(section.kind)
            score = sum(weights[f] for f in features)
            for metric, value in zip(headers, values):
                if metric in wanted and math.isfinite(value):
                    evidence.append(_Evidence(metric, value, score, context,
                                              tuple(features)))
    return evidence

