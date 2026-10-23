TITLE: Who Gets What? A Factorial Audit of How Large Language Models Tailor Mutual Fund Portfolios to Investor Age, Risk Tolerance and Investment Horizon
SUBTITLE: Group Research Report - FinTech: Theory and Practice
META: Shenzhen MSU-BIT University
META: Group members: [names and student numbers to be completed by the group]
META: Date: [submission date]
META: DRAFT STATUS: Full draft for group review. Results from the run of 23 October 2026; manual double coding (Appendix E) still to be completed.

PAGEBREAK

# Abstract

Large language models (LLMs) are now a common first stop for retail investors, yet a chatbot carries none of the suitability duties that bind a licensed adviser. This study audits how three LLMs from different developers recommend Chinese public mutual funds to 200 synthetic investors. The investors are built as a balanced full factorial of five investment horizons, five risk-tolerance classes and eight age bands, one investor per cell, so the three attributes are uncorrelated by construction. Every investor is advised by every model under two deployment prompts: a baseline adviser prompt and the same prompt with an explicit suitability protocol added. Models choose only from a menu of 23 real funds whose identities were verified against public records. Each recommendation is scored against the product-risk matching rule used by Chinese fund distributors, a horizon-based equity ceiling, the minimum holding period of a pension fund, and the investor's own stated loss tolerance, which is checked against five years of fund return data. Two further modules measure test-retest consistency and the effect of changing one attribute at a time.

All 2,508 calls succeeded, and 1,199 of the 1,200 main-sample replies could be coded. Risk tolerance dominated the recommendations (partial eta squared 0.66 to 0.83 for equity exposure), horizon came second (0.41 to 0.53), and age had almost no effect (0.02 to 0.08; about 1.2 percentage points less equity per age band in a pooled model). Under the baseline prompt about half of all recommendations, and 83 to 86% of those made to investors in classes C1 to C3, contained a fund rated above the investor's permitted level, although every rating was shown in the prompt. The suitability protocol lowered rating breaches by 9.5 to 24.5 percentage points and equity above the cap by 6 to 7 points in every model, but 42 to 70% of C1 to C3 recommendations still breached the rule, including 40 to 66% of those in which the model had classified the investor correctly. Equity levels were highly repeatable across queries (ICC 0.95 to 0.98) while fund selections were not (mean Jaccard similarity 0.59 to 0.70). In a 59-month back-test, at most 1% of recommendations per model and condition would have lost more in a year than the investor said they could bear.

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
| Model (within investor) | Doubao, DeepSeek, Kimi | 3 | - |
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
NOTE: Identities verified against at least two public records on 22 October 2026. Ratings (R1 3, R2 4, R3 2, R4 14, R5 0) and stock shares from Eastmoney (Tiantian Fund), retrieved 23 October 2026; adjusted NAV histories from the course data service (Appendix D).

Only Chinese-registered funds are used. Mainland investors cannot buy foreign-domiciled funds directly, and such funds carry no R1-R5 rating. QDII funds provide overseas exposure inside the domestic framework, and their portfolio share is analysed as a measure of international diversification. Identities were checked against fund-manager key-facts statements and periodic reports indexed by several financial data sites. Product risk ratings and return histories then had to come from consistent sources. The course data service (Tonghuashun data via fuyao.aicubes.cn) supplies adjusted net asset values but, as its live responses and field documentation confirmed, no product risk rating. Ratings were therefore taken from the structured rating field of Eastmoney's Tiantian Fund platform, a licensed distributor whose ratings govern sales on that platform, and retrieved for all 23 funds on 23 October 2026, together with each fund's stock share from its 30 June 2026 report. Ratings change over time (one manager re-rated more than twenty funds in August 2026), so the retrieval date is part of the data. The resulting menu contains three R1 funds (money market), four R2 funds (bond), two R3 funds (an enhanced-return bond fund and a flexible hybrid) and fourteen R4 funds, which include the gold fund and the pension fund of funds; no menu fund is rated R5. One consequence matters for the analysis: because every fund is rated R4 or lower, a C4 or C5 investor cannot breach the rating ceiling, so the rating-breach test is informative only for investors in classes C1 to C3. Equity exposure is each fund's latest reported stock share where the fund holds stocks directly, and a stated category assumption for index feeders, the fund of funds and the gold fund.

# 7. AI Recommendation Prompts and Implementation

## 7.1 Prompts

Each request has two messages. The system message plays the platform's deployment instructions: the adviser role, the 23-fund menu (code, name, manager, type, rating and notes on tracked index, QDII status and holding period), the response format and, under SUIT, the protocol. The user message is the investor: "Here is my situation:", the profile, and a request for a portfolio (Appendix C). The JSON format asks for codes, whole-number weights, a reason per fund, a dollar-cost-averaging flag, a rebalancing rule, risk warnings and a short explanation. Structured output trades some realism for reliable coding, and replies that break the format are recorded as failures, never repaired by hand. The risk class code never appears, so under SUIT the model must classify the investor itself and its classification can be scored. The menu order is fixed. Given the sensitivity of LLMs to presentation (Sclar et al., 2024), this keeps conditions comparable at the cost of confounding menu position with fund appeal.

