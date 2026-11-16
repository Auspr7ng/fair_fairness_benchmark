"""Optional targeted smoke checks on one public CVPR paper; not a gold benchmark."""
import hashlib
from pathlib import Path
from urllib.request import urlopen
from team.eval_metrics_tool.metric_extractor import extract_paper, rank_pdf
from team.eval_metrics_tool.section_selector import llm_text

URL = "https://openaccess.thecvf.com/content/CVPR2022/papers/Peng_Fingerprinting_Deep_Neural_Networks_Globally_via_Universal_Adversarial_Perturbations_CVPR_2022_paper.pdf"
TITLE = "Fingerprinting Deep Neural Networks Globally via Universal Adversarial Perturbations"


def probe(destination, existing=None):
    path = Path(existing) if existing else Path(destination)/"cvpr2022_fingerprinting.pdf"
    if not existing:
        path.parent.mkdir(parents=True,exist_ok=True)
        with urlopen(URL,timeout=30) as response:
            data = response.read(20_000_000)
        if not data.startswith(b"%PDF-"):
            raise ValueError("The source did not return a PDF")
        path.write_bytes(data)
    paper = extract_paper(str(path))
    scores = rank_pdf(str(path))
    model_input = llm_text(paper)
    names = [s.name for s in scores]
    return {
        "title":TITLE,"url":URL,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "names":names,"scores":[{"name":s.name,"score":s.score,"where":dict(s.where)} for s in scores],
        "model_input_characters":len(model_input),
        "pages_of_interest":{"6":"Evaluation Metrics defines fingerprint similarity using cosine similarity.","7":"Comparison to Existing Methods uses area under the ROC curve (AUC)."},
        "checks":[
            {"title":"AUC is found","passed":"AUC" in names,"expected":"AUC in the returned names","observed":names},
            {"title":"Reference section is excluded from model input","passed":not any(s.text.strip() and s.text.strip() in model_input for s in paper.sections if s.kind=="references"),"expected":"No complete references section in model input","observed":[s.kind for s in paper.sections]},
            {"title":"Cosine similarity is recognized","passed":"Cosine Similarity" in names,"expected":"Cosine Similarity in the returned names","observed":names},
        ],
        "limits":"Only targeted smoke checks on one paper. The complete correct list and its importance order were not exhaustively labeled. No live model call was made."
    }
