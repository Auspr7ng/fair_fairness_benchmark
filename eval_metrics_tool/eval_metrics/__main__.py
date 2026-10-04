import argparse
import sys

from . import PDFReadError, rank_pdf


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="eval_metrics",
                                description="List the main evaluation metrics a paper reports.")
    p.add_argument("pdf")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--verbose", action="store_true",
                   help="also print each metric's score and where it was found")
    args = p.parse_args(argv)
    if args.top_k < 1:
        p.error("--top-k must be >= 1")
    try:
        ranked = rank_pdf(args.pdf)
    except (FileNotFoundError, PDFReadError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for s in ranked[: args.top_k]:
        if args.verbose:
            where = ", ".join(f"{loc} x{n}" for loc, n in s.where.most_common())
            print(f"{s.name}\tscore={s.score}\t{where}\te.g. {s.example!r}")
        else:
            print(s.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
