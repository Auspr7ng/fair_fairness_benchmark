"""Model input includes results when available and excludes references otherwise."""

from team.eval_metrics_tool.section_selector import experiments_section, llm_text
from team.eval_metrics_tool.section_splitter import PaperContent, split_sections


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


def test_two_column_heading_recovers_experiments_and_excludes_bibliography():
    # Actual heading shapes observed in the CVPR 2022 fingerprinting PDF.
    paper = PaperContent(split_sections(
        "Introduction\nBackground only.\n"
        "i n 5. Experiments\nEvaluation Metrics. We report the ROC curve and AUC.\n"
        "5.4. Resistance against Model Modifications\nAUC remains high.\n"
        "6. Discussion\nLimitations of our approach.\n"
        "References [14] Dorjan Hitaj and Luigi V. Mancini. Have you stolen my\n"
        "Other people's metrics.\n"
    ))
    text = llm_text(paper)
    assert "We report the ROC curve and AUC" in text
    assert "AUC remains high" in text
    assert "Background only" not in text
    assert "Have you stolen" not in text
    assert "Other people's metrics" not in text


def test_heading_recovery_does_not_treat_prose_as_a_heading():
    from team.eval_metrics_tool.section_splitter import classify_heading
    assert classify_heading("We discuss 5. Experiments") is None
    assert classify_heading("See references [14] for details") is None
    assert classify_heading("References to earlier experiments are useful.") is None

