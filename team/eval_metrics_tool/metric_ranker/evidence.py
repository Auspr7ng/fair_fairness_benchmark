"""Conservative, inspectable rules for whether a mention reports a result.

These rules are not a general language-understanding system. Keep rejected
contexts local to a clause so negating BLEU does not also discard a reported F1.
"""
import re
from dataclasses import dataclass

from team.eval_metrics_tool.metric_matcher.matcher import Match
from team.eval_metrics_tool.section_splitter import RESULTS

_BREAK = re.compile(
    r"(?<!et al\.)(?<=[.!?;])\s+|\s+(?:but(?!\s+also)|whereas|while|however)\s+"
    r"|,\s*(?=(?:we\b|our\b|prior\b|earlier\b|previous\b))"
    r"|\s+and\s+(?=(?:we\s+)?(?:report|evaluate|measure|minimi[sz]e|optimi[sz]e|train)\b)",
    re.I,
)
_REPORT = re.compile(
    r"\b(?:report(?:s|ed|ing)?|measur(?:e[ds]?|ing)|evaluat(?:e[ds]?|ing|ion)|"
    r"assess(?:ed|ing)?|achiev(?:e[ds]?|ing)|obtain(?:ed|s)?|scor(?:e[ds]?|ing)|"
    r"metric(?:s)?|performance|improv(?:e[ds]?|ing))\b", re.I,
)
_OWN = re.compile(r"\b(?:we|our|this (?:paper|work|study|model))\b", re.I)
_OWN_REPORT = re.compile(
    r"\bwe\s+(?:(?:also|explicitly|actually|directly|further)\s+)*"
    r"(?:report\w*|measur\w*|evaluat\w*|achiev\w*|obtain\w*|assess\w*|use|used|get)\b"
    r"|\bour\s+(?:evaluation\s+)?(?:metrics?|results?|scores?)\b"
    r"|\bour\s+(?:model|method|system|approach)\s+(?:reports?|achieves?|obtains?|scores?|improves?)\b",
    re.I,
)
_OTHER_WORK = re.compile(
    r"\b(?:prior|previous|earlier|other|existing|related)\s+"
    r"(?:(?:\w+[- ]?){0,2}\s+)?(?:work|author|stud(?:y|ies)|research|method|system|model|paper)s?\b"
    r"|\bet\s+al\b|\baccording to\b|\b(?:baseline|competitor)\s+(?:reports?|achieves?)\b",
    re.I,
)
_CITATION = re.compile(r"\[\d+(?:[\s,;\u2013-]+\d+)*\]")
_NEGATED_USE = re.compile(
    r"\b(?:not|never|no longer)\s+(?:(?:explicitly|actually|directly|also)\s+)?"
    r"(?:report\w*|use[ds]?|using|measur\w*|evaluat\w*|includ\w*|comput\w*|calculat\w*|available)\b"
    r"|\b(?:don't|doesn't|didn't|can't|cannot|won't)\s+"
    r"(?:report\w*|use[ds]?|measur\w*|evaluat\w*|includ\w*)\b"
    r"|\b(?:exclude[ds]?|exclud(?:ing|ed)|omit(?:ted|s|ting)?)\b", re.I,
)
_NOT_REPORTED = re.compile(
    r"^\s*(?:results?\s+|scores?\s+)?(?:is|are|was|were|has been|have been)?\s*"
    r"(?:not\s+(?:reported|used|measured|evaluated|available)|unreported|unused|unavailable|omitted)\b",
    re.I,
)
_PASSIVE_NEGATION = re.compile(
    r"\b(?:is|are|was|were|has been|have been)\s+not\s+"
    r"(?:reported|used|measured|evaluated|available)\b"
    r"|\b(?:is|are|was|were)\s+(?:omitted|excluded|unreported|unavailable)\b",re.I,
)
_LOSS = re.compile(r"\b(?:loss(?:es)?|objective|minimi[sz]\w*|optimi[sz]\w*)\b", re.I)
_EVALUATION = re.compile(r"\b(?:eval(?:uation)?|evaluat\w*|test(?:ing)?|held[- ]out|validation|benchmark)\b", re.I)
_BACKGROUND = re.compile(r"\b(?:background|hypothetical|for illustration|not (?:an?|the|our) (?:evaluation )?metric)\b", re.I)
_NOT_FOR_EVAL = re.compile(
    r"\bnot\s+(?:(?:used|reported|measured|evaluated)\s+)?(?:for|on|in|during)\s+"
    r"(?:evaluation|test(?:ing)?|validation)\b",re.I,
)
_PREVIOUS_USE = re.compile(r"\bwe\s+(?:previously|formerly|earlier)\s+(?:report\w*|measur\w*|evaluat\w*)\b",re.I)
_NON_METRIC_PRECISION = re.compile(r"\bprecision\s+(?:machining|engineering|instruments?|microscopes?)\b", re.I)
_VALUE = re.compile(r"^\s*(?:[:=]|of\b|is\b|was\b|at\b|score(?:\s+of)?\b)?\s*[-+]?\d+(?:\.\d+)?\s*%?")


@dataclass(frozen=True)
class MetricEvidence:
    text: str
    matched_name: str
    section: str
    location: str
    reported: bool
    basis: str
    page: int | None = None
    row: int | None = None
    column: int | None = None


def use_evidence(text: str, match: Match, section: str, location: str,
                 *, page=None, row=None, column=None,
                 table_has_values: bool = False) -> MetricEvidence | None:
    """Accepted evidence, or None for an explicitly irrelevant/negated use.

    A bare background mention may be retained for rank_metrics inspection,
    with reported=False. It is excluded by select_metrics from normal output.
    """
    lo, hi = 0, len(text)
    for boundary in _BREAK.finditer(text):
        if boundary.end() <= match.start:
            lo = boundary.end()
        elif boundary.start() >= match.end:
            hi = boundary.start()
            break
    clause = text[lo:hi].strip()
    prefix = text[lo:match.start]
    suffix = text[match.end:hi]
    own_report = bool(_OWN.search(clause) and _REPORT.search(clause))
    value = bool(_VALUE.match(suffix))
    if (_NEGATED_USE.search(prefix) or _NOT_REPORTED.search(suffix)
            or _PASSIVE_NEGATION.search(clause)):
        return None
    if re.search(r"\bwithout\s+(?:(?:using|reporting|measuring|evaluating)\s+)?(?:any\s+)?$",prefix,re.I):
        return None
    if re.search(r"\b(?:not|rather than|instead of)\s*$",prefix,re.I):
        return None
    if re.search(r"\bno\s+(?:results?\s+(?:for|on)\s+)?$",prefix,re.I):
        return None
    own_claim = bool(_OWN_REPORT.search(clause) or (_OWN.search(clause) and value))
    if (_OTHER_WORK.search(clause) or _CITATION.search(clause)) and not own_claim:
        return None
    if _LOSS.search(clause) and (not _EVALUATION.search(clause) or _NOT_FOR_EVAL.search(clause)):
        return None
    if _PREVIOUS_USE.search(clause):
        return None
    if _BACKGROUND.search(clause) and not own_claim:
        return None
    if match.metric == "Precision" and _NON_METRIC_PRECISION.search(clause):
        return None
    is_table = location.startswith("table_")
    reported = table_has_values if is_table else (
        own_report or value or section == RESULTS or location == "caption"
    )
    if is_table and reported:
        basis = "table with values"
    elif own_report:
        basis = "report statement"
    elif value:
        basis = "reported value"
    else:
        basis = "results context" if reported else "unconfirmed mention"
    return MetricEvidence(clause, match.text, section, location, reported,
                          basis, page, row, column)
