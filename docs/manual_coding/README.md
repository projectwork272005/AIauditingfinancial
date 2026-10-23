# Double coding of the conflict item

Scope: all 1,199 parsed main-sample replies. Decision rules: INSTRUCTIONS.md.

- coder_A.csv, coder_B.csv: the two independent coding passes (blinded item ids, different random orders). Both passes were made by separate instances of an AI assistant (Claude); their raw chunk outputs, with notes on borderline cases, are in ai_coder_outputs/.
- disagreements.csv: the 26 items the passes disagreed on, with the adjudicated code (agreed_code) and the reason.
- key.csv: item id to call id.

Results: 97.8% agreement, Cohen's kappa 0.95; consensus vs keyword rule kappa 0.43 (outputs/tables/T31, T34).
To revise a code, edit agreed_code in disagreements.csv (or a coder file) and run `python src/manual_coding.py finalize`, then `python report/report_supplement.py`.
