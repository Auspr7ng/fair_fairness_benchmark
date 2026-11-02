# Team 2 poster draft

Purdue-themed LaTeX poster for **Toward Agentic Paper Analysis for Defense Reproduction**. Size: 120 × 72 cm, three columns.

`main.tex` is the editable source and needs no external theme, logo, or bibliography files. The university name is typeset text, not an official logo.

## Build

With TeX Live / MacTeX installed:

```sh
latexmk -pdf -outdir=build main.tex
```

The output is `build/main.pdf`. Generated PDFs and compiler files are ignored.

## Content and evidence

- Team 2: metric extraction, reference-value initialization, and validated JSON record updates.
- Cross-team context follows the shared *Landseer Agent Tools* workbook: Team 1 environment preparation, Team 3 repository/model adaptation, Team 4 reproduction and validation.
- Implementation descriptions were checked against repository snapshot `87a5b301c5aca2775e9d210042a21a07fc038493` (November 2, 2026).
- The five-metric local demonstration comes from the team-provided abstract. It is preliminary functionality evidence, not an extraction-accuracy score.
- Landseer integration and end-to-end validation are future work.

## Before final submission

Confirm the complete author list, title, venue, and Landseer citation. Add the demonstration PDF/version, exact metric names, extraction mode, and manually checked output. Replace preliminary statements with evaluated results when available.

## Template attribution

Adapted from the supplied unofficial Georgia Tech/Gemini template, based on https://github.com/k4rtik/uchicago-poster and https://github.com/anishathalye/gemini.
Purdue colors: black and Boilermaker Gold (`#CFB991`).
