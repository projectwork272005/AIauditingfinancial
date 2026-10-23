# Handoff for the report and slides session

Date: 2026-10-23. Everything below is on `main`. Full log of the run: docs/run_status.md.

## What is finished
- Fund menu verified: data/fund_menu.csv (23/23 VERIFIED), data/fund_menu_verification.csv, raw responses in data/fund_sources/raw/.
- Experiment run: 2,508 calls (main 1,200 + consistency 480 + probe 828) plus pilot 60; raw logs outputs/raw/calls_<model>.jsonl, prompts outputs/raw/prompts/, run manifests outputs/logs/.
- Coded results: outputs/experiment_results.csv, outputs/experiment_holdings.csv, outputs/coding_issues.csv.
- Backtest: data/nav/ (fuyao adj_nav), outputs/portfolio_backtest.csv, outputs/tables/T_fund_history_metrics.csv; window 2021-11-01 to 2026-09-30 (59 months).
- Tables: outputs/tables/T01-T21 and outputs/tables/results_digest.md (all numbers for the report come from here).
- Figures: outputs/figures/F00-F08.
- Manual coding sample: docs/manual_coding_sample.csv (60 replies; coder columns empty).

## Changes from the original plan that the report must state
1. Product risk ratings come from Eastmoney / Tiantian Fund (structured field RISKLEVEL), because the fuyao (Tonghuashun) API has no risk-rating field. fuyao is used for NAV history (backtest). Menu: R1 3, R2 4, R3 2, R4 14, no R5.
2. Models were called through OpenRouter instead of the Volcano Engine Ark Agent Plan (Agent Plan key not available; pay-as-you-go endpoints require Chinese real-name verification):
   - doubao: bytedance-seed/seed-2.0-mini (provider Seed / ByteDance)
   - deepseek: deepseek/deepseek-v4-flash (provider SiliconFlow; no first-party DeepSeek provider on OpenRouter)
   - kimi: moonshotai/kimi-k2.6 (provider Moonshot AI)
   Temperature 0.7, max_tokens 2,500, JSON mode, reasoning disabled for all three, provider pinned without fallbacks. Prompts, profiles, fund list, metrics and hypotheses unchanged.
3. Kimi reasoning was disabled after the pilot: with default reasoning all 20 pilot calls used the 2,500-token limit and returned empty content.
4. The menu source line inside the system prompt reads "Eastmoney / Tiantian Fund (product risk ratings and reported asset allocation)", data as of 2026-10-23.
5. Cost: USD 3.13 in total (OpenRouter usage), 3.72 M prompt and 1.46 M completion tokens.

## Main results table (main sample, T11 and T13)

| model | condition | n | rating breach % | equity over cap % | mean equity % |
|---|---|---|---|---|---|
| deepseek | BASE | 200 | 51.5 | 22.0 | 32.0 |
| deepseek | SUIT | 200 | 42.0 | 16.0 | 28.7 |
| doubao | BASE | 200 | 51.5 | 20.5 | 31.0 |
| doubao | SUIT | 199 | 40.7 | 13.1 | 24.7 |
| kimi | BASE | 200 | 49.5 | 18.5 | 28.0 |
| kimi | SUIT | 200 | 25.0 | 11.5 | 23.0 |

SUIT lowers rating breaches in every model (paired McNemar, Holm-adjusted p < 0.001 for all three); equity over cap falls by 6-7 points (p_holm 0.012-0.029). Holding-period and loss-tolerance breaches are at or near 0 in every cell. For all other results use results_digest.md.

## Still open
- Manual double coding of docs/manual_coding_sample.csv by two team members.
- report/*.docx and presentation/*.pptx were not touched by the run session.

## Report build (2026-10-23)
- report/report_source.md now contains the results (Section 9), discussion (10), implications (11), conclusion (13), abstract findings and result-based limitations (12). All numbers come from outputs/tables (T04-T21) and the supplementary tables T22-T25 written by report/report_supplement.py.
- Built with `python report/report_supplement.py && python report/make_appendices.py && node report/build_report.js report/final_report.docx`.
- Still open: group member names and submission date on the title page, manual double coding (Appendix E), slides (need the course template).
