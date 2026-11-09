"""Page text and tables -> a paper structured into sections. Needs no PDF library."""

from .sections import (ABSTRACT, CONCLUSION, INTRO, METHOD, OTHER, REFERENCES, RELATED, RESULTS,
                       PaperContent, Section, Table, build_paper, classify_heading, split_sections)

__all__ = [
    "ABSTRACT", "CONCLUSION", "INTRO", "METHOD", "OTHER", "REFERENCES", "RELATED", "RESULTS",
    "PaperContent", "Section", "Table", "build_paper", "classify_heading", "split_sections",
]
