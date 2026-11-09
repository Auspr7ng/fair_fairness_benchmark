# Fair Fairness Benchmark: course project workspace

This repository organizes the published [Fair Fairness Benchmark (FFB)](https://github.com/ahxt/fair_fairness_benchmark) code alongside our group's reproduction work and supporting tools. The original benchmark is a framework for evaluating in-processing group fairness methods. Our work here is an extension and organization of that code, not a claim that we reproduced every result in the paper.

Last updated: November 8, 2026. Team 2 focuses on paper-analysis tools for a planned Landseer integration; FFB is the local development and demonstration setting.

## Progress at a glance

| Workstream | What is in the repository | Current status |
| --- | --- | --- |
| FFB reference code | Original training scripts, models, metrics, dataset instructions, tutorial, and figures under [`ffb/`](ffb/) | Available as the baseline; the original paper's figures and running logs are upstream results, not new group results. |
| CelebA reproduction | Four ResNet-18/ResNet-20 runners for ERM and DiffDP under [`ffb/reproduce/`](ffb/reproduce/) | Scripts and a dependency/data preflight are implemented. No completed run output is committed; training still needs the CelebA data and dependencies. |
| PDF evaluation-metric extractor | [`team/eval_metrics_tool/`](team/eval_metrics_tool/) | Lists a paper's metrics with a user-configured LLM (any LiteLLM provider), falling back to rule-based PDF text/table extraction, metric matching, and ranking. Scanned PDFs and some table layouts remain unsupported. |
| Metric record initializer | [`team/initialize_metrics_record_tool/`](team/initialize_metrics_record_tool/) | Extracts reported values into a metric-to-value record. Ambiguous or missing values remain empty for review. Bounds and ranges in prose are excluded from exact values. |
| Metric record updater | [`team/insert_into_record_tool/`](team/insert_into_record_tool/) | Validates updates to an initialized record and saves the selected record as JSON. |
| Local repository agent | [`team/agent/`](team/agent/) | A basic Ollama/LangChain agent can list the available reproduction scripts, list a paper's evaluation metrics, and read or update a selected metric record. It can also initialize the selected record when explicitly requested. It is not yet an automated experiment runner. |

| Paper-to-record pipeline | [`team/paper_pipeline.py`](team/paper_pipeline.py) | Connects metric selection and value initialization to persisted JSON without an agent server; reports unresolved values and selection source. |
| Team 2 poster | [`poster/main.tex`](poster/main.tex) and [build/evidence notes](poster/README.md) | Purdue-themed working draft covering our three tools and cross-team roles. Five extracted metric names are a team-reported preliminary demonstration, not an accuracy score. |

## Repository map

```text
.
├── README.md                     Project status and entry points
├── LICENSE                       MIT license inherited from FFB
├── PIPELINE_BLOCKERS.md           Pipeline fixes, prerequisites, and limitations
├── poster/                       Team 2 LaTeX poster draft and build notes
├── ffb/                          Published FFB code and our reproduction work
│   ├── src/                      Original model, training, and metric code
│   ├── benchmark/                Original benchmark helper
│   ├── datasets/                 Dataset instructions (data not committed)
│   ├── tutorial/                 Original notebook
│   ├── img/                      Original paper/README figures
│   ├── reproduce/                Our CelebA reproduction runners
│   ├── requirements.txt          Original FFB dependency list
│   └── readme.md                 Original FFB documentation and historical logs
└── team/                         Group-built supporting tools
    ├── paper_pipeline.py         Paper-to-JSON entry point
    ├── agent/                    Local repository agent
    ├── eval_metrics_tool/        PDF evaluation-metric extractor
    ├── initialize_metrics_record_tool/  Paper-reported metric values
    └── insert_into_record_tool/         Validated metric record updates
```

The code in `ffb/src/`, `ffb/benchmark/`, `ffb/datasets/`, `ffb/tutorial/`, and `ffb/img/` comes from the [upstream FFB project](https://github.com/ahxt/fair_fairness_benchmark). The `ffb/reproduce/` scripts and folders under `team/` are this group's additions. See the [FFB paper](https://arxiv.org/abs/2306.09468) for the benchmark's methods and published results.

## Development milestones

| Date | Repository evidence | Contribution |
| --- | --- | --- |
| Sep 20–21, 2026 | [CelebA runners](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/b1c24bbae4e37feafde39fdf1d2eecc565d4a9f7) and [directory organization](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/7b2e45121c2cc10fc146e57f140fd82b22156e77) | Yuchao added the partial ResNet reproduction scripts. |
| Sep 21, 2026 | [Local agent](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/8ae3588d3b0790a388022c9aa760f9c3b6173d23) and [instructions](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/b5877e2b480ea0e3abb132c60b95afdc20d18216) | Aarush added the Ollama/LangChain demonstration agent. |
| Oct 4, 2026 | [Metric extractor](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/044351ccfdc57b8c7ed4ea2d14d1b76baa7aef00) and [fairness metric patterns](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/c7b8cc8582231bc1c487d540b731f84a4c42f6ca) | Andrew added PDF extraction and expanded the metric dictionary. |
| Oct 26, 2026 | [Shared tool logic](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/3efc8957cd63a62184de0f9452f2f51c3a254e53) | Consolidated record-update validation and extractor fallback behavior. |
| Nov 2, 2026 | [Component organization](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/cf8060fc425deb821ecc797e243564858c969e12) and [section-selection fixes](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/46fe084fcd66bdd3f8e3b85449d3d8c64d9cd735) | Split extraction/initialization components, recover mixed-column experiment headings, and surface empty model-output warnings. |
| Nov 2, 2026 | [Pipeline fixes](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/87a5b301c5aca2775e9d210042a21a07fc038493) and [limitations](PIPELINE_BLOCKERS.md) | Added offline paper-to-record persistence, selected-record initialization, atomic JSON writes, nullable metric handling, and training-launch checks. Commit validation reports 158 tests and 19 subtests; live inference and full torch training were unavailable. |
| Nov 2, 2026 | [Poster draft](https://github.com/Auspr7ng/fair_fairness_benchmark/commit/dd65842a8362394e75424670299b623327188185) | Added Team 2's Purdue LaTeX draft, cross-team context, build instructions, and generated-file exclusions. Desktop LaTeX compilation passed; author details and demonstration evidence remain to be finalized. |

| Nov 8, 2026 | [Poster source](poster/main.tex) and [logo assets](poster/images/) | Replaced the text-only poster header with Purdue’s official horizontal logo; retained source SVG and LaTeX-ready PNG. |

| Nov 8, 2026 | [Poster author line](poster/main.tex) and [review notes](poster/README.md) | Checked GitHub for new updates (none beyond the logo commit) and added the six Team 2 members from the supplied roster. No new experiment-result claims. |

| Nov 8, 2026 | [Poster](poster/main.tex) and [source notes](poster/README.md) | Clarified project-wide model/data targets, assigned papers versus tool roles, the reported local agent demonstration, and the planned FFB comparison using Slack context. |

| Nov 8, 2026 | [Poster](poster/main.tex) and [alignment notes](poster/README.md) | Aligned the poster with the abstract: agentic onboarding motivation, explicit inputs/outputs for three tools, preliminary five-name demonstration, and future integration. |

| Nov 8, 2026 | [Poster workflow diagram](poster/main.tex) | Added a four-team context diagram highlighting Team 2 and marking cross-team handoffs as proposed integration. |

| Nov 8, 2026 | [Poster diagrams](poster/main.tex) | Restored the detailed Team 2 paper-to-record figure alongside the four-team overview. |

| Nov 8, 2026 | [Poster layout](poster/main.tex) | Fixed overlapping team boxes and the execution-environment label using edge-based spacing. |

| Nov 8, 2026 | [Poster validation section](poster/main.tex) | Simplified the result panel to user-reported basic validation against four instructor-provided PDFs; this editing pass did not rerun validation. |
| Nov 9, 2026 | [Metric initializer](team/initialize_metrics_record_tool/) | Preserved column positions in selected plain-text tables, excluded prose bounds and ranges from exact values, and protected saved records from blank paper inputs. Added regression coverage. |

## Try the current work

Run the following commands from the repository root. Each component has its own requirements; the data and Ollama model are not included in the repository.

### Check CelebA reproduction readiness

```bash
python ffb/reproduce/reproduce_resnet18_celeba.py --check
```

This prints whether `ffb/datasets/celeba/raw/celeba.csv` and the required Python packages are present. To prepare the data, follow [`ffb/datasets/readme.md`](ffb/datasets/readme.md). After preparation, the ERM and DiffDP entry points include:

```bash
python ffb/reproduce/reproduce_resnet18_celeba.py --weights random
python ffb/reproduce/reproduce_diffdp_resnet18_celeba.py --weights random
python ffb/reproduce/reproduce_resnet20_celeba.py
python ffb/reproduce/reproduce_diffdp_resnet20_celeba.py
```

These are partial reproduction runners with a default 20,000-row sample and 150 training steps. They write local outputs under `ffb/results/`, which is ignored by Git. We have not committed numerical results, so please do not interpret the published FFB results in [`ffb/readme.md`](ffb/readme.md) as results from these runs. The original `ffb/requirements.txt` pins CUDA-specific PyTorch builds; those pins may need platform-specific installation on macOS or a non-CUDA machine.

### Extract evaluation metrics from a paper

```bash
python -m pip install -r team/eval_metrics_tool/requirements.txt
cd team/eval_metrics_tool
python -m eval_metrics /path/to/paper.pdf --top-k 5
```

The extractor returns metric names, most important first; it does not compute benchmark scores. To use an LLM, set `EVAL_METRICS_MODEL` (and your provider's API key) in your shell or a `.env` copied from [`.env.example`](team/eval_metrics_tool/.env.example). Without one, the extractor ranks metric mentions with its dictionary. Its [README](team/eval_metrics_tool/README.md) explains model setup, scoring rules, tests, and limitations.

### Initialize a paper metric record

```bash
python -m team.initialize_metrics_record_tool /path/to/paper.pdf --top-k 5
python -m team.initialize_metrics_record_tool /path/to/FFB.pdf --metric Accuracy --metric F1 --row-label "Bank Age"
```

This returns JSON with one reported value per metric where the paper gives a clear value. Use `--metric` to choose names or `--row-label` to select a model row in a table. See the [tool README](team/initialize_metrics_record_tool/README.md) for the Python API and limitations.

### Run the paper-to-record pipeline

```bash
python -m team.paper_pipeline /path/to/paper.pdf --output results/paper-record.json --no-llm
```

This offline route needs the extractor dependencies but no running agent server. It saves metric values as JSON and returns selection provenance and unresolved fields separately. Existing output files require explicit `--overwrite`. Value selection is heuristic and needs review. See [pipeline notes](PIPELINE_BLOCKERS.md) for prerequisites and remaining limitations.

### Update a metric record

```bash
python -m team.initialize_metrics_record_tool paper.pdf --metric F1 --metric Accuracy > metrics.json
python -m team.insert_into_record_tool metrics.json F1 0.90
```

The updater changes only an existing metric in the selected JSON record. See its [README](team/insert_into_record_tool/README.md) for the Python API and validation rules.

### Run the local agent

The agent needs Python 3.12, a running [Ollama](https://ollama.com/) service, and the `qwen3:4b` model. From the repository root:

```bash
ollama pull qwen3:4b
python -m pip install -r team/agent/requirements.txt
python team/agent/basic_agent.py
```

By default the agent answers one demonstration question by calling a tool that lists files in `ffb/reproduce/`. Pass `--prompt` to ask which metrics a paper PDF reports, or `--record` to work with a metric record. See its [README](team/agent/README.md) for the recommended virtual environment setup.

## Documentation updates

For each project update, revise the affected component README and keep this overview's status, usage, and repository map consistent. Append a dated development milestone with a commit or file link and the relevant validation evidence. Keep earlier milestones, distinguish implemented functionality from planned work, and label upstream results and team demonstrations accurately. Poster-specific evidence and unfinished submission details belong in [`poster/README.md`](poster/README.md).

## Attribution

FFB was introduced by Xiaotian Han and colleagues in [*FFB: A Fair Fairness Benchmark for In-Processing Group Fairness Methods*](https://arxiv.org/abs/2306.09468). This repository is a fork of their [public implementation](https://github.com/ahxt/fair_fairness_benchmark) and retains its MIT [license](LICENSE). The historical experiment counts and plots in the original documentation belong to the FFB authors.
