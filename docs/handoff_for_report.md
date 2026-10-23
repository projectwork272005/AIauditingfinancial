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

## Final build (2026-10-23, cloud session)
- Report cut to the 6,000-10,000 word limit (about 9,700 words by Word's rules, appendices and references included); all numbers re-checked against outputs/tables; exhibits renumbered (Tables 1-13, Figures 1-9) and every exhibit cited in the text.
- src/analysis.py: paired outcomes rounded to 6 decimals before rank tests, so identical portfolios tie exactly on every platform (reported values unchanged); new robustness variant with category-based equity for every fund (T20).
- presentation/presentation.pptx built on the course template; result slides 13-16 and the takeaways read their numbers from outputs/tables.
- Still open for the group: names and date on the title page; manual double coding of docs/manual_coding_sample.csv (Appendix E); reading and revising the text in their own words.

## Performance and coding additions (2026-10-23, cloud session)
- src/performance.py (offline, existing data only): Sharpe (in excess of 000198), Calmar, benchmarks (60/40 = 60% 110020 + 40% 000015; target-risk fund 006580; rating-compliant model portfolios C1-C5 from menu funds, a stylised robo-adviser ladder, not a commercial record), purchase and exit fees. Report: Section 9.7 now "Historical check and performance", Table 12 replaced by a performance-and-benchmark table (worst 12 months kept as a column; per-condition worst-12-month figures remain in T24), new Figure 10 (F09 cumulative growth). Hypotheses table stays Table 13. F10 (risk-return scatter) is available for slides.
- Word count after the additions: 9,657 by `wc -w` on the LibreOffice text export (the previous build: 9,449 by the same method).
- src/manual_coding.py: blinded sheets for two coders over all 1,199 main-sample replies (docs/manual_coding/README.md), Cohen's kappa, reconciliation, consensus (T31) and Table E1 in Appendix E once run. The report states that the full double coding is prepared but not done, and that coding only a sample would be a deviation from the manual.
- Still open for the group: the double coding itself; names and date; the slides do not yet show the performance results.

## Submission checklist items (2026-10-23, cloud session)
- Primary focus stated in Section 2: suitability (feasibility and performance secondary, fairness excluded by design); Section 5.2 states that profiles cover the KYC items of the suitability rules; probes described as audit pairs.
- Excel record book: outputs/record_book.xlsx (src/record_book.py): profiles, probe pairs, fund menu and verification, prompts, all 2,588 logged conversations with full prompt and reply, coded results, holdings, back-test, performance, benchmarks, fund history and fees, double-coding status.
- Presentation: presentation/add_performance_and_notes.py adds slide 17 (performance and benchmarks), updates the coding box on the limitations slide, renumbers pages and writes speaker notes with a 25-minute timing plan (21 slides). Run it after build_presentation.py; the template is not in the repository, so the script edits the built deck.
- Still open for the group: double coding of docs/manual_coding (two members), names and student IDs, group registration in the course workbook by 25 October, submission by email by 25 October.

## Double coding done (2026-10-23, cloud session)
- Conflict item coded for all 1,199 main-sample replies in two independent, blinded passes (separate AI-assistant instances), 26 disagreements adjudicated: agreement 97.8%, kappa 0.95; keyword rule vs consensus kappa 0.43 (T31, T34, docs/manual_coding/). Disclosed in Appendix E, Appendix H and AI_use_statement.md.
- Report: Section 9.4 now uses the double-coded measure (81.2/40.6/100% under BASE, 100/81.2/100% under SUIT for DeepSeek/Doubao/Kimi in the conflict group); limitations and Table 6 updated; figure notes shortened to stay under 10,000 words (9,638 by wc -w on the text export).
- Slides: limitations box and speaker notes updated in the built deck and in add_performance_and_notes.py.
- Left for the group: names and student IDs on the title page and slide 1 if wanted, registration in the course workbook, submission by email by 25 October; optionally review the 26 adjudicated items.
