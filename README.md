# AI Mutual Fund Recommendation Audit

A reproducible experiment on how large language models (LLMs) tailor mutual fund portfolios to investor **age**, **risk tolerance** and **investment horizon**, and on whether a prompt-level **suitability protocol** makes their advice more suitable. The project uses 200 synthetic investors in a 5 x 5 x 8 full-factorial design, three LLMs and two prompt conditions; recommended portfolios are back-tested against real Chinese fund data.

> **Execution status (22 Oct 2026):** design, samples, fund identity checks, pipeline, coding, back-test and analysis code are complete and tested. **No LLM has been queried yet**; `outputs/` contains no results. The run needs API keys and network access (see *Dependencies*). The report and slides contain no findings until the run is done.

## Repository layout

```
research_design.md          research questions, hypotheses, design, metrics, limitations
AI_use_statement.md         disclosure of AI assistance
config/experiment_config.json   models, prompt conditions, sampling, generation settings
data/
  investor_profiles.csv     200 validated SYNTHETIC investors (main sample)
  probe_profiles.csv        160 SYNTHETIC single-attribute probe profiles (138 distinct texts)
  fund_menu_candidates.csv  23 real funds; identity verified with sources
  fund_menu.csv             final verified menu (created by verify_funds.py)
  nav/                      fund return histories (created by backtest.py fetch)
src/
  design.py                 single source of truth for all category definitions
  generate_profiles.py      builds the synthetic samples (seed 20261022)
  validate_profiles.py      16 integrity checks + distribution tables
  fund_data.py              pluggable fund data sources (course API, Eastmoney, CSV)
  verify_funds.py           risk ratings, allocations; marks menu funds VERIFIED
  prompts.py                BASE and SUIT prompts (BASE is an exact prefix of SUIT)
  llm_client.py             OpenAI-compatible client with retries
  run_experiment.py         resumable, append-only experiment runner
  code_responses.py         deterministic coding of replies -> experiment_results.csv
  backtest.py               historical check of recommended portfolios
  analysis.py               statistical tables + results digest
  figures.py                report/presentation figures
  sample_for_manual_coding.py  draws the human validation sample
tests/                      unit and end-to-end tests (fixture data only)
outputs/                    raw logs, coded results, tables, figures (created by the run)
docs/                       validation report, coding sheet, verification logs, references
report/                     report_source.md, build_report.js, make_appendices.py, draft .docx
presentation/               build_presentation.py and the draft deck (results slides pending)
```

## Setup

```bash
python -m pip install -r requirements.txt     # Python 3.11+ (tested on 3.13)
python -m pytest -q tests                     # 10 tests, fixture data only
```

## Dependencies that must be supplied

| What | Variable / host | Purpose |
|---|---|---|
| Volcano Engine Ark Agent Plan key (course route) | `ARK_API_KEY`, host `ark.cn-beijing.volces.com` | all three models (Doubao, DeepSeek, Kimi; GLM as fallback) through `https://ark.cn-beijing.volces.com/api/plan/v3` |
| *Alternatives (disabled in the config)* | `DEEPSEEK_API_KEY`, `DASHSCOPE_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY` | direct provider routes, kept for reruns outside the course set-up |
| Course fund-data API | `FUYAO_API_KEY` (if required), host `fuyao.aicubes.cn` + its documentation | risk ratings, allocations, NAV history |
| Fallback fund data | hosts `fund.eastmoney.com`, `fundf10.eastmoney.com`, `fundmobapi.eastmoney.com`, `api.fund.eastmoney.com` | used only if the course API is unavailable |

Keys go into the environment (never into files or chat). The config file stores only the variable names.

## Reproducing the experiment

```bash
python src/generate_profiles.py                 # regenerates the identical samples (seed 20261022)
python src/validate_profiles.py                 # must report 16/16 PASS
python src/verify_funds.py --source fuyao       # or --source eastmoney; all funds must be VERIFIED
python src/run_experiment.py --list-models      # read exact model IDs; write them into the config
python src/run_experiment.py --dry-run          # plan: 2,508 calls; token estimate
python src/run_experiment.py --samples pilot    # 60 calls, parsing check, excluded from analysis
python src/run_experiment.py                    # main + consistency + probe; rerun to resume
python src/code_responses.py                    # -> outputs/experiment_results.csv
python src/backtest.py fetch --source fuyao     # fund histories -> data/nav/
python src/backtest.py evaluate                 # -> outputs/portfolio_backtest.csv
python src/analysis.py                          # -> outputs/tables/ (T04-T21 + results_digest.md)
python src/figures.py                           # -> outputs/figures/
python src/sample_for_manual_coding.py          # human validation sample
python src/design_figure.py                     # Figure 1 (design schematic)
python report/make_appendices.py                # appendices regenerated from the data files
node report/build_report.js report/final_report.docx            # needs the docx npm package
python presentation/build_presentation.py --out presentation/presentation.pptx   # needs the course template
```

Report text lives in `report/report_source.md`; results, discussion and conclusion sections are written only after `analysis.py` has produced `outputs/tables/results_digest.md`. The course template and reference report are **not** stored in this public repository; place the template at `reference_materials/AI_Investment_Advisor_SMBU_Template.pptx` (or pass `--template`) before building the slides.

The runner never overwrites earlier results. Every call is appended to `outputs/raw/calls_<model>.jsonl` with prompt hashes, request parameters, model ID returned, token usage and timestamps. A rerun skips calls that already succeeded and retries those that failed. Each run writes a manifest to `outputs/logs/`.

## Known limitations

- Investors are synthetic; findings describe model behaviour, not real client outcomes.
- One 23-fund menu, one date, one five-year back-test window; ratings and returns change.
- Hosted models change without notice; the returned model ID is logged but versions cannot be pinned.
- Equity exposure of feeder funds and FOFs uses category assumptions; reported allocations are used where funds hold stocks directly.
- Text-based codes (conflict acknowledgement) are keyword rules pending manual validation.

See `research_design.md` Section 10 for the full list.
