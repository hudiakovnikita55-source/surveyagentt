"""Command line interface: python -m surveyagent <command> ..."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT_PERSONAS = "data/personas.json"


def _load_questionnaire(source: str):
    from .questionnaire import Questionnaire, load_questionnaire

    if source.startswith(("http://", "https://")):
        from .google_forms import fetch_form

        return fetch_form(source)
    path = Path(source)
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if "responses" in data:  # a responses file carries its questionnaire
            return Questionnaire.from_dict(data["questionnaire"])
        if data.get("questions") and isinstance(data["questions"][0], dict) and "entry_ids" in data["questions"][0]:
            return Questionnaire.from_dict(data)
    return load_questionnaire(path)


def _parse_boost(spec: str) -> dict[str, float]:
    """"PL=4,LV=5" (country codes or English names) -> {"PL": 4.0, "LV": 5.0}."""
    from .personas import geo

    by_name = {c["name"].lower(): code for code, c in geo.COUNTRIES.items()}
    out = {}
    for part in filter(None, (x.strip() for x in spec.split(","))):
        key, _, value = part.partition("=")
        code = key.strip().upper() if key.strip().upper() in geo.COUNTRIES else by_name.get(key.strip().lower())
        if code is None:
            sys.exit(f"Unknown country {key!r} in --country-boost")
        out[code] = float(value)
    return out


def cmd_personas(args) -> None:
    from .export import write_personas_csv
    from .personas import generate_personas, save_personas

    personas = generate_personas(args.count, seed=args.seed, email_domain=args.email_domain, audience=args.audience,
                                 country_boost=_parse_boost(args.country_boost))
    save_personas(personas, args.out)
    csv_path = Path(args.out).with_suffix(".csv")
    write_personas_csv(csv_path, personas)
    print(f"Generated {len(personas)} personas -> {args.out} and {csv_path}")
    _print_stats(personas)


def _print_stats(personas) -> None:
    def show(title, counter, top=40):
        items = ", ".join(f"{k} {v}" for k, v in counter.most_common(top))
        print(f"  {title}: {items}")

    ages = [p.age for p in personas]
    print(f"Personas: {len(personas)}; age {min(ages)}-{max(ages)} (mean {sum(ages) / len(ages):.1f})")
    show("countries", Counter(p.country for p in personas))
    show("gender", Counter(p.gender for p in personas))
    show("occupations", Counter(p.occupation for p in personas), 15)
    show("employment", Counter(p.employment_type for p in personas))
    show("AI attitude", Counter(p.ai["attitude"] for p in personas))
    show("AI frequency", Counter(p.ai["frequency"] for p in personas))
    show("main tool", Counter(p.ai["primary_tool"] for p in personas), 10)
    show("English", Counter(p.english_level for p in personas))
    show("survey style", Counter(f"{p.style['engagement']}/{p.style['verbosity']}" for p in personas), 9)
    marketers = [p.marketing for p in personas if p.marketing]
    if marketers:
        active = [m for m in marketers if m["active"]]
        print(f"  marketing in the last 12 months: {len(active)} of {len(marketers)}; "
              f"no AI in marketing: {sum(not m['uses_ai'] for m in active)}")
        show("marketing setting", Counter(m["setting"] for m in active))


def cmd_stats(args) -> None:
    from .personas import load_personas

    _print_stats(load_personas(args.personas))


def cmd_show(args) -> None:
    from .personas import load_personas, persona_card

    personas = {p.id: p for p in load_personas(args.personas)}
    for pid in args.ids:
        p = personas.get(pid.upper())
        if p is None:
            sys.exit(f"No persona {pid}")
        print(f"=== {p.id} ===\n{p.bio}\n\n{persona_card(p)}\n")


def cmd_inspect(args) -> None:
    from .answering.llm import render_questionnaire

    q = _load_questionnaire(args.form)
    print(render_questionnaire(q))
    google = q.google or {}
    if google:
        print(f"\npages: {google.get('page_count', 0) + 1}; collects e-mail: {google.get('collects_email')}; "
              f"submit URL: {google.get('form_response_url')}")
    if args.save:
        q.save(args.save)
        print(f"Saved questionnaire to {args.save}")


def cmd_answer(args) -> None:
    from .answering.runner import generate_responses
    from .personas import load_personas, preferred_language

    forms = [_load_questionnaire(f) for f in args.form]
    personas = load_personas(args.personas)
    if args.ids:
        wanted = {x.upper() for x in args.ids.split(",")}
        personas = [p for p in personas if p.id in wanted]
    if args.limit:
        personas = personas[: args.limit]
    run = dict(mode=args.mode, model=args.model, effort=args.effort, workers=args.workers, resume=args.resume,
               seed=args.seed)
    if len(forms) == 1:
        print(f"{len(personas)} personas x {len(forms[0].questions)} questions, mode={args.mode}")
        generate_responses(forms[0], personas, args.out, **run)
        return

    # Several language versions: every persona answers the version they would pick, then everything is merged.
    languages = [f.language for f in forms]
    if not all(languages) or len(set(languages)) != len(languages):
        sys.exit("With several --form files, each needs a different `language:` (e.g. EN, PL, RU).")
    out = Path(args.out)
    inputs = []
    for form in forms:
        group = [p for p in personas if preferred_language(p, languages) == form.language]
        path = out.with_name(f"{out.stem}_{form.language.lower()}.json")
        print(f"\n[{form.language}] {len(group)} personas x {len(form.questions)} questions, mode={args.mode}")
        if group:
            generate_responses(form, group, path, **run)
            inputs.append((form, path))
    _write_merged(inputs, out.with_name(f"{out.stem}_merged.csv"), sheet=out.with_name(f"{out.stem}_sheet.xlsx"),
                  versions=forms, language_question=args.language_question)


def _write_merged(inputs, out_path, reference=None, sheet=None, versions=None, language_question="Language") -> None:
    from .merge import _status, collect, merged_record, write_google_sheet, write_merged

    warnings: list[str] = []
    reference, rows = collect(inputs, reference=reference, warnings=warnings)
    records = [{"respondent_id": row.respondent_id, "language": row.language, "submitted_at": row.submitted_at,
                "synthetic": "yes" if row.synthetic else "no", "status": _status(reference, answers),
                **merged_record(reference, answers)} for row, _, answers in rows]
    codebook = write_merged(out_path, reference, records)
    for w in warnings:
        print(f"  warning: {w}")
    by_lang = Counter(r["language"] for r in records)
    status = Counter(r["status"] for r in records)
    print(f"\nMerged {len(records)} responses ({', '.join(f'{k} {v}' for k, v in by_lang.items())}; "
          f"{', '.join(f'{k} {v}' for k, v in status.items())}) -> {out_path}\nCodebook -> {codebook}")
    if sheet:
        write_google_sheet(sheet, reference, rows, versions or [q for q, _ in inputs], language_question)
        print(f"Google Sheet layout (Form Responses 1 + Combined data) -> {sheet}")


def cmd_merge(args) -> None:
    from .questionnaire import load_questionnaire

    inputs = [(load_questionnaire(form), data) for form, data in args.input]
    reference = load_questionnaire(args.reference) if args.reference else None
    _write_merged(inputs, args.out, reference, sheet=args.sheet, language_question=args.language_question)


def cmd_submit(args) -> None:
    from .answering.runner import load_records
    from .google_forms import build_payload, check_structure, fetch_form, submit_all
    from .questionnaire import Questionnaire

    data = json.loads(Path(args.responses).read_text(encoding="utf-8"))
    questionnaire = Questionnaire.from_dict(data["questionnaire"])
    records = load_records(args.responses)
    if not (questionnaire.google or {}).get("form_response_url"):
        sys.exit("These responses were not generated from a Google Form URL, there is nothing to submit to.")
    if args.limit:
        records = records[: args.limit]

    if not args.send:
        print(f"DRY RUN: {len(records)} responses would be sent to {questionnaire.google['form_response_url']}")
        if records:
            print(f"\nPayload of the first response ({records[0]['persona_id']}):")
            for key, value in build_payload(questionnaire, records[0]["answers"]):
                print(f"  {key} = {value}")
        print("\nNothing was sent. Add --send to submit for real (only to a form you own or may fill in).")
        return

    live = fetch_form(questionnaire.google["view_url"])
    problems = check_structure(questionnaire, live)
    if problems:
        sys.exit("The form has changed since the answers were generated:\n  " + "\n  ".join(problems))
    stats = submit_all(questionnaire, records, delay=args.delay)
    print(f"Done: {stats['ok']} accepted, {stats['failed']} failed")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="surveyagent", description="Synthetic survey respondents from personas")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("personas", help="generate personas")
    p.add_argument("--count", type=int, default=100)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=DEFAULT_PERSONAS)
    p.add_argument("--email-domain", default="example.com",
                   help="domain for persona e-mails (default is the reserved example.com)")
    p.add_argument("--audience", choices=["general", "marketing"], default="general",
                   help="general: AI users across professions; marketing: people doing marketing/promotion")
    p.add_argument("--country-boost", default="", help="more personas from some countries, e.g. PL=4,LV=5")
    p.set_defaults(func=cmd_personas)

    p = sub.add_parser("stats", help="distribution summary of a personas file")
    p.add_argument("--personas", default=DEFAULT_PERSONAS)
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("show", help="print persona profiles")
    p.add_argument("ids", nargs="+")
    p.add_argument("--personas", default=DEFAULT_PERSONAS)
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("inspect", help="parse a Google Form URL or questionnaire file and print it")
    p.add_argument("form")
    p.add_argument("--save", help="save the parsed questionnaire as JSON")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("answer", help="generate one response per persona")
    p.add_argument("--form", required=True, action="append",
                   help="Google Form URL, questionnaire .yaml/.json, or saved JSON; repeat it for language versions "
                        "(each persona answers the version they would pick, results are merged)")
    p.add_argument("--personas", default=DEFAULT_PERSONAS)
    p.add_argument("--mode", choices=["llm", "offline"], default="llm")
    p.add_argument("--model", default=None, help="Claude model id (default claude-opus-5)")
    p.add_argument("--effort", default=None, choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--workers", type=int, default=4, help="parallel API requests")
    p.add_argument("--limit", type=int, default=0, help="only the first N personas")
    p.add_argument("--ids", default="", help="comma-separated persona ids, e.g. P001,P017")
    p.add_argument("--out", default="output/responses.json")
    p.add_argument("--resume", action="store_true", help="keep existing responses in --out, answer the rest")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--language-question", default="Language",
                   help="header of the language column in <out>_sheet.xlsx (several --form files only)")
    p.set_defaults(func=cmd_answer)

    p = sub.add_parser("merge", help="merge language versions (synthetic .json or real CSV exports) into one table")
    p.add_argument("--input", nargs=2, action="append", required=True, metavar=("FORM", "DATA"),
                   help="questionnaire file of one language version and its responses (.json from `answer`, or a "
                        "CSV export from Google Forms/Sheets); repeat for every version")
    p.add_argument("--reference", help="version whose labels the merged table uses (default: the EN one)")
    p.add_argument("--out", default="output/merged.csv")
    p.add_argument("--sheet", help="also write an .xlsx in the layout of the form's Google Sheet "
                                   "(Form Responses 1 + Combined data); language blocks follow the --input order")
    p.add_argument("--language-question", default="Language", help="header of the language column in --sheet")
    p.set_defaults(func=cmd_merge)

    p = sub.add_parser("submit", help="submit generated responses to the Google Form (dry run by default)")
    p.add_argument("responses")
    p.add_argument("--send", action="store_true", help="actually send (otherwise only shows the payload)")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--delay", type=float, default=3.0, help="seconds between submissions")
    p.set_defaults(func=cmd_submit)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
