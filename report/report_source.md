TITLE: Who Gets What? A Factorial Audit of How Large Language Models Tailor Mutual Fund Portfolios to Investor Age, Risk Tolerance and Investment Horizon
SUBTITLE: Group Research Report - FinTech: Theory and Practice
META: Shenzhen MSU-BIT University
META: Group members: [names and student numbers to be completed by the group]
META: Date: [submission date]
META: DRAFT STATUS: Sections 9-11 and 13 and the abstract's findings are written only after the experiment has been run. No results appear in this draft.

PAGEBREAK

# Abstract

Large language models (LLMs) are now a common first stop for retail investors, yet a chatbot carries none of the suitability duties that bind a licensed adviser. This study audits how three LLMs from different developers recommend Chinese public mutual funds to 200 synthetic investors. The investors are built as a balanced full factorial of five investment horizons, five risk-tolerance classes and eight age bands, one investor per cell, so the three attributes are uncorrelated by construction. Every investor is advised by every model under two deployment prompts: a baseline adviser prompt and the same prompt with an explicit suitability protocol added. Models choose only from a menu of 23 real funds whose identities were verified against public records. Each recommendation is scored against the product-risk matching rule used by Chinese fund distributors, a horizon-based equity ceiling, the minimum holding period of a pension fund, and the investor's own stated loss tolerance, which is checked against five years of fund return data. Two further modules measure test-retest consistency and the effect of changing one attribute at a time.

PENDING: Findings are added here once the experiment has been run and analysed (outputs/tables/results_digest.md).

**Keywords:** generative AI; robo-advice; mutual funds; suitability; investor profiling; audit experiment; LLM evaluation

PAGEBREAK

# 1. Introduction

Retail investors no longer need to visit a bank branch or answer a robo-adviser's questionnaire before they receive a fund recommendation. They can type a few sentences about themselves into a general-purpose chatbot and get a named portfolio back in seconds. How quickly this habit has spread is hard to measure, but the direction is clear. Choukhmane et al. (2026) were able to recruit about 1,000 US adults who wrote the prompts they would use to ask an LLM for saving and investment advice, and then evaluated the advice those prompts produced. The appeal is obvious: the service is free, always available, and fluent in the language of portfolio construction.

Fluency is not suitability. A licensed fund distributor in mainland China must collect information on a client's risk tolerance, investment horizon and goals, classify both the client and the product, and sell the client only products whose risk rating does not exceed the client's class (Asset Management Association of China [AMAC], 2017; China Securities Regulatory Commission [CSRC], 2020). A chatbot has no such obligation unless the firm deploying it builds one in. Whether general-purpose models nonetheless behave as if they were bound by suitability rules is an empirical question, and an audit experiment is the most direct way to answer it.

The early evidence points in two directions. On average, LLM portfolios look sensible. Fieberg et al. (2025) collected recommendations from 32 models for 64 investor profiles and found that the models generally adjusted market and risk exposure to investor traits, with historical performance comparable to professionally managed benchmarks. Choukhmane et al. (2026) report that following LLM advice would move most of their respondents closer to the prescriptions of life-cycle theory. Other studies suggest that the tailoring is shallow. Ross and Lo (2026) describe GPT-4o as behaving like a decision tree that keys mainly on self-reported risk tolerance. Foltyn and Olsson (2026) show that changing a single word from "man" to "woman" lowers the recommended equity share across 33 models. Human advisers have shown similar weaknesses: Foerster et al. (2017) found that the identity of the adviser explained more of a client's portfolio risk than the client's own risk tolerance, age or sophistication.

Existing audits leave four gaps that this project addresses. First, most vary a handful of attributes at once, which makes it hard to say how much weight a model places on each. We cross horizon, risk tolerance and age orthogonally in a 5 x 5 x 8 design, so their contributions can be separated cleanly. Second, suitability is usually judged against the researchers' own idea of a good portfolio. We score advice against an external, regulation-based rule, using the risk ratings of real products, and add a liquidity test through a fund with a three-year lock-up. Third, little is known about whether a deployment prompt can make a model behave more like a regulated adviser. We test a prompt-level suitability protocol against a baseline prompt within the same investors. Fourth, recommendations are rarely checked against data on the funds actually recommended. We back-test every recommended mix and compare its worst historical 12-month loss with the loss the investor said they could bear.

