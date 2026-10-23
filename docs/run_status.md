# Run status

## Environment

- 2026-10-23, first attempt in a cloud container: blocked (keys not set, hosts ark.cn-beijing.volces.com and fuyao.aicubes.cn denied by the container's network policy). Nothing was run.
- 2026-10-23, rerun on a local machine (macOS, Python 3.14.6): keys `AI_agents` and `fuyao` present (checked by name only); ark.cn-beijing.volces.com answers HTTP 401 without a key, fuyao.aicubes.cn HTTP 200. `pip install -r requirements.txt` OK; `pytest -q tests`: 11 passed.

## Step 1 - fund data

### Facts confirmed from live fuyao responses (raw files in data/fund_sources/raw/)

- Product risk rating: **not provided by fuyao.** /api/fund/profile/detail returns thscode, ticker, fund_name, estab_date, company_id, mgmt_name, manager_name, fund_scale, unit_nav, manager_info, trade_rule, rate_info. /api/fund/diagnostics/detail returns 0-100 diagnostic scores (e.g. anti_risk_score), drawdowns and Sharpe ratios, which are not product risk ratings. /api/fund/portfolio/holdings has no rating either. The field tables in https://fuyao.aicubes.cn/llms-full.txt (read 2026-10-23) list no risk-rating field for any fund endpoint.
- fund_name is an abbreviated display name (e.g. 300ETFA for 110020), so fuyao names cannot be matched to the official names.
- Timestamps (estab_date, nav_date, end_date_ms) are milliseconds, Asia/Shanghai calendar dates (per the docs; e.g. 1634832000000 = 2021-10-22 00:00 Beijing).
- range=fyear returns five years ending at the latest NAV date: 2021-10-22 to 2026-10-22 (1,217 rows for 110020, 1,827 daily rows for money market fund 000198).
- adj_nav: for 000198 unit_nav is fixed at 1.0 and adj_nav rises from 1.3063 to 1.4053 (income is accumulated), so adj_nav is a usable total-return level for money market funds. For 110020 adj_nav equals unit_nav on every row in the window.
- Holdings summary ratios (total_stock_ratio_pct, stock_ratio_pct, total_fund_ratio_pct) are at data level; data.item[] lists individual positions. 000198 holdings: code 3002 "Fund holdings are not available yet".
- LOF funds (163406, 160119, 161725, 160416) return code 3001 "Fund not found" as 16xxxx.OF and are found as 16xxxx.SZ.

### Risk-rating source

Because fuyao has no product risk rating, `verify_funds.py --source eastmoney` was used (Eastmoney hosts reachable). All 23 ratings come from the structured field RISKLEVEL of the Eastmoney basic-information API (fundmobapi.eastmoney.com FundMNNBasicInformation), mapped 1-5 to R1-R5; the page-text fallback was not used for any fund. Result: 23/23 VERIFIED; R1: 3, R2: 4, R3: 2, R4: 14, R5: 0. These are Eastmoney's (distributor) ratings, retrieved 2026-10-23.

Reported stock allocation (for bond, hybrid and non-feeder equity funds) is also from Eastmoney (pingzhongdata Data_assetAllocation, report date 2026-06-30). NAV history for the backtest uses fuyao.

config menu.as_of = 2026-10-23; menu.source states both sources (the planned wording "Tonghuashun financial data API via fuyao.aicubes.cn" alone would be inaccurate for the ratings).

### Code changes (Step 1)

- src/fund_data.py FuyaoSource:
  - `thscode()`: LOF codes starting with 16 use the .SZ suffix.
  - NAV dates converted from ms in Asia/Shanghai (previously read as UTC, which shifted every date one day earlier).
  - estab_date and holdings end_date_ms converted to YYYY-MM-DD.
  - Holdings: read total_stock_ratio_pct / stock_ratio_pct from data level (previously looked in item[0], a single position, and found nothing).
  - `_find_risk()`: ignore fields whose name contains "score" (anti_risk_score = 2 for 007300 had been read as rating R2).
- src/fund_data.py EastmoneySource: same Asia/Shanghai date fix for NAV timestamps.
- src/verify_funds.py:
  - Six funds have abbreviated Eastmoney names (006662, 006580, 007300, 050025, 000071, 160416). A name mismatch now passes only if the retrieved manager and inception date both agree with the candidate file; recorded as name_match = "abbreviated (manager and inception match)". All six agree on both.
  - ETF-feeder detection also checks the fund name: 270042 has official type "QDII/股票型" but is an ETF feeder; its reported direct stock share (0%) had been used as equity exposure instead of the 95% feeder category assumption.
