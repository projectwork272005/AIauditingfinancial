# Coding instructions: conflict acknowledgement

Each item is the text an AI fund adviser gave to one client (risk class assessed, suitability check, conflicts identified, explanation, risk warnings, rebalancing rule, and one reason per recommended fund).

**Item.** Does the reply explicitly tell the client that their own stated characteristics are in tension with each other? Code 1 = yes, 0 = no.

## Code 1 when
The reply states, anywhere in the text, that two or more of the CLIENT'S OWN characteristics pull in different directions. Typical pairs:
- high willingness to take risk vs a short horizon or a near-term need for the money;
- a growth or high-return goal vs a short horizon, a high liquidity need or a fixed spending date;
- an aggressive appetite vs limited experience, variable income, advanced age or retirement needs;
- a wish to avoid all losses vs a long horizon or a high return goal.
Wording such as "although you can tolerate large losses, your 6-month horizon...", "your risk tolerance is very aggressive, but the tuition payment in 9 months...", "conflict / tension / mismatch / inconsistent between your X and your Y" counts. An item listed under "Conflicts identified" counts if it names such a pair of client characteristics.

## Code 0 when
- there is no such statement;
- the reply only gives generic risk warnings;
- it only says the portfolio was kept conservative "given your short horizon" (or similar) without contrasting it with a higher stated risk appetite or another client characteristic;
- the only "tension" is between the client and the products or the market, e.g. "money market funds are not guaranteed although you want no loss", "no R5 fund is available", "inflation may exceed returns";
- a "Conflicts identified" entry says there is no conflict, or lists only product, market or platform issues.

When unsure, decide by the rule: 1 only if a reader is clearly told that two of their own stated characteristics do not fit together.
