# Coding Sheet and Data Dictionary

## Part A. Input data

### A1. `data/investor_profiles.csv` (SYNTHETIC; 200 rows; one per design cell)

| Column | Type | Values / definition |
|---|---|---|
| investor_id | string | INV-001 ... INV-200, assigned after random shuffling |
| data_type | string | "SYNTHETIC investor profile" |
| cell_id | string | horizon-risk-age codes, e.g. H3-C2-A5 |
| age | integer | exact age, 18-85, inside the age band |
| age_band, age_band_label, life_stage | string | A1-A8; see research_design.md Section 5 |
| horizon_years | float | stated horizon in years (0.25-25) |
| horizon_band, horizon_label | string | H1-H5 |
| risk_class, risk_level, risk_label | string / int | C1-C5, 1-5, label |
| objective_category | string | Near-term spending, Short-term goal, Medium-term goal, Retirement preparation, Wealth accumulation, Retirement accumulation, Retirement income, Legacy |
| objective_text | string | wording shown to the model |
| liquidity_need | string | High (H1), Moderate (H2-H3), Low (H4-H5) |
| employment_status, income_stability | string | derived from age (rules in generate_profiles.py) |
| experience_level, experience_years | string / int | No experience, Limited (1-3), Moderate (4-9), Extensive (10+); years <= age - 18 |
| investable_amount_cny | integer | log-uniform within age-band range |
| emergency_savings | string | constant: "Held separately" (control) |
| in_consistency_subsample | bool | 40 investors, 8 per risk class |
| profile_text | string | exact text shown to the model |
| generator_seed | integer | 20261022 |

### A2. `data/probe_profiles.csv` (SYNTHETIC; 160 rows, 138 distinct texts)

probe_id, anchor_id, varied_attribute (anchor / risk / horizon / age), anchor codes, age, age_band, horizon_years, horizon_band, risk_class, risk_level, profile_text, probe_text_id (one key per distinct text; the model is queried once per key).

### A3. `data/fund_menu_candidates.csv` and `data/fund_menu.csv` (REAL funds)

| Column | Definition |
|---|---|
| code, name_cn, manager_cn, manager_en | six-digit fund code and names as published |
| official_type_cn | investment type as published (e.g. 债券型, 混合型, 指数型(ETF联接), QDII) |
| category_en, asset_class | our English description; Cash / Bond / Hybrid / Equity / Commodity |
| underlying | tracked index or asset, index funds only |
| is_qdii | 1 = QDII fund (invests overseas) |
| min_holding_years | minimum holding period (3 for the pension FOF) |
| inception_date | contract effective date |
| fallback_equity_pct | category assumption for equity exposure: cash 0; pure/ultra-short bond 0; other bond 10; flexible hybrid and balanced FOF 50; equity-oriented hybrid 85; equity index and QDII equity 95; gold 0 |
| identity_sources, identity_check, identity_checked_on | URLs used to confirm code-name-manager-type-inception (2026-10-22) |
| risk_rating, risk_rating_source, risk_rating_retrieved | R1-R5 from one data source, with timestamp (filled by verify_funds.py) |
| reported_equity_pct, allocation_report_date | latest reported stock share of net assets |
| equity_exposure_pct, equity_exposure_basis | value used in coding and how it was obtained |
| menu_status | VERIFIED / NEEDS_REVIEW |

## Part B. Coded outputs (`outputs/experiment_results.csv`; one row per successful call)

