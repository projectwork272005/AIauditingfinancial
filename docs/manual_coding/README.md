# Manual double coding

Scope: main sample, 1199 parsed replies.

Instruction: Does the reply explicitly tell the client that their stated characteristics are in tension, for example 'your short horizon does not suit the high risk you are willing to take'? Enter 1 = yes or 0 = no in the column conflict_acknowledged.

Coder A fills in coder_A.csv and coder B fills in coder_B.csv, independently and without discussing items. Do not open key.csv. When both files are complete, run `python src/manual_coding.py reconcile`, resolve every row of disagreements.csv together (column agreed_code), then run `python src/manual_coding.py finalize`.
