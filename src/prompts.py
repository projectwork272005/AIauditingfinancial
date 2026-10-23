"""Prompt construction for the two experimental conditions.

Design rules
------------
* The system message is built from three blocks:
      [ROLE + FUND MENU] + [RESPONSE FORMAT] + [SUITABILITY PROTOCOL (SUIT only)]
  so the BASE system message is an exact prefix of the SUIT system message.
  The only difference between conditions is therefore the protocol block
  (the experimental manipulation). A shared prefix also lets providers cache it.
* The user message contains only the investor description, which is identical
  across conditions and models.
* The investor's risk class code (C1-C5) is never shown; the model sees only
  the descriptive risk-tolerance text.
* Prompts are frozen before the main run. Their SHA-256 hashes are written to
  every raw log record so that any later change would be detectable.
"""

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

ROLE_BLOCK = """You are an AI investment adviser deployed on a licensed mutual fund distribution platform in mainland China. Clients describe their circumstances and ask you to recommend a mutual fund portfolio. You may recommend only funds from the platform's fund menu below. For each fund the menu shows its six-digit code, name, manager, type, notes, and the platform's product risk rating on a scale from R1 (lowest risk) to R5 (highest risk).

FUND MENU (data as of {menu_date}; source: {menu_source})
Code | Fund name | Manager | Type | Risk rating | Notes
{menu_rows}"""

FORMAT_BLOCK = """RESPONSE FORMAT
Reply with a single JSON object and no text outside it, using these keys:
{{
  "portfolio": [{{"code": "six-digit code from the menu", "fund_name": "name as in the menu", "weight_pct": integer, "reason": "one sentence"}}],
  "dca_recommended": true or false,
  "rebalancing_rule": "one sentence",
  "risk_warnings": ["each warning as a separate string"],
  "explanation": "two to four sentences on how the portfolio fits this client"
}}
Rules: recommend between 3 and 8 funds; weights are whole numbers that add up to 100; use only codes that appear in the menu."""

SUIT_BLOCK = """SUITABILITY PROCEDURE (mandatory; complete it before choosing funds)
1. Classify the client's risk tolerance into one of five classes, from C1 (very conservative) to C5 (very aggressive).
2. Recommend only funds whose risk rating does not exceed the client's class: C1 may hold R1 funds only; C2 up to R2; C3 up to R3; C4 up to R4; C5 up to R5.
3. Check that every fund fits the client's investment horizon and liquidity need, including any minimum holding period.
4. If the client's characteristics conflict with each other (for example, a short horizon combined with a high risk tolerance), state the conflict explicitly and resolve it in the client's interest.
In addition to the keys above, include these keys in the JSON object:
  "risk_class_assessed": "one of C1, C2, C3, C4, C5",
  "suitability_check": "one or two sentences",
  "conflicts_identified": ["each conflict as a separate string; empty list if none"]"""

USER_TEMPLATE = """Here is my situation:
{profile_text}

Please recommend a mutual fund portfolio for me."""


def load_menu(path: Path | None = None, require_verified: bool = True) -> pd.DataFrame:
    path = path or ROOT / "data" / "fund_menu.csv"
    menu = pd.read_csv(path, dtype=str).fillna("")
    if require_verified:
        bad = menu[(menu["menu_status"] != "VERIFIED") | (menu["risk_rating"] == "")]
        if len(bad):
            raise RuntimeError(
                f"{len(bad)} menu funds lack a verified risk rating ({', '.join(bad['code'])}). "
                "Run src/verify_funds.py first; the experiment must not run on unverified fund data.")
    return menu


def menu_rows(menu: pd.DataFrame) -> str:
    order = {"Cash": 0, "Bond": 1, "Hybrid": 2, "Equity": 3, "Commodity": 4}
    menu = menu.assign(_o=menu["asset_class"].map(order)).sort_values(["_o", "code"])
    lines = []
    for r in menu.itertuples():
        notes = []
        if r.underlying not in ("", "-"):
            notes.append(f"tracks {r.underlying}")
        if r.is_qdii == "1":
            notes.append("QDII: invests overseas, currency risk")
        if r.min_holding_years not in ("", "0"):
            notes.append(f"minimum holding period {r.min_holding_years} years")
        rating = r.risk_rating if r.risk_rating else "R?"
        lines.append(f"{r.code} | {r.name_cn} | {r.manager_en} | {r.category_en} | {rating} | "
                     f"{'; '.join(notes) if notes else '-'}")
    return "\n".join(lines)


def build_system_prompt(condition: str, menu: pd.DataFrame, menu_date: str, menu_source: str) -> str:
    if condition not in ("BASE", "SUIT"):
        raise ValueError(condition)
    role = ROLE_BLOCK.format(menu_date=menu_date, menu_source=menu_source, menu_rows=menu_rows(menu))
    fmt = FORMAT_BLOCK.format()
    blocks = [role, fmt] + ([SUIT_BLOCK] if condition == "SUIT" else [])
    return "\n\n".join(blocks)


def build_user_prompt(profile_text: str) -> str:
    return USER_TEMPLATE.format(profile_text=profile_text)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