The report proceeds as follows. Section 2 states the research questions and hypotheses. Section 3 reviews the literature on suitability, human and automated advice, and the reliability of LLM outputs. Sections 4 to 8 describe the design, the synthetic sample, the fund menu, the prompts and implementation, and the evaluation framework. Sections 9 to 11 present and interpret the results, Section 12 discusses limitations, and Section 13 concludes. The appendices reproduce the prompts, sample examples, the fund menu, the coding rules and the reproducibility record.

# 2. Research Questions and Hypotheses

The study asks five questions.

**RQ1 (responsiveness).** How strongly do LLM-recommended portfolios vary with the investor's risk tolerance, investment horizon and age, and how much weight does each attribute carry?

**RQ2 (suitability).** How often do recommendations breach objective suitability benchmarks: the product-risk matching rule, horizon-based limits, holding-period constraints, and the investor's stated loss tolerance as checked against historical fund returns?

**RQ3 (prompt-level guardrail).** Does an explicit suitability protocol in the deployment prompt improve alignment and reduce breaches, and does it make portfolios more conservative than the investor's profile warrants?

**RQ4 (reliability).** How consistent are recommendations for the same investor across repeated queries, and how do they change when one attribute is altered and all else is held constant?

**RQ5 (model differences).** Do models from different developers differ on these dimensions?

The hypotheses were fixed before any model was queried.

- **H1.** Portfolio risk rises with risk tolerance in every model and condition.
- **H2.** Portfolio risk rises with investment horizon, holding risk tolerance and age constant.
- **H3.** Portfolio risk falls with age, holding risk tolerance and horizon constant. Life-cycle theory justifies a modest age effect even at a fixed horizon because a younger investor's future labour income acts like a bond holding (Bodie et al., 1992; Cocco et al., 2005).
- **H4 (heuristic dominance).** Risk tolerance explains more variance in equity exposure than horizon and age combined. This follows from Ross and Lo (2026).
- **H5.** The suitability protocol reduces the rate of product-risk breaches within each model.
- **H6.** Breaches concentrate where an investor's attributes pull in opposite directions, namely aggressive investors with horizons under three years. Sycophancy research (Sharma et al., 2024) suggests a model may follow the stated appetite for risk rather than the constraint.
- **H7.** Repeated queries yield highly reliable equity levels but varying fund selections.

# 3. Literature Review and Theoretical Background

## 3.1 What suitability means

Suitability has an economic and a legal meaning. In life-cycle portfolio theory the right share of risky assets depends on risk aversion and on total wealth, including human capital. The ability to adjust labour supply lets a worker take more financial risk (Bodie et al., 1992). When labour income behaves like a bond, the optimal equity share broadly declines with age as the implicit bond holding runs down (Cocco et al., 2005). Horizon matters through liquidity: money needed within months cannot wait for a recovery, whatever the investor's attitude to risk. Risk tolerance itself is measured with questionnaires that combine attitudes, past behaviour and hypothetical losses (Grable & Lytton, 1999). The risk classes in this study follow that logic.

The legal meaning in China is set by the CSRC's *Measures for the Suitability Management of Securities and Futures Investors* (CSRC Order No. 130 of 2016, amended in 2020). The Measures require institutions to collect each investor's objectives, including horizon, product types and expected return, and to classify and match investors and products (CSRC, 2020). For fund distribution, the AMAC (2017) guideline divides ordinary investors into classes C1 (most conservative) to C5 and products into ratings R1 to R5. Distributors apply a ceiling rule: C1 investors may buy only R1 products, C2 investors R1 and R2, and so on up to C5. The rule is deliberately simple. It does not say how much of a moderate investor's money belongs in R3 funds, and it does not stop a short-horizon investor in a high class from holding only R4 equity funds. This gap between the legal ceiling and economic common sense motivates the horizon and liquidity benchmarks used here.

