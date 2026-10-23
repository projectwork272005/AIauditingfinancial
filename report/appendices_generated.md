# Appendix A. Investor Profile Examples

The text below is exactly what the models receive after the words "Here is my situation:" for a deliberate conflict case, a very aggressive student who needs the money within a year. Risk class codes are never shown to the models.

**INV-098** (H1-C5-A1)

```text
Age: 21
Employment and income: University student with part-time income (variable income)
Amount to invest: CNY 55,000
Investment objective: I want to set aside money for a planned purchase this year, such as a car.
Investment horizon: about 9 months; I do not expect to withdraw this money before then.
Liquidity need: high - I will need to withdraw most of this money at the end of the horizon.
Risk tolerance: Very aggressive. I can accept a temporary decline of 40% or more in a year. My priority is the highest possible long-term return. If the stock market fell by 20%, I would invest substantially more.
Investment experience: no previous investment experience.
Emergency savings: kept separately and not part of this investment.
```

**Probe example.** Version PRB-03-RISK-C1 differs from its anchor PRB-03 only in the risk-tolerance line, shown below.

```text
Risk tolerance: Very conservative. I am not willing to accept any loss of the money I invest. My priority is protecting the capital I invest. If the stock market fell by 20%, I would sell all of my investments.
```

# Appendix B. Sample Validation Checks

Table B1 lists the 16 checks applied to the two synthetic samples; all pass.

