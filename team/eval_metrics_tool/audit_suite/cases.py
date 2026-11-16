"""An explicit test oracle: expected results are written before execution.

Contract cases check promised behavior. Challenge cases express desirable
research-use behavior, including documented limitations. A failed challenge
is evidence of a boundary, not necessarily a broken documented promise.
"""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import warnings

from team.eval_metrics_tool.metric_extractor import extract_eval_metrics, extract_paper
from team.eval_metrics_tool.metric_extractor.__main__ import main
from team.eval_metrics_tool.metric_matcher import find_metrics, find_requested_metrics, normalize_metric
from team.eval_metrics_tool.metric_ranker import rank_metrics
from team.eval_metrics_tool.metric_selector import select_metrics
from team.eval_metrics_tool.pdf_reader import PdfPage, read_pdf
from team.eval_metrics_tool.section_selector import llm_text
from team.eval_metrics_tool.section_splitter import PaperContent, Table, build_paper, classify_heading, split_sections


@dataclass
class Case:
    id: str
    area: str
    kind: str
    title: str
    op: str
    input: object
    expected: object
    why: str
    sample: str = ""


CASES = []


def add(id, area, title, op, input, expected, why, sample="", kind="contract"):
    CASES.append(Case(id, area, kind, title, op, input, expected, why, sample))


