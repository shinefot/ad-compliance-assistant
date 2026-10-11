"""
Unit tests: small, fast checks that the rules behave exactly as designed.
Run with:  pytest
"""
from src.applicability import check, check_all
from src.graph import check_citations_exist
from src.schema import ADRecord, Aircraft, SerialRange, Verdict


def make_ad(**overrides) -> ADRecord:
    base = dict(ad_number="2025-01-01", issuing_authority="FAA", applicable_models=["737-800"],
                compliance_time="within 6,000 flight cycles", required_action="Inspect.",
                source_pages=[1], source_file="faa/test.pdf")
    base.update(overrides)
    return ADRecord(**base)


PLANE = Aircraft(id="DEMO-001", model="737-800", msn=30245, engine="CFM56-7B26")


def test_simple_match_applies():
    assert check(make_ad(), PLANE).verdict == Verdict.APPLIES


def test_wrong_model_does_not_apply():
    assert check(make_ad(applicable_models=["A320-214"]), PLANE).verdict == Verdict.DOES_NOT_APPLY


def test_model_name_formatting_is_ignored():
    assert check(make_ad(applicable_models=["Boeing Model 737-800"]), PLANE).verdict == Verdict.APPLIES


def test_serial_exactly_on_lower_boundary_applies():
    ad = make_ad(serial_ranges=[SerialRange(start=30245, end=33000)])
    assert check(ad, PLANE).verdict == Verdict.APPLIES


def test_serial_exactly_on_upper_boundary_applies():
    ad = make_ad(serial_ranges=[SerialRange(start=28001, end=30245)])
    assert check(ad, PLANE).verdict == Verdict.APPLIES


def test_serial_one_outside_range_does_not_apply():
    ad = make_ad(serial_ranges=[SerialRange(start=30246, end=33000)])
    assert check(ad, PLANE).verdict == Verdict.DOES_NOT_APPLY


def test_engine_prefix_matches():
    assert check(make_ad(engine_models=["CFM56-7B"]), PLANE).verdict == Verdict.APPLIES


def test_wrong_engine_does_not_apply():
    assert check(make_ad(engine_models=["LEAP-1B"]), PLANE).verdict == Verdict.DOES_NOT_APPLY


def test_applicability_by_reference_cannot_determine():
    ad = make_ad(applicability_by_reference="Boeing Alert Service Bulletin 737-53A1234")
    assert check(ad, PLANE).verdict == Verdict.CANNOT_DETERMINE


def test_no_models_extracted_cannot_determine():
    assert check(make_ad(applicable_models=[]), PLANE).verdict == Verdict.CANNOT_DETERMINE


def test_superseded_ad_flagged():
    old = make_ad(ad_number="2020-05-05")
    new = make_ad(ad_number="2025-02-02", supersedes=["2020-05-05"])
    verdicts = {r.ad_number: r for r in check_all([old, new], PLANE)}
    assert verdicts["2020-05-05"].verdict == Verdict.DOES_NOT_APPLY
    assert "Superseded" in verdicts["2020-05-05"].reason
    assert verdicts["2025-02-02"].verdict == Verdict.APPLIES


def test_family_name_applies():
    a320 = Aircraft(id="DEMO-003", model="A320-214", msn=5678, engine="CFM56-5B4")
    assert check(make_ad(issuing_authority="EASA", applicable_models=["A320"]), a320).verdict == Verdict.APPLIES


def test_proposed_rule_does_not_apply():
    assert check(make_ad(ad_number="NPRM-FAA-2024-2315"), PLANE).verdict == Verdict.DOES_NOT_APPLY


def test_citation_checker_catches_invented_page():
    evidence = {"2025-01-01": [{"ad_number": "2025-01-01", "page": 3, "text": "..."}]}
    good = "Inspect the bracket [AD 2025-01-01 p.3]."
    bad = "Inspect the bracket [AD 2025-01-01 p.9]."
    assert check_citations_exist(good, evidence) == []
    assert len(check_citations_exist(bad, evidence)) == 1


def test_citation_checker_catches_no_citations():
    evidence = {"2025-01-01": [{"ad_number": "2025-01-01", "page": 3, "text": "..."}]}
    assert check_citations_exist("Inspect the bracket.", evidence)
