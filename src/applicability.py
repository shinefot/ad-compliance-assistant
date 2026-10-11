"""
applicability.py — decides whether an AD applies to an aircraft.

IMPORTANT DESIGN CHOICE: this file uses NO artificial intelligence.
The AI already did its job (reading the PDF and filling in ADRecord).
Checking "is serial 30245 between 28001 and 33000?" is a job for plain code:
it's exact, fast, free, and the same answer every time. That makes it testable
(see tests/test_applicability.py).

When in doubt, every rule here leans toward APPLIES or CANNOT_DETERMINE, never
DOES_NOT_APPLY, because wrongly saying "doesn't apply" is the dangerous mistake.
"""
from .schema import ADRecord, Aircraft, ApplicabilityResult, Verdict

_PREFIXES = ("BOEING", "AIRBUS", "MODEL")


def normalize_model(model: str) -> str:
    """'Boeing Model 737-800 ' -> '737-800'"""
    m = model.upper().strip()
    for p in _PREFIXES:
        m = m.replace(p, "")
    return m.replace(" ", "")


def model_matches(ad_models: list[str], aircraft_model: str) -> bool:
    target = normalize_model(aircraft_model)
    for m in ad_models:
        n = normalize_model(m)
        # Exact match, or the AD names the whole family ("A320" covers "A320-214").
        # The family rule can only create extra APPLIES, which is the safe direction.
        if n == target or target.startswith(n + "-"):
            return True
    return False


def engine_matches(ad_engines: list[str], aircraft_engine: str) -> bool:
    if not ad_engines:  # empty list means "any engine"
        return True
    target = aircraft_engine.upper().replace(" ", "")
    # Prefix match: an AD for "CFM56-7B" covers "CFM56-7B26". Safe direction again.
    return any(target.startswith(e.upper().replace(" ", "")) for e in ad_engines)


def serial_matches(ad: ADRecord, msn: int) -> bool:
    if not ad.serial_ranges:  # empty list means "all serial numbers"
        return True
    return any(r.start <= msn <= r.end for r in ad.serial_ranges)


def check(ad: ADRecord, aircraft: Aircraft, superseded_by: dict[str, str] | None = None) -> ApplicabilityResult:
    """Return APPLIES / DOES_NOT_APPLY / CANNOT_DETERMINE with a human-readable reason."""
    superseded_by = superseded_by or {}

    def result(v: Verdict, reason: str) -> ApplicabilityResult:
        return ApplicabilityResult(ad_number=ad.ad_number, verdict=v, reason=reason)

    if ad.ad_number.upper().startswith("NPRM"):
        return result(Verdict.DOES_NOT_APPLY,
                      "This is a PROPOSED rule (NPRM), not an AD in force. It creates no legal requirement yet.")

    if not ad.applicable_models:
        return result(Verdict.CANNOT_DETERMINE, "No aircraft models were extracted from this AD; read it manually.")

    if not model_matches(ad.applicable_models, aircraft.model):
        return result(
            Verdict.DOES_NOT_APPLY,
            f"Model {aircraft.model} is not in the AD's list: {', '.join(ad.applicable_models)}.",
        )

    if ad.ad_number in superseded_by:
        return result(
            Verdict.DOES_NOT_APPLY,
            f"Superseded by AD {superseded_by[ad.ad_number]}; check that AD instead.",
        )

    if ad.applicability_by_reference:
        return result(
            Verdict.CANNOT_DETERMINE,
            f"Model matches, but affected aircraft are defined in '{ad.applicability_by_reference}', "
            "which this system cannot see.",
        )

    if not serial_matches(ad, aircraft.msn):
        ranges = ", ".join(f"{r.start}-{r.end}" for r in ad.serial_ranges)
        return result(Verdict.DOES_NOT_APPLY, f"MSN {aircraft.msn} is outside the AD's serial ranges ({ranges}).")

    if not engine_matches(ad.engine_models, aircraft.engine):
        return result(
            Verdict.DOES_NOT_APPLY,
            f"Engine {aircraft.engine} is not in the AD's list: {', '.join(ad.engine_models)}.",
        )

    return result(Verdict.APPLIES, "Model, serial number and engine all match the AD's applicability.")


def build_superseded_map(ads: list[ADRecord]) -> dict[str, str]:
    """{old_ad_number: new_ad_number} for every AD that another AD in our dataset supersedes."""
    out: dict[str, str] = {}
    for ad in ads:
        for old in ad.supersedes:
            out[old] = ad.ad_number
    return out


def check_all(ads: list[ADRecord], aircraft: Aircraft) -> list[ApplicabilityResult]:
    sup = build_superseded_map(ads)
    return [check(ad, aircraft, sup) for ad in ads]
