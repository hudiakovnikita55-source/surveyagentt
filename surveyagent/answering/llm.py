"""Answering with Claude: one request per persona, structured JSON output.

The system prompt (answering guidelines + the rendered questionnaire) is identical
for every persona and is cached; only the persona profile changes between requests.
"""

from __future__ import annotations

import json
from datetime import date

from ..personas.generator import Persona, persona_card
from ..questionnaire import CHOICE_TYPES, END, GRID_TYPES, SCALE_TYPES, TEXT_TYPES, Question, Questionnaire

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_EFFORT = "medium"
# Server-side refusal fallbacks (re-run a declined request on another model inside the same call).
FALLBACK_BETA = "server-side-fallback-2026-07-01"
FALLBACK_MODELS = {"claude-opus-5", "claude-fable-5", "claude-fable-5-1"}
OTHER = "__other__"

GUIDELINES = """\
You are role-playing one real person who is filling in an online survey. The persona profile in the \
user message is that person and the questionnaire is below. Answer every question the way this specific \
person would, in their own words, and return the answers in the requested JSON format.

The purpose is realistic synthetic survey data: responses that look like what real respondents write. \
Real survey data is varied and a little messy, so follow these rules.

Consistency
- Stay consistent with the profile: demographics, job, tools, how often they use AI, attitude, \
satisfaction, trust and concerns. For factual questions (age group, country, company size, income band, \
education, years of experience...) choose the option that matches the profile; if none matches exactly, \
choose the closest one. Use "Other" only when nothing is close.
- Stay consistent across questions (e.g. do not claim daily use in one answer and rare use in another).

Ratings and choices
- Base ratings on the profile and apply the person's rating-scale habit: "tends to agree" leans towards \
agreeing, "prefers the middle" avoids the end points, "uses the extremes" likes the end points.
- People are not perfectly logical. Small inconsistencies between related rating items are normal; \
do not make every answer tidy.
- In multi-select questions pick what really applies. Rushed respondents tick fewer boxes.

Open answers
- Match the person's verbosity: terse = a few words or a fragment (roughly 1-10 words); moderate = one or \
two sentences; elaborate = two to four sentences and never more than about 80 words.
- Use the person's tone and concrete details from the profile (their tools, tasks, the good and bad \
experience, pet peeve, their sector). Specific, slightly personal details make an answer believable; \
generic statements do not. Do not reuse the profile's wording verbatim, say it the way this person would.
- Write like someone typing into a web form, not like an assistant: no greetings, no "As a <job title>...", \
no summaries or conclusions, no bullet points or markdown, no em dashes. Avoid words typical of \
AI-written text such as leverage, streamline, game-changer, revolutionize, invaluable, crucial, landscape, \
delve, seamless, robust, navigate, empower.
- It is fine to be negative, unsure, bored or ambivalent. Not everyone likes AI, and not everyone likes surveys.
- Write open answers in the language of the questionnaire. If that is not the person's native language, \
write at their level and follow their writing notes (slips typical of their first language are good, but \
keep them natural and occasional). Do not add spelling typos on purpose; that is handled separately.

Skipping
- Some questions have "logic" lines (e.g. "No" -> end of survey, or skip to a later question). Follow \
them like a real respondent: questions you would not be shown must be null. Only those questions may \
be null.
- Some multi-select options must be ticked alone; never combine them with other options.
- Required questions must always be answered.
- Optional questions: careful respondents answer nearly all of them, rushed ones often skip optional open \
questions. Use the skip probability from the profile as a rough guide. Put the ids of skipped questions in \
"skipped"; their values are ignored (use an empty string for skipped open questions).

Special fields
- Never invent contact details. If a question asks for an e-mail address, use the e-mail from the profile. \
Leave phone numbers, company names and social media handles empty when optional, or write \
"prefer not to say" when required.
- "__other__" means the "Other:" option. Use it only where the questionnaire allows it and then write the \
free text into the matching "<id>__other" field; in all other cases leave "<id>__other" as an empty string.
- Grids: answer every row; rows are referred to as "r1", "r2", ... in the order listed.
- Dates use YYYY-MM-DD, times HH:MM.
"""

