"""Questionnaire model shared by the Google Forms parser, the answerers and the exporters.

Answer values by question type:
    short_text / paragraph / email   -> str
    single_choice / dropdown         -> option str, or {"other": "free text"}
    checkboxes                       -> list of option str / {"other": "free text"}
    scale / rating                   -> int
    grid                             -> {row label: column label}
    checkbox_grid                    -> {row label: [column labels]}
    date                             -> "YYYY-MM-DD"
    time                             -> "HH:MM"
    None                             -> not answered
"""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

TEXT_TYPES = {"short_text", "paragraph"}
CHOICE_TYPES = {"single_choice", "dropdown"}
SCALE_TYPES = {"scale", "rating"}
GRID_TYPES = {"grid", "checkbox_grid"}
QUESTION_TYPES = TEXT_TYPES | CHOICE_TYPES | SCALE_TYPES | GRID_TYPES | {"checkboxes", "date", "time", "email"}

TYPE_ALIASES = {
    "text": "short_text", "short": "short_text", "short_answer": "short_text", "string": "short_text",
    "long_text": "paragraph", "long": "paragraph", "textarea": "paragraph",
    "radio": "single_choice", "choice": "single_choice", "single": "single_choice", "multiple_choice": "single_choice",
    "select": "dropdown", "checkbox": "checkboxes", "multi": "checkboxes", "multiple": "checkboxes",
    "linear_scale": "scale", "likert": "scale", "stars": "rating", "matrix": "grid",
    "multiple_choice_grid": "grid", "checkbox_matrix": "checkbox_grid",
}


@dataclass
class Question:
    id: str
    title: str
    type: str
    required: bool = False
    description: str = ""
    options: list[str] = field(default_factory=list)
    has_other: bool = False
    scale_min: int | None = None
    scale_max: int | None = None
    scale_labels: list[str] = field(default_factory=list)  # [low label, high label]
    rows: list[str] = field(default_factory=list)          # grid rows
    page: int = 0
    section: str = ""
    entry_ids: list[str] = field(default_factory=list)     # Google Forms entry ids (one per grid row)
    date_has_year: bool = True
    date_has_time: bool = False

    def __post_init__(self) -> None:
        self.type = TYPE_ALIASES.get(self.type, self.type)
        if self.type not in QUESTION_TYPES:
            raise ValueError(f"Question {self.id!r}: unsupported type {self.type!r}")
        if self.type in SCALE_TYPES:
            if self.scale_min is None:
                self.scale_min = int(self.options[0]) if self.options else 1
            if self.scale_max is None:
                self.scale_max = int(self.options[-1]) if self.options else 5
        if self.type in CHOICE_TYPES | {"checkboxes"} | GRID_TYPES and not self.options:
            raise ValueError(f"Question {self.id!r} ({self.type}) needs options")
        if self.type in GRID_TYPES and not self.rows:
            raise ValueError(f"Question {self.id!r} ({self.type}) needs rows")

    @property
    def scale_values(self) -> list[int]:
        return list(range(int(self.scale_min), int(self.scale_max) + 1))


