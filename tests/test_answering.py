import csv
import json
import random
from types import SimpleNamespace

import pytest

from surveyagent.answering.heuristic import HeuristicAnswerer
from surveyagent.answering.humanize import humanize
from surveyagent.answering.llm import FALLBACK_BETA, OTHER, LLMAnswerer, build_schema, parse_output
from surveyagent.answering.runner import generate_responses, load_records
from surveyagent.personas import generate_personas
from surveyagent.questionnaire import load_questionnaire, normalize_answer

EXAMPLE = "examples/ai_at_work_survey.yaml"
AGE_BRACKETS = {"18-24": (18, 24), "25-34": (25, 34), "35-44": (35, 44), "45-54": (45, 54), "55-64": (55, 64),
                "65 or older": (65, 120)}


@pytest.fixture(scope="module")
def survey():
    return load_questionnaire(EXAMPLE)


@pytest.fixture(scope="module")
def personas():
    return generate_personas(100, seed=42)


# --------------------------------------------------------------------------- questionnaire

def test_load_example(survey):
    assert len(survey.questions) == 15
    assert survey.question("statements").type == "grid"
    assert survey.question("recommend").scale_values == list(range(0, 11))
    assert survey.question("country").has_other


def test_normalize(survey):
    country = survey.question("country")
    assert normalize_answer(country, "germany") == "Germany"
    assert normalize_answer(country, "Liechtenstein") == {"other": "Liechtenstein"}
    with pytest.raises(ValueError):
        normalize_answer(survey.question("age"), "33")
    with pytest.raises(ValueError):
        normalize_answer(survey.question("satisfaction"), 6)
    with pytest.raises(ValueError):
        normalize_answer(survey.question("tasks"), "")  # required
    assert normalize_answer(survey.question("concern"), "") is None
    grid = survey.question("statements")
    with pytest.raises(ValueError):  # required grid must have every row
        normalize_answer(grid, {"AI makes me more productive": "Agree"})


# --------------------------------------------------------------------------- offline answers

def test_offline_answers_are_valid_and_consistent(survey, personas):
    answerer = HeuristicAnswerer(survey)
    for p in personas:
        answers = answerer.answer(p)
        for q in survey.questions:
            normalize_answer(q, answers[q.id])  # raises if invalid
        lo, hi = AGE_BRACKETS[answers["age"]]
        assert lo <= p.age <= hi
        assert answers["country"] in (p.country, {"other": p.country})
        if p.gender in ("female", "male"):
            assert answers["gender"].lower() == p.gender
        assert answers["company_size"] == {
            "1 (just me)": "Just me", "2–10": "2-10", "11–50": "11-50", "51–250": "51-250",
            "251–1,000": "251-1,000"}.get(p.company_size, "More than 1,000")


def test_humanize_is_deterministic_and_gentle():
    style = {"typos": "medium", "casing": "mostly lowercase", "ends_with_full_stop": False}
    text = "Mostly I use it for summarising documents and drafting emails for different customers every week."
    a = humanize(text, style, random.Random(1))
    assert a == humanize(text, style, random.Random(1))
    assert not a.endswith(".") and a[0].islower()
    assert humanize("Senior Engineer", style, random.Random(1)) == "senior engineer"
    assert humanize("anna@example.com", style, random.Random(1)) == "anna@example.com"


# --------------------------------------------------------------------------- LLM mode (mocked client)

def test_schema_is_strict(survey):
    schema = build_schema(survey)

    def check(node):
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])
            for child in node["properties"].values():
                check(child)
        if node.get("type") == "array":
            check(node["items"])

    check(schema)
    assert schema["properties"]["tools"]["items"]["enum"][-1] == OTHER
    assert "tools__other" in schema["properties"]
    assert set(schema["properties"]["statements"]["required"]) == {"r1", "r2", "r3", "r4"}
    assert set(schema["properties"]["skipped"]["items"]["enum"]) == {"policy", "concern", "comments"}


