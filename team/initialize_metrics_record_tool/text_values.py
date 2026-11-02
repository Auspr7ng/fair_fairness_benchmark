"""Find reported metric values in paper prose."""

import math
import re

from team.eval_metrics_tool.eval_metrics.matcher import find_metrics
from .evidence import _NUMBER, _Evidence, _context_features, _section_features

_NUMBERS = re.compile(rf'(?<![\w.])(?P<value>{_NUMBER})(?!\w|\.\d)\s*(?P<percent>%)?')
_DIRECT = re.compile(r'^\s*(?:(?:score|value)\s*)?(?:[:=]|(?:of|is|was|at)\b)?\s*$', re.I)
_COUNT = re.compile(r'^\s*(?:samples?|examples?|epochs?|parameters?|participants?|datasets?|runs?|iterations?)\b', re.I)
_DELTA = re.compile(r'\b(?:improv\w*|increas\w*|decreas\w*|gain\w*|reduc\w*)\s+(?:\w+\s+){0,3}(?:by|of)\s*$', re.I)
# Sentence punctuation, excluding decimal points. Do not require PDF headings.
_SENTENCE_BREAK = re.compile(r'(?<=[!?;])\s+|(?<!\d)\.\s+|(?<=\d)\.(?!\d)\s+')


def _crawl_text(paper, wanted, weights, window):
    evidence = []
    for section in paper.sections:
        for sentence in _SENTENCE_BREAK.split(section.text):
            # Joining line wraps lets indirect wording span PDF lines.
            text = ' '.join(sentence.split())
            mentions = find_metrics(text, context_given=True)
            numbers = [n for n in _NUMBERS.finditer(text)
                       if not any(n.start() < m.end and n.end() > m.start
                                  for m in mentions)]
            for index, number in enumerate(numbers):
                # ± values are uncertainty, not independent metric results.
                if re.search(r'(?:±|\+/-)\s*$', text[:number.start()]):
                    continue
                distances = [(max(m.start - number.end(), number.start() - m.end, 0), m)
                             for m in mentions]
                if not distances:
                    continue
                distance, mention = min(distances, key=lambda pair: pair[0])
                if distance > window or mention.metric not in wanted:
                    continue
                after = number.start() >= mention.end
                bridge = (text[mention.end:number.start()] if after
                          else text[number.end():mention.start])
                # Local cues stop at the previous/next value, so baseline cues
                # do not automatically contaminate another model's result.
                lo = numbers[index - 1].end() if index else max(0, number.start() - window)
                hi = numbers[index + 1].start() if index + 1 < len(numbers) else min(len(text), number.end() + window)
                local = text[lo:number.end()] if after else text[number.start():hi]
                if after and mention.start >= lo:
                    local = text[lo:number.end()]
                features = _section_features(section.kind) + _context_features(local)
                direct = bool(_DIRECT.fullmatch(bridge)) if after else not bridge.strip()
                if direct:
                    features.append('direct_statement')
                value = float(number.group('value'))
                if not math.isfinite(value):
                    continue
                prefix = text[max(0, number.start() - 100):number.start()]
                suffix = text[number.end():]
                if prefix.count('[') > prefix.count(']'):
                    features.append('citation')
                if (1900 <= value <= 2100 and value.is_integer()
                        or _COUNT.match(suffix)):
                    features.append('year_or_count')
                if _DELTA.search(prefix) or re.match(r'\s*(?:percentage\s+points?|points?)\b', suffix, re.I):
                    features.append('delta')
                proximity = weights['proximity'] * math.exp(-distance / 40.0)
                score = proximity + sum(weights[f] for f in features)
                evidence.append(_Evidence(mention.metric, value, score, text,
                                          tuple(['proximity'] + features)))
    return evidence
