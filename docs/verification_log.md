# Verification Log

This log records how factual claims, regulatory anchors, fund data and citations used in the project were checked. Each entry gives the claim, the sources consulted, the date and the outcome. Entries were added while the work was being done; nothing here was back-filled from memory.

Search access in the build environment was limited: direct page fetching failed for most sites (DNS errors), so checks below were made through a web-search service that returns source URLs and short extracts. Where only secondary sources could be reached, the entry says so.

## Regulatory anchors

| # | Claim used in the project | Sources consulted (retrieved 2026-10-22) | Outcome |
|---|---|---|---|
| R-1 | Under the fund-distribution suitability guideline, ordinary investors are classified C1-C5 (conservative to aggressive) and products R1-R5; matching rule: C1 -> R1 only; C2 -> R1-R2; C3 -> R1-R3; C4 -> R1-R4; C5 -> R1-R5. | Debon Fund suitability matching statement (2023): https://www.dbfund.com.cn/upload/pdf/2023-06-09-184303-德邦基金管理有限公司销售适当性匹配意见-202306.pdf ; China Merchants Fund document: https://www.cmfchina.com/upload/20240611/202406111718089072198.pdf ; China Securities Journal report (2017-07-03): https://www.cs.com.cn/tzjj/201707/t20170703_5354116.html | Confirmed by several fund-manager implementation documents, which agree with each other. The guideline's own text could not be opened, so the report cites it as the framework and the managers' documents as evidence of the matching table. |
| R-2 | The *Measures for the Suitability Management of Securities and Futures Investors* were issued as CSRC Order No. 130 on 12 December 2016, took effect on 1 July 2017, and were amended by CSRC Order No. 177 on 30 October 2020. | Search extracts from consolidated texts (fadada.com legal database; CICC Wealth Management copy: https://www.ciccwm.com/ib/pdf/zjqhtzzsdxglbf.pdf) | Confirmed (dates and order numbers). |
| R-3 | Article 6 of the Measures requires institutions to collect investors' investment-objective information, including investment horizon, product types and expected return. | Same as R-2 (extract of Article 6) | Confirmed from secondary extract; article text to be quoted only in paraphrase. |
| R-4 | Fund distributors must classify product risk into at least five levels, R1-R5, and may delegate rating to a third party. | Search extract summarising the AMAC guideline, as quoted in fund-company documents (R-1 sources) | Confirmed from secondary sources. |

## Fund data

See `data/fund_menu_verification.csv` for per-fund entries.

## Literature

See `docs/references_verification.md`.

## Pricing information (used only for budgeting, not in the report)

API prices for the budget estimate came from third-party summaries (CloudZero, Puter, Activepieces, MorphLLM, OpenRouter comparison pages) and from OpenAI's model pages. The official DeepSeek and Alibaba pricing pages could not be fetched. Actual spending is taken from the `usage` fields that the API returns and is stored in the raw logs.
