# Research Design

**Working title:** *Who Gets What? A Factorial Audit of How Large Language Models Tailor Mutual Fund Portfolios to Investor Age, Risk Tolerance and Investment Horizon*

**Status (22 October 2026):** design frozen; synthetic samples generated and validated; pipeline, coding, back-test and analysis code implemented and tested on fixtures. **No model has been queried yet.** The experiment requires API keys and network access that the current environment does not have (see Section 11). Nothing in this document reports a result.

---

## 1. Review of the reference materials (Phase 1)

| File | What it is | What we take from it | What we change or do not reuse |
|---|---|---|---|
| `Auditing_AI_Mutual_Fund_Advisors_Research_Report.docx` | A completed class report auditing two Chinese LLMs (Doubao-Seed-2.0-mini, DeepSeek-V4-Flash) on 2,058 questionnaire-based profiles x 2 information conditions (from memory vs. a 50-fund E Fund list). Reports hallucination, allocation errors, an equity-vs-requested-risk curve, conflict handling and a model x condition ANOVA. | The audit logic (fixed prompts, synthetic clients, coded outputs), the emphasis on effect sizes at large N, and the finding that a product list removes fabricated funds. | We do not reuse its research question, profiles, prompts, fund list or numbers. Its results are not ours and are not cited as evidence. Four of its references could not be verified (see `docs/references_verification.md`). Its 50-fund list carries risk ratings that predate E Fund's August 2026 re-rating of 20+ funds, so it cannot be used without re-verification. |
| `run_ai_recommendations.py` | A script that reads prompts from an Excel sheet, calls an OpenAI-compatible chat API in 8 threads with exponential back-off, and writes replies back into the workbook, skipping rows already answered. | Provider-agnostic OpenAI-compatible calls; retries; resumability. | It overwrites the source workbook, logs no prompt hashes, model versions, token usage or timestamps, and keeps no raw record of failed attempts. Our runner (`src/run_experiment.py`) is append-only JSONL, logs every request parameter and hash, randomises call order and never edits inputs. |
| `AI_Investment_Advisor_SMBU_Template.pptx` | A 29-slide, 16:9 Shenzhen MSU-BIT University class deck (Calibri / Microsoft YaHei; navy 365B7E, red BE4D4C, grey 7F8C99; campus photographs on title and section slides; logo top right; numbered footer). | The visual system and section rhythm (title, contents, section dividers, content slides, takeaways, thank-you slide). | All content is replaced by our own project; no placeholder or template results are carried over. |

**Data in the reference files.** The report contains results tables and a fund list but no raw data. The script contains no data, only an Excel path and an empty API key. The deck repeats the report's numbers. None of these numbers is used anywhere in this project.

## 2. Research problem and questions

General-purpose LLMs are increasingly used as informal investment advisers. Suitability rules in China, and in most other jurisdictions, require advice to reflect each client's risk tolerance, investment horizon and circumstances. Recent audits suggest that LLMs reduce this multi-factor judgement to one or two inputs (Ross & Lo, 2026), echoing the "one size fits all" behaviour of human advisers (Foerster et al., 2017). They also suggest that how the model is deployed matters more than which model is used. We ask:

- **RQ1 - Responsiveness.** How strongly do LLM-recommended portfolios vary with the investor's risk tolerance, investment horizon and age, and how much weight does each attribute carry?
- **RQ2 - Suitability.** How often do recommendations breach objective suitability benchmarks: the regulatory product-risk matching rule, horizon-based limits and the investor's own stated loss tolerance (checked against historical fund data)?
- **RQ3 - Prompt-level guardrail.** Does adding an explicit suitability protocol to the deployment prompt improve alignment and reduce breaches, and at what cost (for example, over-conservatism)?
- **RQ4 - Reliability.** How consistent are recommendations for the same investor across repeated queries, and how do they shift when one attribute changes and everything else is held constant?
- **RQ5 - Model differences.** Do three models from different developers (Doubao by ByteDance, DeepSeek, and Kimi by Moonshot AI) differ on RQ1-RQ4?

**Why this question.** It follows directly from the brief: investor characteristics, consistency, suitability and alignment with fund evidence. It tests a policy-relevant idea, whether a cheap prompt-level protocol can stand in for a hard-coded suitability gate. And it can be answered with synthetic clients, a verified fund menu and an objective, regulation-anchored scoring rule, which an "is this advice good?" question cannot.

## 3. Hypotheses

Hypotheses were fixed before any model was queried. Directional hypotheses are tested one-sided only where stated; all reported p-values are two-sided unless noted, with Holm correction within each table.