TYPE_LABELS = {
    "short_text": "open question, short answer", "paragraph": "open question, paragraph",
    "single_choice": "single choice", "dropdown": "single choice (dropdown)", "checkboxes": "multi-select",
    "scale": "rating scale", "rating": "star rating", "grid": "grid, one column per row",
    "checkbox_grid": "grid, any number of columns per row", "date": "date", "time": "time", "email": "e-mail",
}


def render_questionnaire(q: Questionnaire) -> str:
    lines = [f'QUESTIONNAIRE: "{q.title}"']
    if q.language:
        lines.append(f"Language of this version: {q.language}")
    if q.description:
        lines.append(q.description)
    section = None
    for question in q.questions:
        if question.type == "email":
            continue
        if question.section and question.section != section:
            section = question.section
            lines.append(f"\n--- Section: {section} ---")
        meta = [TYPE_LABELS[question.type], "required" if question.required else "optional"]
        if question.type in SCALE_TYPES:
            meta.append(f"{question.scale_min}-{question.scale_max}")
            if len(question.scale_labels) == 2:
                meta.append(f"{question.scale_min} = {question.scale_labels[0]}, "
                            f"{question.scale_max} = {question.scale_labels[1]}")
        if question.has_other:
            meta.append(f'"Other" allowed ({OTHER} + {question.id}__other)')
        lines.append(f"\n[{question.id}] ({'; '.join(meta)}) {question.title}")
        if question.description:
            lines.append(f"    note: {question.description}")
        if question.type in GRID_TYPES:
            for i, row in enumerate(question.rows, 1):
                lines.append(f'    r{i} = "{row}"')
            lines.append("    columns: " + " | ".join(f'"{o}"' for o in question.options))
        elif question.options and question.type not in SCALE_TYPES:
            lines.append("    options: " + " | ".join(f'"{o}"' for o in question.options))
        for option, target in question.go_to.items():
            where = "end of survey" if target == END else f"skip to [{target}]"
            lines.append(f'    logic: "{option}" -> {where}')
        for option in question.exclusive:
            lines.append(f'    "{option}" must be the only selected option')
    return "\n".join(lines)


def _question_schema(q: Question) -> dict:
    if q.type in TEXT_TYPES:
        return {"type": "string"}
    if q.type in CHOICE_TYPES:
        return {"type": "string", "enum": q.options + ([OTHER] if q.has_other else [])}
    if q.type == "checkboxes":
        return {"type": "array", "items": {"type": "string", "enum": q.options + ([OTHER] if q.has_other else [])}}
    if q.type in SCALE_TYPES:
        return {"type": "integer", "enum": q.scale_values}
    if q.type in GRID_TYPES:
        cell: dict = {"type": "string", "enum": q.options}
        if q.type == "checkbox_grid":
            cell = {"type": "array", "items": cell}
        keys = [f"r{i}" for i in range(1, len(q.rows) + 1)]
        return {"type": "object", "properties": {k: cell for k in keys}, "required": keys,
                "additionalProperties": False}
    if q.type == "date":
        return {"type": "string", "format": "date"}
    if q.type == "time":
        return {"type": "string", "description": "HH:MM"}
    raise ValueError(q.type)


def build_schema(q: Questionnaire) -> dict:
    """JSON schema for one complete response. Every field is required (skips are listed in "skipped")."""
    properties: dict = {}
    conditional = q.conditional_ids()
    for question in q.questions:
        if question.type == "email":
            continue
        schema = _question_schema(question)
        if question.id in conditional:  # null = not shown because of the form's logic
            schema = {"anyOf": [schema, {"type": "null"}]}
        properties[question.id] = schema
        if question.has_other and question.type in CHOICE_TYPES | {"checkboxes"}:
            properties[f"{question.id}__other"] = {"type": "string"}
    optional = [x.id for x in q.questions if not x.required and x.type != "email"]
    if optional:
        properties["skipped"] = {"type": "array", "items": {"type": "string", "enum": optional}}
    return {"type": "object", "properties": properties, "required": list(properties),
            "additionalProperties": False}