def fake_model_output(survey, persona):
    """What a well-behaved model would return, built from the offline answers."""
    answers = HeuristicAnswerer(survey).answer(persona)
    out = {"skipped": ["comments"]}
    for q in survey.questions:
        value = answers[q.id]
        if q.type == "grid":
            value = {f"r{i}": value[row] for i, row in enumerate(q.rows, 1)}
        elif isinstance(value, list):
            value = [OTHER if isinstance(v, dict) else v for v in value]
        elif isinstance(value, dict):
            value = OTHER
        out[q.id] = value if value is not None else ""
        if q.has_other:
            out[f"{q.id}__other"] = "Notion AI" if q.id == "tools" else ""
    out["concern"] = "Honestly the made-up sources, I check everything twice."
    return out


class FakeClient:
    def __init__(self, survey, personas):
        self.survey = survey
        self.by_name = {p.full_name: p for p in personas}
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **params):
        self.calls.append(params)
        user = params["messages"][0]["content"]
        name = user.rsplit("as ", 1)[1].rstrip(".")
        data = fake_model_output(self.survey, self.by_name[name])
        return SimpleNamespace(
            stop_reason="end_turn", model=params["model"],
            content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=json.dumps(data))],
            usage=SimpleNamespace(input_tokens=900, output_tokens=400, cache_read_input_tokens=2000,
                                  cache_creation_input_tokens=0),
        )


def test_llm_request_and_parsing(survey, personas):
    client = FakeClient(survey, personas)
    answerer = LLMAnswerer(survey, client=client)
    raw, usage = answerer.answer(personas[0])
    params = client.calls[0]
    assert params["model"] == "claude-opus-5"
    assert params["betas"] == [FALLBACK_BETA] and params["fallbacks"] == "default"
    assert params["thinking"] == {"type": "adaptive"}
    assert params["output_config"]["format"]["type"] == "json_schema"
    assert params["system"][-1]["cache_control"] == {"type": "ephemeral"}
    assert personas[0].full_name in params["messages"][0]["content"]
    assert raw["comments"] is None  # listed in "skipped"
    assert {"other": "Notion AI"} in raw["tools"] or "Notion AI" not in json.dumps(raw)
    assert set(raw["statements"]) == set(survey.question("statements").rows)
    assert usage["output_tokens"] == 400


def test_parse_output_handles_other_and_empty(survey):
    data = {"country": OTHER, "country__other": "Liechtenstein", "concern": "  ", "policy": "Yes",
            "skipped": ["policy"]}
    raw = parse_output(survey, data)
    assert raw["country"] == {"other": "Liechtenstein"}
    assert raw["concern"] is None and raw["policy"] is None


def test_runner_llm_mode_with_resume(tmp_path, survey, personas):
    out = tmp_path / "responses.json"
    subset = personas[:6]
    client = FakeClient(survey, personas)
    generate_responses(survey, subset[:3], out, mode="llm", client=client, workers=2, log=lambda *_: None)
    assert len(load_records(out)) == 3
    records = generate_responses(survey, subset, out, mode="llm", client=client, workers=2, resume=True,
                                 log=lambda *_: None)
    assert [r["persona_id"] for r in records] == [p.id for p in subset]
    assert len(client.calls) == 6  # the first three were not asked again
    for r in records:
        for q in survey.questions:
            normalize_answer(q, r["answers"][q.id])
    with open(out.with_suffix(".csv"), encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 7 and "How much do you agree with the following statements? [AI makes me more productive]" in rows[0]


def test_invalid_llm_answer_falls_back(tmp_path, survey, personas):
    class BadClient(FakeClient):
        def _create(self, **params):
            response = super()._create(**params)
            data = json.loads(response.content[1].text)
            data["tasks"] = ""  # required question left empty
            response.content[1].text = json.dumps(data)
            return response

    out = tmp_path / "r.json"
    records = generate_responses(survey, personas[:1], out, mode="llm", client=BadClient(survey, personas),
                                 log=lambda *_: None)
    assert records[0]["answers"]["tasks"]
    assert any(w.startswith("tasks:") for w in records[0]["warnings"])