## 3.2 Human and automated advisers

The record of human advice is mixed. Foerster et al. (2017) found that Canadian advisers placed clients in similar portfolios regardless of risk preferences or life-cycle stage; adviser fixed effects explained more of a portfolio's risk than the client's own characteristics. In an audit study, Mullainathan et al. (2012) found that advisers reinforced biases that served their own interests, encouraging return chasing and high-fee active funds. Gennaioli et al. (2015) explain why such advice survives: investors delegate to "money doctors" they trust, and trust rather than quality sustains the relationship. A fluent chatbot may earn similar trust.

Robo-advisers were meant to standardise good practice. D'Acunto et al. (2019) found that a portfolio optimiser improved diversification and reduced behavioural biases among previously undiversified investors. Capponi et al. (2022) model an adviser that learns the client's risk profile through repeated interaction, trading timely information against noise in the reported profile. Both concern systems built for advice. A general-purpose LLM has no questionnaire, product database or suitability check unless a deployer adds them, which is the situation this study simulates.

## 3.3 Large language models as investment advisers

Niszczota and Abbas (2023) tested GPT models on financial literacy questions and studied how people use them for advice. Lo and Ross (2024) identify three obstacles to trusting such systems: tailoring general expertise to an individual, aligning with the user's ethical standards, and meeting regulatory requirements. Oehler and Horn (2024) compared ChatGPT's portfolios with those of established robo-advisers. Fieberg et al. (2025), with 32 models and 64 profiles, found that models generally set market and risk exposure in line with investor traits.

Studies of how the tailoring happens are less reassuring. Ross and Lo (2026) fitted interpretable models to GPT-4o's recommendations for 1,000 synthetic clients and found decision-tree-like heuristics; giving the model tools improved diversification but made recommendations more alike across clients. Choukhmane et al. (2026) found that LLM advice would move households towards life-cycle prescriptions, including equity shares that fall with age, but that it varied with prompt wording: about two-thirds of the gender gap in recommended equity came from how men and women wrote their prompts. Foltyn and Olsson (2026) isolated the label effect across 33 models: female framing lowered recommended equity by about 1.8 percentage points. Barbieri et al. (2026) argue that recommendations should first be audited as executable actions, checking validity and stability across repeated runs before judging returns.

## 3.4 Why LLM outputs need special scrutiny

Four properties of LLMs shape the audit design. Models can produce fluent but false content (Ji et al., 2023), such as fund codes that do not exist. Outputs vary across identical runs, even under nominally deterministic settings (Atil et al., 2024), so one query per client says little about stability. Outputs are sensitive to prompt form as well as content (Sclar et al., 2024), so condition comparisons are clean only if everything else is held fixed. And assistants trained on human preferences tend to tell users what they appear to want (Sharma et al., 2024), so an investor who asks for growth may receive growth even when a short horizon makes it unwise.

## 3.5 The audit method and the gap

Audit studies identify differential treatment by sending otherwise identical applications that differ in one attribute (Bertrand & Mullainathan, 2004; Mullainathan et al., 2012). LLM audits extend the method with synthetic clients in any number and complete control over wording. None of the studies above combines an orthogonal design that separates the weights of age, horizon and risk tolerance; scoring against a real regulatory matching rule with real product ratings; a within-investor test of a prompt-level guardrail; and a historical check of each recommended portfolio. This study combines them in the Chinese fund market, where the C1-C5 and R1-R5 framework gives an unusually explicit yardstick.

# 4. Research Methodology and Experimental Design

## 4.1 Relationship to the reference materials

