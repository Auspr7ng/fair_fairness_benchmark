"""Model input includes results when available and excludes references otherwise."""

from eval_metrics import experiments_section, llm_text
from eval_metrics.extraction import PaperContent
from eval_metrics.sections import split_sections


def test_results_sections_are_selected_instead_of_background_and_references():
    paper = PaperContent(split_sections(
        "Introduction\nBackground discussion.\n"
        "Experiments\nWe report accuracy.\n"
        "Results\nWe also report F1.\n"
        "References\nOther work reports BLEU.\n"
    ))
    text = llm_text(paper)
    assert text == experiments_section(paper)
    assert "We report accuracy." in text
    assert "We also report F1." in text
    assert "Background discussion." not in text
    assert "Other work reports BLEU." not in text


def test_body_fallback_excludes_references_and_empty_papers_stay_empty():
    paper = PaperContent(split_sections(
        "Introduction\nWe measure accuracy.\n"
        "References\nOther work reports BLEU.\n"
    ))
    assert experiments_section(paper) == ""
    assert "We measure accuracy." in llm_text(paper)
    assert "Other work reports BLEU." not in llm_text(paper)
    assert llm_text(PaperContent([])) == ""
