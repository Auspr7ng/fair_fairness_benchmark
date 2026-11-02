"""Shared value-evidence representation, weights, and context cues."""

import re
from dataclasses import dataclass

# Each feature's contribution can be overridden through the initializer.
_NUMBER = r'[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?'

VALUE_WEIGHTS = {
    'proximity': 4.0,          # exponentially decays with character distance
    'direct_statement': 3.0,  # e.g. "F1 = 0.87" or "92% accuracy"
    'result_cue': 3.0,        # achieved, obtained, reached, reported, ...
    'our_method': 2.0,        # our/proposed method; table row labeled Ours
    'table_alignment': 5.0,   # value aligned with a metric header/row label
    'results_section': 1.0,   # optional hint; unrecognized sections score normally
    'summary_section': 0.5,
    'baseline': -3.0,
    'related_work': -3.0,
    'references': -6.0,
    'citation': -6.0,
    'year_or_count': -5.0,
    'delta': -5.0,            # improvement amount rather than absolute result
    'repeat_support': 2.0,    # logarithmic bonus for independent repetitions
}

_RESULT = re.compile(r'\b(?:achiev\w*|obtain\w*|reach\w*|report\w*|yield\w*|scor\w*|measur\w*|evaluat\w*|record\w*|results?\s+(?:show|indicate|demonstrate))\b', re.I)
_OURS = re.compile(r'\b(?:ours|our(?:\s+\w+){0,3}|proposed(?:\s+(?:method|model|approach))?)\b', re.I)
_BASELINE = re.compile(r'\b(?:baseline|previous|prior|existing|competing|competitor)\b', re.I)

@dataclass(frozen=True)
class _Evidence:
    metric: str
    value: float
    score: float
    context: str
    features: tuple[str, ...]


def _section_features(kind):
    return {
        'results': ['results_section'],
        'abstract': ['summary_section'],
        'conclusion': ['summary_section'],
        'related_work': ['related_work'],
        'references': ['references'],
    }.get(kind, [])


def _context_features(text):
    features = []
    if _RESULT.search(text):
        features.append('result_cue')
    if _OURS.search(text):
        features.append('our_method')
    if _BASELINE.search(text):
        features.append('baseline')
    return features
