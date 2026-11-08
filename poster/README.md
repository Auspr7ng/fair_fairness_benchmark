# Team 2 poster draft

Purdue-themed LaTeX poster for **Agentic Onboarding Tools for Empirical Evaluation of Machine Learning Defenses**. Size: 120 × 72 cm, three columns.

`main.tex` is the editable source and uses the bundled Purdue logo in `images/`; no external theme or bibliography files are required. The official logo retains its original proportions.

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

Confirm the venue and Landseer citation. Add the demonstration PDF/version, exact metric names, extraction mode, and manually checked output. Replace preliminary statements with evaluated results when available.

## Template attribution

Adapted from the supplied unofficial Georgia Tech/Gemini template, based on https://github.com/k4rtik/uchicago-poster and https://github.com/anishathalye/gemini.
Purdue colors: black and Boilermaker Gold (`#CFB991`).

## November 8, 2026 update

Replaced the text-only header with Purdue’s official horizontal logo for a dark background. `images/purdue-logo.svg` is the unmodified source from https://www.purdue.edu/purdue/images/logo.svg; `images/purdue-logo.png` is the high-resolution rendering used by LaTeX. Keep both image files with the source.

### Repository review and authors

Checked `origin/master` on November 8, 2026: no commits beyond `83ad893` before this update, so no new implementation or experiment results were added to the poster. The author line now follows the user-supplied Team 2 screenshot order: Aarush Kumar, Andrew Zeng, Benjamin Taylor, Bhanu Adaveni, Rudra Vaishnav, and Yuchao Shen. Existing preliminary-result and future-integration qualifications are retained.

### Slack-informed clarification (November 8, 2026)

Reviewed the project channel and the six-member Team 2 discussion. The poster now distinguishes assigned papers from shared tool responsibilities, explains the ResNet-20/CIFAR-10 common target and CelebA fairness exception, and adds the FFB comparison plan. The September 21 local Qwen tool-call success is explicitly a team-reported script-listing demonstration, not a verified paper-to-experiment run. November 2 Dockerfile shares are preparation evidence, not proof of successful builds. No private contact details or meeting credentials are included.

Source pointers:
- Project paper assignments: https://vip-tml.slack.com/archives/C0BT7TY1XB2/p1787606783549289
- ResNet-20 direction: https://vip-tml.slack.com/archives/C0BT7TY1XB2/p1789061192160359
- Dataset direction: https://vip-tml.slack.com/archives/C0BT7TY1XB2/p1789061224816559
- FFB Dockerfile share: https://vip-tml.slack.com/archives/C0BT7TY1XB2/p1793652447771249

The Team 2 discussion also reports an earlier code run and shares a reproduction report; the report was not inspected in this review, so no numerical reproduction results are claimed. A live end-to-end agent evaluation is still needed.

### Abstract alignment (November 8, 2026)

Reframed the title and motivation around agentic onboarding for empirical ML defense evaluation. The narrative now proceeds from simultaneous privacy/robustness/fairness guarantees to defense interactions, onboarding difficulty, and Team 2's three paper-analysis operations. Each tool has explicit inputs and outputs. Cross-team assignments, Dockerfile progress, and model/data adaptation plans were compressed out of the poster's main narrative; Landseer remains a framework under development and planned integration target. The five-name demonstration is retained as preliminary functionality evidence. No complete integration, extraction-accuracy score, or reproduced experiment result is claimed.

This supersedes the expanded cross-team emphasis in the preceding Slack-informed revision. The Google abstract draft was read for comparison and was not edited. Local changes containing Slack-derived context remain unpublished pending explicit approval.
