"""Metric dictionary: canonical metric names and the patterns that detect them.

To add a metric, append a ``MetricSpec`` to ``METRICS``. Three kinds of pattern
are available, all written as regex *without* word boundaries (the matcher adds
them):

* ``patterns``         - matched case-insensitively. For full names and
                         unambiguous spellings ("mean squared error").
* ``cs_patterns``      - matched case-sensitively. For distinctive acronyms
                         ("BLEU", "mAP", "F1").
* ``context_patterns`` - matched case-sensitively, and in running text only
                         when a number follows ("EM = 85.2", "AP of 41.0").
                         Anywhere in a table they always count. For short or
                         ambiguous acronyms ("EM", "IS", "R2", "AP").

When several patterns overlap in the text, the longest match wins, so
"Top-1 accuracy" is Top-1 Accuracy rather than Accuracy, and "PR-AUC" is not
also counted as AUC.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricSpec:
    name: str
    patterns: tuple[str, ...] = ()
    cs_patterns: tuple[str, ...] = ()
    context_patterns: tuple[str, ...] = ()


# Words that make "precision" mean numeric precision rather than the metric.
_NOT_NUMERIC = "".join(
    f"(?<!{w} )" for w in ("mixed", "half", "floating-point", "double", "single",
                           "numerical", "high", "low", "full")
)

METRICS: tuple[MetricSpec, ...] = (
    MetricSpec("Accuracy", patterns=(r"accuracy", r"accuracies"),
               context_patterns=(r"Acc\.?",)),
    MetricSpec("Top-1 Accuracy",
               patterns=(r"top[- ]?1\s+(?:accuracy|acc\.?|error)",),
               context_patterns=(r"Top[- ]?1",)),
    MetricSpec("Top-5 Accuracy",
               patterns=(r"top[- ]?5\s+(?:accuracy|acc\.?|error)",),
               context_patterns=(r"Top[- ]?5",)),
    MetricSpec("Precision",
               patterns=(_NOT_NUMERIC + r"precision(?!\s*[-–]\s*recall)"
                         r"(?!\s+(?:arithmetic|training|floating|format|loss))",)),
    MetricSpec("Recall",
               patterns=(r"(?<![-–])(?<!we )(?<!to )recall"
                         r"(?!\s+(?:that|the|how|from))(?!\s*@)",)),
    MetricSpec("F1",
               patterns=(r"(?:(?:macro|micro|weighted|sample)[- ]?)?f[- ]?(?:1|one)[- ]?(?:score|measure)",
                         r"f[- ]?measure", r"f[- ]?score"),
               cs_patterns=(r"(?:[Mm]acro|[Mm]icro|[Ww]eighted)[- ]?F[- ]?1",
                            r"F[- ]?1", r"F_1")),
    MetricSpec("AUC",
               patterns=(r"roc[- ]?auc", r"auc[- ]?roc", r"auroc",
                         r"area under (?:the )?(?:roc|receiver operating characteristic)(?: curve)?"),
               cs_patterns=(r"AUC", r"AUROC")),
    MetricSpec("PR-AUC",
               patterns=(r"pr[- ]?auc", r"auc[- ]?pr", r"auprc", r"aupr",
                         r"area under (?:the )?precision[- –]recall(?: curve)?")),
    MetricSpec("mAP",
               patterns=(r"mean average precision", r"average precision"),
               cs_patterns=(r"mAP(?:@[\d.:]+)?", r"AP(?:50|75|@[\d.]+)"),
               context_patterns=(r"AP",)),
    MetricSpec("IoU",
               patterns=(r"intersection[- ]over[- ]union", r"jaccard index"),
               cs_patterns=(r"m?(?:IoU|IOU)",)),
    MetricSpec("BLEU", patterns=(r"bleu score",),
               cs_patterns=(r"(?:Sacre)?BLEU(?:-\d)?",)),
    MetricSpec("ROUGE", patterns=(r"rouge(?:[- ]?(?:1|2|l|lsum|su4))?",)),
    MetricSpec("METEOR", cs_patterns=(r"METEOR",), context_patterns=(r"Meteor",)),
    MetricSpec("CIDEr", cs_patterns=(r"CIDEr(?:-D)?", r"CIDER")),
    MetricSpec("chrF", cs_patterns=(r"chrF(?:\+\+|\+)?",)),
    MetricSpec("Perplexity", patterns=(r"perplexity",), cs_patterns=(r"PPL",)),
    MetricSpec("Exact Match",
               patterns=(r"exact[- ]match(?:\s+(?:score|accuracy))?",),
               context_patterns=(r"EM",)),
    MetricSpec("WER", patterns=(r"word error rate",), cs_patterns=(r"WER",)),
    MetricSpec("CER", patterns=(r"character error rate",), cs_patterns=(r"CER",)),
    MetricSpec("pass@k", patterns=(r"pass\s*@\s*(?:k|\d+)",)),
    MetricSpec("MSE", patterns=(r"mean squared? error",), cs_patterns=(r"MSE",)),
    MetricSpec("RMSE", patterns=(r"root mean squared? error",), cs_patterns=(r"RMSE",)),
    MetricSpec("MAE", patterns=(r"mean absolute error",), cs_patterns=(r"MAE",)),
    MetricSpec("R²",
               patterns=(r"r[- ]squared", r"coefficient of determination"),
               cs_patterns=(r"R²", r"R\^2"),
               context_patterns=(r"R2",)),
    MetricSpec("FID", patterns=(r"fr[eé]chet inception distance",),
               cs_patterns=(r"FID",)),
    MetricSpec("Inception Score", patterns=(r"inception score",),
               context_patterns=(r"IS",)),
    MetricSpec("PSNR", patterns=(r"peak signal[- ]to[- ]noise ratio",),
               cs_patterns=(r"PSNR",)),
    MetricSpec("SSIM", patterns=(r"structural similarity(?: index)?(?: measure)?",),
               cs_patterns=(r"(?:MS-)?SSIM",)),
    MetricSpec("LPIPS", cs_patterns=(r"LPIPS",)),
    MetricSpec("MRR", patterns=(r"mean reciprocal rank",), cs_patterns=(r"MRR",)),
    MetricSpec("NDCG",
               patterns=(r"ndcg(?:\s*@\s*\d+)?",
                         r"normalized discounted cumulative gain"),),
    MetricSpec("Hits@k", patterns=(r"hits?\s*@\s*(?:k|\d+)", r"hit rate")),
    MetricSpec("Recall@k", patterns=(r"recall\s*@\s*(?:k|\d+)",),
               cs_patterns=(r"R@\d+",)),
    MetricSpec("Pearson Correlation",
               patterns=(r"pearson(?:['’]s)?\s+(?:correlation|r|coefficient|corr\.?)(?:\s+coefficient)?",),
               cs_patterns=(r"PLCC",), context_patterns=(r"Pearson",)),
    MetricSpec("Spearman Correlation",
               patterns=(r"spearman(?:['’]s)?\s+(?:rank\s+)?(?:correlation|rho|coefficient|r)",
                         r"spearman(?:['’]s)?\s+rank"),
               cs_patterns=(r"SRCC",), context_patterns=(r"Spearman",)),
)
