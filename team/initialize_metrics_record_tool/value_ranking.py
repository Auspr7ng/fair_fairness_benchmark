"""Combine repeated evidence and rank candidate values per metric."""

import math
from collections import defaultdict


def _rank_values(evidence, weights):
    """Aggregate support without letting duplicated snippets dominate."""
    grouped = defaultdict(dict)
    for item in evidence:
        if item.score <= 0:
            continue
        contexts = grouped[(item.metric, item.value)]
        contexts[item.context] = max(contexts.get(item.context, 0), item.score)
    ranked = defaultdict(list)
    for (metric, value), contexts in grouped.items():
        scores = sorted(contexts.values(), reverse=True)
        # Repetition contributes sublinearly and is discounted by evidence strength.
        support = sum(min(score / max(scores[0], 1), 1) for score in scores[1:])
        score = scores[0] + weights['repeat_support'] * math.log1p(support)
        ranked[metric].append((value, score))
    for values in ranked.values():
        values.sort(key=lambda pair: (-pair[1], pair[0]))
    return ranked
