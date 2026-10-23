TITLE: Who Gets What? A Factorial Audit of How Large Language Models Tailor Mutual Fund Portfolios to Investor Age, Risk Tolerance and Investment Horizon
SUBTITLE: Group Research Report - FinTech: Theory and Practice
META: Shenzhen MSU-BIT University
META: Group members: [names and student numbers to be completed by the group]
META: Date: [submission date]
META: Experiment run on 23 October 2026. Manual double coding of the conflict measure (Appendix E) is to be completed by the group.

PAGEBREAK

# Abstract

Retail investors increasingly ask general-purpose chatbots for fund advice, but a chatbot carries none of the suitability duties of a licensed distributor. We audited three Chinese large language models (Doubao, DeepSeek and Kimi) on 200 synthetic investors forming a balanced 5 x 5 x 8 factorial of investment horizon, risk tolerance and age, so that the three attributes are uncorrelated. Every investor was advised by every model under a baseline adviser prompt and under the same prompt with a suitability protocol added, choosing from a menu of 23 verified Chinese funds whose risk ratings were shown. Recommendations were scored against the C1-C5/R1-R5 matching rule, a horizon-based equity cap, a lock-up constraint and the investor's stated loss limit over a 59-month back-test. Risk tolerance dominated the portfolios (partial eta squared 0.66-0.83), horizon came second (0.41-0.53) and age barely mattered (0.02-0.08). Under the baseline prompt, 83-86% of recommendations to C1-C3 investors contained a fund rated above the permitted level. The protocol cut rating breaches by 9.5-24.5 percentage points in every model, yet 42-70% of C1-C3 recommendations still breached the rule, often after the model had classified the investor correctly. Equity levels were highly repeatable (ICC 0.95-0.98) but fund choices were not (Jaccard similarity 0.59-0.70). Suitability rules should therefore be enforced outside the model, not only stated in its prompt.

**Keywords:** generative AI; robo-advice; mutual funds; suitability; investor profiling; audit experiment; LLM evaluation

PAGEBREAK

# 1. Introduction

Retail investors no longer need a bank branch or a robo-adviser questionnaire to obtain a fund recommendation: a few sentences typed into a general-purpose chatbot return a named portfolio in seconds. Choukhmane et al. (2026) recruited about 1,000 US adults who wrote the prompts they would use to seek such advice, a sign of how ordinary the practice has become. The service is free, always available and fluent in the language of portfolio construction.

Fluency is not suitability. A licensed fund distributor in mainland China must assess a client's risk tolerance, horizon and goals, classify both client and product, and sell only products whose risk rating does not exceed the client's class (Asset Management Association of China [AMAC], 2017; China Securities Regulatory Commission [CSRC], 2020). A chatbot has no such duty unless its deployer builds one in. Whether general-purpose models nonetheless behave as if bound by suitability rules is an empirical question that an audit experiment can answer directly.

The evidence so far is mixed. Fieberg et al. (2025) found that 32 models adjusted risk exposure to investor traits, and Choukhmane et al. (2026) that LLM advice would move most respondents towards life-cycle prescriptions. Yet Ross and Lo (2026) describe GPT-4o as a decision tree keyed mainly on self-reported risk tolerance, and Foltyn and Olsson (2026) show that a single gendered word shifts recommended equity across 33 models.

This study addresses four gaps. It crosses horizon, risk tolerance and age orthogonally, so that the weight a model gives each attribute can be separated. It scores advice against an external regulatory rule using real product ratings rather than the researchers' idea of a good portfolio. It tests within the same investors whether a prompt-level suitability protocol makes a model behave more like a regulated adviser. And it back-tests every recommended portfolio against the loss the investor said they could bear.

Sections 2 and 3 set out the questions and the literature, Sections 4 to 8 the method, Sections 9 to 11 the results and their interpretation, and Sections 12 and 13 the limitations and conclusions.

# 2. Research Questions and Hypotheses

**RQ1 (responsiveness).** How strongly do recommended portfolios vary with risk tolerance, investment horizon and age, and how much weight does each attribute carry?

**RQ2 (suitability).** How often do recommendations breach the product-risk matching rule, horizon-based limits, holding-period constraints and the investor's stated loss tolerance?

**RQ3 (prompt-level guardrail).** Does an explicit suitability protocol in the deployment prompt reduce breaches, and does it make advice more conservative than the profile warrants?

**RQ4 (reliability).** How consistent are recommendations across repeated queries, and how do they change when a single attribute is altered?

**RQ5 (model differences).** Do models from different developers differ on these dimensions?

The hypotheses were fixed before any model was queried.

- **H1.** Portfolio risk rises with risk tolerance in every model and condition.
- **H2.** Portfolio risk rises with investment horizon, other attributes held constant.
- **H3.** Portfolio risk falls with age, other attributes held constant, because a younger investor's future labour income acts like a bond holding (Bodie et al., 1992; Cocco et al., 2005).
- **H4 (heuristic dominance).** Risk tolerance explains more variance in equity exposure than horizon and age combined (Ross & Lo, 2026).
- **H5.** The suitability protocol reduces product-risk breaches within each model.
- **H6.** Breaches concentrate where attributes conflict, namely aggressive investors with horizons under three years, because models tend to follow what the user appears to want (Sharma et al., 2024).
- **H7.** Repeated queries give highly reliable equity levels but varying fund selections.

# 3. Literature Review and Theoretical Background

## 3.1 What suitability means

Suitability has an economic and a legal meaning. In life-cycle theory the right share of risky assets depends on risk aversion and total wealth, including human capital: flexible labour supply lets a worker take more financial risk (Bodie et al., 1992), and when labour income behaves like a bond, the optimal equity share declines with age (Cocco et al., 2005). Horizon matters through liquidity, since money needed within months cannot wait for a recovery.

