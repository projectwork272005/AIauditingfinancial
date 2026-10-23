# AI Mutual Fund Recommendation Audit

A reproducible experiment on how large language models (LLMs) tailor mutual fund portfolios to investor **age**, **risk tolerance** and **investment horizon**, and on whether a prompt-level **suitability protocol** makes their advice more suitable. The project uses 200 synthetic investors in a 5 x 5 x 8 full-factorial design, three LLMs and two prompt conditions; recommended portfolios are back-tested against real Chinese fund data.

> **Execution status (23 Oct 2026):** complete. All 2,508 calls (plus a 60-call pilot) were run on 23 October 2026 through OpenRouter, coded, back-tested and analysed. Results are in `outputs/`, the report in `report/final_report.docx` and the slides in `presentation/presentation.pptx`. Still open for the group: names on the title page and the manual double coding of `docs/manual_coding_sample.csv`.

## Results at a glance

All numbers come from `outputs/tables/` (main sample: 200 investors x 2 prompts x 3 models).

- Risk tolerance drives the portfolios (partial eta squared 0.66-0.83), horizon comes second (0.41-0.53), age barely matters (0.02-0.08).
- Under the baseline prompt, 82.5-85.8% of recommendations to C1-C3 investors include a fund rated above their ceiling, although ratings are in the prompt.
- The suitability protocol lowers rating breaches by 9.5, 11.1 and 24.5 points (DeepSeek, Doubao, Kimi), but 41.7-70.0% of C1-C3 recommendations still breach.
- Equity levels are repeatable (ICC 0.95-0.98); fund choices are not (Jaccard 0.59-0.70).
- In the 2021-26 back-test at most 1% of portfolios per model and prompt lost more in a year than the investor accepts.

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
report/                     report_source.md, build_report.js, make_appendices.py, report_supplement.py, final_report.docx
presentation/               build_presentation.py and presentation.pptx (result slides drawn from outputs/tables)
```

## Setup

```bash
python -m pip install -r requirements.txt     # Python 3.11+ (tested on 3.13)
python -m pytest -q tests                     # 11 tests, fixture data only
```

## Dependencies that must be supplied

| What | Variable / host | Purpose |
|---|---|---|
| OpenRouter key (route used for the run) | `OPENROUTER_API_KEY`, host `openrouter.ai` | all three models, each pinned to one provider (Seed, SiliconFlow, Moonshot AI), reasoning disabled |
| Volcano Engine Ark Agent Plan key (course route, disabled) | `AI_agents` (also `ARK_API_KEY`), host `ark.cn-beijing.volces.com` | kept in the config; the available keys were not Agent Plan keys (see `docs/run_status.md`) |
| Course fund-data API (Tonghuashun data) | `fuyao` (also `FUYAO_API_KEY`), host `fuyao.aicubes.cn` | adjusted NAV history for the back-test |
| Eastmoney / Tiantian Fund | hosts `fundmobapi.eastmoney.com`, `fund.eastmoney.com` | product risk ratings and reported stock shares (the course API has no rating field) |

Keys go into the environment (never into files or chat). The config file stores only the variable names.

## Reproducing the experiment

```bash
python src/generate_profiles.py                 # regenerates the identical samples (seed 20261022)
python src/validate_profiles.py                 # must report 16/16 PASS
python src/verify_funds.py --source eastmoney   # ratings and allocations; all funds must be VERIFIED
python src/run_experiment.py --list-models      # read exact model IDs; write them into the config
python src/run_experiment.py --dry-run          # plan: 2,508 calls; token estimate
python src/run_experiment.py --samples pilot    # 60 calls, parsing check, excluded from analysis
python src/run_experiment.py                    # main + consistency + probe; rerun to resume
python src/code_responses.py                    # -> outputs/experiment_results.csv
python src/backtest.py fetch --source fuyao     # fund histories -> data/nav/
python src/backtest.py evaluate                 # -> outputs/portfolio_backtest.csv
python src/analysis.py                          # -> outputs/tables/ (T04-T21 + results_digest.md)
python src/performance.py                       # Sharpe, Calmar, benchmarks, fees -> T26-T30, T33, F09-F10
python report/report_supplement.py              # -> outputs/tables/T22-T25, T32 (cited in the report)
python src/manual_coding.py prepare             # blinded double-coding sheets; then reconcile, finalize
python src/figures.py                           # -> outputs/figures/
python src/sample_for_manual_coding.py          # human validation sample
python src/design_figure.py                     # Figure 1 (design schematic)
python report/make_appendices.py                # appendices regenerated from the data files
node report/build_report.js report/final_report.docx            # needs the docx npm package
python presentation/build_presentation.py --template reference_materials/AI_Investment_Advisor_SMBU_Template.pptx
```

Report text lives in `report/report_source.md`; every number in Sections 9 to 13 is taken from `outputs/tables/`. The course template and reference report are **not** stored in this public repository; place the template at `reference_materials/AI_Investment_Advisor_SMBU_Template.pptx` (or pass `--template`) before building the slides.

The runner never overwrites earlier results. Every call is appended to `outputs/raw/calls_<model>.jsonl` with prompt hashes, request parameters, model ID returned, token usage and timestamps. A rerun skips calls that already succeeded and retries those that failed. Each run writes a manifest to `outputs/logs/`.

## Known limitations

- Investors are synthetic; findings describe model behaviour, not real client outcomes.
- One 23-fund menu with no R5 fund (rating breaches possible only for C1-C3), ratings from one distributor on one date, one benign 59-month back-test window.
- Models reached through OpenRouter (not the course's Ark route), DeepSeek via a third-party provider, reasoning disabled.
- Hosted models change without notice; the returned model ID is logged but versions cannot be pinned.
- Equity exposure of feeder funds and FOFs uses category assumptions; reported allocations are used where funds hold stocks directly.
- Text-based codes (conflict acknowledgement) are keyword rules pending manual validation.

See `research_design.md` Section 10 for the full list.
