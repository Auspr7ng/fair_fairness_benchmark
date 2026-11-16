"""Regression checks for metric meaning and evidence of reported use.

Positive controls are as important as exclusions: a sentence about another
metric, a citation, or a training loss must not erase genuine evaluation.
"""
import pytest
from team.eval_metrics_tool.metric_matcher import normalize_metric
from team.eval_metrics_tool.metric_ranker import rank_metrics
from team.eval_metrics_tool.metric_selector import select_metrics
from team.eval_metrics_tool.section_splitter import PaperContent,Table,split_sections


def paper(text,tables=()):
    return PaperContent(split_sections(text),list(tables))


def selected(text):
    return select_metrics(paper(text),use_llm=False).names


@pytest.mark.parametrize("alias,expected",[
    ("Top-1 error","Top-1 Error"),("top1 error rate","Top-1 Error"),
    ("Top-1 accuracy","Top-1 Accuracy"),("Top-5 error","Top-5 Error"),
    ("top5 error rate","Top-5 Error"),("top5 acc.","Top-5 Accuracy"),
    ("average precision","Average Precision"),("AP","Average Precision"),
    ("AP50","Average Precision"),("AP@0.75","Average Precision"),
    ("mean average precision","mAP"),("mAP","mAP"),("mAP@0.5:0.95","mAP"),
    ("worst-group error","Worst-Group Error"),("worst-group accuracy","Worst-Group Accuracy"),
    ("worst-group performance","Worst-Group Performance"),
    ("robust error rate","Robust Error"),("robust accuracy","Robust Accuracy"),
    ("certified radius","Certified Radius"),
])
def test_preserves_metric_meaning(alias,expected):
    assert normalize_metric(alias)==expected


@pytest.mark.parametrize("text",[
    "We do not report BLEU.","We never report BLEU.","We don't report BLEU.",
    "We did not evaluate BLEU.","We exclude BLEU from our evaluation.",
    "We omit BLEU.","Our evaluation proceeds without BLEU.",
    "BLEU is not reported.","No BLEU results are available.",
    "F1 and BLEU are not reported.",
    "Earlier work reports BLEU = 35.","Previous authors measured BLEU = 35.",
    "Smith et al. report BLEU = 35.","Smith [12] reports BLEU = 35.",
    "According to [2], BLEU is 35.","We discuss earlier work's BLEU metric.",
    "We minimize MSE as the training loss.","Our training loss is MSE = 0.3.",
    "We use MSE as our optimization objective.",
    "BLEU is discussed as background.","Precision machining was used to make the test rig.",
    "We use MSE as a training loss, not for evaluation.",
    "MSE is the training loss and is not reported on the test set.",
    "We previously reported BLEU = 35.",
    "BLEU was excluded.",
])
def test_explicit_non_result_uses_are_excluded(text):
    assert selected("Experiments\n"+text)==[]


@pytest.mark.parametrize("text,expected",[
    ("We do not report BLEU. We report F1 = 0.91.",["F1"]),
    ("We do not report BLEU but we report F1 = 0.91.",["F1"]),
    ("Earlier work reports BLEU = 35, whereas we report F1 = 0.91.",["F1"]),
    ("Earlier work reports BLEU = 35; our model achieves accuracy = 90%.",["Accuracy"]),
    ("We minimize MSE as the training loss and evaluate MAE = 0.2.",["MAE"]),
    ("We report F1 without retraining.",["F1"]),
    ("Without extra tuning, we report F1 = 0.91.",["F1"]),
    ("We report not only BLEU but also F1.",["BLEU","F1"]),
    ("We report F1 = 0.91, compared with Smith [12].",["F1"]),
    ("Our F1 = 0.91 exceeds earlier work [2].",["F1"]),
    ("We report MSE on the held-out test set.",["MSE"]),
    ("Our evaluation metric is MSE, also used as a training loss.",["MSE"]),
    ("We report average precision = 0.8 and mAP = 0.7.",["Average Precision","mAP"]),
    ("We report Top-1 error = 5% and Top-1 accuracy = 95%.",["Top-1 Accuracy","Top-1 Error"]),
    ("We report F1 but not BLEU.",["F1"]),
    ("We report F1, not BLEU.",["F1"]),
    ("We report F1 rather than BLEU.",["F1"]),
    ("We report F1 instead of BLEU.",["F1"]),
    ("We report F1 without BLEU.",["F1"]),
    ("We report not just BLEU but also F1.",["BLEU","F1"]),
    ("We previously reported BLEU but we report F1 here.",["F1"]),
])
def test_retains_genuine_results_in_mixed_context(text,expected):
    assert selected("Experiments\n"+text)==expected


