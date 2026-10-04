"""PDF -> structured content (sections of text, plus tables). No scoring here."""

import os
from dataclasses import dataclass, field

import pdfplumber

from .sections import OTHER, Section, split_sections


class PDFReadError(Exception):
    """The file exists but could not be read as a PDF."""


@dataclass
class Table:
    rows: list[list[str]]
    section: str = OTHER  # section kind the table's page mostly belongs to
    page: int = 0


@dataclass
class PaperContent:
    sections: list[Section]
    tables: list[Table] = field(default_factory=list)


def _clean(cell) -> str:
    return " ".join((cell or "").split())


def extract_paper(pdf_path: str) -> PaperContent:
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    page_texts: list[str] = []
    page_tables: list[list[list[list[str]]]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_texts.append(page.extract_text() or "")
                try:
                    tables = page.extract_tables()
                except Exception:  # a bad table must not sink the whole paper
                    tables = []
                page_tables.append([[[_clean(c) for c in row] for row in t] for t in tables])
    except Exception as exc:
        raise PDFReadError(f"Could not read {pdf_path!r} as a PDF: {exc}") from exc

    full_text = "\n".join(page_texts)
    sections = split_sections(full_text)

    # Attribute each page's tables to the section covering most of that page.
    tables: list[Table] = []
    offset = 0
    for i, (text, found) in enumerate(zip(page_texts, page_tables)):
        lo, hi = offset, offset + len(text)
        offset = hi + 1
        if not found:
            continue
        kind = max(sections, key=lambda s: max(0, min(hi, s.end) - max(lo, s.start))).kind
        tables.extend(Table(rows=t, section=kind, page=i + 1) for t in found if t)
    return PaperContent(sections=sections, tables=tables)
