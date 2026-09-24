"""CSV exports for personas and responses."""

from __future__ import annotations

import csv
from pathlib import Path

from .questionnaire import GRID_TYPES, Questionnaire, format_answer

PERSONA_COLUMNS = [
    ("id", lambda p: p.id), ("name", lambda p: p.full_name), ("gender", lambda p: p.gender), ("age", lambda p: p.age),
    ("country", lambda p: p.country), ("city", lambda p: p.city), ("nationality", lambda p: p.nationality),
    ("background", lambda p: p.background), ("native_languages", lambda p: ", ".join(p.native_languages)),
    ("english", lambda p: p.english_level), ("education", lambda p: p.education),
    ("occupation", lambda p: p.occupation), ("job_title", lambda p: p.job_title),
    ("seniority", lambda p: p.seniority), ("employment", lambda p: p.employment_type),
    ("industry", lambda p: p.industry), ("company_size", lambda p: p.company_size),
    ("work_mode", lambda p: p.work_mode), ("years_experience", lambda p: p.years_experience),
    ("income_band", lambda p: p.income_band), ("ai_attitude", lambda p: p.ai["attitude"]),
    ("ai_tools", lambda p: ", ".join(p.ai["tools"])), ("ai_frequency", lambda p: p.ai["frequency"]),
    ("ai_since", lambda p: p.ai["since_year"]), ("ai_use_cases", lambda p: "; ".join(p.ai["use_cases"])),
    ("employer_policy", lambda p: p.ai["employer_policy"] or ""), ("satisfaction_1_10", lambda p: p.ai["satisfaction_1_10"]),
    ("concerns", lambda p: "; ".join(p.ai["concerns"])), ("survey_style", lambda p: (
        f"{p.style['engagement']}, {p.style['verbosity']}, {p.style['tone']}")),
    ("bio", lambda p: p.bio),
]


def write_personas_csv(path: str | Path, personas: list) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([name for name, _ in PERSONA_COLUMNS])
        for p in personas:
            writer.writerow([get(p) for _, get in PERSONA_COLUMNS])


def write_responses_csv(path: str | Path, questionnaire: Questionnaire, records: list[dict]) -> None:
    """One row per respondent, one column per question (grid rows get "Title [Row]" columns, like Sheets)."""
    columns = []
    for q in questionnaire.questions:
        if q.type in GRID_TYPES:
            columns.extend((q, row, f"{q.title} [{row}]") for row in q.rows)
        else:
            columns.append((q, None, q.title))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["persona_id", "persona_name", "generated_at"] + [title for _, _, title in columns])
        for record in records:
            answers = record["answers"]
            row = [record["persona_id"], record.get("persona_name", ""), record.get("generated_at", "")]
            for q, grid_row, _ in columns:
                value = answers.get(q.id)
                if grid_row is not None:
                    value = (value or {}).get(grid_row)
                row.append(format_answer(value))
            writer.writerow(row)
