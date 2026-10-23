# Reference Verification Record

Every source cited in the report was checked before use. Checks were made on 2026-10-22 through a web-search service that returns bibliographic records and source URLs (publisher pages, RePEc/IDEAS, NBER, arXiv, ICLR, PubMed Central, university repositories). Direct page fetching was not available in the build environment, so full texts were **not** read for most items; the report therefore cites these works only for claims stated in their abstracts or bibliographic records, and says so where it matters.

Status codes: **V** = bibliographic details confirmed by at least one authoritative record; **V-abs** = confirmed, and the claim we cite appears in the abstract; **X** = could not be confirmed, not cited.

## Sources cited in the report

| Short cite | Status | Confirming record(s) | Notes |
|---|---|---|---|
| AMAC (2017) | V | China Securities Journal report, 28 Jun 2017 (https://cs.com.cn/tzjj/jjdt/201706/t20170629_5347795.html); Han Kun Law Offices note; copy hosted by aiBank | Guideline issued and effective 28 Jun 2017, document 中基协发〔2017〕4号. Matching table C1-C5 / R1-R5 confirmed through fund-manager implementation documents (see verification_log.md, R-1). |
| Atil et al. (2024) | V-abs | arXiv:2408.04667 (v1-v5) | Later versions retitled "Non-determinism of 'deterministic' LLM settings". Cited for: outputs vary across identical runs even at temperature 0. |
| Barbieri, Vargas & Ferraz (2026) | V-abs | arXiv:2606.27570 | Cited for: recommendations audited as executable actions; validity, repeat-run stability. |
| Bertrand & Mullainathan (2004) | V | AER 94(4), 991-1013; NBER WP 9873 | Cited for: audit/correspondence method. |
| Bodie, Merton & Samuelson (1992) | V | NBER WP 3954/3043 listing | Pages 427-450 (NBER listing); a query variant with 449 was not confirmed. |
| Capponi, Ólafsson & Zariphopoulou (2022) | V-abs | IDEAS: Management Science 68(4), 2485-2512; DOI 10.1287/mnsc.2021.4014 | |
| Choukhmane, de Silva, Lin & Akuzawa (2026) | V-abs | NBER WP 35574; arXiv:2608.01607; MIT Sloan WP 7377-26 | Replaces the reference report's "Choukhmane (2025)" and "Choukhmane et al. (2026)" entries, whose details did not match any record. |
| Cocco, Gomes & Maenhout (2005) | V-abs | IDEAS: RFS 18(2), 491-533; DOI 10.1093/rfs/hhi017 | Cited for: optimal equity share broadly declines with age when labour income is bond-like. |
| Cohen (1988) | V | Standard reference text (2nd ed., Lawrence Erlbaum) | Effect-size conventions. |
| CSRC (2016/2020) | V | Consolidated text extracts (fadada.com; CICC Wealth Management copy) | Order No. 130 (12 Dec 2016, effective 1 Jul 2017), amended by Order No. 177 (30 Oct 2020). |
| D'Acunto, Prabhala & Rossi (2019) | V-abs | IDEAS: RFS 32(5), 1983-2020; DOI 10.1093/rfs/hhz014 | |
| Fieberg, Hornuf, Meiler & Streich (2025) | V-abs | IDEAS: CESifo WP 11666; TU Dresden repository | 32 LLMs x 64 profiles. |
| Foerster, Linnainmaa, Melzer & Previtero (2017) | V-abs | NBER WP 20712; JF 72(4), 1441-1482 | Cited for: advisor fixed effects explain more portfolio variation than client traits ("one size fits all"). |
| Foltyn & Olsson (2026) | V-abs | Swopec NHH DP 4/2026; CEPR DP21323 | 33 LLMs, five vendors; female framing -> ~1.8 pp less equity. Replaces the unverifiable "Li et al. (2026)". |
| Gennaioli, Shleifer & Vishny (2015) | V | JF 70(1), 91-114 (RePEc; author bibliographies) | |
| Grable & Lytton (1999) | V-abs | Financial Services Review 8, 163-181 (UGA open journals) | Risk-tolerance measurement. |
| Holm (1979) | V | Standard reference (Scand. J. Statistics 6(2), 65-70) | Multiple-comparison correction. |
| Ji et al. (2023) | V | ACM Computing Surveys 55(12), Article 248 (DBLP/BibSonomy; arXiv:2202.03629 v5 author list) | |
| Koo & Li (2016) | V | J. Chiropractic Medicine 15(2), 155-163; DOI 10.1016/j.jcm.2016.02.012; PMC4913118 | ICC selection and interpretation. |
| Lo & Ross (2024) | V-abs | Harvard Data Science Review, published 6 Aug 2024 (hdsr.mitpress.mit.edu/pub/jnml28pl) | |
| Mullainathan, Noeth & Schoar (2012) | V-abs | NBER WP 17929 | |
| Niszczota & Abbas (2023) | V | Finance Research Letters 58, 104333; DOI 10.1016/j.frl.2023.104333 | |
| Oehler & Horn (2024) | V | Finance Research Letters 60, 104898; DOI 10.1016/j.frl.2023.104898 | Findings known only from a secondary summary; cited for its existence and question, not for numbers. |
| Ross & Lo (2026) | V-abs | ICLR 2026 workshop listing (https://iclr.cc/virtual/2026/10016482) | Spotlight, 2nd Workshop on Advances in Financial AI, 27 Apr 2026; GPT-4o, 1,000 synthetic profiles; "decision tree" heuristics. |
| Sclar, Choi, Tsvetkov & Suhr (2024) | V-abs | ICLR 2024 poster; arXiv:2310.11324 | Prompt-format sensitivity. |
| Sharma et al. (2024) | V-abs | ICLR 2024 proceedings; arXiv:2310.13548 (19 authors) | Sycophancy in RLHF-trained assistants. |

## Sources from the reference report that were NOT confirmed and are not cited

| Entry in reference report | Outcome |
|---|---|
| Wang, X., & Gu, B. (2026). "Who invests, who gets funded? A two-sided audit of GPT-4 Turbo financial advice against CRSP fund data." *Journal of Business Ethics*. | No record found under this title, authors or journal. Not cited. |
| Li, Y., et al. (2026). "Stereotypes in the machine: Gender and racial bias in LLM-generated financial advice." | No record found. Not cited; Foltyn & Olsson (2026) is cited for the verified gender-bias evidence instead. |
| Ross, J., & Lo, A. W. (2026). arXiv:2604.23837 | The arXiv paper "One size fits none: Heuristic collapse in LLM investment advice" exists (posted 26 Apr 2026), but its author list could not be confirmed. The ICLR workshop version by Ross & Lo, which could be confirmed, is cited instead. |
| Choukhmane, T. (2025). "How good is generative AI personal financial advice?" | No record under this title; the verified Choukhmane et al. (2026) NBER paper is cited instead. |