In China, the CSRC's suitability measures (Order No. 130 of 2016, amended in 2020) require institutions to assess each investor's objectives, horizon and risk tolerance and to match investors with products (CSRC, 2020). For fund distribution, the AMAC (2017) guideline sorts investors into classes C1 to C5 and products into ratings R1 to R5 and applies a ceiling rule: C1 investors may buy only R1 products, C2 investors R1 and R2, and so on. The rule neither limits how much of a portfolio may sit at the ceiling nor stops a short-horizon investor in a high class from holding only equity funds, which is why this study adds horizon and liquidity benchmarks.

## 3.2 Human, robo- and LLM advisers

Human advice is uneven. The identity of a Canadian adviser explained more of a client's portfolio risk than the client's own characteristics (Foerster et al., 2017), and advisers in an audit study reinforced biases that served their own interests (Mullainathan et al., 2012). Investors nonetheless delegate to "money doctors" they trust (Gennaioli et al., 2015), as they may to a fluent chatbot. Robo-advisers improved diversification (D'Acunto et al., 2019) and can learn a client's risk profile through interaction (Capponi et al., 2022), but they are built for advice; a general-purpose LLM has no questionnaire, product database or suitability check unless a deployer adds them.

Research on LLM advice is recent. Niszczota and Abbas (2023) tested GPT models on financial literacy, Lo and Ross (2024) named tailoring, ethical alignment and regulatory compliance as obstacles to trusting them, and Oehler and Horn (2024) compared ChatGPT with robo-advisers. Fieberg et al. (2025) found sensible average tailoring across 32 models, but closer studies are less reassuring: Ross and Lo (2026) found decision-tree-like heuristics in GPT-4o's advice to 1,000 synthetic clients, Choukhmane et al. (2026) traced about two-thirds of the gender gap in recommended equity to how men and women worded their prompts, and Foltyn and Olsson (2026) isolated a label effect of about 1.8 percentage points. Barbieri et al. (2026) argue that recommendations should first be audited as executable actions, checking validity and stability across repeated runs.

## 3.3 Why LLM outputs need special scrutiny

Four properties of LLMs shape the design. Models can produce fluent but false content (Ji et al., 2023), outputs vary across identical runs (Atil et al., 2024), outputs are sensitive to the form of the prompt (Sclar et al., 2024), and assistants trained on human preferences tend to tell users what they appear to want (Sharma et al., 2024). An audit therefore needs a fixed product menu, repeated queries and conditions that differ in one element only.

Audit studies identify differential treatment by varying one attribute of otherwise identical applications (Bertrand & Mullainathan, 2004). No study so far combines an orthogonal design, scoring against a real matching rule with real product ratings, a within-investor test of a prompt-level guardrail and a back-test of every recommended portfolio. This study does so in the Chinese fund market, whose C1-C5 and R1-R5 framework offers an unusually explicit yardstick.

# 4. Research Methodology and Experimental Design

## 4.1 Relationship to the reference materials

The course's example audit, API-calling script and presentation template served as orientation only; this study uses its own question, profiles, prompts and fund menu. Four references in the example could not be found in any bibliographic database and its fund list predates an August 2026 re-rating by the issuer, so every fund and reference used here was verified afresh. Our runner keeps the example script's OpenAI-compatible calls and retries and adds append-only logging, prompt hashing and randomised call order.

## 4.2 Design overview

Three investor attributes vary between investors; two prompt conditions and three models vary within investors (Table 1, Figure 1). Each of the 200 synthetic investors occupies one cell of the 5 x 5 x 8 factorial and is advised by every model under both conditions. The 1,200 main observations are therefore repeated measures on 200 investors, and comparisons between conditions or models are paired by investor.

TABLE: Table 1. Design overview and observations
| Component | Specification | Unique units | Observations |
|---|---|---|---|
| Investor attributes (between investors) | Horizon (5) x risk tolerance (5) x age band (8), one investor per cell | 200 investors | - |
| Prompt condition (within investor) | BASE vs SUIT (BASE plus suitability protocol) | 2 | - |
| Model (within investor) | Doubao, DeepSeek, Kimi | 3 | - |
| Main sample | Investors x conditions x models | 200 investors | 1,200 |
| Consistency module | 40 of the 200 investors, two extra replicates | 40 investors | 480 |
| Probe module | 10 anchors x 16 single-attribute versions | 138 distinct texts | 828 |
| Total | | | 2,508 (plus a 60-call pilot, excluded) |
NOTE: All investors are synthetic. Consistency replicates 2 and 3 add to each investor's main-sample reply. Probe versions that coincide across anchors are queried once.

FIGURE: outputs/figures/F00_design_pipeline.png | Figure 1. Experimental pipeline | Inputs (1, 2) and treatments (3, 4) are fixed before any model is queried. All calls are logged before coding (5); coded portfolios are back-tested (6) and analysed (7).

## 4.3 Conditions and controls

The conditions represent two ways a platform might deploy a general-purpose model. Under BASE, the system prompt casts the model as an adviser on a licensed distribution platform, lists the menu with each fund's risk rating and specifies a JSON reply. Under SUIT, a four-step protocol is appended: classify the client into C1 to C5; recommend only funds rated at or below that class; check each fund against the horizon, liquidity need and minimum holding period; and state and resolve any conflict in the profile. BASE is an exact prefix of SUIT (verified by an automated test), and because ratings appear in both, a BASE breach cannot be blamed on missing information. Everything else is held constant, gender, names and cities never appear, and calls run in random order.

# 5. Synthetic Investor Sample Construction

## 5.1 Category definitions

All category definitions were fixed before the profiles were generated and are stored in one code module that every later step reads. Horizon bands are half-open intervals (Table 2). The five risk classes combine attitudes, reactions to losses and the maximum acceptable decline, as risk-tolerance questionnaires do (Grable & Lytton, 1999), and differ in degree rather than kind (Table 3). Age bands cover ages 18 to 85 without gaps and follow life-cycle stages: 18-24, 25-34, 35-44, 45-54, 55-59, 60-64, 65-74 and 75-85 (A1 to A8).

TABLE: Table 2. Investment horizon categories
| Code | Label | Definition | Horizons stated in profiles |
|---|---|---|---|
| H1 | Short-term | Less than 1 year | 3, 6 or 9 months |
| H2 | Short-to-medium term | 1 to less than 3 years | 1.5, 2 or 2.5 years |
| H3 | Medium-term | 3 to less than 5 years | 3 to 4.5 years |
| H4 | Medium-to-long term | 5 to less than 10 years | 5 to 9 years |
| H5 | Long-term | 10 years or more | 10 to 25 years (at most 15 for ages 75-85) |
NOTE: The horizon is the time until the money is expected to be withdrawn. Exact values were drawn at random within each band (seed 20261022).

TABLE: Table 3. Risk tolerance categories
| Code | Label | Maximum acceptable one-year decline | Reaction to a 20% market fall | Highest permitted rating |
|---|---|---|---|---|
| C1 | Very conservative | None | Sell everything | R1 |
| C2 | Conservative | About 5% | Sell part | R2 |
| C3 | Moderate | About 15% | Hold and wait | R3 |
| C4 | Aggressive | About 25% | Hold, possibly add | R4 |
| C5 | Very aggressive | 40% or more | Invest substantially more | R5 |
NOTE: Each class also states a priority, from protecting capital (C1) to the highest long-term return (C5). Models see the label and statements, never the code. Permitted ratings follow the distributors' matching table (AMAC, 2017).

## 5.2 Sampling and consistency of profiles

The main sample is a balanced full factorial: each of the 200 combinations occurs exactly once, giving 40 investors per horizon band and risk class and 25 per age band, with every pair of attributes independent (Cramer's V = 0). Random sampling would have produced uneven cells and confounded age with horizon. Exact values were drawn within cells with a fixed seed, and identifiers were assigned after shuffling.

The price of orthogonality is realism: the sample contains, for example, 80-year-olds with horizons above ten years. Each profile therefore also states employment, objective, liquidity need, experience and amount, derived from age and horizon by explicit rules: only investors aged 60 or older are retired, experience cannot exceed age minus 18, and legacy goals occur only from age 65 with a long horizon, which is how an 80-year-old can coherently hold a 12-year horizon. These attributes serve realism and enter robustness checks as covariates; the probe module isolates each attribute.

## 5.3 Validation, consistency subsample and probes

A validation script written independently of the generator applies 16 checks to counts, identifiers, factorial coverage, band consistency, the consistency rules, duplicates and attribute independence; all pass (Appendix B). Forty investors, eight per risk class, are queried twice more under each condition and model. For the probe module, ten anchors were rewritten with one attribute moved through all its levels, using neutral wording valid at every level; the 160 versions reduce to 138 distinct texts. A 60-call pilot with 10 investors checked parsing and is excluded from the analysis.

# 6. Fund Menu and Data Sources

Models choose from a fixed menu of 23 Chinese public mutual funds rather than from memory. A menu mirrors a platform's shelf, makes every reply codable and separates suitability from the fabrication of non-existent products (Ji et al., 2023). The funds are open-end retail funds with at least three years of history from 14 managers. They span money market, bond, hybrid, broad and sector index funds, four QDII funds investing in US, Hong Kong and global energy equities, a gold fund and a target-risk pension fund of funds whose three-year minimum holding period provides a direct liquidity test (Table 4; full list in Appendix D). Only Chinese-registered funds are used, because mainland investors cannot buy foreign-domiciled funds directly and such funds carry no R1-R5 rating; QDII funds supply overseas exposure within the domestic framework.

TABLE: Table 4. Composition of the fund menu
| Asset class | Funds | Example (code) | QDII | Equity exposure basis |
|---|---|---|---|---|
| Cash | 3 | Tianhong Yu'e Bao money market (000198) | 0 | 0% |
| Bond | 5 | ChinaAMC pure bond A (000015) | 0 | Reported stock share |
| Hybrid | 5 | Invesco Great Wall emerging growth A (260108) | 0 | Reported share; 50% for the pension FOF |
| Equity | 9 | GF Nasdaq-100 feeder QDII A (270042) | 4 | Reported share; 95% for index feeders |
| Commodity | 1 | Huaan gold ETF feeder A (000216) | 0 | 0% |
| Total | 23 | 14 managers | 4 | |
NOTE: Identities verified against at least two public records on 22 October 2026. Ratings (R1 3, R2 4, R3 2, R4 14, R5 0) and stock shares from Eastmoney (Tiantian Fund), retrieved 23 October 2026; adjusted NAV histories from the course data service.

The course data service (Tonghuashun data via fuyao.aicubes.cn) supplies adjusted net asset values but no product risk rating. Ratings were therefore taken from the structured rating field of Eastmoney's Tiantian Fund, a licensed distributor, on 23 October 2026, with each fund's stock share from its 30 June 2026 report. Because ratings change (one manager re-rated more than twenty funds in August 2026), the retrieval date is part of the data. The menu contains no R5 fund, so a C4 or C5 investor cannot breach the rating ceiling and the rating test is informative only for classes C1 to C3. Equity exposure is each fund's reported stock share, or a stated category assumption for index feeders, the fund of funds and the gold fund.

# 7. AI Recommendation Prompts and Implementation

## 7.1 Prompts

Each request has two messages. The system message carries the platform's instructions: the adviser role, the menu (code, name, manager, type, rating and notes on index, QDII status and holding period), the reply format and, under SUIT, the protocol. The user message is the investor: "Here is my situation:", the profile and a request for a portfolio (Appendix C). The JSON format asks for codes, whole-number weights, reasons, a dollar-cost-averaging flag, a rebalancing rule, risk warnings and an explanation; replies that break it are recorded as failures, never repaired by hand. The risk class code never appears, so under SUIT the model must classify the investor itself. The fixed menu order keeps conditions comparable but confounds menu position with fund appeal (Sclar et al., 2024).

## 7.2 Models and configuration

Three models from three Chinese developers are audited (Table 5). The course route, the Volcano Engine Ark Agent Plan, could not be used because the group's keys were ordinary Ark keys, which the Agent Plan endpoint rejected. The same model families were therefore called through OpenRouter, an OpenAI-compatible gateway, with each model pinned to one serving provider and fallbacks disabled. Temperature is 0.7, as in the course's reference script, so sampling is stochastic and the consistency module measures the variation. Reasoning modes were disabled for all three models; for Kimi this was done after the pilot, in which it spent its whole output allowance on hidden reasoning and returned no answer.

TABLE: Table 5. Model configuration
| Setting | Doubao | DeepSeek | Kimi |
|---|---|---|---|
| Developer | ByteDance | DeepSeek | Moonshot AI |
| Model identifier | bytedance-seed/seed-2.0-mini | deepseek/deepseek-v4-flash | moonshotai/kimi-k2.6 |
| Serving provider (pinned) | Seed (ByteDance) | SiliconFlow | Moonshot AI |
| Temperature | 0.7 | 0.7 | 0.7 |
| Reasoning | Disabled | Disabled | Disabled |
| Output | JSON mode, up to 2,500 tokens | Same | Same |
NOTE: Access through OpenRouter (https://openrouter.ai/api/v1) on 23 October 2026; settings in config/experiment_config.json. The serving provider and returned model identifier are logged for every call.

## 7.3 Execution, coding and historical check

The 2,508 calls ran in one random order. Each call is appended to a log as soon as it finishes, with the model requested and returned, request parameters, SHA-256 hashes of both messages, the raw reply, token usage and timestamps; logs are never edited and the prompts were frozen after the pilot. The providers reported 3.72 million prompt and 1.46 million completion tokens for all 2,588 logged calls, costing USD 3.13 in total.

A deterministic script codes each reply, recording whether the JSON parsed directly or only after light repair; off-menu codes are dropped from the risk measures and the remaining weights rescaled, and nothing is imputed (Appendix E). Each portfolio is then back-tested with monthly rebalancing on adjusted net asset values over the longest window of complete months, up to 60, that ends in September 2026 and is covered for every fund. Its worst rolling 12-month return is compared with the maximum one-year loss the investor accepts: none, 5%, 15%, 25% and 40% for C1 to C5. These are historical, descriptive measures, not forecasts.

# 8. Evaluation Metrics and Statistical Methods

## 8.1 Metrics

Table 6 defines the outcomes. Equity exposure is the main continuous outcome because suitability rules and life-cycle theory speak to it most directly. The equity caps express the view that money needed within a year should be almost entirely in assets that cannot fall sharply and that full equity exposure is defensible only over horizons long enough to recover from a deep bear market. Because the caps are judgements, the rating breach, which involves none, is always reported beside them.

TABLE: Table 6. Evaluation metrics
| Metric | Calculation |
|---|---|
| Feasibility | Valid JSON with an on-menu fund; off-menu codes; weights summing to 100 within 1 point |
| Equity exposure (%) | Sum of weight x fund equity exposure (main outcome) |
| Weighted product risk (1-5) | Sum of weight x rating |
| Rating breach | Any fund rated above the investor's ceiling; weight of such funds |
| Equity over cap | Equity more than 5 points above min(risk cap, horizon cap) |
| Holding-period breach | A fund's lock-up exceeds the horizon |
| Loss-tolerance breach | Worst historical 12-month return below minus the stated maximum loss |
| Conflict handling | Conflict vocabulary; conflicts listed (SUIT) |
| Classification (SUIT) | Assessed vs actual class; weighted kappa |
| Reliability | ICC(1,1) of equity over three replicates; Jaccard similarity of fund sets |
| Probe slope | Change in equity per one-level step of one attribute |
NOTE: Equity caps are 0, 20, 50, 80 and 100% for C1-C5 and 10, 30, 50, 80 and 100% for H1-H5; they are the researchers' operationalisation, not regulatory limits. QDII share is also recorded.

## 8.2 Statistical methods

The attributes are orthogonal and balanced, so their effects can be estimated without confounding; conditions and models vary within investors, so their comparisons are paired (Table 7). With 200 paired investors per model, the Wilcoxon test has about 80% power for d_z = 0.2, so effect sizes lead the interpretation. Robustness checks drop repaired parses, off-menu replies and invalid weight sums, count a breach only above 5% of the portfolio, add experience, log amount and income stability as covariates, and recompute equity with category assumptions for every fund.

TABLE: Table 7. Statistical methods by research question
| Question | Method | Effect size |
|---|---|---|
| RQ1 | Spearman correlations per model x condition; Type II ANOVA of equity on the three attributes; pooled OLS with attribute x condition terms, model fixed effects and investor-clustered errors | rho; partial eta squared; points per category step |
| RQ2 | Breach rates by model, condition and risk class; conflict vs non-conflict profiles | Percentages |
| RQ3 | Within-investor BASE vs SUIT: McNemar (exact below 25 discordant pairs); Wilcoxon signed-rank | Discordant pairs; rank-biserial r; d_z |
| RQ4 | ICC(1,1); within-investor SD; Jaccard; slopes within probe anchors | ICC with 95% CI (Koo & Li, 2016) |
| RQ5 | Friedman test paired by investor; pairwise Wilcoxon; Cochran's Q | Kendall's W; rank-biserial r |
NOTE: p-values are two-sided and Holm-adjusted within each set of tests (Holm, 1979). Interpretation rests on effect sizes, not significance alone (Cohen, 1988).

# 9. Experimental Results

All 2,508 planned calls succeeded on 23 October 2026. Every number below comes from tables written by the analysis scripts (references such as T10 denote files in outputs/tables) and refers to the main sample unless stated.

## 9.1 Data quality and feasibility

The models almost always produced executable advice. Of 2,568 coded replies, including the pilot, three Doubao replies were malformed JSON and two DeepSeek replies each named one off-menu fund, leaving 1,199 codable main-sample replies, all with weights summing to 100 (T04). DeepSeek alone deviated from the format, naming only one or two funds in 51 main-sample replies. Kimi built the most diversified portfolios (5.2-5.7 funds on average, against 4.2-4.6) and recommended dollar-cost averaging most often (61-69% of replies, against 20-28% for Doubao).

## 9.2 Responsiveness to risk tolerance, horizon and age (RQ1)

Equity exposure followed risk tolerance closely (Figure 2). Under BASE, mean equity rose from 0.1-0.8% for C1 investors to 62.5-72.9% for C5 investors, and under SUIT from 0% to 53.2-64.1%, with rho = 0.69-0.83 and partial eta squared 0.66-0.83 (Table 8, Figure 5). Horizon mattered mainly at one point (Figure 3): investors who needed their money within a year received almost no equity (BASE means 0.9-7.0%), those with one to three years 26.3-34.2%, and those with ten years or more only 42.0-44.5%. Age barely mattered (Figure 4); its correlation with equity was negative in every cell but small (-0.04 to -0.11) and never significant after Holm adjustment.

TABLE: Table 8. Responsiveness of equity exposure to the three investor attributes
| Model | Condition | rho risk | rho horizon | rho age | Partial eta sq. risk | Partial eta sq. horizon | Partial eta sq. age |
|---|---|---|---|---|---|---|---|
| DeepSeek | BASE | 0.76 | 0.43 | -0.06 | 0.79 | 0.53 | 0.04 |
| DeepSeek | SUIT | 0.69 | 0.50 | -0.05 | 0.71 | 0.50 | 0.04 |
| Doubao | BASE | 0.83 | 0.38 | -0.11 | 0.83 | 0.50 | 0.08 |
| Doubao | SUIT | 0.83 | 0.33 | -0.09 | 0.78 | 0.41 | 0.08 |
| Kimi | BASE | 0.73 | 0.48 | -0.04 | 0.76 | 0.52 | 0.03 |
| Kimi | SUIT | 0.71 | 0.47 | -0.05 | 0.66 | 0.46 | 0.02 |
NOTE: Spearman correlations (n = 200; 199 for Doubao SUIT) from T08 and Type II ANOVA from T09. All risk and horizon effects have Holm-adjusted p < 0.001; no age effect has Holm-adjusted p < 0.05.

The pooled regression with investor-clustered errors gives 18.2 percentage points more equity per risk-class step (95% CI 16.5 to 19.8), 8.7 per horizon step (7.0 to 10.4) and 1.2 less per age band (-2.1 to -0.3), with R squared 0.73 (T10); adding experience, amount and income stability leaves these estimates unchanged (T21). Risk class alone accounts for 51-70% of the total variance in equity, horizon and age together for 15-23% (T09). QDII shares, 7.2-10.7% on average, rise with risk class and horizon and are unrelated to age (T19).

FIGURE: outputs/figures/F01_equity_by_risk_class.png | Figure 2. Mean equity exposure by investor risk class | Dotted line: equity ceiling implied by the risk class (0, 20, 50, 80 and 100%). n = 40 per point (39 for Doubao SUIT C5).

FIGURE: outputs/figures/F02_equity_by_horizon.png | Figure 3. Mean equity exposure by investment horizon | n = 40 per point (39 for Doubao SUIT H4).

FIGURE: outputs/figures/F03_equity_by_age_band.png | Figure 4. Mean equity exposure by age band | n = 25 per point (24 for Doubao SUIT A2).

FIGURE: outputs/figures/F04_relative_importance_partial_eta.png | Figure 5. Relative importance of the three attributes | Partial eta squared from a Type II ANOVA of equity exposure on risk class, horizon band and age band, per model and condition.

## 9.3 Suitability breaches (RQ2)

Under BASE, about half of all recommendations contained a fund rated above the investor's permitted level (Table 9); since no menu fund is rated R5, only C1-C3 investors can breach the rule, and among them the rate was 82.5-85.8% (Figure 6). The breaches were mostly one notch above the ceiling but substantial: 90.5% of breaching replies to C1 investors went no higher than R2, typically bond funds, yet these funds made up 49.8% of the portfolio on average (T23).

TABLE: Table 9. Suitability outcomes by model and condition
| Model | Condition | n | Rating breach, all (%) | Rating breach, C1-C3 (%) | Equity over cap (%) | Mean equity (%) |
|---|---|---|---|---|---|---|
| DeepSeek | BASE | 200 | 51.5 | 85.8 | 22.0 | 32.0 |
| DeepSeek | SUIT | 200 | 42.0 | 70.0 | 16.0 | 28.7 |
| Doubao | BASE | 200 | 51.5 | 85.8 | 20.5 | 31.0 |
| Doubao | SUIT | 199 | 40.7 | 67.5 | 13.1 | 24.7 |
| Kimi | BASE | 200 | 49.5 | 82.5 | 18.5 | 28.0 |
| Kimi | SUIT | 200 | 25.0 | 41.7 | 11.5 | 23.0 |
NOTE: From T11, T13 and T22. C1-C3 column: n = 120 per cell. Holding-period and loss-tolerance breaches were 0-1% in every cell (T11). Mean equity for Doubao is over the 199 investors with codable replies in both conditions.

FIGURE: outputs/figures/F05_rating_breach_by_risk_class.png | Figure 6. Share of replies with a fund rated above the permitted level, by risk class | n = 40 per bar (39 for Doubao SUIT C5). No breach is possible for C4 and C5 because the menu contains no R5 fund.

Equity above the combined risk and horizon cap was rarer (18.5-22.0% under BASE) and concentrated among aggressive investors: 32.5-40.0% of C4 and 55.0-62.5% of C5 recommendations (T12). The models cut equity sharply for horizons under one year but treated a C4 or C5 investor with a one-to-three-year horizon almost like a long-horizon one (Figure 7); C5 investors with H2 horizons received 78% equity on average under BASE, against a horizon cap of 30%. As H6 predicted, 50.0-65.6% of BASE recommendations to C4-C5 investors with horizons under three years exceeded the cap, against 15.6-21.9% for those with horizons of five years or more (T17). The fund with a three-year lock-up went to a shorter-horizon investor only once.

FIGURE: outputs/figures/F06_heatmap_risk_by_horizon.png | Figure 7. Mean equity exposure by risk class and horizon | Pooled over the three models; each cell averages 24 replies (8 investors x 3 models).

## 9.4 Effect of the suitability protocol (RQ3)

The protocol improved every suitability measure in every model (Table 10). Rating breaches fell by 9.5 points for DeepSeek, 11.1 for Doubao and 24.5 for Kimi, almost entirely in one direction: among investors whose breach status changed, the protocol removed a breach in 19, 24 and 49 cases and added one in 0, 2 and 0. Equity above the cap fell by 6-7 points and mean equity by 3.4-6.3 points (d_z = -0.27 to -0.63, all Holm p < 0.001). The pooled regression gives 4.9 points less equity under SUIT (95% CI -5.9 to -3.8) and a slightly flatter risk gradient (T10).

TABLE: Table 10. Paired effect of the suitability protocol (SUIT minus BASE)
| Model | Outcome | BASE | SUIT | Difference | Discordant pairs (BASE only vs SUIT only) | Holm p |
|---|---|---|---|---|---|---|
| DeepSeek | Rating breach (%) | 51.5 | 42.0 | -9.5 | 19 vs 0 | < 0.001 |
| Doubao | Rating breach (%) | 51.8 | 40.7 | -11.1 | 24 vs 2 | < 0.001 |
| Kimi | Rating breach (%) | 49.5 | 25.0 | -24.5 | 49 vs 0 | < 0.001 |
| DeepSeek | Equity over cap (%) | 22.0 | 16.0 | -6.0 | 14 vs 2 | 0.029 |
| Doubao | Equity over cap (%) | 20.1 | 13.1 | -7.0 | 16 vs 2 | 0.012 |
| Kimi | Equity over cap (%) | 18.5 | 11.5 | -7.0 | 16 vs 2 | 0.012 |
NOTE: From T13. McNemar tests on 200 paired investors (199 for Doubao).

The protocol did not, however, produce compliance. Under SUIT, 41.7-70.0% of recommendations to C1-C3 investors still breached the ceiling (T22). Misclassification was not the main cause: the models' own classifications matched the true class in 60.0% (DeepSeek), 86.4% (Doubao) and 88.5% (Kimi) of cases, with quadratic weighted kappa of 0.73, 0.94 and 0.88 (T18), and among correctly classified C1-C3 investors 58.5%, 66.4% and 39.8% of recommendations still breached the rule (T25).

The protocol did change how conflicts were handled. For C4-C5 investors with horizons under three years, SUIT replies listed the conflict in 90.6-100% of cases, and mean equity fell from 38.3 to 26.7% (DeepSeek), 46.5 to 33.9% (Doubao) and 29.7 to 14.0% (Kimi). For aggressive long-horizon investors, where no conflict exists, equity barely changed for DeepSeek and Kimi and fell by 6.9 points for Doubao (T17).

## 9.5 Consistency and single-attribute sensitivity (RQ4)

Asking the same question three times gave similar equity levels but different portfolios (Table 11). The intraclass correlation of equity across replicates was 0.95-0.98, with a mean within-investor standard deviation of 3.1-4.5 points, but the mean Jaccard similarity of the fund sets was only 0.59-0.70, and the breach verdict differed between replicates for 5.0-17.5% of investors.

TABLE: Table 11. Consistency across three replicates
| Model | Condition | Investors | ICC(1,1) equity [95% CI] | Mean within-investor SD (points) | Mean Jaccard of fund sets | Same breach verdict (%) |
|---|---|---|---|---|---|---|
| DeepSeek | BASE | 40 | 0.98 [0.96, 0.99] | 3.9 | 0.61 | 90.0 |
| DeepSeek | SUIT | 40 | 0.95 [0.91, 0.97] | 4.5 | 0.64 | 90.0 |
| Doubao | BASE | 40 | 0.97 [0.95, 0.98] | 4.3 | 0.60 | 95.0 |
| Doubao | SUIT | 39 | 0.95 [0.92, 0.97] | 4.4 | 0.59 | 84.6 |
| Kimi | BASE | 40 | 0.98 [0.97, 0.99] | 3.1 | 0.67 | 85.0 |
| Kimi | SUIT | 40 | 0.96 [0.93, 0.98] | 4.1 | 0.70 | 82.5 |
NOTE: From T15. One Doubao SUIT replicate could not be parsed, leaving 39 investors.

The probes, which change one attribute at a time, confirm the dominance of risk tolerance and qualify the horizon effect (Figure 8, T16). One risk class up raised equity by 20.3-24.0 points, in the expected direction for every anchor in every cell; one horizon band longer raised it by only 1.0-3.8 points, in the expected direction for 3 to 8 of 10 anchors; and one age band older lowered it by 1.4-3.0 points. The stated horizon alone thus moves the models far less than the 8.7 points per band in the main sample, where horizon comes bundled with consistent objectives.

FIGURE: outputs/figures/F07_single_attribute_probes.png | Figure 8. Single-attribute probes | Mean equity exposure as one attribute moves through its levels while the rest of the anchor profile is held constant; averaged over the 10 anchors.

## 9.6 Model differences (RQ5)

Under BASE the models behaved much alike: their breach rates did not differ (Cochran's Q = 2.46, p = 0.29), and their equity levels differed only slightly (Friedman test, Kendall's W = 0.045), with Kimi recommending 3.3-4.1 points less equity than the others. Under SUIT they diverged: Kimi's breach rate of 25.0% compares with 40.7-42.0% for the others (Q = 45.2, p < 0.001), and equity differences grew (W = 0.084; T14). Kimi cost about 7 to 11 times as much per call (USD 2.56 for 876 logged calls, against USD 0.33 for Doubao and USD 0.23 for DeepSeek for 856 calls each).

## 9.7 Historical check

Over the common 59-month window, November 2021 to September 2026, the median worst 12-month return was positive for C1 and C2 recommendations, slightly negative for C3, and -10.5% to -18.7% for C4 and C5 (Table 12, Figure 9). Only four main-sample portfolios lost more in a year than the investor accepted: two DeepSeek C3 recommendations per condition, with worst years down to -18.8% against a 15% limit. The period explains this. The menu's money market and bond funds never had a negative 12-month return and the enhanced-return bond fund lost at most 1.1%, so the rating breaches of C1-C2 investors, which consisted mostly of such funds, caused no such losses. The R4 funds lost 9.3-36.9% in their worst year (the gold fund aside), but the models diluted them enough to keep aggressive investors within their limits.

TABLE: Table 12. Worst rolling 12-month return of recommended portfolios, by risk class
| Risk class | Stated maximum loss (%) | Median worst 12 months, BASE (%) | Median worst 12 months, SUIT (%) | Lowest, BASE / SUIT (%) | Exceeds stated loss, BASE / SUIT (%) |
|---|---|---|---|---|---|
| C1 | 0 | 1.3 | 1.3 | 0.6 / 0.9 | 0.0 / 0.0 |
| C2 | 5 | 1.3 | 1.4 | -3.3 / -3.6 | 0.0 / 0.0 |
| C3 | 15 | -2.6 | -0.5 | -18.4 / -18.8 | 1.7 / 1.7 |
| C4 | 25 | -13.2 | -10.5 | -24.7 / -24.0 | 0.0 / 0.0 |
| C5 | 40 | -18.7 | -16.5 | -28.3 / -28.0 | 0.0 / 0.0 |
NOTE: From T24. Pooled over models, n = 120 per cell (119 for SUIT C5); monthly rebalancing on adjusted NAVs. Historical and descriptive, not a forecast.

FIGURE: outputs/figures/F08_backtest_worst_12m_vs_tolerance.png | Figure 9. Worst historical 12-month return against the investor's stated loss limit | Mean worst rolling 12-month return per risk class; dotted line: maximum one-year loss the investor accepts. Window November 2021 to September 2026.

## 9.8 Robustness

Excluding replies with off-menu funds, invalid weight sums or repaired parses changes the correlations by at most 0.003 and the breach rates by at most 0.3 points, and counting a breach only when the breaching funds exceed 5% of the portfolio lowers the rates by at most 0.5 points (T20). Recomputing equity with category assumptions for every fund raises mean equity by 1.1-3.3 points and the share above the cap by 1.0-4.0 points, leaving the risk correlations at 0.66-0.81. Covariates leave the attribute and condition effects unchanged (T21).

# 10. Discussion and Interpretation

## 10.1 The hypotheses

Table 13 sets the results against the hypotheses fixed before the run. Five are supported, one only weakly, and one in part, because the menu contained no R5 fund.

TABLE: Table 13. Hypotheses and results
| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1. Risk rises with risk tolerance | Supported | rho 0.69-0.83; +18.2 points per class; all probe anchors |
| H2. Risk rises with horizon | Supported | rho 0.33-0.50; +8.7 points per band; weak in probes |
| H3. Risk falls with age | Weak support | No cell significant; -1.2 points per band pooled (p = 0.009) |
| H4. Risk tolerance dominates | Supported | Eta squared 0.51-0.70 vs 0.15-0.23 |
| H5. Protocol reduces rating breaches | Supported | -9.5 to -24.5 points; Holm p < 0.001 |
| H6. Breaches concentrate in conflict profiles | Partly supported | Over cap 50-66% vs 16-22%; rating test not possible |
| H7. Stable equity, varying fund choice | Supported | ICC 0.95-0.98; Jaccard 0.59-0.70 |
NOTE: Main sample, BASE condition where relevant. Sources: Tables 8 to 11, Figure 8, T09, T10 and T17.

## 10.2 Tailoring that rests on one attribute

All three models tailor, but mainly along one dimension: stated risk tolerance drives most of the variation, horizon acts largely as a switch between "money needed within a year" and everything else, and age barely registers. This matches the decision-tree description of GPT-4o by Ross and Lo (2026), extends it to three Chinese models, and is at odds with life-cycle theory, which expects an age gradient even at a fixed horizon (Bodie et al., 1992; Cocco et al., 2005). The probes suggest that the models respond to the overall story of a profile, such as saving for a purchase next year, more than to the stated number of years.

## 10.3 The rating rule is visible but not followed

The most striking result is how often the models broke the matching rule although every rating was in the prompt. Their breaches follow an economic rather than a regulatory idea of caution: a very conservative investor typically received money market plus bond funds, a mix that lost nothing in the back-test but that the rule forbids for a C1 client. The models seem to read "conservative" as "low volatility", not as "within the rating ceiling". The protocol halved the breach rate for Kimi, but two-thirds or more of C1-C3 recommendations from DeepSeek and Doubao still breached the rule, often after correct classification. Knowing a rule and applying it are different steps, so a rule written into a prompt is not a control in the regulatory sense. Unlike classic sycophancy (Sharma et al., 2024), the models departed from the rule towards what they apparently judged to be good advice, not towards what the client asked for.

## 10.4 Aggressive clients with short horizons

Under the baseline prompt a C5 investor who needed the money in one to three years received about three-quarters equity, more than twice the horizon cap: as H6 anticipated, the stated appetite for risk won. The protocol helped most here, flagging the conflict in almost every case and cutting equity substantially, while leaving aggressive long-horizon investors largely untouched in two of the three models; it targets the conflict rather than making all advice more conservative.

## 10.5 Reliability, model differences and the back-test

Equity levels were repeatable but fund choices were not, and the breach verdict changed between replicates for up to 17.5% of investors, so an audit based on one query per client would misclassify a noticeable share of cases (Atil et al., 2024; Barbieri et al., 2026). The models were close under the baseline prompt and differed mainly in how strongly they responded to the protocol, so model differences lie less in default risk-taking than in instruction-following. Finally, the rarity of loss-tolerance breaches does not show that rating breaches are harmless: the window was benign for Chinese bond and money market funds, and in a period of rising rates or credit stress the same breaches could cause losses for investors who accept none.

# 11. Implications for AI-Based Investment Advice

**Platforms.** Showing ratings to the model and adding a suitability protocol to its prompt do not keep advice within the matching rule. The rule should be enforced in code: the model should be offered only products at or below the client's ceiling, or every recommendation should be checked automatically before it is shown. The model's own classification, which matched the true class in 60-89% of cases, can be an input but not the control.

**Prompt design.** A suitability protocol is cheap and worthwhile: it cut breaches by up to half and made the models flag almost every risk-horizon conflict. Its effect differs strongly between models, so it must be tested on the model actually deployed.

**Supervisors and auditors.** Audits should use repeated queries per profile, and back-tests over one benign window should be complemented by stress scenarios.

**Investors and developers.** The models respond strongly to stated risk attitude and weakly to age and horizon, so users should state their horizon and liquidity needs explicitly and be wary of high-equity portfolios offered for short horizons. For developers, the gap between classifying a client correctly and recommending within that class is a measurable benchmark of constraint-following.

# 12. Limitations

**Synthetic investors.** The clients are stylised descriptions delivered in one message, whereas real clients are vaguer and converse. This is close to a best case for tailoring, so the failures observed here probably understate those in practice.

**One menu, one date, one window.** The menu is a single 23-fund shelf with ratings from one distributor on one date, and other distributors may rate the same funds differently. It contains no R5 fund, so the rating test is informative only for C1-C3 investors and H6 could be tested only with the equity caps. The back-test covers one 59-month window in which the bond and money market funds never lost more than 1.1% over twelve months, so the rarity of loss-tolerance breaches is partly a property of the period.

**Models and access.** Hosted models change without notice and sample stochastically, so a later rerun may differ (Atil et al., 2024). The models were reached through OpenRouter rather than the course's Ark route, DeepSeek through a third-party provider and all with reasoning disabled, so the results describe the direct-answer behaviour of these deployments.

**Prompts and benchmarks.** Each condition uses one wording and one menu order, so the protocol effect is that of this particular protocol (Sclar et al., 2024). The equity caps and five-point tolerance are the researchers' operationalisation, and some equity exposures rest on category assumptions, although the robustness checks vary these choices.

**Coding and scope.** Conflict acknowledgement is coded with keyword rules and remains indicative until the planned manual validation (Appendix E) is complete. Gender, region, fees, taxes and platform availability are outside the scope of the study.

# 13. Conclusion

This study audited how three Chinese LLMs recommend public mutual funds to 200 synthetic investors whose age, risk tolerance and horizon were varied independently, with and without a suitability protocol in the prompt. Almost all 2,508 replies were executable portfolios drawn from the given menu. The models tailored their advice mainly to stated risk tolerance; horizon mattered mostly when the money was needed within a year, and age hardly at all. Under the baseline prompt, more than four in five recommendations to C1-C3 investors broke the product-risk matching rule although the ratings were in the prompt, and aggressive investors with short horizons received far more equity than their horizon justified. The suitability protocol reduced both problems in every model, most strongly for Kimi, but most C1-C3 investors advised by DeepSeek and Doubao still received a product above their ceiling, often after correct classification. Equity levels were stable across repeated queries while fund choices were not.

A general-purpose LLM can produce sensible-looking, diversified portfolios but cannot be relied on to apply a regulatory rule it has been told about. Suitability constraints belong in the system around the model, not only in its prompt. Future work should test conversational profiles, menus with R5 products, reasoning modes and stress-period back-tests.

PAGEBREAK

# References

REFERENCES: docs/references_apa.md

PAGEBREAK

APPENDICES: report/appendices_generated.md