## 7.2 Models and configuration

Three models from three Chinese developers are audited (Table 6): Doubao-Seed 2.0 mini (ByteDance), DeepSeek V4 Flash (DeepSeek) and Kimi K2.6 (Moonshot AI). The course specified access through the Volcano Engine Ark Agent Plan. That route could not be used: the keys available to the group were ordinary Ark keys, which the Agent Plan endpoint rejected, and the pay-as-you-go alternative required a verification step the account holder could not complete. The same three model families were therefore called through OpenRouter, an OpenAI-compatible gateway. Each model was pinned to a single serving provider with fallbacks disabled, so every reply for a model comes from the same deployment: ByteDance's own Seed service, Moonshot AI's own service, and SiliconFlow for DeepSeek, for which no first-party provider was offered. Every call uses identical messages and settings, and the provider and model identifier returned with each reply are logged. Temperature is 0.7 for every model, as in the course's reference script, so sampling is stochastic; the consistency module measures this directly. Reasoning modes were disabled for all three models. For Kimi this was done after the pilot, where the model spent its whole output allowance on hidden reasoning and returned no answer; the 20 failed pilot calls remain in the log.

TABLE: Table 6. Model configuration
| Setting | Doubao | DeepSeek | Kimi |
|---|---|---|---|
| Developer | ByteDance | DeepSeek | Moonshot AI |
| Model identifier | bytedance-seed/seed-2.0-mini | deepseek/deepseek-v4-flash | moonshotai/kimi-k2.6 |
| Serving provider (pinned) | Seed (ByteDance) | SiliconFlow | Moonshot AI |
| Temperature | 0.7 | 0.7 | 0.7 |
| Reasoning | Disabled | Disabled | Disabled |
| Output | JSON mode, up to 2,500 tokens | Same | Same |
| Retries | 5 attempts, exponential back-off, 180 s timeout | Same | Same |
NOTE: Access through OpenRouter (https://openrouter.ai/api/v1) on 23 October 2026, after the Volcano Engine Ark Agent Plan route failed (docs/run_status.md). Settings are in config/experiment_config.json; the serving provider is recorded for every call.

## 7.3 Execution, coding and historical check

The 2,508 calls run in one random order across models, conditions and modules. Each call is appended to a log the moment it finishes. The record holds the call identifier, the condition and investor, the model requested and returned, every request parameter, SHA-256 hashes of both messages, the raw reply, the finish reason, token usage and timestamps. Logs are never edited. A rerun skips completed calls and retries failed ones, and each run writes a manifest. A 60-call pilot checks parsing before the main run and is excluded from the analysis, and the prompts are frozen after it. A dry run estimated about 4.0 million input tokens. Actual usage, taken from the provider reports in the logs, was 3.72 million prompt tokens and 1.46 million completion tokens for all 2,588 logged calls, at a total cost of USD 3.13.

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

The experiment ran on 23 October 2026. All 2,508 planned calls succeeded in one run (run_20261023T083039Z), after a 60-call pilot that is excluded from the analysis. Every number in this section comes from the tables written by the analysis scripts (outputs/tables/T04 to T25 and results_digest.md); none was entered by hand. Unless stated otherwise, results refer to the main sample of 200 investors x 2 conditions x 3 models.

## 9.1 Data quality and feasibility

The models almost always produced executable advice (Table 9). Of the 2,568 replies coded across all modules, including the pilot, five had problems: three Doubao replies were malformed JSON (a value without a key inside a portfolio entry) and could not be parsed, and two DeepSeek replies each contained one fund code that is not on the menu. In the main sample this leaves 1,199 codable replies, with one Doubao SUIT reply lost. Stated weights summed to 100 in every coded reply, and no reply needed a repaired or extracted parse. The only systematic format deviation came from DeepSeek, which recommended fewer than the requested three to eight funds in 51 main-sample replies (10.5% under BASE and 15.0% under SUIT); these replies are kept as given. Kimi built the most diversified portfolios (5.2 to 5.7 funds on average) and recommended dollar-cost averaging most often. All three models stated a rebalancing rule in every reply.

TABLE: Table 9. Feasibility and response behaviour, main sample
| Model | Condition | Replies | Codable (%) | Any off-menu fund (%) | 3-8 funds (%) | Mean funds | DCA recommended (%) | Mean risk warnings |
|---|---|---|---|---|---|---|---|---|
| DeepSeek | BASE | 200 | 100.0 | 0.5 | 89.5 | 4.57 | 60.5 | 3.54 |
| DeepSeek | SUIT | 200 | 100.0 | 0.0 | 85.0 | 4.21 | 50.0 | 3.26 |
| Doubao | BASE | 200 | 100.0 | 0.0 | 100.0 | 4.52 | 27.5 | 3.02 |
| Doubao | SUIT | 200 | 99.5 | 0.0 | 99.5 | 4.40 | 20.1 | 2.78 |
| Kimi | BASE | 200 | 100.0 | 0.0 | 100.0 | 5.67 | 69.0 | 3.98 |
| Kimi | SUIT | 200 | 100.0 | 0.0 | 100.0 | 5.16 | 61.0 | 3.87 |
NOTE: From outputs/tables/T04_feasibility_and_behaviour.csv. DCA: dollar-cost averaging. Codable: valid JSON with at least one on-menu fund.

## 9.2 Responsiveness to risk tolerance, horizon and age (RQ1)

Recommended equity exposure followed risk tolerance closely in every model and condition (Figure 2). Under BASE, mean equity rose from 0.1 to 0.8% for C1 investors to 62.5 to 72.9% for C5 investors; under SUIT from 0% to 53.2 to 64.1%. The Spearman correlation between risk class and equity was 0.69 to 0.83, and risk class alone had a partial eta squared of 0.66 to 0.83 in the three-factor ANOVA (Table 10, Figure 5).

Horizon mattered as well, but mostly at one point (Figure 3). Investors who needed their money within a year received almost no equity (BASE means 0.9 to 7.0%), while the jump to a one-to-three-year horizon was large (to 26.3 to 34.2%). Beyond three years, equity rose more slowly, reaching 42.0 to 44.5% for horizons of ten years or more. Horizon correlations were 0.33 to 0.50 and partial eta squared 0.41 to 0.53.

Age had almost no effect (Figure 4). The correlation between age band and equity was negative in all six model x condition cells (-0.04 to -0.11) but small, and none was significant after Holm adjustment; the age term in the ANOVA had partial eta squared 0.02 to 0.08 and Holm-adjusted p of at least 0.14. Under BASE, the youngest band (18-24) received 30.2 to 35.8% equity and the oldest (75-85) 24.7 to 29.0%. Pooling all models and conditions, the regression with investor-clustered errors estimates 18.2 percentage points more equity per risk-class step (95% CI 16.5 to 19.8), 8.7 per horizon step (7.0 to 10.4) and 1.2 less per age band (-2.1 to -0.3; p = 0.009), with R squared 0.73 (outputs/tables/T10). Adding experience, log amount and income stability as covariates leaves these estimates essentially unchanged (risk 18.3, horizon 8.6, age -1.6; T21), and none of the covariates is significant.

TABLE: Table 10. Responsiveness of equity exposure to the three investor attributes
| Model | Condition | rho risk | rho horizon | rho age | Partial eta sq. risk | Partial eta sq. horizon | Partial eta sq. age |
|---|---|---|---|---|---|---|---|
| DeepSeek | BASE | 0.76 | 0.43 | -0.06 | 0.79 | 0.53 | 0.04 |
| DeepSeek | SUIT | 0.69 | 0.50 | -0.05 | 0.71 | 0.50 | 0.04 |
| Doubao | BASE | 0.83 | 0.38 | -0.11 | 0.83 | 0.50 | 0.08 |
| Doubao | SUIT | 0.83 | 0.33 | -0.09 | 0.78 | 0.41 | 0.08 |
| Kimi | BASE | 0.73 | 0.48 | -0.04 | 0.76 | 0.52 | 0.03 |
| Kimi | SUIT | 0.71 | 0.47 | -0.05 | 0.66 | 0.46 | 0.02 |
NOTE: Spearman correlations (n = 200; 199 for Doubao SUIT) from T08 and Type II ANOVA from T09. All risk and horizon effects have Holm-adjusted p < 0.001; no age effect has Holm-adjusted p < 0.05.

FIGURE: outputs/figures/F01_equity_by_risk_class.png | Figure 2. Mean equity exposure by investor risk class | Dotted line: equity ceiling implied by the risk class (0, 20, 50, 80 and 100%). Main sample, n = 40 per point (39 for Doubao SUIT C5).

FIGURE: outputs/figures/F02_equity_by_horizon.png | Figure 3. Mean equity exposure by investment horizon | Main sample, n = 40 per point.

FIGURE: outputs/figures/F03_equity_by_age_band.png | Figure 4. Mean equity exposure by age band | Main sample, n = 25 per point.

FIGURE: outputs/figures/F04_relative_importance_partial_eta.png | Figure 5. Relative importance of the three attributes | Partial eta squared from a Type II ANOVA of equity exposure on risk class, horizon band and age band, per model and condition.

The variance shares make the hierarchy plain. Risk class alone accounts for 51 to 70% of the total variance in equity exposure, against 15 to 23% for horizon and age together (T09). QDII funds follow the same pattern: their portfolio share averages 7.2 to 10.7%, rises with risk class (rho 0.64 to 0.73) and horizon (0.33 to 0.46), and is unrelated to age (T19).

## 9.3 Suitability breaches (RQ2)

Table 11 reports the four suitability tests. Under BASE, 49.5 to 51.5% of recommendations included at least one fund rated above the investor's permitted level. Because no fund on the menu is rated R5, investors in classes C4 and C5 cannot breach the rating rule, so the informative rate is the one among C1 to C3 investors: 82.5 to 85.8% under BASE (T22, Figure 6). Most of these breaches were one notch above the ceiling, but they were not token positions (T23). For C1 investors, whose ceiling is R1 (money market funds only), 90.5% of breaching replies reached no higher than R2, typically bond funds, yet the breaching funds made up 49.8% of the portfolio on average. All C3 breaches involved an R4 fund, at an average weight of 30.0%. Counting a breach only when the breaching funds exceed 5% of the portfolio changes the rates by at most 0.5 percentage points (T20).

TABLE: Table 11. Suitability outcomes by model and condition, main sample
| Model | Condition | n | Rating breach, all (%) | Rating breach, C1-C3 (%) | Equity over cap (%) | Holding-period breach (%) | Loss-tolerance breach (%) | Mean equity (%) |
|---|---|---|---|---|---|---|---|---|
| DeepSeek | BASE | 200 | 51.5 | 85.8 | 22.0 | 0.5 | 1.0 | 32.0 |
| DeepSeek | SUIT | 200 | 42.0 | 70.0 | 16.0 | 0.0 | 1.0 | 28.7 |
| Doubao | BASE | 200 | 51.5 | 85.8 | 20.5 | 0.0 | 0.0 | 31.0 |
| Doubao | SUIT | 199 | 40.7 | 67.5 | 13.1 | 0.0 | 0.0 | 24.7 |
| Kimi | BASE | 200 | 49.5 | 82.5 | 18.5 | 0.0 | 0.0 | 28.0 |
| Kimi | SUIT | 200 | 25.0 | 41.7 | 11.5 | 0.0 | 0.0 | 23.0 |
NOTE: From T11, T13 and T22. C1-C3 columns: n = 120 per cell. C4 and C5 investors cannot breach the rating rule because the menu has no R5 fund. Mean equity for Doubao is over the 199 investors with codable replies under both conditions.

FIGURE: outputs/figures/F05_rating_breach_by_risk_class.png | Figure 6. Share of replies with a fund rated above the permitted level, by risk class | Main sample, n = 40 per bar (39 for Doubao SUIT C5). No breach is possible for C4 and C5 because the menu contains no R5 fund.

Equity above the combined risk and horizon cap was rarer (18.5 to 22.0% under BASE) and arose almost entirely among aggressive investors. Under BASE it affected 32.5 to 40.0% of C4 and 55.0 to 62.5% of C5 recommendations (T12). Figure 7 shows why: the models cut equity sharply for horizons under one year, but treated a C4 or C5 investor with a one-to-three-year horizon almost like a long-horizon investor. Pooled across models, C5 investors with an H2 horizon received 78% equity under BASE, against a horizon cap of 30%.

FIGURE: outputs/figures/F06_heatmap_risk_by_horizon.png | Figure 7. Mean equity exposure by risk class and horizon | Pooled over the three models; each cell averages 24 replies (8 investors x 3 models).

This is the pattern H6 anticipated. Among C4 and C5 investors with horizons under three years, the conflict group, 50.0 to 65.6% of BASE recommendations exceeded the equity cap, against 15.6 to 21.9% among C4 and C5 investors with horizons of five years or more (T17). The pension fund of funds, with its three-year lock-up, was recommended to an investor with a shorter horizon only once (one DeepSeek BASE reply). Back-tested losses exceeded the investor's stated tolerance in only two C3 portfolios per condition, both from DeepSeek (Section 9.7).

## 9.4 Effect of the suitability protocol (RQ3)

Adding the suitability protocol improved every suitability measure in every model (Table 12). Rating breaches fell by 9.5 points for DeepSeek, 11.1 for Doubao and 24.5 for Kimi. The paired changes run almost entirely in one direction: among investors whose breach status differed between conditions, the protocol removed a breach in 19, 24 and 49 cases and added one in 0, 2 and 0 cases. Equity above the cap fell by 6 to 7 points, mean equity by 3.4 to 6.3 points and the weighted product-risk score by 0.12 to 0.20. The pooled regression gives the same picture: 4.9 points less equity under SUIT (95% CI -5.9 to -3.8) and a slightly flatter risk gradient (-1.8 points per risk step), with no change in the horizon or age gradients (T10).

TABLE: Table 12. Paired effect of the suitability protocol (SUIT minus BASE)
| Model | Outcome | BASE | SUIT | Difference | Paired statistic | Holm p |
|---|---|---|---|---|---|---|
| DeepSeek | Rating breach (%) | 51.5 | 42.0 | -9.5 | Discordant 19 vs 0 | < 0.001 |
| Doubao | Rating breach (%) | 51.8 | 40.7 | -11.1 | Discordant 24 vs 2 | < 0.001 |
| Kimi | Rating breach (%) | 49.5 | 25.0 | -24.5 | Discordant 49 vs 0 | < 0.001 |
| DeepSeek | Equity over cap (%) | 22.0 | 16.0 | -6.0 | Discordant 14 vs 2 | 0.029 |
| Doubao | Equity over cap (%) | 20.1 | 13.1 | -7.0 | Discordant 16 vs 2 | 0.012 |
| Kimi | Equity over cap (%) | 18.5 | 11.5 | -7.0 | Discordant 16 vs 2 | 0.012 |
| DeepSeek | Equity (%) | 32.0 | 28.7 | -3.4 [-5.2, -1.6] | d_z = -0.27 | < 0.001 |
| Doubao | Equity (%) | 31.0 | 24.7 | -6.3 [-7.6, -4.9] | d_z = -0.63 | < 0.001 |
| Kimi | Equity (%) | 28.0 | 23.0 | -5.0 [-6.6, -3.3] | d_z = -0.42 | < 0.001 |
NOTE: From T13. Binary outcomes: McNemar test; discordant pairs are investors with a breach under BASE only vs under SUIT only. Equity: Wilcoxon signed-rank test, mean difference with 95% CI. Doubao: 199 pairs. p-values Holm-adjusted within the table of paired tests.

The protocol did not, however, make the models comply with the rule. Under SUIT, 41.7 to 70.0% of recommendations to C1 to C3 investors still contained a fund above the investor's ceiling (T22). This was not mainly a failure to classify the investor. The models' own classifications agreed exactly with the true class in 60.0% (DeepSeek), 86.4% (Doubao) and 88.5% (Kimi) of cases, with quadratic weighted kappa of 0.73, 0.94 and 0.88 (T18). Among C1 to C3 investors whom the model had classified correctly, 58.5% (DeepSeek), 66.4% (Doubao) and 39.8% (Kimi) of recommendations still included a fund rated above that class (T25).

The protocol changed how conflicts were handled. In the conflict group, SUIT replies listed a conflict in 100% (DeepSeek and Kimi) and 90.6% (Doubao) of cases, and mean equity fell from 38.3 to 26.7% (DeepSeek), 46.5 to 33.9% (Doubao) and 29.7 to 14.0% (Kimi). Under BASE, conflict vocabulary appeared in 0 to 6% of these replies for DeepSeek and Doubao and in 50% for Kimi. For aggressive investors with long horizons, where no conflict exists, SUIT left equity almost unchanged for DeepSeek (79.6 to 80.3%) and Kimi (79.2 to 79.3%) and lowered it by 6.9 points for Doubao (78.7 to 71.8%) (T17). The models also listed conflicts for 6 to 69% of these no-conflict investors.

## 9.5 Consistency and single-attribute sensitivity (RQ4)

Asking the same question three times gave very similar equity levels but different portfolios (Table 13). The intraclass correlation of equity exposure across replicates was 0.95 to 0.98, and the average within-investor standard deviation was 3.1 to 4.5 points, although single investors varied by up to 38 points. The funds chosen varied much more: the mean Jaccard similarity between replicate fund sets was 0.59 to 0.70, and all three replicates named the same set of funds for only 2.5 to 15.0% of investors. Whether a recommendation breached the rating rule was the same in all three replicates for 82.5 to 95.0% of investors, so for the rest the verdict depended on which reply was drawn.

TABLE: Table 13. Consistency across three replicates (40 investors)
| Model | Condition | Investors | ICC(1,1) equity [95% CI] | Mean within-investor SD (points) | Mean Jaccard of fund sets | Identical fund sets (%) | Same breach verdict (%) |
|---|---|---|---|---|---|---|---|
| DeepSeek | BASE | 40 | 0.98 [0.96, 0.99] | 3.9 | 0.61 | 15.0 | 90.0 |
| DeepSeek | SUIT | 40 | 0.95 [0.91, 0.97] | 4.5 | 0.64 | 12.5 | 90.0 |
| Doubao | BASE | 40 | 0.97 [0.95, 0.98] | 4.3 | 0.60 | 10.0 | 95.0 |
| Doubao | SUIT | 39 | 0.95 [0.92, 0.97] | 4.4 | 0.59 | 5.1 | 84.6 |
| Kimi | BASE | 40 | 0.98 [0.97, 0.99] | 3.1 | 0.67 | 2.5 | 85.0 |
| Kimi | SUIT | 40 | 0.96 [0.93, 0.98] | 4.1 | 0.70 | 7.5 | 82.5 |
NOTE: From T15. One Doubao SUIT replicate could not be parsed, leaving 39 investors.

The probe module, which changes one attribute at a time with neutral wording, confirms the dominance of risk tolerance and qualifies the horizon effect (Table 14, Figure 8). Moving an anchor investor one risk class up raised equity by 20.3 to 24.0 points, in the expected direction for all ten anchors in every model and condition. Moving the horizon one band longer raised equity by only 1.0 to 3.8 points, in the expected direction for 3 to 8 of the 10 anchors, with about one reversal per anchor. Moving the age one band older lowered equity by 1.4 to 3.0 points, in the expected direction for 8 or 9 anchors but with 1.5 to 2.3 reversals per anchor. The horizon slope in the probes is thus much smaller than the 8.7 points per band in the main sample, where horizon comes bundled with consistent objectives and liquidity needs.

TABLE: Table 14. Single-attribute probes: mean change in equity per one-level step
| Model | Condition | Risk class step | Horizon step | Age band step |
|---|---|---|---|---|
| DeepSeek | BASE | +22.6 (10 of 10) | +2.3 (6 of 10) | -1.8 (8 of 10) |
| DeepSeek | SUIT | +22.6 (10 of 10) | +3.8 (8 of 10) | -1.5 (8 of 10) |
| Doubao | BASE | +24.0 (10 of 10) | +1.7 (8 of 10) | -1.5 (9 of 10) |
| Doubao | SUIT | +22.2 (10 of 10) | +1.0 (3 of 10) | -2.5 (8 of 10) |
| Kimi | BASE | +23.2 (10 of 10) | +3.4 (8 of 10) | -1.4 (9 of 10) |
| Kimi | SUIT | +20.3 (10 of 10) | +3.4 (8 of 10) | -3.0 (8 of 10) |
NOTE: From T16. Percentage points of equity per step, averaged over 10 anchors; in brackets, the number of anchors whose slope has the expected sign (positive for risk and horizon, negative for age).

FIGURE: outputs/figures/F07_single_attribute_probes.png | Figure 8. Single-attribute probes | Mean equity exposure as one attribute moves through its levels while the rest of the anchor profile is held constant; averaged over the 10 anchors.

## 9.6 Model differences (RQ5)

Under BASE the three models behaved much alike. Their rating-breach rates did not differ (Cochran's Q = 2.46, p = 0.29), and although their equity levels differed significantly (Friedman test, Holm p < 0.001), the effect was small (Kendall's W = 0.045): Kimi recommended 3.3 to 4.1 points less equity than the other two. Under SUIT the models diverged. Rating breaches differed clearly (Q = 45.2, p < 0.001), with Kimi at 25.0% against 40.7 to 42.0% for the others, and the equity differences grew (W = 0.084), with DeepSeek the most equity-heavy (T14). Kimi and Doubao also classified investors more accurately than DeepSeek (Section 9.4). In style, Kimi spread money over more funds and gave more risk warnings, Doubao rarely recommended dollar-cost averaging, and DeepSeek alone often named fewer than three funds (Table 9). Kimi cost about seven to eleven times as much per call as the other two (USD 2.56 for its 856 successful calls, against 0.33 for Doubao and 0.23 for DeepSeek; docs/run_status.md).

## 9.7 Historical check

All recommended portfolios were back-tested over the same 59 months, November 2021 to September 2026, the longest window that ends in September 2026 and is covered by every fund. Table 15 summarises the worst rolling 12-month return by risk class (Figure 9). Recommendations for C1 and C2 investors had positive worst 12-month returns in the median, those for C3 investors lost at most a few percent, and those for C4 and C5 investors lost 10.5 to 18.7% in their worst year in the median. Only four portfolios in the main sample lost more in a year than the investor had said they could accept: two DeepSeek recommendations to C3 investors under each condition, with worst 12-month returns down to -18.4% (BASE) and -18.8% (SUIT) against a stated limit of 15%.

TABLE: Table 15. Worst rolling 12-month return of recommended portfolios, by risk class
| Risk class | Stated maximum loss (%) | Median worst 12 months, BASE (%) | Median worst 12 months, SUIT (%) | Lowest, BASE (%) | Lowest, SUIT (%) | Exceeds stated loss, BASE / SUIT (%) |
|---|---|---|---|---|---|---|
| C1 | 0 | 1.3 | 1.3 | 0.6 | 0.9 | 0.0 / 0.0 |
| C2 | 5 | 1.3 | 1.4 | -3.3 | -3.6 | 0.0 / 0.0 |
| C3 | 15 | -2.6 | -0.5 | -18.4 | -18.8 | 1.7 / 1.7 |
| C4 | 25 | -13.2 | -10.5 | -24.7 | -24.0 | 0.0 / 0.0 |
| C5 | 40 | -18.7 | -16.5 | -28.3 | -28.0 | 0.0 / 0.0 |
NOTE: From T24. Main sample pooled over models, n = 120 per cell (119 for SUIT C5). Window 1 November 2021 to 30 September 2026, monthly rebalancing, adjusted NAVs from the course data service. Historical and descriptive, not a forecast.

FIGURE: outputs/figures/F08_backtest_worst_12m_vs_tolerance.png | Figure 9. Worst historical 12-month return against the investor's stated loss limit | Mean worst rolling 12-month return per risk class; dotted line: maximum one-year loss the investor accepts. Window November 2021 to September 2026.

The low loss-breach rate has a simple reason. In this window the menu's money market and bond funds never had a negative 12-month return, and the enhanced-return bond fund (R3) lost at most 1.1% (T_fund_history_metrics). The rating breaches of C1 and C2 investors, which mostly consisted of such funds, therefore did not translate into losses beyond the investor's stated limit. The R4 equity funds, by contrast, had worst 12-month returns between -9.3 and -36.9% (the gold fund aside), but the models diluted them enough that the portfolios of C4 and C5 investors stayed within their limits.

## 9.8 Robustness

The main results do not depend on the coding decisions. Excluding replies with off-menu funds, invalid weight sums or repaired parses changes the correlations by at most 0.003 and the breach rates by at most 0.3 points, because almost no reply falls into these groups. Counting a rating breach only when the breaching funds exceed 5% of the portfolio lowers the rates by at most 0.5 points (T20). The covariate-adjusted regression leaves the attribute and condition effects unchanged (T21). The planned variant that recomputes equity with category assumptions for every fund was not produced by the analysis script and is not reported.

# 10. Discussion and Interpretation

## 10.1 The hypotheses

Table 16 sets the results against the hypotheses fixed before the run. Five are supported, one only weakly, and one could be tested only in part, because the menu turned out to contain no R5 fund.

TABLE: Table 16. Hypotheses and results
| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1. Risk rises with risk tolerance | Supported | rho 0.69-0.83 in all six cells; +18.2 points per class; all 10 probe anchors in the expected direction |
| H2. Risk rises with horizon | Supported | rho 0.33-0.50; +8.7 points per band; much weaker in probes (+1.0 to +3.8) |
| H3. Risk falls with age | Weak support | Negative in all cells but not significant in any (rho -0.04 to -0.11); -1.2 points per band pooled |
| H4. Risk tolerance explains more than horizon and age combined | Supported | eta squared 0.51-0.70 vs 0.15-0.23 |
| H5. Protocol reduces rating breaches in each model | Supported | -9.5, -11.1 and -24.5 points; Holm p < 0.001 |
| H6. Breaches concentrate in conflict profiles | Supported for equity caps; rating test not possible | Over cap 50-66% vs 16-22% (BASE); C4-C5 cannot breach ratings |
| H7. Stable equity levels, varying fund choice | Supported | ICC 0.95-0.98; Jaccard 0.59-0.70 |
NOTE: Main sample unless stated. Sources: Tables 10 to 14 and T09, T10, T17.

## 10.2 Tailoring that rests on one attribute

All three models tailor, but they do so mainly along one dimension. Self-reported risk tolerance explains most of the variation in their portfolios, horizon matters mostly as a switch between "money needed within a year" and everything else, and age barely registers. This matches the decision-tree description of GPT-4o by Ross and Lo (2026) and extends it to three Chinese models. It is at odds with life-cycle theory, which expects a clear age gradient even at a fixed horizon (Bodie et al., 1992; Cocco et al., 2005). The probe results suggest why the horizon effect is larger in the main sample than in the probes. Main-sample profiles that state a short horizon also state matching objectives and liquidity needs, while the probes change only the number of years. A plausible reading is that the models react to the overall story of a profile, such as "saving for a purchase next year", more than to the stated horizon itself. The design cannot prove this, but it does show that a stated horizon on its own moves the models little.

## 10.3 The rating rule is visible but not followed

The most striking result is how often the models broke the product-risk matching rule even though each fund's rating was in the prompt. Under the baseline prompt, more than four in five recommendations to C1 to C3 investors included a fund above the permitted rating. The breaches follow an economic rather than a regulatory idea of caution. A very conservative investor was typically offered money market funds plus bond funds, a mix that most advisers would call conservative and that lost nothing in the back-test window. Under the distributor's rules, however, a C1 investor may hold only R1 products. The models appear to treat "conservative" as "low volatility", not as "within the rating ceiling".

The suitability protocol narrowed this gap but did not close it. Its effect was large and consistent in direction, and for Kimi it halved the breach rate. Yet most models still broke the rule for a majority of C1 to C3 investors, and they did so even after classifying the investor correctly in their own reply. Knowing the rule and applying it are evidently different steps. For a platform, this means that writing the rule into the prompt is not a control in the regulatory sense. Instruction-following failures of this kind are consistent with the sycophancy literature (Sharma et al., 2024), although here the models departed from the rule towards what they apparently judged to be good advice, not towards what the client asked for.

## 10.4 Short horizons and aggressive clients

The second weakness concerns aggressive investors with short horizons. Under the baseline prompt, a C5 investor who needed the money in one to three years received about three-quarters equity on average, more than double the horizon-based ceiling. This is the conflict that H6 anticipated, and the stated appetite for risk won. The protocol helped most exactly here: all models flagged the conflict in almost every case and cut equity substantially. For aggressive investors with long horizons, two of the three models left equity unchanged, which suggests that the protocol targets the conflict rather than making all advice more conservative. Doubao was the exception, lowering equity for these investors too.

## 10.5 Reliability and model differences

Equity levels were highly repeatable, but the specific funds were not, and the breach verdict changed between replicates for up to one investor in six. An audit or compliance check based on a single query per client would therefore misclassify a noticeable share of cases (Atil et al., 2024; Barbieri et al., 2026). The three models were close to one another under the baseline prompt and differed mainly in how strongly they responded to the protocol. Kimi responded most, which suggests that differences between models lie less in their default risk-taking than in how faithfully they follow added instructions.

## 10.6 How much the back-test can tell

The back-test found almost no portfolios that lost more than the investor said they could bear. This should not be read as evidence that the rating breaches were harmless. The window from late 2021 to 2026 was benign for Chinese bond and money market funds, and the menu's R2 and R3 bond funds never lost more than 1.1% over any twelve months. In a period of rising rates or credit stress, the same breaches could produce real losses for investors who had said they could accept none. The back-test also shows that the models diluted high-risk funds enough to keep aggressive investors' worst years within their limits, which is evidence of sensible portfolio construction, not of compliance with the rating rule.

# 11. Implications for AI-Based Investment Advice

**For platforms deploying general-purpose models.** Showing product ratings to the model and adding a suitability protocol to the prompt are not enough to keep advice within the distributor's matching rule. The rule should be enforced in code, outside the model: the shelf offered to the model for a given client should contain only products at or below that client's rating ceiling, or every recommendation should pass an automatic check before it is shown. The model's own risk classification can be used as an input, since it agreed with the true class in 60 to 89% of cases, but not as the control itself.

**For prompt design.** A suitability protocol is cheap and clearly worthwhile. It lowered rating breaches by up to half and almost removed unflagged risk-horizon conflicts, without making advice for aggressive long-horizon investors more conservative in two of three models. Its effect differs strongly between models, so a protocol has to be tested on the model actually deployed.

**For supervisors and auditors.** Model outputs are stochastic, so audits should use repeated queries per profile and report the breach rate across replicates, not a single verdict. Back-tests over one benign window can understate the risk of rating breaches and should be complemented by stress scenarios.

**For investors.** The models respond strongly to the stated attitude to risk and only weakly to age and to the time until the money is needed. An investor who uses a chatbot should state the horizon and any lock-up constraints explicitly and should treat a high-equity portfolio offered for a short horizon with suspicion.

**For model developers.** The gap between classifying a client correctly and then recommending products above that class points to a weakness in following explicit constraints during generation. It is measurable with the method used here and could serve as a benchmark task.

# 12. Limitations

Several limitations follow from the design itself, and others became visible in the results.

**Synthetic investors.** The clients are stylised descriptions written to a template, not real people. A real client's request is vaguer, often inconsistent in ways no rule anticipates, and usually arrives as a conversation rather than a single message. The study therefore measures how models respond to clearly stated profiles. That is close to a best case for tailoring, so failures observed here are likely to understate failures in practice.

**One menu at one point in time.** The 23-fund menu is a single shelf with ratings and allocations retrieved on one date. Ratings change (one manager re-rated more than twenty funds in August 2026), and a different shelf might draw different choices. The back-test window covers a single five-year period. Historical losses describe what the recommended mixes did, not what they will do.

**Model drift and stochastic output.** Hosted models are updated without notice, and responses at temperature 0.7 vary from one call to the next. The study records the model identifier returned with every reply and measures run-to-run variation directly, but it cannot guarantee that a rerun months later would reproduce the same numbers (Atil et al., 2024).

**One wording per condition.** Each condition uses one wording and one fixed menu order. Given the sensitivity of LLMs to prompt format (Sclar et al., 2024), the effect of the suitability protocol is the effect of this particular protocol, and position effects in the menu cannot be separated from the appeal of individual funds.

**Normative benchmarks.** The rating breach rests on an external rule. The equity caps and the five-point tolerance are the researchers' operationalisation, and equity exposure for index feeder funds and the pension fund of funds relies on category assumptions. Robustness checks vary some of these choices but cannot remove the element of judgement, and the planned variant with category-based equity for every fund was not produced.

**Model access and settings.** The models were reached through OpenRouter rather than the course's Volcano Engine Ark route, and DeepSeek was served by a third-party provider (SiliconFlow) rather than by its developer. A different deployment of the same model may behave differently. Reasoning modes were disabled for all three models, so the results describe their direct-answer behaviour, not their reasoning variants.

**No R5 product and one rating source.** The menu turned out to contain no R5 fund, so the rating test is informative only for C1 to C3 investors, and the conflict hypothesis (H6) could be tested only with the equity caps. The ratings are those of one distributor (Eastmoney's Tiantian Fund) on one date; other distributors may rate the same funds differently.

**A benign back-test window.** In the 59-month window, the menu's bond and money market funds never lost more than 1.1% over twelve months. The near absence of loss-tolerance breaches is therefore partly a property of the period and says little about how the same portfolios would fare in a bond market sell-off.

**Automated text coding.** Conflict acknowledgement is coded with keyword rules. Until the planned manual validation has been carried out (Appendix E), this measure is treated as indicative.

**Scope.** Gender, region and other demographic signals were deliberately excluded, so the study says nothing about fairness. Fees, taxes and product availability on specific platforms are also outside its scope.

# 13. Conclusion

This study audited how three Chinese LLMs recommend public mutual funds to 200 synthetic investors whose age, risk tolerance and investment horizon were varied independently, under a baseline adviser prompt and under the same prompt with a suitability protocol. All 2,508 queries were answered, and almost all replies were executable portfolios drawn from the given menu.

The models tailored their advice, but mainly to the investor's stated risk tolerance. Horizon mattered mostly when the money was needed within a year, and age hardly mattered at all. Under the baseline prompt, more than four in five recommendations to conservative and moderate investors broke the product-risk matching rule that Chinese distributors must follow, even though the ratings were in the prompt, and aggressive investors with short horizons received far more equity than their horizon justified. A suitability protocol in the prompt reduced both problems in every model, most strongly for Kimi, but left a majority of conservative and moderate investors with at least one product above their ceiling, often after the model had classified them correctly. Equity levels were stable across repeated queries, while the specific funds and, for some investors, the breach verdict were not. In a benign five-year back-test, the recommended portfolios rarely lost more than investors said they could bear.

The practical lesson is that a general-purpose LLM can produce sensible-looking, diversified portfolios but cannot be relied on to apply a regulatory rule it has been told about. Suitability constraints belong in the system around the model, not only in its prompt. Future work should test real conversational profiles, menus that include R5 products, reasoning modes and stress-period back-tests, and should complete the planned human validation of the text coding.

PAGEBREAK

# References

REFERENCES: docs/references_apa.md

PAGEBREAK

APPENDICES: report/appendices_generated.md
