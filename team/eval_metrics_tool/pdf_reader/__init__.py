"""PDF file -> per-page text and tables."""

from .reader import X_TOLERANCE_RATIO, PDFReadError, PdfPage, read_pdf

__all__ = ["X_TOLERANCE_RATIO", "PDFReadError", "PdfPage", "read_pdf"]