add("M01", "Names", "Common F1 aliases", "match", "macro-F1, F-measure, F1-score", ["F1", "F1", "F1"], "Common spellings should be recognized.")
add("M02", "Names", "Longest name wins", "match", "Top-1 accuracy and PR-AUC", ["Top-1 Accuracy", "PR-AUC"], "Avoid counting a long metric name again as a shorter one.")
add("M03", "Names", "Ambiguous acronyms are filtered", "match", "The EM algorithm and AP news; it IS shown.", [], "Ordinary acronyms should not become metrics.")
add("M04", "Names", "Acronyms next to explicit scores", "match", "EM = 85.2; AP of 41.0; R2: 0.91", ["Exact Match", "Average Precision", "R²"], "A score supplies context for otherwise ambiguous acronyms; AP is distinct from mean AP.")
add("M05", "Names", "Fairness metric names", "match", "demographic parity difference and equalized odds gap", ["Demographic Parity", "Equalized Odds"], "The dictionary covers common fairness measures.")
add("M06", "Names", "Word boundaries", "match", "inaccuracy recallable precisionist", [], "A word containing a metric name should not count.")
add("M07", "Names", "Numeric precision is filtered", "match", "We use mixed precision training. Recall that x holds.", [], "Known non-metric uses are filtered.")
add("M08", "Names", "Explicitly requested custom name", "requested", {"text":"Quantum Consistency Index is 0.8", "wanted":["Quantum Consistency Index"]}, ["Quantum Consistency Index"], "The lower-level requested-name matcher can find custom names.")
add("M09", "Names", "Error is not accuracy", "normalize", "Top-1 error", "Top-1 Error", "Error rate and accuracy have opposite meanings; preserving that distinction matters.", "04_wrong_name.pdf", "challenge")
add("M10", "Names", "AP is not necessarily mean AP", "normalize", "average precision", "Average Precision", "Average precision for one class and mean average precision across classes are distinct.", kind="challenge")
add("M11", "Names", "Integer scores after acronyms", "match", "We report EM 85 on the test set.", ["Exact Match"], "A plain integer score is understandable to a reader.", "10_integer_acronym.pdf", "challenge")
add("M12", "Names", "A name split across lines", "rank", "Experiments\nOur demographic\nparity difference is 0.10.", ["Demographic Parity"], "PDF text often wraps a metric across lines.", "05_wrapped_name.pdf", "challenge")
add("M13", "Names", "Novel metric outside the dictionary", "rank", "Experiments\nWe report a Quantum Consistency Index of 0.8.", ["Quantum Consistency Index"], "A fixed dictionary cannot discover a new metric name.", "07_novel_metric.pdf", "challenge")
add("M14", "Names", "Non-metric precision", "rank", "Experiments\nPrecision machining was used to make the test rig.", [], "A familiar word can have a non-statistical meaning.", kind="challenge")
add("S01", "Sections", "Numbered heading recognized", "heading", "4.1 Results and Discussion", "results", "Common numbered headings are supported.")
add("S02", "Sections", "A heading mentioned in prose", "heading", "We discuss 5. Experiments", None, "A sentence mentioning a section is not a heading.")
add("S03", "Sections", "Two-column heading repair", "heading", "i n 5. Experiments", "results", "One known two-column extraction artifact is handled.")
add("S04", "Sections", "Results selected, references excluded", "selected", {"text":"Introduction\nBACKGROUND\nExperiments\nRESULT_A\nResults\nRESULT_B\nReferences\nCITATION", "markers":["BACKGROUND","RESULT_A","RESULT_B","CITATION"]}, {"BACKGROUND":False,"RESULT_A":True,"RESULT_B":True,"CITATION":False}, "The model should receive results from both recognized result sections.")
add("S05", "Sections", "No heading still permits extraction", "rank", "We report accuracy = 90%.", ["Accuracy"], "Papers without a recognized heading have a usable fallback.")
add("S06", "Sections", "Topic heading after Related Work", "rank", "Related Work\nEarlier authors report BLEU.\n4 Benchmarking Fairness Methods\nWe report accuracy = 90%.", ["Accuracy"], "An unrecognized heading leaves real results inside the ignored Related Work section.", "03_unusual_heading.pdf", "challenge")
add("S07", "Sections", "Separately titled findings reach the model", "selected", {"text":"Experiments\nRESULT_A\nConclusion\nSummary.\n5 Additional Findings\nRESULT_B", "markers":["RESULT_A","RESULT_B"]}, {"RESULT_A":True,"RESULT_B":True}, "Once a recognized results section exists, results stored elsewhere can be omitted.", kind="challenge")
add("S08", "Sections", "Whole-body fallback includes related work", "selected", {"text":"Introduction\nOWN_RESULT\nRelated Work\nOTHER_PAPER\nReferences\nCITATION", "markers":["OWN_RESULT","OTHER_PAPER","CITATION"]}, {"OWN_RESULT":True,"OTHER_PAPER":False,"CITATION":False}, "With no results heading the model sees related work, which can confuse a model.", kind="challenge")
add("R01", "Relevance", "Recognized related work is ignored", "rank", "Related Work\nBLEU and METEOR were used earlier.\nExperiments\nWe report accuracy = 90%.", ["Accuracy"], "Known background headings prevent unrelated metric leakage.")
add("R02", "Relevance", "References are ignored", "rank", "Experiments\nWe report F1.\nReferences\nBLEU and ROUGE.", ["F1"], "References should not add evaluation metrics.")
add("R03", "Relevance", "A negated metric is excluded", "rank", "Experiments\nWe do not report BLEU.\nWe report F1 = 0.91.", ["F1"], "A mention is not proof that the paper reports the metric.", "02_negation.pdf", "challenge")
add("R04", "Relevance", "Other authors within Results", "rank", "Experiments\nEarlier work reports BLEU = 35.\nOur experiment reports accuracy = 90%.", ["Accuracy"], "Section weights alone cannot decide whose result is being described.", "08_citation.pdf", "challenge")
add("R05", "Relevance", "Training loss versus evaluation metric", "rank", "Method\nWe minimize MSE as the training loss.\nExperiments\nOur evaluation metric is accuracy = 90%.", ["Accuracy"], "A training objective need not be a reported evaluation metric.", "09_training_loss.pdf", "challenge")
add("R06", "Relevance", "Repeated background should not dominate", "rank_top", {"text":"Introduction\n" + "BLEU is discussed as background.\n"*12 + "Experiments\nOur only reported evaluation metric is accuracy = 90%.","k":1}, ["Accuracy"], "Repeated weak evidence can overwhelm a genuine result.", kind="challenge")
add("R07", "Relevance", "Table header gets more weight", "table_rank", {"text":"Introduction\nBLEU is mentioned.\n", "rows":[["Model","F1"],["Ours","0.91"]]}, ["F1","BLEU"], "Structured table evidence outranks one background mention.")
add("R08", "Relevance", "Stable alphabetical tie break", "rank", "Experiments\nWe report F1 and accuracy.", ["Accuracy","F1"], "Equal scores have a reproducible order.")
add("P01", "PDF and CLI", "A clear PDF through the public API", "pdf", "01_clear.pdf", ["F1","BLEU"], "Reads a real generated PDF, splits it, and returns expected names.", "01_clear.pdf")
add("P02", "PDF and CLI", "Multiple pages in order", "pdf", "11_multipage.pdf", ["Accuracy","F1"], "Result text is preserved across pages while references are excluded.", "11_multipage.pdf")
add("P03", "PDF and CLI", "PDF with no metrics", "pdf", "06_no_metric.pdf", [], "A readable paper with no metric names yields an empty list.", "06_no_metric.pdf")
add("P04", "PDF and CLI", "Ruled table is detected", "tables", "12_ruled_table.pdf", 1, "A grid supplies the structured table evidence promised by the reader.", "12_ruled_table.pdf")
add("P05", "PDF and CLI", "Borderless table as structure", "tables", "13_borderless_table.pdf", 1, "Common academic tables have no grid; the default table reader can miss their structure.", "13_borderless_table.pdf", "challenge")
add("P06", "PDF and CLI", "Borderless table text remains useful", "pdf_set", "13_borderless_table.pdf", ["BLEU","F1"], "A missed table can still contribute searchable prose.", "13_borderless_table.pdf")
add("P07", "PDF and CLI", "Image-only PDF warns about missing text", "image_warning", "14_image_only.pdf", {"names":[],"warning":True}, "An empty result should be distinguished from a page the tool could not read.", "14_image_only.pdf", "challenge")
add("P08", "PDF and CLI", "Missing file is explained", "api_error", "missing.pdf", "FileNotFoundError", "Callers receive a specific error for a missing file.")
add("P09", "PDF and CLI", "Invalid PDF is explained", "api_error", "15_invalid.pdf", "PDFReadError", "A damaged or incorrectly named file should not look like an empty paper.", "15_invalid.pdf")
add("P10", "PDF and CLI", "Zero requested metrics is rejected", "top_k_error", 0, "ValueError", "Invalid API limits should fail before reading a paper.")
add("P11", "PDF and CLI", "Negative requested metrics is rejected", "top_k_error", -2, "ValueError", "Negative limits should not silently slice a result.")
add("P12", "PDF and CLI", "CLI error is readable", "cli_error", "missing.pdf", {"exit":1,"says_error":True,"traceback":False}, "A user-facing failure should explain the problem without an internal traceback.")
add("P13", "PDF and CLI", "CLI exposes evidence", "cli_verbose", "01_clear.pdf", {"exit":0,"score":True,"where":True}, "Verbose output helps a reader check why a name appeared.", "01_clear.pdf")
add("P14", "PDF and CLI", "CLI and API agree", "cli_api", "01_clear.pdf", True, "Both entry points should return the same ordered names.", "01_clear.pdf")
add("P15", "PDF and CLI", "PDF Top-1 error preserves meaning", "pdf", "04_wrong_name.pdf", ["Top-1 Error"], "The naming error is observable through the full PDF pipeline.", "04_wrong_name.pdf", "challenge")
add("P16", "PDF and CLI", "Results table on a mixed-section page", "mixed_table", None, ["F1"], "Whole-page majority tagging can attribute a results table to Related Work.", kind="challenge")