@dataclass
class Questionnaire:
    title: str
    questions: list[Question]
    description: str = ""
    source: str = ""
    google: dict | None = None  # form_response_url, view_url, fbzx, page_count, collects_email

    def question(self, qid: str) -> Question:
        for q in self.questions:
            if q.id == qid:
                return q
        raise KeyError(qid)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Questionnaire":
        questions = [Question(**q) for q in data["questions"]]
        return cls(title=data.get("title", ""), questions=questions, description=data.get("description", ""),
                   source=data.get("source", ""), google=data.get("google"))

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_questionnaire(path: str | Path) -> Questionnaire:
    """Load a questionnaire from a .json or .yaml/.yml file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        import yaml  # optional dependency, only needed for YAML files

        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    questions = []
    for i, raw in enumerate(data["questions"], 1):
        raw = dict(raw)
        raw.setdefault("id", f"q{i}")
        raw["id"] = str(raw["id"])
        if "other" in raw:
            raw["has_other"] = bool(raw.pop("other"))
        if "min" in raw:
            raw["scale_min"] = raw.pop("min")
        if "max" in raw:
            raw["scale_max"] = raw.pop("max")
        if "labels" in raw:
            raw["scale_labels"] = list(raw.pop("labels"))
        raw["options"] = [str(o) for o in raw.get("options", [])]
        questions.append(Question(**raw))
    ids = [q.id for q in questions]
    if len(set(ids)) != len(ids):
        raise ValueError("Question ids must be unique")
    return Questionnaire(title=data.get("title", path.stem), description=data.get("description", ""),
                         questions=questions, source=str(path), google=data.get("google"))


# --------------------------------------------------------------------------- #
# Validation / normalisation
# --------------------------------------------------------------------------- #

def _match_option(value: str, options: list[str]) -> str | None:
    if value in options:
        return value
    low = {o.lower().strip(): o for o in options}
    key = value.lower().strip()
    if key in low:
        return low[key]
    close = difflib.get_close_matches(key, list(low), n=1, cutoff=0.85)
    return low[close[0]] if close else None


def _normalize_choice(q: Question, value: Any) -> Any:
    if isinstance(value, dict) and "other" in value:
        text = str(value["other"]).strip()
        if not q.has_other or not text:
            raise ValueError("'Other' is not available or empty")
        return {"other": text}
    if not isinstance(value, str):
        raise ValueError(f"expected a string, got {type(value).__name__}")
    match = _match_option(value, q.options)
    if match is None:
        if q.has_other and value.strip():
            return {"other": value.strip()}
        raise ValueError(f"{value!r} is not one of the options")
    return match


def normalize_answer(q: Question, value: Any) -> Any:
    """Coerce a raw answer into the canonical form, raising ValueError when impossible."""
    if value is None or value == "" or value == []:
        if q.required:
            raise ValueError("required question left empty")
        return None
    t = q.type
    if t in TEXT_TYPES or t == "email":
        if not isinstance(value, str):
            value = str(value)
        value = value.strip()
        if t == "email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("not an e-mail address")
        return value
    if t in CHOICE_TYPES:
        return _normalize_choice(q, value)
    if t == "checkboxes":
        items = value if isinstance(value, list) else [value]
        out, seen = [], set()
        for item in items:
            norm = _normalize_choice(q, item)
            key = json.dumps(norm, sort_keys=True)
            if key not in seen:
                seen.add(key)
                out.append(norm)
        return out
    if t in SCALE_TYPES:
        try:
            number = int(round(float(value)))
        except (TypeError, ValueError):
            raise ValueError(f"{value!r} is not a number") from None
        if number not in q.scale_values:
            raise ValueError(f"{number} outside {q.scale_min}..{q.scale_max}")
        return number
    if t in GRID_TYPES:
        if not isinstance(value, dict):
            raise ValueError("grid answer must be an object {row: column}")
        out = {}
        for row, col in value.items():
            row_match = _match_option(str(row), q.rows)
            if row_match is None:
                raise ValueError(f"unknown row {row!r}")
            if t == "grid":
                col_match = _match_option(str(col), q.options)
                if col_match is None:
                    raise ValueError(f"unknown column {col!r}")
                out[row_match] = col_match
            else:
                cols = col if isinstance(col, list) else [col]
                matched = [_match_option(str(c), q.options) for c in cols]
                if None in matched:
                    raise ValueError(f"unknown column in {cols!r}")
                out[row_match] = matched
        if q.required and len(out) < len(q.rows):
            raise ValueError("every row of a required grid must be answered")
        return out
    if t == "date":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)):
            raise ValueError("date must be YYYY-MM-DD")
        return str(value)
    if t == "time":
        m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::\d{2})?", str(value))
        if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
            raise ValueError("time must be HH:MM")
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    raise ValueError(f"unsupported type {t}")


def format_answer(value: Any) -> str:
    """Flatten an answer for CSV output (Google-Sheets-like)."""
    if value is None:
        return ""
    if isinstance(value, dict) and set(value) == {"other"}:
        return str(value["other"])
    if isinstance(value, list):
        return ", ".join(format_answer(v) for v in value)
    return str(value)
