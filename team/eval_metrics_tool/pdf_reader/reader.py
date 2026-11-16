"""PDF -> per-page text and tables. No section splitting or scoring here."""

import os
from dataclasses import dataclass

import pdfplumber

# Word gap as a fraction of font size. pdfplumber's default fixed 3pt gap glues
# words in tightly set papers ("averageprecision", "8 RelatedWork"). Passing
# x_tolerance_ratio=None to read_pdf keeps that default.
X_TOLERANCE_RATIO = 0.15


class PDFReadError(Exception):
    """The file exists but could not be read as a PDF."""


@dataclass
class PdfPage:
    text: str
    tables: list[list[list[str]]]  # each table is a list of rows of cleaned cells


def _clean(cell) -> str:
    return " ".join((cell or "").split())


def read_pdf(pdf_path: str,
             x_tolerance_ratio: float | None = X_TOLERANCE_RATIO) -> list[PdfPage]:
    """One PdfPage per page, in order.

    Raises FileNotFoundError if the file is missing and PDFReadError if it is
    not a readable PDF.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    pages: list[PdfPage] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance_ratio=x_tolerance_ratio) or ""
                try:
                    tables = page.extract_tables()
                except Exception:  # a bad table must not sink the whole paper
                    tables = []
                pages.append(PdfPage(text, [[[_clean(c) for c in row] for row in t] for t in tables]))
    except Exception as exc:
        raise PDFReadError(f"Could not read {pdf_path!r} as a PDF: {exc}") from exc
    return pages