def llm_case(id, title, reply, expected, why, kind="contract"):
    add(id,"Model handling",title,"llm",reply,expected,why,kind=kind)


def decision(names, source="llm", reason=False):
    return {"names":names,"source":source,"has_reason":reason}


llm_case("L01","Valid JSON reply",'["F1", "Accuracy"]',decision(["F1","Accuracy"]),"Checks model plumbing with a fixed reply; it does not test model reasoning.")
llm_case("L02","Reasoning text and code fence",'<think>["wrong"]</think>```json\n["F1"]\n```',decision(["F1"]),"Common reasoning wrappers are removed.")
llm_case("L03","Spaces and repeated names",'[" F1 ", "f1", "Accuracy", "Accuracy"]',decision(["F1","Accuracy"]),"Repeated names and stray spaces are cleaned.")
llm_case("L04","Provider failure falls back",{"error":"connection refused"},decision(["Accuracy","F1"],"dictionary",True),"A model outage still allows dictionary extraction.")
llm_case("L05","Malformed JSON falls back",'[F1, Accuracy]',decision(["Accuracy","F1"],"dictionary",True),"An unusable model answer should not stop the pipeline.")
llm_case("L06","Empty successful reply is flagged",'[]',decision([],"llm",True),"An empty reply is not proof that the paper reports no metrics.")
llm_case("L07","All non-string entries are rejected",'[17, null, {"metric":"F1"}]',decision(["Accuracy","F1"],"dictionary",True),"A malformed array currently gets cleaned into a successful empty result.","challenge")
llm_case("L08","Unsupported model claim is flagged",'["Invented Super Score"]',decision(["Accuracy","F1"],"dictionary",True),"The tool accepts an unsupported model name without checking for paper evidence.","challenge")
llm_case("L09","Too many model names are limited",'["F1", "Accuracy", "BLEU", "ROUGE", "WER", "CER"]',decision(["F1","Accuracy","BLEU","ROUGE","WER"]),"The caller's maximum is respected.")
llm_case("L10","Two JSON arrays in one answer",'Example: ["BLEU"]. Final answer: ["F1"]',decision(["F1"]),"The greedy array parser cannot isolate a final array when another one appears earlier.","challenge")
add("L11","Model handling","Model receives bounded input","input_length",None,True,"Very long whole-body fallback text is sent without a length limit. The 50,000-character threshold is an audit policy, not an advertised tool limit.",kind="challenge")
add("L12","Model handling","Unconfigured model falls back","no_model",None,decision(["Accuracy","F1"],"dictionary",True),"Dictionary fallback explains that no model was configured.")


class FakeProvider:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def completion(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.reply, dict):
            raise RuntimeError(self.reply["error"])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.reply))])


