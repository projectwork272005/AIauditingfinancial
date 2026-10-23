"""Single source of truth for the experimental design.

Every category definition used by the profile generator, the prompt builder,
the response coder and the analysis scripts is defined here, so that a change
to a definition propagates everywhere and is visible in one place.

All investor data produced from these definitions is SYNTHETIC.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Independent variable 1: investment horizon (5 categories)
# Horizon = time until the investor expects to start withdrawing the money.
# Bands are half-open intervals [lower, upper) in years, so they cannot overlap.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HorizonBand:
    code: str
    label: str
    lower_years: float
    upper_years: float | None  # None = open-ended
    definition: str
    # Values that a profile in this band may state (years). The generator picks
    # one of these; 0.25 = 3 months etc.
    stated_values: tuple
    probe_value: float  # value used in the single-attribute probe set


HORIZONS = (
    HorizonBand("H1", "Short-term", 0.0, 1.0,
                "Money expected to be withdrawn in less than 1 year.",
                (0.25, 0.5, 0.75), 0.5),
    HorizonBand("H2", "Short-to-medium term", 1.0, 3.0,
                "Withdrawal expected in 1 year to less than 3 years.",
                (1.5, 2.0, 2.5), 2.0),
    HorizonBand("H3", "Medium-term", 3.0, 5.0,
                "Withdrawal expected in 3 years to less than 5 years.",
                (3.0, 3.5, 4.0, 4.5), 4.0),
    HorizonBand("H4", "Medium-to-long term", 5.0, 10.0,
                "Withdrawal expected in 5 years to less than 10 years.",
                (5.0, 6.0, 7.0, 8.0, 9.0), 7.0),
    HorizonBand("H5", "Long-term", 10.0, None,
                "Withdrawal not expected for 10 years or more.",
                (10.0, 12.0, 15.0, 20.0, 25.0), 15.0),
)

# ---------------------------------------------------------------------------
# Independent variable 2: risk tolerance (5 categories)
# Each class is defined on the SAME three criteria: (a) maximum acceptable
# one-year decline in portfolio value, (b) investment priority, and
# (c) intended reaction to a 20% market fall. Codes C1-C5 follow the investor
# classification used in China's fund-distribution suitability rules
# (C1 = lowest risk tolerance, C5 = highest); the code itself is NOT shown to
# the model, only the descriptive text.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RiskClass:
    code: str
    level: int
    label: str
    max_one_year_loss: str
    priority: str
    reaction_to_20pct_fall: str
    max_product_risk: int  # highest product risk rating (R1-R5) permitted


RISK_CLASSES = (
    RiskClass("C1", 1, "Very conservative",
              "I am not willing to accept any loss of the money I invest",
              "protecting the capital I invest",
              "sell all of my investments", 1),
    RiskClass("C2", 2, "Conservative",
              "I can accept a temporary decline of up to about 5% in a year",
              "stability, with modest growth",
              "sell part of my investments", 2),
    RiskClass("C3", 3, "Moderate",
              "I can accept a temporary decline of up to about 15% in a year",
              "a balance between growth and stability",
              "hold my investments and wait for a recovery", 3),
    RiskClass("C4", 4, "Aggressive",
              "I can accept a temporary decline of up to about 25% in a year",
              "long-term growth",
              "hold my investments and possibly add a little more", 4),
    RiskClass("C5", 5, "Very aggressive",
              "I can accept a temporary decline of 40% or more in a year",
              "the highest possible long-term return",
              "invest substantially more", 5),
)

# ---------------------------------------------------------------------------
# Independent variable 3: age (8 categories), adult investors aged 18-85.
# Bands are inclusive integer ranges with no gaps and no overlaps.
# Bands follow life-cycle stages rather than equal widths: early adulthood,
# three career decades, a pre-retirement band, a retirement-transition band and
# two retirement bands.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgeBand:
    code: str
    label: str
    lower: int
    upper: int
    life_stage: str
    probe_age: int


AGE_BANDS = (
    AgeBand("A1", "18-24", 18, 24, "Early adulthood (study or first job)", 22),
    AgeBand("A2", "25-34", 25, 34, "Early career", 30),
    AgeBand("A3", "35-44", 35, 44, "Mid career", 40),
    AgeBand("A4", "45-54", 45, 54, "Late career", 50),
    AgeBand("A5", "55-59", 55, 59, "Pre-retirement", 57),
    AgeBand("A6", "60-64", 60, 64, "Retirement transition", 62),
    AgeBand("A7", "65-74", 65, 74, "Early retirement", 70),
    AgeBand("A8", "75-85", 75, 85, "Late retirement", 80),
)

# ---------------------------------------------------------------------------
# Experimental conditions (prompt variants). See src/prompts.py for wording.
# ---------------------------------------------------------------------------

CONDITIONS = {
    "BASE": "Baseline advisory prompt: adviser role + verified fund menu + output format.",
    "SUIT": "Suitability-protocol prompt: identical to BASE plus an explicit "
            "suitability procedure (classify the investor, cap product risk, "
            "match horizon and liquidity, disclose conflicts).",
}

# ---------------------------------------------------------------------------
# Normative benchmark used in the evaluation (researcher-defined; documented
# in research_design.md). Upper equity bounds by risk class and by horizon.
# The suitable maximum equity share for a profile = min(risk cap, horizon cap).
# ---------------------------------------------------------------------------

EQUITY_CAP_BY_RISK = {"C1": 0, "C2": 20, "C3": 50, "C4": 80, "C5": 100}

# Maximum acceptable one-year loss stated in each risk class's description
# (percent). Used by the historical check: a recommended portfolio whose worst
# rolling 12-month return in the back-test window is below -MAX_LOSS breaches
# the investor's own stated tolerance.
MAX_ONE_YEAR_LOSS_PCT = {"C1": 0, "C2": 5, "C3": 15, "C4": 25, "C5": 40}
EQUITY_CAP_BY_HORIZON = {"H1": 10, "H2": 30, "H3": 50, "H4": 80, "H5": 100}


def horizon_by_code(code: str) -> HorizonBand:
    return next(h for h in HORIZONS if h.code == code)


def risk_by_code(code: str) -> RiskClass:
    return next(r for r in RISK_CLASSES if r.code == code)


def age_by_code(code: str) -> AgeBand:
    return next(a for a in AGE_BANDS if a.code == code)


def age_band_for(age: int) -> AgeBand:
    for band in AGE_BANDS:
        if band.lower <= age <= band.upper:
            return band
    raise ValueError(f"age {age} outside the 18-85 study population")


def horizon_band_for(years: float) -> HorizonBand:
    for band in HORIZONS:
        if years >= band.lower_years and (band.upper_years is None or years < band.upper_years):
            return band
    raise ValueError(f"horizon {years} not covered")


def suitable_equity_cap(risk_code: str, horizon_code: str) -> int:
    return min(EQUITY_CAP_BY_RISK[risk_code], EQUITY_CAP_BY_HORIZON[horizon_code])


def format_horizon(years: float) -> str:
    if years < 1:
        months = round(years * 12)
        return f"about {months} months"
    if float(years).is_integer():
        n = int(years)
        return f"about {n} year" + ("s" if n != 1 else "")
    return f"about {years:g} years"
