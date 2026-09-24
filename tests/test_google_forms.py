import json

import pytest

from surveyagent.google_forms import FormError, build_payload, check_structure, parse_form_html, response_url, submit_response
from surveyagent.questionnaire import normalize_answer

VIEW_URL = "https://docs.google.com/forms/d/e/1FAIpQLSexample/viewform"


def opt(label, other=0):
    return [label, None, None, None, other]


def form_html(collect_email=3):
    items = [
        [111, "What is your name?", None, 0, [[1001, None, 1]]],
        [112, "Favourite colour", "Pick one", 2, [[1002, [opt("Red"), opt("Blue"), opt("", 1)], 1]]],
        [113, "Which tools do you use?", None, 4, [[1003, [opt("ChatGPT"), opt("Claude"), opt("", 1)], 0]]],
        [114, "About your work", "Second page", 8],
        [115, "How satisfied are you?", None, 5, [[1005, [["1"], ["2"], ["3"], ["4"], ["5"]], 1, ["Bad", "Great"]]]],
        [116, "Do you agree?", None, 7, [
            [1006, [["No"], ["Maybe"], ["Yes"]], 1, ["AI helps me"], None, None, None, None, None, None, None, [0]],
            [1007, [["No"], ["Maybe"], ["Yes"]], 1, ["AI worries me"], None, None, None, None, None, None, None, [0]]]],
        [117, "Date of birth", None, 9, [[1008, None, 0, None, None, None, None, [0, 1]]]],
        [118, "When do you start work?", None, 10, [[1009, None, 0, None, None, None, [0]]]],
        [119, "Country", None, 3, [[1010, [["France"], ["Germany"]], 0]]],
        [120, "Just some text", "Info block", 6],
        [121, "Comments", None, 1, [[1011, None, 0]]],
    ]
    settings = [None, None, None, None, None, None, collect_email]
    data = [None, ["Form description", items, None, None, None, None, None, None, "Test form", None, settings],
            "/forms", "Test doc"]
    return (f"<html><script>var FB_PUBLIC_LOAD_DATA_ = {json.dumps(data)};</script>"
            f'<input type="hidden" name="fbzx" value="-123456789"></html>')


@pytest.fixture
def form():
    return parse_form_html(form_html(), VIEW_URL)


def test_parse_structure(form):
    assert form.title == "Test form"
    assert form.description == "Form description"
    types = [(q.id, q.type) for q in form.questions]
    assert types == [("email", "email"), ("q1", "short_text"), ("q2", "single_choice"), ("q3", "checkboxes"),
                     ("q4", "scale"), ("q5", "grid"), ("q6", "date"), ("q7", "time"), ("q8", "dropdown"),
                     ("q9", "paragraph")]
    q2 = form.question("q2")
    assert q2.options == ["Red", "Blue"] and q2.has_other and q2.required and q2.description == "Pick one"
    assert form.question("q3").has_other and not form.question("q3").required
    q4 = form.question("q4")
    assert (q4.scale_min, q4.scale_max, q4.scale_labels) == (1, 5, ["Bad", "Great"])
    assert q4.page == 1 and q4.section == "About your work"
    q5 = form.question("q5")
    assert q5.rows == ["AI helps me", "AI worries me"] and q5.entry_ids == ["1006", "1007"]
    assert form.question("q6").date_has_year and not form.question("q6").date_has_time
    assert form.question("q9").description == "Just some text\nInfo block"
    assert form.google == {"view_url": VIEW_URL, "form_response_url": VIEW_URL.replace("viewform", "formResponse"),
                           "fbzx": "-123456789", "page_count": 1, "collects_email": True}


def test_no_email_question_when_not_collected():
    form = parse_form_html(form_html(collect_email=1), VIEW_URL)
    assert "email" not in [q.id for q in form.questions]


def test_private_form_is_rejected():
    with pytest.raises(FormError):
        parse_form_html("<html>Sign in to continue</html>", VIEW_URL)


def test_response_url():
    assert response_url(VIEW_URL + "/") == "https://docs.google.com/forms/d/e/1FAIpQLSexample/formResponse"


ANSWERS = {
    "email": "anna.meyer@example.com", "q1": "Anna", "q2": {"other": "Green"},
    "q3": ["ChatGPT", {"other": "DeepL"}], "q4": 4, "q5": {"AI helps me": "Yes", "AI worries me": "Maybe"},
    "q6": "1990-05-07", "q7": "09:30", "q8": "Germany", "q9": None,
}


def test_payload(form):
    for q in form.questions:  # the sample answers are valid for the form
        normalize_answer(q, ANSWERS[q.id])
    pairs = build_payload(form, ANSWERS)
    assert ("emailAddress", "anna.meyer@example.com") in pairs
    assert ("entry.1001", "Anna") in pairs
    assert ("entry.1002", "__other_option__") in pairs and ("entry.1002.other_option_response", "Green") in pairs
    assert [v for k, v in pairs if k == "entry.1003"] == ["ChatGPT", "__other_option__"]
    assert ("entry.1003.other_option_response", "DeepL") in pairs
    assert ("entry.1005", "4") in pairs
    assert ("entry.1006", "Yes") in pairs and ("entry.1007", "Maybe") in pairs
    assert {("entry.1008_year", "1990"), ("entry.1008_month", "5"), ("entry.1008_day", "7")} <= set(pairs)
    assert {("entry.1009_hour", "09"), ("entry.1009_minute", "30")} <= set(pairs)
    assert not any(k == "entry.1011" for k, _ in pairs)  # unanswered optional question
    assert ("pageHistory", "0,1") in pairs and ("fbzx", "-123456789") in pairs


def test_submit_uses_form_response_url(form):
    calls = {}

    class FakeSession:
        def post(self, url, data, headers, timeout):
            calls.update(url=url, data=data, headers=headers)
            return type("Resp", (), {"status_code": 200})()

    assert submit_response(form, ANSWERS, session=FakeSession()) == 200
    assert calls["url"].endswith("/formResponse")
    assert calls["headers"]["User-Agent"].startswith("surveyagent")


def test_check_structure_detects_changes(form):
    changed = parse_form_html(form_html().replace('"Blue"', '"Green"'), VIEW_URL)
    assert check_structure(form, form) == []
    assert any("Favourite colour" in p for p in check_structure(form, changed))
