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

## Step 2 - models: BLOCKED (Agent Plan key)

- `python src/run_experiment.py --list-models`: the plan endpoint has no /models route (HTTP 404 for https://ark.cn-beijing.volces.com/api/plan/v3/models).
- Instead, one test call ("Reply with the word OK.", max_tokens 20) was sent per candidate name to /api/plan/v3/chat/completions on 2026-10-23:
  - doubao-seed-2.0-mini, deepseek-v4-flash, kimi-k2.6, kimi-k2.8-preview, kimi-k3, glm-5.3-flash: HTTP 401 AuthenticationError ("The API key or AK/SK in the request is missing or invalid").
  - kimi-k2.5, glm-5, glm-4.7: HTTP 404 UnsupportedModel ("does not support the agent plan feature").
- The same key is accepted as an account key elsewhere: /api/v3 answers 404 InvalidEndpointOrModel (model not activated for pay-as-you-go), /api/coding/v3 answers 400 InvalidSubscription (no Coding Plan). The key in `AI_agents` is therefore a valid Ark key, but not an Agent Plan key.
- Volcano's Agent Plan quick start (https://www.volcengine.com/docs/82379/2373738, read 2026-10-23) states that the plan requires its own dedicated Agent Plan API Key from the Agent Plan console; other Ark API keys cannot be used with it.
- Config model names were set from the official Agent Plan model table (https://www.volcengine.com/docs/82379/2366394): doubao = doubao-seed-2.0-mini, deepseek = deepseek-v4-flash, kimi = kimi-k2.8-preview (kimi-k3 forces thinking and is not in the Small tier). They are not yet confirmed by a successful call.
- `python src/run_experiment.py --dry-run`: 2,508 planned calls, 0 completed, estimated 4.01 M input tokens.

Needed to continue: an Agent Plan API Key (Agent Plan console, with an active Agent Plan subscription) in `AI_agents`. Steps 3-6 not started; no model output exists.
- 2026-10-23, second key supplied for `AI_agents`: identical results (plan endpoint 401 in OpenAI and Anthropic formats; /api/v3 404 model not activated; /api/coding/v3 400 InvalidSubscription for account 2133393355). It is also a regular Ark key, not an Agent Plan key.

## Step 2 (revised) - models via OpenRouter

Volcano Engine Ark could not be used: both keys supplied for `AI_agents` were ordinary Ark keys rejected by the Agent Plan endpoint, and the pay-as-you-go route needs custom inference endpoints, which require Chinese real-name verification that the account holder cannot complete. The same three model families were therefore called through OpenRouter (https://openrouter.ai/api/v1, key in `OPENROUTER_API_KEY`). Config: the ark-agent-plan entries are disabled, three `route: openrouter` entries are enabled; the unused alternative-openrouter deepseek template was removed.

| key | model ID | provider (pinned, allow_fallbacks false) | reasoning |
|---|---|---|---|
| doubao | bytedance-seed/seed-2.0-mini | Seed (ByteDance; the only provider) | disabled |
| deepseek | deepseek/deepseek-v4-flash | SiliconFlow (fp8; no first-party DeepSeek provider on OpenRouter) | disabled |
| kimi | moonshotai/kimi-k2.6 | Moonshot AI (first party) | disabled |

Prices on 2026-10-23 (USD per 1M input / output tokens): seed-2.0-mini 0.10 / 0.40; deepseek-v4-flash 0.091 / 0.182; kimi-k2.6 0.65 / 3.41. Kimi was chosen over GLM because a Kimi chat model is available. Temperature 0.7, max_tokens 2500 and JSON mode unchanged.

Other changes:
- config menu.source shortened to "Eastmoney / Tiantian Fund (product risk ratings and reported asset allocation)", because this string is inserted into the system prompt ("FUND MENU (data as of ...; source: ...)"); the longer explanation is in Step 1 above. NAV data are not shown to the models.
- src/llm_client.py: the serving provider returned by OpenRouter is logged in `provider`.

## Step 3 - pilot (60 calls, 2026-10-23)

- First pass: doubao 20/20 and deepseek 20/20 ok; kimi 0/20, every call finish_reason "length" with 2,499 of 2,500 completion tokens spent on reasoning and empty content (Kimi reasons by default on OpenRouter). Reasoning was then disabled for kimi, matching the other two models (the original Ark config also disabled thinking for doubao and deepseek). The 20 failed records stay in outputs/raw/calls_kimi.jsonl; the rerun retried them: 20/20 ok.
- `python src/code_responses.py`: 60 replies coded, 0 issues; parse_status ok 60/60; off-menu codes 0; weight sum 100 in every reply; funds per reply: doubao mean 5.0, deepseek 4.75, kimi 5.85 (range 3-7).
- Cost per successful call: doubao USD 0.00040, deepseek 0.00031, kimi 0.00277; forecast for the main run (836 calls per model) USD 2.91. Pilot spend including the failed kimi calls: about USD 0.28.

## Step 5 (part) - NAV data for the backtest

- `python src/backtest.py fetch --source fuyao` (2026-10-23): 23/23 funds, range=fyear, adj_nav, dates 2021-10-20/22 to 2026-09-30 (window end fixed at 2026-09-30 by backtest.py).
- adj_nav check against unit_nav from the same raw files: adj_nav includes distributions. Examples over the five years: 000015 unit -2.1% vs adj +17.5%; 100018 +0.9% vs +17.9%; 110017 +2.2% vs +22.4%; 161725 -61.6% vs -59.5%; money market funds unit 0% vs adj +7.4% to +7.7%. Funds with adj_nav equal to unit_nav throughout (e.g. 110020, 000083, 163406) show no distribution in the window.
