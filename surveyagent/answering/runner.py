"""Generate a full set of responses: answer, validate, humanise, save."""

from __future__ import annotations

import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from ..export import write_responses_csv
from ..personas.generator import Persona
from ..questionnaire import CHOICE_TYPES, GRID_TYPES, SCALE_TYPES, TEXT_TYPES, Question, Questionnaire, normalize_answer
from .heuristic import HeuristicAnswerer
from .humanize import humanize


def _last_resort(q: Question):
    """A valid answer for any question, used only if both answerers failed on it."""
    if q.type in TEXT_TYPES:
        return "-"
    if q.type in CHOICE_TYPES:
        return q.options[0]
    if q.type == "checkboxes":
        return [q.options[0]]
    if q.type in SCALE_TYPES:
        return q.scale_values[len(q.scale_values) // 2]
    if q.type == "grid":
        return {row: q.options[0] for row in q.rows}
    if q.type == "checkbox_grid":
        return {row: [q.options[0]] for row in q.rows}
    if q.type == "date":
        return datetime.now().date().isoformat()
    if q.type == "time":
        return "12:00"
    return None


def finalize_answers(questionnaire: Questionnaire, persona: Persona, raw: dict, fallback: HeuristicAnswerer,
                     rng: random.Random, warnings: list[str]) -> dict:
    """Validate every answer; replace invalid ones and add typing noise to free text."""
    answers = {}
    for q in questionnaire.questions:
        if q.type == "email":
            answers[q.id] = persona.email
            continue
        try:
            value = normalize_answer(q, raw.get(q.id))
        except ValueError as exc:
            warnings.append(f"{q.id}: {exc} -> offline fallback")
            try:
                value = normalize_answer(q, fallback.answer_question(q, persona, rng, allow_skip=False))
            except ValueError:
                value = normalize_answer(q, _last_resort(q))
        if q.type in TEXT_TYPES and isinstance(value, str) and "@" not in value:
            value = humanize(value, persona.style, rng)
        answers[q.id] = value
    return answers


def load_records(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("responses", [])


def save_records(path: str | Path, questionnaire: Questionnaire, records: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = {"questionnaire": questionnaire.to_dict(), "responses": records}
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def generate_responses(questionnaire: Questionnaire, personas: list[Persona], out_path: str | Path, *,
                       mode: str = "llm", model: str | None = None, effort: str | None = None, workers: int = 4,
                       resume: bool = False, seed: int = 0, client=None, log=print) -> list[dict]:
    fallback = HeuristicAnswerer(questionnaire, seed=seed)
    llm = None
    if mode == "llm":
        from .llm import DEFAULT_EFFORT, DEFAULT_MODEL, LLMAnswerer

        llm = LLMAnswerer(questionnaire, model=model or DEFAULT_MODEL, effort=effort or DEFAULT_EFFORT,
                          client=client)
    elif mode != "offline":
        raise ValueError(f"unknown mode {mode!r}")

    records = load_records(out_path) if resume else []
    done = {r["persona_id"] for r in records}
    todo = [p for p in personas if p.id not in done]
    if done:
        log(f"Resuming: {len(done)} responses already in {out_path}, {len(todo)} to go")

    lock = threading.Lock()
    totals = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
    failures: list[str] = []

    def work(persona: Persona) -> dict:
        rng = random.Random(f"{seed}:{persona.id}:post")
        warnings: list[str] = []
        usage = None
        if llm is not None:
            raw, usage = llm.answer(persona)
        else:
            raw = fallback.answer(persona)
        answers = finalize_answers(questionnaire, persona, raw, fallback, rng, warnings)
        record = {
            "persona_id": persona.id, "persona_name": persona.full_name,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mode": mode, "model": usage["model"] if usage else None, "answers": answers,
        }
        if warnings:
            record["warnings"] = warnings
        return record, usage

    with ThreadPoolExecutor(max_workers=max(1, workers if llm else 1)) as pool:
        futures = {pool.submit(work, p): p for p in todo}
        for n, future in enumerate(as_completed(futures), 1):
            persona = futures[future]
            try:
                record, usage = future.result()
            except Exception as exc:  # keep going; the persona can be retried with --resume
                failures.append(persona.id)
                log(f"[{n}/{len(todo)}] {persona.id} {persona.full_name}: FAILED ({type(exc).__name__}: {exc})")
                continue
            with lock:
                records.append(record)
                if usage:
                    for k in totals:
                        totals[k] += usage.get(k, 0)
                save_records(out_path, questionnaire, records)
            note = f" ({len(record['warnings'])} fixed)" if record.get("warnings") else ""
            log(f"[{n}/{len(todo)}] {persona.id} {persona.full_name}: ok{note}")

    order = {p.id: i for i, p in enumerate(personas)}
    records.sort(key=lambda r: order.get(r["persona_id"], len(order)))
    save_records(out_path, questionnaire, records)
    csv_path = Path(out_path).with_suffix(".csv")
    write_responses_csv(csv_path, questionnaire, records)
    log(f"Saved {len(records)} responses to {out_path} and {csv_path}")
    if llm is not None:
        log("Tokens: input {input_tokens:,} (cache read {cache_read_input_tokens:,}, cache write "
            "{cache_creation_input_tokens:,}), output {output_tokens:,}".format(**totals))
    if failures:
        log(f"{len(failures)} personas failed: {', '.join(failures)}. Re-run with --resume to retry them.")
    return records