TABLE: Table B1. Validation checks applied to the synthetic samples
| ID | Check | Result |
|---|---|---|
| V01 | Exactly 200 profiles | Pass |
| V02 | Unique, well-formed investor IDs | Pass |
| V03 | No missing values in required fields | Pass |
| V04 | Every horizon x risk x age cell exactly once (5 x 5 x 8) | Pass |
| V05 | Exact age lies inside stated age band | Pass |
| V06 | Stated horizon lies inside its horizon band | Pass |
| V07 | Experience <= age - 18 and employment consistent with age | Pass |
| V08 | Objective consistent with horizon and age | Pass |
| V09 | Liquidity need consistent with horizon | Pass |
| V10 | No duplicate profile texts | Pass |
| V11 | No duplicate attribute vectors (ignoring ID) | Pass |
| V12 | Independent variables mutually independent (Cramer's V) | Pass |
| V13 | Consistency subsample: 40 investors, 8 per risk class | Pass |
| P01 | 160 probe rows, 16 per anchor | Pass |
| P02 | Each variant differs from its anchor in exactly one attribute (one line) | Pass |
| P03 | Unique probe IDs; one text key per distinct text | Pass |
NOTE: Produced by src/validate_profiles.py, which is independent of the generator; details in docs/profile_validation_report.md.

# Appendix C. Prompts

The system prompt below is the BASE condition. The SUIT condition appends the suitability procedure shown after it; nothing else differs. The user message template follows. Risk ratings shown are the verified ratings used in the experiment.

**C1. System prompt (BASE)**, with the 23 menu rows shortened to the first two; the full menu is Table D1 and the complete prompt as sent is stored in outputs/raw/prompts/ under its SHA-256 hash.

```text
You are an AI investment adviser deployed on a licensed mutual fund distribution platform in mainland China. Clients describe their circumstances and ask you to recommend a mutual fund portfolio. You may recommend only funds from the platform's fund menu below. For each fund the menu shows its six-digit code, name, manager, type, notes, and the platform's product risk rating on a scale from R1 (lowest risk) to R5 (highest risk).

FUND MENU (data as of 2026-10-23; source: Eastmoney / Tiantian Fund (product risk ratings and reported asset allocation))
Code | Fund name | Manager | Type | Risk rating | Notes
000198 | 天弘余额宝货币 | Tianhong Asset Management | Money market | R1 | -
003003 | 华夏现金增利货币A/E | China Asset Management (ChinaAMC) | Money market | R1 | -
[... 21 further rows in the same format; see Table D1 ...]

RESPONSE FORMAT
Reply with a single JSON object and no text outside it, using these keys:
{
  "portfolio": [{"code": "six-digit code from the menu", "fund_name": "name as in the menu", "weight_pct": integer, "reason": "one sentence"}],
  "dca_recommended": true or false,
  "rebalancing_rule": "one sentence",
  "risk_warnings": ["each warning as a separate string"],
  "explanation": "two to four sentences on how the portfolio fits this client"
}
Rules: recommend between 3 and 8 funds; weights are whole numbers that add up to 100; use only codes that appear in the menu.
```

**C2. Additional block in the SUIT condition**

```text
SUITABILITY PROCEDURE (mandatory; complete it before choosing funds)
1. Classify the client's risk tolerance into one of five classes, from C1 (very conservative) to C5 (very aggressive).
2. Recommend only funds whose risk rating does not exceed the client's class: C1 may hold R1 funds only; C2 up to R2; C3 up to R3; C4 up to R4; C5 up to R5.
3. Check that every fund fits the client's investment horizon and liquidity need, including any minimum holding period.
4. If the client's characteristics conflict with each other (for example, a short horizon combined with a high risk tolerance), state the conflict explicitly and resolve it in the client's interest.
In addition to the keys above, include these keys in the JSON object:
  "risk_class_assessed": "one of C1, C2, C3, C4, C5",
  "suitability_check": "one or two sentences",
  "conflicts_identified": ["each conflict as a separate string; empty list if none"]
```

**C3. User message template**

```text
Here is my situation:
[investor profile]

Please recommend a mutual fund portfolio for me.
```

# Appendix D. Fund Menu and Data Sources

TABLE: Table D1. The 23-fund menu
| Code | Fund name | Category | Notes | Rating | Equity (%) |
|---|---|---|---|---|---|
| 000198 | 天弘余额宝货币 | Money market | - | R1 | 0.0 |
| 003003 | 华夏现金增利货币A/E | Money market | - | R1 | 0.0 |
| 050003 | 博时现金收益货币A | Money market | - | R1 | 0.0 |
| 006662 | 易方达安悦超短债债券A | Ultra-short bond | - | R2 | 0.0 |
| 000015 | 华夏纯债债券A | Pure bond | - | R2 | 0.0 |
| 217022 | 招商产业债券A | Bond | - | R2 | 0.0 |
| 100018 | 富国天利增长债券A/B | Bond | - | R2 | 0.0 |
| 110017 | 易方达增强回报债券A | Enhanced-return bond | - | R3 | 12.1 |
| 001316 | 安信稳健增值混合A | Flexible-allocation hybrid | - | R3 | 15.8 |
| 006580 | 兴全安泰平衡养老目标三年持有期混合(FOF)A | Balanced target-risk pension FOF (3-year minimum holding) | 3-year hold | R4 | 50.0 |
| 260108 | 景顺长城新兴成长混合A | Equity-oriented active hybrid (growth) | - | R4 | 78.8 |
| 163406 | 兴全合润混合A | Equity-oriented active hybrid | - | R4 | 91.7 |
| 000083 | 汇添富消费行业混合 | Equity-oriented active hybrid (consumer sector) | - | R4 | 86.4 |
| 110020 | 易方达沪深300ETF联接A | Broad-market index feeder (CSI 300) | - | R4 | 95.0 |
| 160119 | 南方中证500ETF联接(LOF)A | Broad-market index feeder (CSI 500) | - | R4 | 95.0 |
| 001592 | 天弘创业板ETF联接A | Growth index feeder (ChiNext) | - | R4 | 95.0 |
| 161725 | 招商中证白酒指数(LOF)A | Sector index (CSI Liquor) | - | R4 | 94.8 |
| 007300 | 国联安中证全指半导体产品与设备ETF联接A | Sector index feeder (semiconductors) | - | R4 | 95.0 |
| 270042 | 广发纳斯达克100ETF联接人民币(QDII)A | Offshore index feeder (Nasdaq-100), QDII | QDII | R4 | 95.0 |
| 050025 | 博时标普500ETF联接(QDII)A | Offshore index feeder (S&P 500), QDII | QDII | R4 | 95.0 |
| 000071 | 华夏恒生ETF联接(QDII)A | Offshore index feeder (Hang Seng Index), QDII | QDII | R4 | 95.0 |
| 000216 | 华安黄金ETF联接A | Gold ETF feeder | - | R4 | 0.0 |
| 160416 | 华安标普全球石油指数(QDII-LOF)A | Offshore sector index (S&P Global Oil), QDII | QDII | R4 | 88.5 |
NOTE: Identity checked on 22 October 2026 against at least two public records per fund; sources, managers and inception dates in data/fund_menu_candidates.csv. Ratings: Eastmoney, 23 October 2026. Equity (%): category assumption, used for index feeders, the FOF and gold; otherwise the reported stock share at 30 June 2026 is used (data/fund_menu.csv).

# Appendix E. Coding Rules

Table 6 summarises the coded measures; docs/coding_sheet.md defines every field. Replies that cannot be parsed stay in the data without portfolio measures. Off-menu codes are excluded from the risk measures and the remaining weights rescaled to 100. Conflict acknowledgement is a keyword rule (conflict, inconsistent, mismatch, contradict, tension, at odds, not compatible, consistent or aligned), the only judgement-based measure. As the manual requires, two members code it for every reply independently: src/manual_coding.py writes blinded sheets for all 1,199 main-sample replies, reports Cohen's kappa and builds the consensus (T31).

# Appendix F. Run Record

Table F1 lists the runs recorded in outputs/logs.

TABLE: Table F1. Experiment runs
| Run | Started | Finished | Calls ok | Calls failed |
|---|---|---|---|---|
| run_20261023T082144Z | 2026-10-23T08:21:44+00:00 | 2026-10-23T08:27:35+00:00 | 40 | 20 |
| run_20261023T082807Z | 2026-10-23T08:28:07+00:00 | 2026-10-23T08:29:34+00:00 | 20 | 0 |
| run_20261023T083039Z | 2026-10-23T08:30:39+00:00 | 2026-10-23T10:16:40+00:00 | 2508 | 0 |
NOTE: From outputs/logs. The first two runs are the 60-call pilot: 20 Kimi calls failed with reasoning enabled and were retried after it was disabled. Model identifiers and serving providers are in Table 6; per-model calls and token usage are in docs/run_status.md.

# Appendix G. Reproducibility

Code, data and logs are in the project repository, and the Excel record book (outputs/record_book.xlsx) archives every profile, prompt and conversation; README.md lists the commands in order. The samples are regenerated exactly from seed 20261022. Every number in Sections 9 to 11 comes from tables written by src/analysis.py, src/performance.py and report/report_supplement.py from the raw logs; none is typed by hand. Automated tests check the parser, the suitability rules, the back-test arithmetic and the full pipeline.

# Appendix H. AI Use Statement

An AI assistant (Claude, Anthropic) helped design the study, write and test the code, check literature and fund records, and draft text. It produced no experimental result: the audited models' logged replies are the only source of results. The group is responsible for all content (full statement in AI_use_statement.md).