def test_repeated_unconfirmed_mentions_do_not_win_or_fill_results():
    text="Introduction\n" + "BLEU is important.\n"*30 + "Experiments\nWe report accuracy = 90%."
    result=select_metrics(paper(text),use_llm=False)
    assert result.names==["Accuracy"]
    candidates=rank_metrics(paper(text))
    assert candidates[0].name=="Accuracy"
    assert next(s for s in candidates if s.name=="BLEU").reported is False


def test_bare_background_is_inspectable_but_not_returned_as_reported():
    text="Introduction\nAccuracy is an important topic."
    assert selected(text)==[]
    assert rank_metrics(paper(text))[0].evidence[0].basis=="unconfirmed mention"


def test_evidence_preserves_the_accepted_clause_and_excludes_negation():
    result=select_metrics(paper("Experiments\nWe do not report BLEU but we report F1 = 0.91."),use_llm=False)
    proof=result.evidence["F1"][0]
    assert proof.text=="we report F1 = 0.91."
    assert proof.section=="results" and proof.reported
    assert proof.matched_name=="F1"


def test_table_evidence_has_a_source_location():
    table=Table([["Model","F1"],["Ours","0.91"]],section="results",page=3)
    result=select_metrics(paper("Experiments\nScores follow.",[table]),use_llm=False)
    assert result.names==["F1"]
    proof=result.evidence["F1"][0]
    assert (proof.page,proof.row,proof.column)==(3,1,2)
    assert proof.basis=="table with values"


def test_names_only_table_is_not_proof_of_a_result():
    table=Table([["Metric","F1"],["Alternative","BLEU"]],section="results")
    assert select_metrics(paper("Experiments\nCandidates only.",[table]),use_llm=False).names==[]


@pytest.mark.parametrize("source,reply,expected,origin",[
    ("We do not report BLEU. We report F1.",'["BLEU","F1"]',["F1"],"llm"),
    ("We report Top-1 error = 5%.",'["Top-1 Accuracy"]',["Top-1 Error"],"dictionary"),
    ("We report average precision = 0.8.",'["mAP"]',["Average Precision"],"dictionary"),
    ("Earlier work reports BLEU. We report F1.",'["BLEU"]',["F1"],"dictionary"),
    ("We minimize MSE as the training loss. We report accuracy.",'["MSE"]',["Accuracy"],"dictionary"),
    ("We report a Quantum Consistency Index of 0.8.",'["Quantum Consistency Index"]',["Quantum Consistency Index"],"llm"),
    ("We report F1 = 0.9.",'["F1 score"]',["F1 score"],"llm"),
])
def test_model_names_need_matching_reported_evidence(fake_litellm,source,reply,expected,origin):
    fake_litellm.reply=reply
    result=select_metrics(paper("Experiments\n"+source),model="audit/fake")
    assert result.names==expected and result.source==origin
    assert all(result.evidence[name] for name in result.names)


def test_verbose_model_output_exposes_evidence(fake_litellm,tmp_path,capsys):
    from reportlab.pdfgen import canvas
    from team.eval_metrics_tool.metric_extractor.__main__ import main
    path=tmp_path/"paper.pdf"
    c=canvas.Canvas(str(path));c.drawString(50,750,"Experiments");c.drawString(50,725,"We report F1 = 0.9.");c.save()
    fake_litellm.reply='["F1"]'
    assert main([str(path),"--model","audit/fake","--verbose"])==0
    output=capsys.readouterr().out
    assert "evidence: section=results" in output and "We report F1 = 0.9." in output