The course provided an example audit that compared recommendations made from memory with recommendations made from a supplied fund list, an API-calling script and a presentation template. We used them as orientation only. This study asks a different question, uses its own profiles, prompts and fund menu, and re-verifies every fund and reference. Four references in the example could not be found in any bibliographic database, and its fund list predates an August 2026 revision of the issuer's risk ratings. Our runner keeps the example script's OpenAI-compatible calls, retries and resumability, and adds append-only logging, prompt hashing, randomised call order and token accounting.

## 4.2 Design overview

Three investor attributes vary between investors, and two prompt conditions and three models vary within investors (Table 1, Figure 1). Each of the 200 synthetic investors occupies one cell of the 5 (horizon) x 5 (risk tolerance) x 8 (age) factorial and is advised by every model under both conditions. The design is therefore repeated-measures: the 1,200 main observations are not 1,200 different investors, and comparisons between conditions or models are paired by investor.

TABLE: Table 1. Design overview and planned observations
| Component | Specification | Unique units | Observations |
|---|---|---|---|
| Investor attributes (between investors) | Horizon (5) x risk tolerance (5) x age band (8), one investor per cell | 200 investors | - |
| Prompt condition (within investor) | BASE vs SUIT (BASE plus suitability protocol) | 2 | - |
| Model (within investor) | Doubao, DeepSeek, Kimi (via Volcano Ark) | 3 | - |
| Main sample | Investors x conditions x models | 200 investors | 1,200 |
| Consistency module | 40 investors, two extra replicates | 40 investors | 480 |
| Probe module | 10 anchors x 16 single-attribute versions | 138 distinct texts | 828 |
| Total | | | 2,508 (plus a 60-call pilot, excluded) |
NOTE: All investors are synthetic. Consistency replicates 2 and 3 add to each investor's main-sample reply. Probe versions that coincide across anchors are queried once.

FIGURE: outputs/figures/F00_design_pipeline.png | Figure 1. Experimental pipeline | Inputs (1, 2) and treatments (3, 4) are fixed before any model is queried. All calls are logged before coding (5); coded portfolios are back-tested (6) and analysed (7).

## 4.3 Experimental conditions and controls

The conditions represent two ways a fund platform might deploy a general-purpose model. Under BASE, the system prompt casts the model as an adviser on a licensed distribution platform, lists the menu with each fund's risk rating and specifies a JSON response. Under SUIT, the same prompt is followed by a four-step protocol: classify the client into C1 to C5; recommend only funds rated at or below that class; check each fund against the horizon, liquidity need and any minimum holding period; and state and resolve any conflict in the client's profile. The BASE prompt is an exact prefix of the SUIT prompt (verified by an automated test), so the protocol is the only difference. Because ratings appear in both conditions, a BASE breach cannot be blamed on missing information.

Everything else is held constant: profile templates and field order; the absence of gender, names, cities and dependants; the statement that emergency savings are held separately; the menu, its order and wording; messages, output limits and temperature. Calls are issued in random order so that a provider incident or silent model update cannot coincide with one condition.

# 5. Synthetic Investor Sample Construction

## 5.1 Category definitions

All category definitions were fixed before the profiles were generated and are stored in one code module that every later step reads. Horizon bands are half-open intervals, so a stated horizon belongs to exactly one band (Table 2). The five risk classes are defined on the same three criteria, so they differ in degree rather than kind (Table 3). Age bands cover ages 18 to 85 without gaps and follow life-cycle stages: 18-24, 25-34, 35-44, 45-54, 55-59, 60-64, 65-74 and 75-85 (A1 to A8). The narrower bands between 55 and 64 cover the years in which retirement decisions are made.

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

## 5.2 Sampling strategy