- **H1.** Portfolio risk (equity exposure; weighted product risk) increases with risk tolerance (Spearman rho > 0) in every model x condition cell.
- **H2.** Portfolio risk increases with investment horizon, holding risk tolerance and age constant.
- **H3.** Portfolio risk decreases with age, holding risk tolerance and horizon constant. Life-cycle theory justifies a modest age effect even at a fixed horizon (Bodie et al., 1992; Cocco et al., 2005).
- **H4 (heuristic dominance).** Risk tolerance explains more variance in equity exposure than horizon and age combined (partial eta squared comparison).
- **H5.** The suitability-protocol prompt (SUIT) lowers the rate of product-risk breaches relative to the baseline prompt (BASE), within model.
- **H6.** Breaches concentrate where attributes conflict: aggressive investors (C4-C5) with horizons under three years.
- **H7.** Across repeated queries, equity exposure is highly reliable (ICC > 0.75), while the specific funds chosen vary (mean Jaccard similarity < 1).

## 4. Design overview

| Element | Specification |
|---|---|
| Unit of analysis | One model reply for one investor under one prompt condition |
| Independent variables (investor) | Horizon (5 levels), risk tolerance (5), age band (8), crossed in a full factorial: 5 x 5 x 8 = **200 cells, one investor per cell** |
| Experimental factor (prompt) | BASE vs SUIT, **within investor** (repeated measures) |
| Model factor | 3 models, **within investor** (repeated measures) |
| Main sample | 200 unique synthetic investors x 2 conditions x 3 models = **1,200 observations** |
| Consistency module | 40 investors (8 per risk class) queried twice more per condition and model = **480 observations** (plus their main-sample replies = 3 replicates) |
| Probe module | 10 anchor investors x 16 versions with exactly one attribute changed = 160 probe profiles (**138 distinct texts**) x 2 conditions x 3 models = **828 observations** |
| Pilot | 10 investors x 2 conditions x 3 models = 60 calls, used only to check parsing; excluded from analysis |
| Total planned calls | **2,508** (+ pilot) |

**Unique investors vs observations.** There are exactly 200 unique investors in the main sample. Every investor is evaluated under every condition and model, so the 1,200 main observations form a **repeated-measures** design, not 1,200 independent investors. Analyses that compare conditions or models are paired by investor; pooled regressions use standard errors clustered by investor.

## 5. Independent variables and categories

All category definitions live in `src/design.py`.

**Investment horizon** (time until the money is expected to be withdrawn; half-open bands):

| Code | Label | Definition | Stated values used |
|---|---|---|---|
| H1 | Short-term | < 1 year | 3, 6 or 9 months |
| H2 | Short-to-medium term | 1 to < 3 years | 1.5, 2, 2.5 years |
| H3 | Medium-term | 3 to < 5 years | 3, 3.5, 4, 4.5 years |
| H4 | Medium-to-long term | 5 to < 10 years | 5-9 years |
| H5 | Long-term | >= 10 years | 10-25 years (<= 15 for ages 75-85; <= 20 for ages 65-74) |

**Risk tolerance.** Every class is defined on the same three criteria. The class code is never shown to the model; only the label and the descriptive text are.

| Code | Label | Max acceptable one-year decline | Priority | Reaction to a 20% market fall | Highest product rating permitted |
|---|---|---|---|---|---|
| C1 | Very conservative | none | protecting capital | sell everything | R1 |
| C2 | Conservative | about 5% | stability, modest growth | sell part | R2 |
| C3 | Moderate | about 15% | balance of growth and stability | hold and wait | R3 |
| C4 | Aggressive | about 25% | long-term growth | hold, possibly add | R4 |
| C5 | Very aggressive | 40% or more | highest long-term return | invest substantially more | R5 |

The C1-C5 / R1-R5 matching rule is the one fund distributors apply under the AMAC (2017) guideline implementing the CSRC suitability measures (CSRC, 2020).

**Age** (inclusive bands covering ages 18-85 with no gaps; bands follow life-cycle stages):

| A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 |
|---|---|---|---|---|---|---|---|
| 18-24 | 25-34 | 35-44 | 45-54 | 55-59 | 60-64 | 65-74 | 75-85 |

## 6. Synthetic sample construction

