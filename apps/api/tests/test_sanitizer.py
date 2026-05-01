import pytest
from app.util.sanitizer import check, assert_clean


def test_clean_passes():
    r = check("Counter unattended for 8 minutes during business hours.")
    assert r.ok
    assert r.violations == []


@pytest.mark.parametrize(
    "bad",
    [
        "Customer stole the product.",
        "Employee was caught taking cash.",
        "He admitted to the theft.",
        "Customer and employee got into an argument.",
        "Audio captured a conversation about price.",
        "Confessed during the shift.",
        "Witnesses said the door was open.",
    ],
)
def test_banned_terms_blocked(bad: str):
    r = check(bad)
    assert not r.ok, f"sanitizer should have flagged: {bad}"


def test_demographic_adjective_with_person_blocked():
    r = check("A young man entered the counter.")
    assert not r.ok
    assert any(v.startswith("demographic:") for v in r.violations)


def test_assert_clean_raises():
    with pytest.raises(ValueError):
        assert_clean("Customer stole product.")


def test_assert_clean_passes_neutral_copy():
    assert_clean("Possible product-loss exit flagged for review at 17:14.")
