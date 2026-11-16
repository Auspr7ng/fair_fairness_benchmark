"""Heading-based section splitting, and assembling pages into a structured paper."""

import re
from dataclasses import dataclass, field

# Section kinds. Anything not recognised is "other".
ABSTRACT, INTRO, RELATED, METHOD, RESULTS, CONCLUSION, REFERENCES, OTHER = (
    "abstract", "introduction", "related_work", "method", "results",
    "conclusion", "references", "other",
)

_NUM = r"(?:(?:\d+(?:\.\d+)*|[IVX]+)\.?\s+)?"
# An appendix title is a few plain words ("Appendix B: Modeling Details"), so a
# wrapped sentence ("Appendix D for details). We also ...") is not a heading.
_APPENDIX = (r"appendix(?:\s+(?-i:[A-Z])(?:\.\d+)*\b)?"
             r"(?:\s*[:.—–-]?\s+(?-i:[A-Z])[\w-]+(?:\s+[\w-]+){0,8})?")
_RESULT_WORD = (r"(?:experiments?|experimental\s+(?:results|evaluation|setup|settings?)"
                r"|results?|evaluations?|empirical\s+(?:results|evaluation)|main results"
                r"|discussion|analysis)")
_HEADINGS = [
    (ABSTRACT, r"abstract"),
    (INTRO, r"introduction"),
    (RELATED, r"(?:related\s+works?|literature\s+review|prior\s+work|previous\s+work)"),
    (METHOD, r"(?:methods?|methodology|approach|proposed\s+(?:method|approach|model)"
             r"|model|problem\s+(?:formulation|setup|statement)|preliminaries)"),
    (RESULTS, _RESULT_WORD + r"(?:\s*(?:and|&)\s*" + _RESULT_WORD + r")?"),
    (CONCLUSION, r"(?:conclusions?(?:\s+and\s+future\s+work)?|concluding\s+remarks"
                 r"|limitations|future\s+work)"),
    (REFERENCES, r"(?:references|bibliography)"),
    (OTHER, r"(?:" + _APPENDIX + r"|appendices|supplementary\s+\w+(?:\s+[\w-]+){0,6})"),
]
_HEADING_RES = [(kind, re.compile(rf"^\s*{_NUM}{pat}\s*[:.]?\s*$", re.I))
                for kind, pat in _HEADINGS]
# "Abstract—We propose..." / "Abstract. We ..." on a single line.
_INLINE_ABSTRACT = re.compile(r"^\s*abstract\s*[—–:.\-]+\s*\S", re.I)
# Two-column PDFs can place a short equation fragment before the heading in
# the adjacent column (e.g. "i n 5. Experiments"). Accept only single-letter
# fragments and a complete numbered result heading, not prose mentioning it.
_COLUMN_RESULTS = re.compile(
    rf"^(?:[A-Za-z]\s+){{1,6}}\d+(?:\.\d+)*\.?\s+{_RESULT_WORD}\s*[:.]?\s*$",
    re.I,
)
# A bibliography heading can share a line with the other column's citation.
_COLUMN_REFERENCES = re.compile(r"^\s*(?:references|bibliography)\s+\[\d+\](?:\s|$)", re.I)


@dataclass
class Section:
    kind: str
    heading: str
    text: str
    start: int  # character offsets into the full text
    end: int


@dataclass
class Table:
    rows: list[list[str]]
    section: str = OTHER  # section kind the table's page mostly belongs to
    page: int = 0


@dataclass
class PaperContent:
    sections: list[Section]
    tables: list[Table] = field(default_factory=list)


def classify_heading(line: str) -> str | None:
    if _COLUMN_REFERENCES.match(line):
        return REFERENCES
    if len(line) > 70:
        return None
    if _COLUMN_RESULTS.match(line):
        return RESULTS
    if _INLINE_ABSTRACT.match(line):
        return ABSTRACT
    for kind, regex in _HEADING_RES:
        if regex.match(line):
            return kind
    return None


def split_sections(text: str) -> list[Section]:
    """Split ``text`` into sections; falls back to one "other" section."""
    sections: list[Section] = []
    kind, heading, start = OTHER, "", 0
    pos = 0
    for line in text.splitlines(keepends=True):
        found = classify_heading(line.strip())
        if found is not None:
            if pos > start:
                sections.append(Section(kind, heading, text[start:pos], start, pos))
            kind, heading, start = found, line.strip(), pos
        pos += len(line)
    if pos > start or not sections:
        sections.append(Section(kind, heading, text[start:pos], start, pos))
    return sections


def build_paper(pages) -> PaperContent:
    """Split a list of pages into sections and tag each table with its section.

    Each page needs ``.text`` and ``.tables`` (see ``pdf_reader.PdfPage``).
    """
    full_text = "\n".join(page.text for page in pages)
    sections = split_sections(full_text)

    # Attribute each page's tables to the section covering most of that page.
    tables: list[Table] = []
    offset = 0
    for i, page in enumerate(pages):
        lo, hi = offset, offset + len(page.text)
        offset = hi + 1
        if not page.tables:
            continue
        kind = max(sections, key=lambda s: max(0, min(hi, s.end) - max(lo, s.start))).kind
        tables.extend(Table(rows=t, section=kind, page=i + 1) for t in page.tables if t)
    return PaperContent(sections=sections, tables=tables)