def parse_output(q: Questionnaire, data: dict) -> dict:
    """Convert the model's JSON into canonical (not yet validated) answers."""
    skipped = set(data.get("skipped") or [])
    answers: dict = {}
    for question in q.questions:
        if question.type == "email":
            continue
        if question.id in skipped and not question.required:
            answers[question.id] = None
            continue
        value = data.get(question.id)
        other_text = str(data.get(f"{question.id}__other") or "").strip()
        if question.type in CHOICE_TYPES and value == OTHER:
            value = {"other": other_text} if other_text else None
        elif question.type == "checkboxes" and isinstance(value, list):
            value = [({"other": other_text} if v == OTHER else v) for v in value if v != OTHER or other_text]
        elif question.type in GRID_TYPES and isinstance(value, dict):
            value = {question.rows[int(k[1:]) - 1]: v for k, v in value.items()
                     if k[1:].isdigit() and 0 < int(k[1:]) <= len(question.rows)}
        elif question.type in TEXT_TYPES and isinstance(value, str):
            value = value.strip() or None
        answers[question.id] = value
    return answers


class AnswerError(RuntimeError):
    pass


class LLMAnswerer:
    def __init__(self, questionnaire: Questionnaire, model: str = DEFAULT_MODEL, effort: str = DEFAULT_EFFORT,
                 client=None, use_fallbacks: bool = True, max_tokens: int = 16000):
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client
        self.questionnaire = questionnaire
        self.model = model
        self.effort = effort
        self.use_fallbacks = use_fallbacks and model in FALLBACK_MODELS
        self.max_tokens = max_tokens
        self.schema = build_schema(questionnaire)
        self.system = [
            {"type": "text", "text": GUIDELINES},
            {"type": "text", "text": render_questionnaire(questionnaire), "cache_control": {"type": "ephemeral"}},
        ]

    def request_params(self, persona: Persona) -> dict:
        user = (f"PERSONA PROFILE\n{persona_card(persona)}\n\n"
                f"Today is {date.today().isoformat()}. Fill in the questionnaire now as {persona.full_name}.")
        params: dict = dict(
            model=self.model, max_tokens=self.max_tokens, system=self.system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": self.schema}},
        )
        if not self.model.startswith("claude-haiku"):  # Haiku 4.5 has no adaptive thinking / effort
            params["thinking"] = {"type": "adaptive"}
            params["output_config"]["effort"] = self.effort
        return params

    def answer(self, persona: Persona) -> tuple[dict, dict]:
        """Returns (raw answers, token usage) for one persona."""
        params = self.request_params(persona)
        if self.use_fallbacks:
            response = self.client.beta.messages.create(**params, betas=[FALLBACK_BETA], fallbacks="default")
        else:
            response = self.client.messages.create(**params)

        if response.stop_reason == "refusal":
            raise AnswerError(f"model declined the request ({getattr(response, 'stop_details', None)})")
        if response.stop_reason == "max_tokens":
            raise AnswerError("response was cut off by max_tokens")
        blocks = list(response.content)
        # After a server-side fallback, only the blocks after the last switch point belong to the final answer.
        start = max((i for i, b in enumerate(blocks) if b.type == "fallback"), default=-1) + 1
        text = "".join(b.text for b in blocks[start:] if b.type == "text")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AnswerError(f"model returned invalid JSON: {exc}") from exc

        usage = response.usage
        stats = {
            "model": getattr(response, "model", self.model),
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        }
        return parse_output(self.questionnaire, data), stats