- **Balanced full factorial.** Each horizon x risk x age combination occurs exactly once, so the three factors are orthogonal (Cramer's V = 0 for every pair; check V12).
- **Within-cell variation** (seed 20261022): exact age within the band; exact horizon within the band; objective wording; employment; experience; investable amount.
- **Consistency rules** (validated, checks V05-V09): employment depends on age (students only up to 21, retirees only from 60); experience <= age - 18; objective depends on horizon and age (near-term spending only for H1; retirement income only from age 50; legacy only from 65 with H5); liquidity need follows horizon.
- **Controls held constant in every profile:** emergency savings held separately; mainland China resident (implied); no gender, name or region (to keep demographic signals out of scope); same field order and sentence templates.
- **IDs** are assigned after shuffling, so the ID carries no information.
- **Validation** (`src/validate_profiles.py`): 16 checks, all passing. Report: `docs/profile_validation_report.md`.

Secondary attributes (objective, employment, experience, amount) are not independent variables. They make profiles realistic and internally consistent, and they enter robustness checks as covariates. Because objective and employment are derived from age and horizon, main-sample "age" and "horizon" effects are **bundle effects** (attribute plus its realistic correlates). The probe module isolates the pure textual effect of each attribute.

**Probe module.** Ten anchor investors are spread so that each risk class and horizon appears twice and each age band at least once. For each anchor, one attribute at a time is moved through all its other levels, with neutral secondary wording valid at every level ("stable regular income (salary or pension)", CNY 200,000, "some experience with mutual funds"). Check P02 confirms that every variant differs from its anchor in exactly one line.

## 7. Recommendation procedure

1. **Fund menu.** The menu has 23 real Chinese public mutual funds from 14 managers, covering money market, bond, hybrid, broad and sector index, QDII (overseas equity), gold and a target-risk pension FOF with a 3-year minimum holding period. Code, name, manager, type and inception date were checked against at least two public records (`data/fund_menu_candidates.csv`). Product risk ratings, the latest reported stock share and NAV histories are retrieved from one data source, preferably the course API, with URLs and timestamps (`src/verify_funds.py`). The runner refuses to start until every fund is VERIFIED.
   - *Why domestic funds only:* the profiles are mainland-Chinese investors who cannot buy foreign-domiciled funds directly. QDII funds are Chinese-registered funds and provide the overseas exposure within the same R1-R5 rating system.
2. **Prompts** (`src/prompts.py`).
   - The system message contains the adviser role, the menu with risk ratings, and a JSON response format.
   - SUIT adds a four-step suitability protocol (classify C1-C5; cap product risk; check horizon, liquidity and holding periods; disclose and resolve conflicts) and three extra JSON keys.
   - BASE is an exact prefix of SUIT (tested), so the protocol is the only difference.
   - The user message is the investor description, identical across conditions and models.
3. **Models** (`config/experiment_config.json`). Doubao-Seed (ByteDance), DeepSeek V4 Flash (DeepSeek) and Kimi (Moonshot AI; GLM by Zhipu AI if Kimi is not offered), all reached with one key through the Volcano Engine Ark Agent Plan endpoint used in the course (`https://ark.cn-beijing.volces.com/api/plan/v3`, OpenAI-compatible).
   - Temperature 0.7 for all models, as in the course reference script.
   - Reasoning or thinking modes are set to the minimum available.
   - JSON mode is used where supported; output limit 2,500 tokens.
   - Exact model IDs are read from each provider's `/models` endpoint and logged.
4. **Execution** (`src/run_experiment.py`).
   - Calls are issued in random order, so conditions and models are not confounded with time.
   - Failed calls are retried on later runs and never filled in.
   - Every call is written as one JSON line containing: call ID, model requested and returned, request parameters, SHA-256 of both prompts, the full user prompt, raw reply, finish reason, token usage, latency and timestamps.
5. **Coding** (`src/code_responses.py`). Deterministic and rule-based (`docs/coding_sheet.md`).
6. **Historical check** (`src/backtest.py`). Returns of every recommended mix over 60 months (2021-10 to 2026-09), rebalanced monthly.

## 8. Dependent variables and metrics

| Metric | What it measures | Calculation | Why it matters |
|---|---|---|---|
| Parse success; codable | Format compliance | Valid JSON with a usable portfolio | Advice that cannot be read cannot be executed |
| Off-menu rate | Feasibility | Share of replies naming a code not on the menu | Fabricated or unavailable products |
| Weight-sum validity | Feasibility | Weights sum to 100 +/- 1 | Executability |
| Equity exposure (%) | Portfolio risk | Sum of weight x fund equity exposure (reported stock share for directly invested funds; category assumption for feeders, FOFs and gold) | Main DV for RQ1 |
| Weighted product risk | Portfolio risk | Sum of weight x R-level | Uses the platform's own ratings |
| Rating breach | Suitability (regulatory) | Any fund rated above the investor's permitted level; breach weight = weight in such funds | Direct test of the C/R matching rule |
| Equity over cap | Suitability (researcher benchmark) | Equity > min(risk cap, horizon cap) + 5 pp; caps C1-C5: 0/20/50/80/100; H1-H5: 10/30/50/80/100 | Captures horizon mismatch the rating rule ignores |
| Holding-period breach | Suitability (liquidity) | Fund minimum holding period > horizon | Money locked beyond the date it is needed |
| Loss-tolerance breach | Suitability (evidence-based) | Worst rolling 12-month historical return of the recommended mix < -(stated max loss) | Tests advice against the investor's own words and real fund data |
| QDII share | International diversification | Weight in QDII funds | Exploratory |
| Conflict acknowledgement | Communication | Conflict vocabulary in the reply; conflicts listed (SUIT) | Whether the adviser tells the client |
| Risk-class accuracy (SUIT) | Profiling | Assessed vs true class; quadratic weighted kappa | Whether the model classifies correctly |
| Test-retest reliability | Consistency | ICC(1,1) of equity across 3 replicates; within-investor SD; Jaccard of fund sets; breach-flag agreement | RQ4 |
| Probe slope | Sensitivity | Change in equity per one-level change, one attribute varied, within anchor | RQ4; separates attribute effects from bundle effects |

The equity caps and the 5 pp tolerance are **researcher-defined operationalisations** informed by the regulatory matching rule and life-cycle theory. They are not regulatory limits, and the report treats them as such. Robustness checks vary the breach definition.

## 9. Statistical methods

- **Descriptives** by model x condition x factor level (n, mean, SD, median).
- **RQ1:**
  - Spearman rho between each ordinal factor and equity or weighted risk, per cell.
  - Type II ANOVA on equity per cell with partial eta squared for each factor (residual df = 184).
  - Pooled OLS with factor x condition interactions and model fixed effects, standard errors clustered by investor.
- **RQ2/RQ3:**
  - Breach rates per cell and per risk class.
  - Paired BASE vs SUIT comparisons within model: McNemar tests (exact when there are fewer than 25 discordant pairs) for binary outcomes; Wilcoxon signed-rank for continuous outcomes.
  - Effect sizes: difference in proportions, discordant odds ratio, matched-pairs rank-biserial r, Cohen's d_z.
- **RQ4:** ICC(1,1) with 95% CI (Koo & Li, 2016); within-anchor slopes and Spearman rho; direction reversals.
- **RQ5:** Friedman test across models (paired by investor) with Kendall's W; pairwise Wilcoxon; Cochran's Q for breach flags.
- **Multiplicity:** Holm (1979) correction within each table family. Interpretation leans on effect sizes and confidence intervals (Cohen, 1988), not on p-values alone.
- **Robustness:**
  - Exclude repaired parses, off-menu replies and invalid weight sums.
  - Count a breach only when it carries more than 5% of the weight.
  - Adjust for experience, log amount and income stability.
  - Base equity exposure on category assumptions only (sensitivity of the exposure mapping).
- **Power:** with 200 paired investors per model, a Wilcoxon test has about 80% power for d_z of about 0.2 at alpha = .05. A Spearman test on n = 200 has about 80% power for rho of about 0.20.

## 10. Limitations (anticipated)

1. **Synthetic investors.** Synthetic profiles are not real clients. Results describe model behaviour on stylised descriptions, not outcomes for real households.
2. **One menu, one window.** The menu is a single 23-fund shelf at one date; ratings change (E Fund re-rated 20+ funds in August 2026), and the back-test window covers one market regime. Historical returns describe past behaviour only; they do not forecast.
3. **Model drift and sampling noise.** Model versions change without notice and sampling is stochastic. We log returned model IDs and measure consistency, but a later rerun may differ.
4. **Prompt format.** Prompt wording and format affect outputs (Sclar et al., 2024). We test one wording per condition and a fixed menu order, so position effects in the menu cannot be separated from fund attractiveness.
5. **Normative benchmarks.** The equity caps are our operationalisation, and equity exposure for feeder funds and FOFs relies on category assumptions.
6. **Automated coding.** Conflict acknowledgement uses keyword rules. A manual validation sample (`docs/coding_sheet.md`, Part C) is planned to estimate their accuracy.
7. **Out of scope.** Gender, region and other demographic signals are deliberately excluded; fairness is not tested.

## 11. Execution status and dependencies

| Step | Status |
|---|---|
| Reference review, design, hypotheses | Done |
| Investor and probe samples (200 + 160) | Done; validated (16/16 checks) |
| Fund identity verification (23 funds) | Done via web search, sources recorded |
| Fund risk ratings, allocation, NAV history | **Pending**: needs `fuyao.aicubes.cn` (course API) documentation and access, or Eastmoney access |
| Pipeline, coder, back-test, analysis, figures | Implemented; 10 automated tests pass on fixtures |
| Pilot and main experiment | **Not run**: needs an Ark Agent Plan API key (`ARK_API_KEY`) and the allowed host `ark.cn-beijing.volces.com` |
| Report and presentation | Drafted from the design; results sections to be written only from real outputs |
