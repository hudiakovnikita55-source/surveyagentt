from collections import Counter

import pytest

from surveyagent.personas import generate_personas, load_personas, persona_card, save_personas
from surveyagent.personas import geo


@pytest.fixture(scope="module")
def personas():
    return generate_personas(100, seed=42)


def test_count_and_uniqueness(personas):
    assert len(personas) == 100
    assert len({p.id for p in personas}) == 100
    assert len({p.full_name for p in personas}) == 100
    assert len({p.email for p in personas}) == 100
    assert all(p.email.endswith("@example.com") for p in personas)


def test_deterministic():
    a = [p.to_dict() for p in generate_personas(20, seed=7)]
    b = [p.to_dict() for p in generate_personas(20, seed=7)]
    c = [p.to_dict() for p in generate_personas(20, seed=8)]
    assert a == b
    assert a != c


def test_everyone_is_in_europe_and_diverse(personas):
    europe = {c["name"] for c in geo.COUNTRIES.values()}
    assert all(p.country in europe for p in personas)
    assert len({p.country for p in personas}) >= 25
    assert len({p.occupation for p in personas}) >= 30
    genders = Counter(p.gender for p in personas)
    assert genders["female"] >= 35 and genders["male"] >= 35
    assert len({p.ai["attitude"] for p in personas}) == 4
    assert any(not p.background.split(", ")[1].startswith("grew up") for p in personas)  # some migrants


def test_profiles_are_internally_consistent(personas):
    for p in personas:
        assert 22 <= p.age <= 64
        assert int(p.birth_date[:4]) in (2026 - p.age, 2026 - p.age - 1)
        assert 0 <= p.years_experience <= p.age - 16
        assert p.income_eur > 0
        assert p.ai["tools"] and p.ai["primary_tool"] == p.ai["tools"][0]
        assert p.ai["use_cases"]
        assert 1 <= p.ai["satisfaction_1_10"] <= 10
        if p.employment_type == "employee":
            assert p.ai["employer_policy"]
        else:
            assert p.ai["employer_policy"] is None
        if p.employment_type == "freelancer":
            assert p.company_size == "1 (just me)"
        if p.seniority == "head":
            assert p.age >= 32
        langs = [x.split(" (")[0] for x in p.other_languages]
        assert len(langs) == len(set(langs)) and not set(langs) & set(p.native_languages)
        assert (p.english_level == "native") == ("English" in p.native_languages)


def test_gendered_surnames():
    people = generate_personas(400, seed=3)
    polish_women = [p for p in people if p.gender == "female" and p.nationality == "Polish"]
    czech_women = [p for p in people if p.gender == "female" and p.nationality == "Czech"]
    assert polish_women and czech_women
    assert not any(p.last_name.endswith(("ski", "cki")) for p in polish_women)
    assert all(p.last_name.endswith(("ová", "á")) for p in czech_women)
    assert not any(p.last_name.endswith(("ová", "á")) for p in people if p.gender == "male" and p.nationality == "Czech")


def test_roundtrip_and_card(tmp_path, personas):
    path = tmp_path / "personas.json"
    save_personas(personas[:5], path)
    loaded = load_personas(path)
    assert [p.to_dict() for p in loaded] == [p.to_dict() for p in personas[:5]]
    card = persona_card(loaded[0])
    assert loaded[0].full_name in card and "How this person fills in surveys" in card


def test_committed_personas_match_generator():
    """data/personas.json is the output of `python -m surveyagent personas` with default settings."""
    committed = load_personas("data/personas.json")
    assert [p.to_dict() for p in committed] == [p.to_dict() for p in generate_personas(100, seed=42)]