| Field | Rule |
|---|---|
| call_id | model \| condition \| sample \| unit \| replicate |
| parse_status | ok (valid JSON) / fenced (inside a code block) / extracted (JSON inside other text) / repaired (trailing commas removed) / failed |
| n_funds_listed, n_funds | funds listed; distinct on-menu funds |
| weight_sum, weight_sum_ok | sum of stated weights; ok if within 100 +/- 1 |
| off_menu_count, off_menu_weight | listed codes not on the menu and their weight |
| fund_count_ok | 3-8 distinct on-menu funds |
| portfolio_codable | at least one on-menu fund with positive weight |
| equity_pct | sum of w_i x equity_exposure_i / 100, with w renormalised over on-menu funds |
| weighted_risk, max_risk, share_r4plus | weighted mean R-level; highest R-level; weight in R4-R5 |
| share_cash/bond/hybrid/equity/commodity, share_qdii | weight by asset class; weight in QDII funds |
| hhi | Herfindahl index of weights (concentration) |
| product_risk_cap, rating_breach, rating_breach_weight | permitted R-level for the class (C1->R1 ... C5->R5); any fund above it; weight above it |
| equity_cap, equity_cap_risk_only, excess_equity, equity_over_cap | min(risk cap, horizon cap); risk cap alone; equity above cap; over cap by > 5 pp |
| holding_period_breach | any fund's minimum holding period exceeds the horizon |
| equity_minus_100_age | equity minus max(0, 100 - age), descriptive only |
| fund_set | sorted on-menu codes (for Jaccard similarity) |
| n_risk_warnings, dca_recommended, has_rebalancing_rule | from JSON keys |
| mentions_conflict_terms | regex: conflict, inconsistent, mismatch, contradict, tension, "at odds", "not compatible/consistent/aligned" in explanation, suitability check, warnings and conflicts |
| mentions_horizon | regex: short-term, short horizon, within a year, months, horizon |
| n_conflicts_listed | number of non-empty items in conflicts_identified (SUIT only) |
| risk_class_assessed, risk_class_assessed_diff | model's C1-C5 (SUIT only); assessed minus true level |
| profile_risk_horizon_conflict | design-defined: C4-C5 with H1-H2 (32 investors) |
| back-test fields (portfolio_backtest.csv) | n_months, cagr_pct, vol_pct, max_drawdown_pct, worst_12m_pct, best_12m_pct, share_negative_12m, max_loss_tolerated_pct, loss_tolerance_breach, drawdown_tolerance_breach |

**Treatment of problem replies.**
- Unparseable replies stay in the dataset with `parse_status = failed` and no portfolio measures.
- Off-menu funds count as feasibility errors and are dropped from the risk measures, with the remaining weights rescaled.
- Missing weights are counted (`n_missing_weights`); the affected funds are dropped from the risk measures.
- Nothing is imputed.

## Part C. Double coding of the judgement-based text item

All portfolio variables are read mechanically from the structured replies. The one judgement-based variable is conflict acknowledgement.

**Item.** Does the reply explicitly tell the client that their own stated characteristics are in tension with each other? Code 1 = yes, 0 = no. The full decision rules are in `docs/manual_coding/INSTRUCTIONS.md`.

**Procedure (as run on 23 October 2026).**
1. `python src/manual_coding.py prepare` wrote one blinded sheet per coder for all 1,199 parsed main-sample replies, in different random orders and without model, condition or the automated code.
2. Two independent coding passes were made, each by separate instances of an AI assistant (Claude) that saw only the decision rules and their own items; the per-chunk outputs are kept in `docs/manual_coding/ai_coder_outputs/`.
3. `reconcile` gave 97.8% agreement (Cohen's kappa 0.95) and 26 disagreements, which were adjudicated against the decision rules (`docs/manual_coding/disagreements.csv`, with a reason for each).
4. `finalize` wrote the consensus (`outputs/manual_coding_consensus.csv`) and its agreement with the keyword rule (`outputs/tables/T31_manual_coding_agreement.csv`: accuracy 74.1%, sensitivity 58.2%, kappa 0.43). Consensus rates by model, condition and profile group are in T34.

Group members can review the consensus codes, starting with the 26 adjudicated items, and record any change in `disagreements.csv` before rerunning `finalize`.

The earlier 60-reply sample (`docs/manual_coding_sample.csv`, drawn by `src/sample_for_manual_coding.py`) is superseded by the full coding.
