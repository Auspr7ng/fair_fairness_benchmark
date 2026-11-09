"""Find reported metric values in ruled tables and selected plain-text rows."""

import math
import re

from team.eval_metrics_tool.metric_matcher import find_requested_metrics, normalize_metric
from .evidence import _NUMBER, _Evidence, _context_features, _section_features

_NUMERIC_CELL = rf'(?P<value>{_NUMBER})(?:\s*%)?(?:\s*(?:±|\+/-)\s*{_NUMBER}(?:\s*%)?)?(?:\s*[*†‡]+)?'
_CELL = re.compile(_NUMERIC_CELL)
_ROW_CELL = re.compile(rf'(?:{_NUMERIC_CELL}|n/?a|[-–—]+)(?=\s|$)', re.I)
_PDF_MARKS = re.compile(r'(?:\s*\(cid:\d+\))+\s*$')
_ROW_HEADERS = {'method', 'model', 'dataset', 'senattr'}
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
                number = _CELL.fullmatch(cell.strip())
                if number and math.isfinite(value := float(number.group('value'))):
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
    found = False
    label = re.compile(
        r'^\s*' + r'\s+'.join(map(re.escape, row_label.split())) + r'\s+',
        re.I,
    )
    for section in paper.sections:
        if section.kind == 'references':
            continue
        headers = []
        header_line = -100
        for line_number, line in enumerate(section.text.splitlines()):
            match = label.match(line)
            if match and headers and line_number - header_line <= 40:
                # Parse every cell, including missing values, so later values
                # cannot slide left. PDF extraction can append glyph marks.
                row = _PDF_MARKS.sub('', line[match.end():])
                cells = []
                while row:
                    cell = _ROW_CELL.match(row)
                    if not cell:
                        break
                    cells.append(cell.group('value'))
                    row = row[cell.end():].lstrip()
                if row or len(cells) != len(headers):
                    continue
                found = True
                context = line.strip()
                features = ['table_alignment'] + _section_features(section.kind)
                score = sum(weights[f] for f in features)
                for metric, cell in zip(headers, cells):
                    if metric in wanted and cell is not None and math.isfinite(value := float(cell)):
                        evidence.append(_Evidence(metric, value, score, context, tuple(features)))
                continue
            tokens = line.split()
            while tokens and tokens[0].casefold() in _ROW_HEADERS:
                tokens.pop(0)
            recognized = [(_TABLE_HEADERS.get(token.lower()) or normalize_metric(token))
                          for token in tokens]
            known = sum(name is not None for name in recognized)
            if known and known >= len(tokens) - 2:
                headers = recognized
                header_line = line_number
    return evidence, found