def evaluate(case, fixture_dir):
    root = Path(fixture_dir)
    op, value = case.op, case.input
    evidence = {}
    if op == "match":
        actual = [m.metric for m in find_metrics(value)]
    elif op == "normalize":
        actual = normalize_metric(value)
    elif op == "requested":
        actual = [m.metric for m in find_requested_metrics(value["text"],value["wanted"])]
    elif op in {"rank","rank_top","table_rank"}:
        text = value if isinstance(value,str) else value["text"]
        tables = [Table(value["rows"],section="results")] if op == "table_rank" else []
        scores = rank_metrics(PaperContent(split_sections(text),tables))
        actual = [s.name for s in scores]
        if op == "rank_top":
            actual = actual[:value["k"]]
        evidence["scores"] = [{"name":s.name,"score":s.score,"where":dict(s.where),
                               "example":s.example,"reported":s.reported,
                               "evidence":[asdict(e) for e in s.evidence]} for s in scores]
    elif op == "heading":
        actual = classify_heading(value)
    elif op == "selected":
        text = llm_text(PaperContent(split_sections(value["text"])))
        actual = {m:m in text for m in value["markers"]}
        evidence["model_input"] = text
    elif op in {"pdf","pdf_set","tables","image_warning","api_error"}:
        path = root/value
        if op == "tables":
            pages = read_pdf(str(path))
            actual = sum(len(p.tables) for p in pages)
            evidence["read_text"] = "\n".join(p.text for p in pages)
        elif op == "api_error":
            try:
                extract_eval_metrics(str(path),use_llm=False)
                actual = "NO ERROR"
            except Exception as exc:
                actual = type(exc).__name__
        else:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                names = extract_eval_metrics(str(path),use_llm=False)
            actual = {"names":names,"warning":bool(caught)} if op == "image_warning" else sorted(names) if op == "pdf_set" else names
            evidence["read_text"] = "\n".join(s.text for s in extract_paper(str(path)).sections)
    elif op == "top_k_error":
        try:
            extract_eval_metrics(str(root/"01_clear.pdf"),top_k=value,use_llm=False)
            actual = "NO ERROR"
        except Exception as exc:
            actual = type(exc).__name__
    elif op in {"cli_error","cli_verbose","cli_api"}:
        out,err = StringIO(),StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = main([str(root/value),"--no-llm"] + (["--verbose"] if op=="cli_verbose" else []))
        evidence.update(stdout=out.getvalue(),stderr=err.getvalue())
        if op == "cli_error":
            actual = {"exit":rc,"says_error":"error:" in err.getvalue(),"traceback":"Traceback" in err.getvalue()}
        elif op == "cli_verbose":
            actual = {"exit":rc,"score":"score=" in out.getvalue(),"where":"results x" in out.getvalue()}
        else:
            actual = rc == 0 and out.getvalue().splitlines()==extract_eval_metrics(str(root/value),use_llm=False)
    elif op == "mixed_table":
        related = "Related Work\n" + "Background from earlier work without any metric names. "*30
        p = build_paper([PdfPage(related+"\nExperiments\nOur scores follow in the table.",[[["Model","F1"],["Ours","0.91"]]])])
        actual = [s.name for s in rank_metrics(p)]
        evidence["table_assigned_section"] = p.tables[0].section
        evidence["page_text"] = related+"\nExperiments\nOur scores follow in the table."
    elif op in {"llm","no_model","input_length"}:
        p = PaperContent(split_sections("Experiments\nWe report F1 = 0.9 and accuracy = 90%."))
        if case.id=="L09":
            p=PaperContent(split_sections("Experiments\nWe report F1, Accuracy, BLEU, ROUGE, WER and CER."))
        from team.eval_metrics_tool.llm_metric_finder import llm
        fake = FakeProvider('["F1"]' if op=="input_length" else value)
        with ExitStack() as stack:
            stack.enter_context(patch.object(llm,"load_env",return_value=None))
            stack.enter_context(patch.dict("os.environ",{"EVAL_METRICS_MODEL":""}))
            stack.enter_context(patch.dict("sys.modules",{"litellm":fake}))
            if op == "input_length":
                p = PaperContent(split_sections("Introduction\n" + "Background material. "*8000))
                result = select_metrics(p,model="audit/fake")
                size = len(fake.calls[0]["messages"][1]["content"])
                evidence["characters_sent"] = size
                actual = size <= 50_000
            else:
                result = select_metrics(p,model=None if op=="no_model" else "audit/fake")
                actual = decision(result.names,result.source,bool(result.reason))
                evidence["reason"] = result.reason
                evidence["model_paper_text"] = llm_text(p)
    else:
        raise ValueError(op)
    return {**asdict(case),"actual":actual,"passed":actual==case.expected,"evidence":evidence}