The main sample is a balanced full factorial: each of the 200 combinations of horizon, risk class and age band occurs exactly once, giving 40 investors per horizon band and risk class and 25 per age band. Random sampling would have produced uneven cells and correlated attributes, making it impossible to tell an age effect from the effect of the horizon that tends to accompany age. With one investor per cell, every pair of attributes is independent (Cramer's V = 0). The price is realism: the sample contains, for example, 80-year-olds with horizons over ten years. Rather than discard such cells, the profiles were made internally consistent (Section 5.3). Exact ages, horizons and secondary attributes were drawn within each cell with a fixed seed, and identifiers were assigned after shuffling, so an identifier carries no information.

## 5.3 Secondary attributes and consistency

Each profile also states employment, an objective, a liquidity need, investment experience and an amount to invest, derived from age and horizon by explicit rules. Only investors aged 21 or younger are students and only those aged 60 or older are retired. Experience cannot exceed age minus 18 years. Near-term spending objectives occur only with horizons under a year, retirement-income objectives only from age 50, and legacy objectives only from age 65 with a long horizon, which is how an 80-year-old can coherently hold a 12-year horizon. These attributes are not independent variables; they serve realism and enter robustness checks as covariates. As a result, main-sample age and horizon effects are effects of realistic bundles (a 70-year-old is also retired), and the probe module isolates each attribute on its own.

## 5.4 Validation, consistency subsample and probes

A validation script written independently of the generator applies 16 checks covering counts, identifiers, missing values, factorial coverage, band consistency, the consistency rules, duplicates and attribute independence. All pass (Appendix B). Forty investors, eight per risk class, form the consistency subsample and are queried twice more under each condition and model. For the probe module, ten anchors were spread so that each risk class and horizon appears twice and each age band at least once. Each anchor was rewritten with one attribute moved through all its other levels, using neutral secondary wording valid at every level (for example "stable regular income (salary or pension)"). Coinciding versions are queried once. Table 4 summarises the samples.

TABLE: Table 4. Composition of the synthetic samples
| Sample | Unique profiles | Structure | Use |
|---|---|---|---|
| Main | 200 | One per horizon x risk x age cell | RQ1-RQ3, RQ5 |
| Consistency | 40 of the 200 | 8 per risk class | RQ4: replicates 2 and 3 |
| Probe | 160 versions of 10 anchors (138 distinct texts) | One attribute differs from the anchor | RQ4: sensitivity |
| Pilot | 10 of the 200 | Random | Parsing check only |
NOTE: All profiles are synthetic. A check confirms that every probe version differs from its anchor in exactly one line.

# 6. Fund Menu and Data Sources

Models choose from a fixed menu of 23 Chinese public mutual funds rather than from memory. A platform deployment would restrict advice to the platform's shelf; a menu makes every recommendation codable; and it separates suitability from fabrication, since a model answering from memory can name products that do not exist (Ji et al., 2023). Off-menu codes are still counted as feasibility errors.

The funds are open-end funds sold to mainland retail investors, mostly A shares, each with at least three years of history. They cover money market, ultra-short, pure and enhanced bond, flexible and equity-oriented hybrid, broad and sector equity index, four QDII funds investing in US, Hong Kong and global energy equities, a gold fund, and a target-risk pension fund of funds with a three-year minimum holding period (Table 5; full list in Appendix D). Fourteen managers are represented and none contributes more than three funds. The pension fund's lock-up provides a direct liquidity test: recommending it to an investor who needs the money within three years is unsuitable regardless of risk class.

TABLE: Table 5. Composition of the fund menu
| Asset class | Funds | Example (code) | QDII | Equity exposure basis |
|---|---|---|---|---|
| Cash | 3 | Tianhong Yu'e Bao money market (000198) | 0 | 0% |
| Bond | 5 | ChinaAMC pure bond A (000015) | 0 | Reported stock share |
| Hybrid | 5 | Invesco Great Wall emerging growth A (260108) | 0 | Reported share; 50% for the pension FOF |
| Equity | 9 | GF Nasdaq-100 feeder QDII A (270042) | 4 | Reported share; 95% for index feeders |
| Commodity | 1 | Huaan gold ETF feeder A (000216) | 0 | 0% |
| Total | 23 | 14 managers | 4 | |
NOTE: Identities verified against at least two public records on 22 October 2026. Ratings, allocations and return histories come from one source, with timestamps (Appendix D).

Only Chinese-registered funds are used. Mainland investors cannot buy foreign-domiciled funds directly, and such funds carry no R1-R5 rating. QDII funds provide overseas exposure inside the domestic framework, and their portfolio share is analysed as a measure of international diversification. Identities were checked against fund-manager key-facts statements and periodic reports indexed by several financial data sites. Risk ratings and return histories must come from a single source, because ratings are assigned by managers or distributors and change: one manager re-rated more than twenty funds in August 2026. The pipeline retrieves both from the course-provided fund data service, with Eastmoney's Tiantian Fund platform as a fallback. It records the raw response and retrieval time per fund and will not run while any fund lacks a verified rating. Equity exposure is each fund's latest reported stock share where the fund holds stocks directly, and a stated category assumption for index feeders, the fund of funds and the gold fund.

# 7. AI Recommendation Prompts and Implementation

## 7.1 Prompts

Each request has two messages. The system message plays the platform's deployment instructions: the adviser role, the 23-fund menu (code, name, manager, type, rating and notes on tracked index, QDII status and holding period), the response format and, under SUIT, the protocol. The user message is the investor: "Here is my situation:", the profile, and a request for a portfolio (Appendix C). The JSON format asks for codes, whole-number weights, a reason per fund, a dollar-cost-averaging flag, a rebalancing rule, risk warnings and a short explanation. Structured output trades some realism for reliable coding, and replies that break the format are recorded as failures, never repaired by hand. The risk class code never appears, so under SUIT the model must classify the investor itself and its classification can be scored. The menu order is fixed. Given the sensitivity of LLMs to presentation (Sclar et al., 2024), this keeps conditions comparable at the cost of confounding menu position with fund appeal.

## 7.2 Models and configuration

Three models from three Chinese developers are audited (Table 6): Doubao-Seed (ByteDance), DeepSeek V4 Flash (DeepSeek) and Kimi (Moonshot AI). All three are reached with one key through the Volcano Engine Ark Agent Plan, the access route specified for the course, using its OpenAI-compatible endpoint with identical messages and settings. Exact identifiers are taken from the plan's model list and recorded with the identifier returned in every response, because hosted models change without notice. Temperature is 0.7 for every model, as in the course's reference script; sampling is therefore stochastic, which the consistency module measures directly.

TABLE: Table 6. Model configuration
| Setting | Doubao | DeepSeek | Kimi (fallback: GLM) |
|---|---|---|---|
| Developer | ByteDance | DeepSeek | Moonshot AI (Zhipu AI) |
| Model identifier | doubao-seed-2.0-mini, confirmed at run time | Flash tier, recorded at run time | Recorded at run time |
| Temperature | 0.7 | 0.7 | 0.7 |
| Reasoning | Thinking disabled | Thinking disabled | Endpoint default, recorded |
| Output | JSON mode, up to 2,500 tokens | Same | Same |
| Retries | 5 attempts, exponential back-off, 180 s timeout | Same | Same |
NOTE: Access through the Volcano Engine Ark Agent Plan endpoint (https://ark.cn-beijing.volces.com/api/plan/v3). Settings are in config/experiment_config.json; any parameter a model rejects is dropped and the change is recorded per call.

## 7.3 Execution, coding and historical check

The 2,508 calls run in one random order across models, conditions and modules. Each call is appended to a log the moment it finishes. The record holds the call identifier, the condition and investor, the model requested and returned, every request parameter, SHA-256 hashes of both messages, the raw reply, the finish reason, token usage and timestamps. Logs are never edited. A rerun skips completed calls and retries failed ones, and each run writes a manifest. A 60-call pilot checks parsing before the main run and is excluded from the analysis, and the prompts are frozen after it. A dry run estimates about 3.8 million input tokens; actual usage is taken from provider reports.

A deterministic script codes each reply, so the same logs always give the same dataset. It records whether the JSON parsed directly or only after removing a code fence, extracting the object from surrounding text or deleting trailing commas. Unparseable replies stay in the data without portfolio measures. Off-menu codes count as feasibility errors and are dropped from the risk measures, with the remaining weights rescaled to 100. Nothing is imputed (rules in Appendix E).

Each coded portfolio is then back-tested over the longest window of complete months, up to 60, that ends in September 2026 and is covered for every fund (the exact window is reported with the results). Adjusted net asset values from the course data service are taken at month ends and the portfolio is rebalanced monthly. The script computes annualised return, volatility, maximum drawdown and the worst rolling 12-month return, and compares the last with the maximum one-year loss the investor said they could accept: none, 5%, 15%, 25% and 40% for C1 to C5. These are historical, descriptive measures, not forecasts.

# 8. Evaluation Metrics and Statistical Methods

## 8.1 Metrics

Table 7 defines the outcome measures. Equity exposure is the main continuous outcome because suitability rules and life-cycle theory speak to it most directly. The weighted product-risk score needs no assumption about holdings because it uses the platform's own ratings.

TABLE: Table 7. Evaluation metrics
| Metric | Calculation | Relevance |
|---|---|---|
| Parse success; codable | Valid JSON with at least one on-menu fund | Unusable advice cannot be executed |
| Off-menu rate; weight-sum validity | Codes not on the menu; weights sum to 100 within 1 point | Feasibility |
| Equity exposure (%) | Sum of weight x fund equity exposure | Main outcome (RQ1) |
| Weighted product risk (1-5) | Sum of weight x rating | Uses the platform's ratings |
| Rating breach; breach weight | Any fund rated above the investor's ceiling; its weight | Regulatory rule |
| Equity over cap | Equity more than 5 points above min(risk cap, horizon cap) | Horizon mismatch |
| Holding-period breach | A fund's lock-up exceeds the horizon | Liquidity |
| Loss-tolerance breach | Worst historical 12-month return below minus the stated maximum loss | Evidence-based suitability |
| QDII share | Weight in QDII funds | International diversification |
| Conflict acknowledgement | Conflict vocabulary; conflicts listed (SUIT) | Communication |
| Classification accuracy (SUIT) | Assessed vs actual class; weighted kappa | Profiling |
| Reliability | ICC(1,1) over three replicates; Jaccard similarity of fund sets | RQ4 |
| Probe slope | Change in equity per one-level step of one attribute | RQ4 |
NOTE: Equity caps are 0, 20, 50, 80 and 100% for C1-C5 and 10, 30, 50, 80 and 100% for H1-H5. They are the researchers' operationalisation of the matching rule and life-cycle reasoning, not regulatory limits.

The risk caps translate the product ceilings into equity terms. A C1 investor may hold only money market funds, a C2 investor may add bond funds with limited equity, and each further class unlocks riskier products. The horizon caps express the view that money needed within a year should be almost entirely in assets that cannot fall sharply, and that full equity exposure is defensible only over horizons long enough to recover from a deep bear market. Because both sets of caps are judgements, the rating breach, which involves none, is always reported beside them, and stricter and looser variants are tested.

## 8.2 Statistical methods

The attributes are orthogonal and balanced, so their effects can be estimated without confounding; conditions and models vary within investors, so their comparisons are paired (Table 8).

TABLE: Table 8. Statistical methods by research question
| Question | Method | Effect size |
|---|---|---|
| RQ1 | Spearman correlations per model x condition; Type II ANOVA of equity on the three attributes; pooled OLS with attribute x condition terms, model fixed effects and investor-clustered errors | rho; partial eta squared; points per category step |
| RQ2 | Breach rates by model, condition and risk class; conflict vs non-conflict profiles | Percentages with 95% CIs |
| RQ3 | Within-investor BASE vs SUIT: McNemar (exact below 25 discordant pairs); Wilcoxon signed-rank | Difference in proportions; discordant odds ratio; rank-biserial r; d_z |
| RQ4 | ICC(1,1); within-investor SD; Jaccard; slopes within probe anchors | ICC with 95% CI (Koo & Li, 2016) |
| RQ5 | Friedman test paired by investor; pairwise Wilcoxon; Cochran's Q | Kendall's W; rank-biserial r |
NOTE: p-values are two-sided and Holm-adjusted within each table (Holm, 1979). Interpretation rests on effect sizes and intervals, not significance alone (Cohen, 1988).

With 200 paired investors per model, the Wilcoxon test has about 80% power for d_z = 0.2, and a Spearman test on 200 investors has similar power for rho of about 0.2. Small effects will therefore often be significant, which is why effect sizes lead the interpretation. Robustness checks repeat the main analyses without repaired parses, off-menu replies or invalid weight sums; count a breach only above 5% of the portfolio; add experience, log amount and income stability as covariates; and recompute equity with category assumptions for every fund.

# 9. Experimental Results

PENDING: This section is written only from the outputs of the experiment (outputs/tables/results_digest.md and outputs/figures). Planned exhibits: 9.1 data quality and feasibility (coded replies, parse failures, off-menu and weight-sum errors by model and condition); 9.2 responsiveness to risk tolerance, horizon and age (Figures 2-4: mean equity by attribute level; Spearman correlations; Figure 5: partial eta squared); 9.3 suitability breaches (rating, horizon, holding-period and loss-tolerance breaches by risk class; Figure 6: rating breaches; Figure 7: risk x horizon heat map); 9.4 effect of the suitability protocol (paired tests); 9.5 consistency and single-attribute sensitivity (ICC, Jaccard; Figure 8: probe curves); 9.6 model differences; 9.7 historical check (Figure 9: worst 12-month return against stated tolerance); 9.8 robustness. No result is reported before the experiment has been run.

# 10. Discussion and Interpretation

PENDING: Written after the results are available.

# 11. Implications for AI-Based Investment Advice

PENDING: Written after the results are available.

# 12. Limitations

Several limitations follow from the design itself, and others will be added once the results show where the method strained.

**Synthetic investors.** The clients are stylised descriptions written to a template, not real people. A real client's request is vaguer, often inconsistent in ways no rule anticipates, and usually arrives as a conversation rather than a single message. The study therefore measures how models respond to clearly stated profiles. That is close to a best case for tailoring, so failures observed here are likely to understate failures in practice.

**One menu at one point in time.** The 23-fund menu is a single shelf with ratings and allocations retrieved on one date. Ratings change (one manager re-rated more than twenty funds in August 2026), and a different shelf might draw different choices. The back-test window covers a single five-year period. Historical losses describe what the recommended mixes did, not what they will do.

**Model drift and stochastic output.** Hosted models are updated without notice, and responses at temperature 0.7 vary from one call to the next. The study records the model identifier returned with every reply and measures run-to-run variation directly, but it cannot guarantee that a rerun months later would reproduce the same numbers (Atil et al., 2024).

**One wording per condition.** Each condition uses one wording and one fixed menu order. Given the sensitivity of LLMs to prompt format (Sclar et al., 2024), the effect of the suitability protocol is the effect of this particular protocol, and position effects in the menu cannot be separated from the appeal of individual funds.

**Normative benchmarks.** The rating breach rests on an external rule. The equity caps and the five-point tolerance are the researchers' operationalisation, and equity exposure for index feeder funds and the pension fund of funds relies on category assumptions. Robustness checks vary these choices but cannot remove the element of judgement.

**Automated text coding.** Conflict acknowledgement is coded with keyword rules. Until the planned manual validation has been carried out (Appendix E), this measure is treated as indicative.

**Scope.** Gender, region and other demographic signals were deliberately excluded, so the study says nothing about fairness. Fees, taxes and product availability on specific platforms are also outside its scope.

# 13. Conclusion

PENDING: Written after the results are available.

PAGEBREAK

# References

REFERENCES: docs/references_apa.md

PAGEBREAK

APPENDICES: report/appendices_generated.md
