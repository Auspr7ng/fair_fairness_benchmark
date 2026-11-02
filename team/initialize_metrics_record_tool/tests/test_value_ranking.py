"""Candidate ranking must not mistake duplicate snippets for independent evidence."""

import unittest

from team.initialize_metrics_record_tool.evidence import VALUE_WEIGHTS, _Evidence
from team.initialize_metrics_record_tool.value_ranking import _rank_values


class ValueRankingTests(unittest.TestCase):
    def test_duplicate_snippets_do_not_increase_support(self):
        item = _Evidence('F1', 0.87, 5.0, 'F1 = 0.87', ())
        self.assertEqual(_rank_values([item], VALUE_WEIGHTS),
                         _rank_values([item, item], VALUE_WEIGHTS))

    def test_independent_support_wins_and_nonpositive_evidence_is_ignored(self):
        items = [
            _Evidence('F1', 0.87, 5.0, 'Results: F1 = 0.87', ()),
            _Evidence('F1', 0.87, 5.0, 'Summary: F1 = 0.87', ()),
            _Evidence('F1', 0.80, 5.0, 'Baseline: F1 = 0.80', ()),
            _Evidence('Accuracy', 99.0, -1.0, 'Unreliable evidence', ()),
        ]
        ranked = _rank_values(items, VALUE_WEIGHTS)
        self.assertEqual([value for value, score in ranked['F1']], [0.87, 0.80])
        self.assertGreater(ranked['F1'][0][1], ranked['F1'][1][1])
        self.assertNotIn('Accuracy', ranked)
