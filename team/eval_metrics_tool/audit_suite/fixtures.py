"""Small inspectable PDF examples. No downloaded papers or private data."""
from pathlib import Path

TEXTS = {
    "01_clear": "Abstract\nWe report F1.\nExperiments\nWe report F1 = 0.91 and BLEU = 32.4.\nReferences\n[1] ROUGE in an earlier paper.",
    "02_negation": "Experiments\nWe do not report BLEU.\nWe report F1 = 0.91.",
    "03_unusual_heading": "Related Work\nEarlier authors report BLEU.\n4 Benchmarking Fairness Methods\nWe report accuracy = 90%.",
    "04_wrong_name": "Experiments\nWe report Top-1 error = 5%.",
    "05_wrapped_name": "Experiments\nOur demographic\nparity difference is 0.10.",
    "06_no_metric": "Introduction\nWe describe a new data collection procedure.\nConclusion\nFurther research is needed.",
    "07_novel_metric": "Experiments\nWe report a Quantum Consistency Index of 0.80.",
    "08_citation": "Experiments\nEarlier work reports BLEU = 35.\nOur experiment reports accuracy = 90%.",
    "09_training_loss": "Method\nWe minimize MSE as the training loss.\nExperiments\nOur evaluation metric is accuracy = 90%.",
    "10_integer_acronym": "Experiments\nWe report EM 85 on the test set.",
    "11_multipage": ["Introduction\nWe describe our model.", "Experiments\nWe report accuracy = 90% and F1 = 0.85.", "References\n[1] BLEU in another paper."],
}


def make_fixtures(destination):
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab
    from PIL import Image, ImageDraw
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("AuditSans",str(Path(reportlab.__file__).parent/"fonts/Vera.ttf")))
    for name, pages in TEXTS.items():
        pages = pages if isinstance(pages, list) else [pages]
        (destination / f"{name}.txt").write_text("\n\n--- PAGE ---\n\n".join(pages), encoding="utf-8")
        c = canvas.Canvas(str(destination / f"{name}.pdf"), invariant=1)
        c.setTitle(name + " - generated audit example")
        for page in pages:
            c.setFont("AuditSans", 12)
            for i, line in enumerate(page.splitlines()):
                c.drawString(55, 770 - i * 21, line)
            c.showPage()
        c.save()
    for name, ruled in [("12_ruled_table", True), ("13_borderless_table", False)]:
        c = canvas.Canvas(str(destination / f"{name}.pdf"), invariant=1)
        c.setFont("AuditSans", 12)
        c.drawString(55, 770, "Experiments")
        rows = [["Model", "F1", "BLEU"], ["Ours", "0.91", "32.4"]]
        for r, row in enumerate(rows):
            for j, cell in enumerate(row):
                c.drawString(65 + j * 135, 710 - r * 32, cell)
        if ruled:
            for x in [55, 190, 325, 460]:
                c.line(x, 665, x, 735)
            for y in [665, 700, 735]:
                c.line(55, y, 460, y)
        c.save()
    # An image-only page visibly contains a metric, but has no searchable text.
    im = Image.new("RGB", (1000, 240), "white")
    d = ImageDraw.Draw(im)
    d.text((30, 30), "EXPERIMENTS\nWe report accuracy = 90%.", fill="black", font_size=42)
    c = canvas.Canvas(str(destination / "14_image_only.pdf"), invariant=1)
    c.drawImage(ImageReader(im), 55, 600, width=500, height=120)
    c.save()
    (destination / "14_image_only.txt").write_text("Visible image text: EXPERIMENTS / We report accuracy = 90%.\nNo searchable text layer.", encoding="utf-8")
    (destination / "15_invalid.pdf").write_text("This is ordinary text, not a PDF.", encoding="utf-8")


if __name__ == "__main__":
    import sys
    make_fixtures(sys.argv[1])
