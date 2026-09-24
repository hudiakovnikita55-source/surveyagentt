"""Read a public Google Form and turn answers into a form submission.

Google Forms embeds the whole form definition in the page as
`var FB_PUBLIC_LOAD_DATA_ = [...]`. The layout (reverse-engineered, not an
official API) is roughly:

    data[1][0]   form description
    data[1][1]   list of items: [item_id, title, description, type, entries, ...]
                 entries: [[entry_id, options, required, labels/row, ..., flags], ...]
                 option:  [label, null, null, null, is_other]
    data[1][8]   form title
    data[1][10]  settings; [6] > 1 means the form collects e-mail addresses
    data[3]      document name

Only forms that are open without signing in are supported: forms restricted to
an organisation, with "limit to 1 response" or verified e-mail collection
require a Google login and are rejected on purpose.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .questionnaire import CHOICE_TYPES, GRID_TYPES, SCALE_TYPES, TEXT_TYPES, Question, Questionnaire

USER_AGENT = "surveyagent/0.1 (synthetic survey test responses)"

ITEM_TYPES = {
    0: "short_text", 1: "paragraph", 2: "single_choice", 3: "dropdown", 4: "checkboxes",
    5: "scale", 7: "grid", 9: "date", 10: "time", 18: "rating",
}
TYPE_TEXT_BLOCK, TYPE_PAGE_BREAK = 6, 8
TYPE_IMAGE, TYPE_VIDEO, TYPE_FILE_UPLOAD = 11, 12, 13


class FormError(RuntimeError):
    pass


def _get(seq: Any, *path: int, default: Any = None) -> Any:
    cur = seq
    for idx in path:
        if not isinstance(cur, list) or idx >= len(cur) or cur[idx] is None:
            return default
        cur = cur[idx]
    return cur


def _load_data(html: str) -> list:
    match = re.search(r"FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);\s*</script>", html, re.S)
    if not match:
        match = re.search(r"FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);", html, re.S)
    if not match:
        raise FormError("FB_PUBLIC_LOAD_DATA_ not found: the form is private, requires sign-in, "
                        "or the URL is not a /viewform link")
    return json.loads(match.group(1))


def response_url(view_url: str) -> str:
    parts = urlsplit(view_url)
    path = re.sub(r"/(viewform|formResponse)/?$", "", parts.path.rstrip("/")) + "/formResponse"
    return urlunsplit((parts.scheme or "https", parts.netloc or "docs.google.com", path, "", ""))


def parse_form_html(html: str, url: str = "") -> Questionnaire:
    """Parse the HTML of a Google Form `viewform` page into a Questionnaire."""
    data = _load_data(html)
    items = _get(data, 1, 1, default=[])
    if not items:
        raise FormError("The form has no questions (or they could not be read)")

    questions: list[Question] = []
    page = 0
    section = ""
    pending_note = ""
    for item in items:
        item_type = _get(item, 3)
        title = (_get(item, 1, default="") or "").strip()
        description = (_get(item, 2, default="") or "").strip()
        if item_type == TYPE_PAGE_BREAK:
            page += 1
            section = title
            pending_note = description
            continue
        if item_type == TYPE_TEXT_BLOCK:
            pending_note = "\n".join(x for x in (title, description) if x)
            continue
        if item_type in (TYPE_IMAGE, TYPE_VIDEO):
            continue
        entries = _get(item, 4, default=[])
        if item_type == TYPE_FILE_UPLOAD:
            if any(_get(e, 2) == 1 for e in entries):
                raise FormError(f"Question {title!r} requires a file upload (needs sign-in); not supported")
            continue
        if item_type not in ITEM_TYPES or not entries:
            continue

        qtype = ITEM_TYPES[item_type]
        first = entries[0]
        if pending_note:
            description = "\n".join(x for x in (pending_note, description) if x)
            pending_note = ""
        kwargs: dict[str, Any] = dict(
            id=f"q{len(questions) + 1}", title=title or f"Question {len(questions) + 1}", type=qtype,
            required=any(_get(e, 2) == 1 for e in entries), description=description, page=page,
            section=section, entry_ids=[str(_get(e, 0)) for e in entries],
        )
        raw_options = _get(first, 1, default=[]) or []
        options = [str(_get(o, 0, default="")) for o in raw_options]
        has_other = any(_get(o, 4) == 1 for o in raw_options)

        if qtype in CHOICE_TYPES or qtype == "checkboxes":
            kwargs["options"] = [o for o, raw in zip(options, raw_options) if not (_get(raw, 4) == 1 and o == "")]
            kwargs["has_other"] = has_other
        elif qtype in SCALE_TYPES:
            numbers = [int(o) for o in options if re.fullmatch(r"-?\d+", o)]
            if numbers:
                kwargs["scale_min"], kwargs["scale_max"] = min(numbers), max(numbers)
            else:  # layout of this item type is not known; assume the common 1..5
                kwargs["scale_min"], kwargs["scale_max"] = 1, 5
            labels = _get(first, 3, default=[]) or []
            kwargs["scale_labels"] = [str(x) for x in labels if x is not None][:2]
        elif qtype == "grid":
            kwargs["options"] = options
            kwargs["rows"] = [str(_get(e, 3, 0, default=f"Row {i + 1}")) for i, e in enumerate(entries)]
            if _get(first, 11, 0) == 1:
                kwargs["type"] = "checkbox_grid"
        elif qtype == "date":
            flags = _get(first, 7, default=[]) or []
            kwargs["date_has_time"] = _get(flags, 0) == 1
            kwargs["date_has_year"] = _get(flags, 1, default=1) == 1
        questions.append(Question(**kwargs))

    email_setting = _get(data, 1, 10, 6, default=1)
    collects_email = isinstance(email_setting, int) and email_setting > 1
    if collects_email:
        questions.insert(0, Question(id="email", title="Email", type="email", required=True))

    fbzx = None
    m = re.search(r'name="fbzx"\s+value="(-?\d+)"', html)
    if m:
        fbzx = m.group(1)

    title = _get(data, 1, 8) or _get(data, 3) or "Google Form"
    return Questionnaire(
        title=str(title).strip(), description=str(_get(data, 1, 0, default="") or "").strip(),
        questions=questions, source=url,
        google=dict(view_url=url, form_response_url=response_url(url) if url else None, fbzx=fbzx,
                    page_count=page, collects_email=collects_email),
    )


def fetch_form(url: str, session=None, timeout: float = 20) -> Questionnaire:
    """Download and parse a public Google Form (the link from Send -> link, or forms.gle/...)."""
    import requests

    if "/forms/d/" in url and "/d/e/" not in url and "/edit" in url:
        raise FormError("This is the editor link. Use the public link (Send -> link icon), "
                        "it looks like https://docs.google.com/forms/d/e/<id>/viewform")
    session = session or requests.Session()
    resp = session.get(url, params={"hl": "en"}, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    if "accounts.google.com" in resp.url or "ServiceLogin" in resp.url:
        raise FormError("The form requires signing in to Google; only public forms are supported")
    resp.raise_for_status()
    view_url = urlunsplit(urlsplit(resp.url)._replace(query="", fragment=""))
    return parse_form_html(resp.text, view_url)


# --------------------------------------------------------------------------- #
# Submission
# --------------------------------------------------------------------------- #

def build_payload(questionnaire: Questionnaire, answers: dict) -> list[tuple[str, str]]:
    """Translate canonical answers into the (name, value) pairs Google Forms expects."""
    pairs: list[tuple[str, str]] = []

    def add_choice(entry: str, value: Any) -> None:
        if isinstance(value, dict) and "other" in value:
            pairs.append((f"entry.{entry}", "__other_option__"))
            pairs.append((f"entry.{entry}.other_option_response", str(value["other"])))
        else:
            pairs.append((f"entry.{entry}", str(value)))

    for q in questionnaire.questions:
        value = answers.get(q.id)
        if value is None:
            continue
        if q.type == "email":
            pairs.append(("emailAddress", str(value)))
            continue
        if not q.entry_ids:
            raise FormError(f"Question {q.id} has no Google Forms entry id")
        entry = q.entry_ids[0]
        if q.type in TEXT_TYPES:
            pairs.append((f"entry.{entry}", str(value)))
        elif q.type in CHOICE_TYPES:
            add_choice(entry, value)
        elif q.type == "checkboxes":
            for v in value:
                add_choice(entry, v)
        elif q.type in SCALE_TYPES:
            pairs.append((f"entry.{entry}", str(value)))
        elif q.type in GRID_TYPES:
            for row, col in value.items():
                row_entry = q.entry_ids[q.rows.index(row)]
                for c in (col if isinstance(col, list) else [col]):
                    pairs.append((f"entry.{row_entry}", str(c)))
        elif q.type == "date":
            year, month, day = (int(x) for x in str(value).split("-"))
            if q.date_has_year:
                pairs.append((f"entry.{entry}_year", str(year)))
            pairs.append((f"entry.{entry}_month", str(month)))
            pairs.append((f"entry.{entry}_day", str(day)))
        elif q.type == "time":
            hour, minute = str(value).split(":")[:2]
            pairs.append((f"entry.{entry}_hour", hour.zfill(2)))
            pairs.append((f"entry.{entry}_minute", minute.zfill(2)))

    google = questionnaire.google or {}
    page_count = int(google.get("page_count") or 0)
    if page_count:
        pairs.append(("pageHistory", ",".join(str(i) for i in range(page_count + 1))))
    pairs.append(("fvv", "1"))
    if google.get("fbzx"):
        pairs.append(("fbzx", google["fbzx"]))
        pairs.append(("partialResponse", json.dumps([None, None, google["fbzx"]])))
    return pairs


def submit_response(questionnaire: Questionnaire, answers: dict, session=None, timeout: float = 20) -> int:
    """POST one response. Returns the HTTP status code (200 means Google accepted it)."""
    import requests

    google = questionnaire.google or {}
    url = google.get("form_response_url")
    if not url:
        raise FormError("This questionnaire did not come from a Google Form (no formResponse URL)")
    session = session or requests.Session()
    resp = session.post(url, data=build_payload(questionnaire, answers),
                        headers={"User-Agent": USER_AGENT, "Referer": google.get("view_url") or url},
                        timeout=timeout)
    return resp.status_code


def check_structure(saved: Questionnaire, live: Questionnaire) -> list[str]:
    """Differences between the questionnaire used for answering and the live form."""
    problems = []
    live_by_title = {(q.title, q.type): q for q in live.questions}
    for q in saved.questions:
        other = live_by_title.get((q.title, q.type))
        if other is None:
            problems.append(f"question {q.title!r} no longer exists in the form")
        elif other.entry_ids != q.entry_ids or other.options != q.options or other.rows != q.rows:
            problems.append(f"question {q.title!r} changed (options or ids)")
    return problems


def submit_all(questionnaire: Questionnaire, responses: list[dict], delay: float = 3.0, log=print) -> dict:
    """Submit responses one by one with a fixed pause between them."""
    import requests

    session = requests.Session()
    stats = {"ok": 0, "failed": 0}
    for i, record in enumerate(responses, 1):
        status = submit_response(questionnaire, record["answers"], session=session)
        ok = status == 200
        stats["ok" if ok else "failed"] += 1
        log(f"[{i}/{len(responses)}] {record.get('persona_id')}: HTTP {status} {'ok' if ok else 'FAILED'}")
        if i < len(responses):
            time.sleep(delay)
    return stats
