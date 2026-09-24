"""Offline answers for questions tagged with a `topic` in the questionnaire file.

Answers are picked by option *position*, not by wording, so one implementation serves every language
version of a questionnaire whose options are in the same order (see surveys/ai_marketing/*.yaml).
The facts come from the persona's `marketing` block (audience="marketing") and its AI profile.

`answer()` returns UNKNOWN when the topic is unknown, the question does not have the expected shape,
or the persona has no data for it; the generic heuristics take over then.
"""

from __future__ import annotations

import random

from ..personas import geo, work
from ..personas.generator import Persona
from ..questionnaire import Question, Questionnaire

UNKNOWN = object()

BUSY = ("some", "most", "almost always")  # task-grid levels that count as "uses AI a fair amount"
CONCERN_KEYS = {text: key for key, text in work.CONCERNS.items()}


def answer(q: Question, p: Persona, rng: random.Random, context: dict, questionnaire: Questionnaire,
           allow_skip: bool = True):
    handler = HANDLERS.get(q.topic)
    if handler is None or not p.marketing:
        return UNKNOWN
    shape = SHAPES.get(q.topic)
    if shape and (len(q.options), len(q.rows)) != shape:
        return UNKNOWN
    if q.topic not in ("consent", "did_marketing") and not p.marketing["active"]:
        return UNKNOWN  # only reachable if the eligibility logic was ignored
    ctx = _Context(q, p, rng, context, questionnaire, allow_skip)
    return handler(ctx)


class _Context:
    def __init__(self, q, p, rng, answers, questionnaire, allow_skip):
        self.q, self.p, self.rng, self.answers, self.allow_skip = q, p, rng, answers, allow_skip
        self.questionnaire = questionnaire
        self.lang = (questionnaire.language or "EN").upper()
        self.m = p.marketing

    def option(self, index: int) -> str:
        return self.q.options[index]

    def text(self, table: dict) -> str:
        return table.get(self.lang, table["EN"])

    def uses_ai(self) -> bool:
        """Follows the respondent's own earlier answer to the AI-use question when there is one."""
        for q in self.questionnaire.questions:
            if q.topic == "ai_use" and self.answers.get(q.id) in q.options[:2]:
                return self.answers[q.id] == q.options[0]
        return bool(self.m.get("uses_ai"))


# --------------------------------------------------------------------------- #
# Screening and profile questions
# --------------------------------------------------------------------------- #

def _consent(c: _Context):
    return c.option(0 if c.m["consents"] else 1)


def _did_marketing(c: _Context):
    return c.option(0 if c.m["active"] else 1)


def _work_country(c: _Context):
    return geo.country_name(c.p.country, c.lang, c.rng)


OTHER_ROLE_TEXT = {
    "sales": {"EN": "sales, with a lot of marketing on the side", "PL": "sprzedaż, ale sporo marketingu",
              "RU": "продажи, но много маркетинга"},
    "design": {"EN": "graphic designer (promo materials)", "PL": "grafik, materiały promocyjne",
               "RU": "дизайнер, промо-материалы"},
    "video": {"EN": "video content for promotion", "PL": "produkcja wideo do promocji", "RU": "видео для продвижения"},
    "pr": {"EN": "PR / communications", "PL": "PR i komunikacja", "RU": "PR и коммуникации"},
    "ecommerce": {"EN": "e-commerce manager", "PL": "e-commerce", "RU": "e-commerce менеджер"},
    "marketing": {"EN": "marketing next to my main job", "PL": "marketing obok głównej pracy",
                  "RU": "маркетинг в дополнение к основной работе"},
}


def _setting(c: _Context):
    setting = c.m["setting"]
    if setting == "other" and c.q.has_other:  # a form with an "Other:" text field
        return {"other": c.text(OTHER_ROLE_TEXT[c.m["other_role"]])}
    return c.option(["agency", "in_house", "freelance", "own_business", "other"].index(setting))


def _years(c: _Context):
    y = c.m["years"]
    return c.option(0 if y < 1 else 1 if y <= 3 else 2 if y <= 6 else 3 if y <= 10 else 4)


def _org_size(c: _Context):
    if c.m["setting"] == "freelance":  # "the organisation for which you do most of your marketing" is fuzzy here
        return c.option(0 if c.rng.random() < 0.7 else 5)
    index = {"1 (just me)": 0, "2–10": 1, "11–50": 2, "51–250": 3}.get(c.p.company_size, 4)
    if c.rng.random() < 0.03:
        index = 5
    return c.option(index)


# --------------------------------------------------------------------------- #
# AI use
# --------------------------------------------------------------------------- #

def _ai_use(c: _Context):
    return c.option(0 if c.m["uses_ai"] else 1)


def _ai_frequency(c: _Context):
    freq = c.p.ai["frequency"]
    if freq == "never":  # said "yes" to AI use elsewhere (LLM answer kept): the lowest frequency
        return c.option(4)
    index = {"several times a day": 0, "daily": 0, "a few times a week": 1, "about once a week": 2,
             "a few times a month": 3}[freq]
    if index == 3 and c.p.ai["attitude"] == "skeptic" and c.rng.random() < 0.4:
        index = 4
    return c.option(index)


OTHER_TOOL_TEXT = {
    "DeepL": {"EN": "translation (DeepL)", "PL": "tłumaczenie (DeepL)", "RU": "перевод (DeepL)"},
    "DeepL Write": {"EN": "DeepL Write", "PL": "DeepL Write", "RU": "DeepL Write"},
    "ElevenLabs": {"EN": "AI voice-over (ElevenLabs)", "PL": "lektor AI (ElevenLabs)", "RU": "озвучка (ElevenLabs)"},
    "transcription": {"EN": "transcription", "PL": "transkrypcja nagrań", "RU": "расшифровка интервью"},
}


def _tool_types(c: _Context):
    kinds = c.m["ai_tool_kinds"] or ["text"]
    chosen = [c.option(i) for i, kind in enumerate(("text", "visual", "ads", "analytics", "chatbot")) if kind in kinds]
    if c.p.style["engagement"] == "rushed":
        chosen = chosen[:2]
    if "other" in kinds and c.rng.random() < 0.3:  # "Other (please specify)" as the last option
        tool = next(t for t in c.p.ai["tools"] if t in work.TOOL_KINDS["other"])
        key = tool if tool in OTHER_TOOL_TEXT else "transcription"
        chosen.append({"other": c.text(OTHER_TOOL_TEXT[key])} if c.q.has_other else c.option(5))
    return chosen or [c.option(0)]


def _task_use(c: _Context):
    out = {}
    for row, task in zip(c.q.rows, work.MARKETING_TASKS):
        level = c.m["tasks"][task]
        if level == "no":
            index = 5
        else:
            index = work.AI_TASK_LEVELS.index(level)
            if c.rng.random() < 0.12:  # people are not perfectly consistent
                index = max(0, min(4, index + c.rng.choice((-1, 1))))
        out[row] = c.option(index)
    return out


# --------------------------------------------------------------------------- #
# Rating grids
# --------------------------------------------------------------------------- #

def _rate(c: _Context, score: float, agree_scale: bool) -> int:
    """Continuous score on 0..4 -> option index, applying the persona's rating habit."""
    habit = c.p.style.get("scale_habit", "none")
    if habit == "tends to agree" and agree_scale:
        score += 0.35
    elif habit == "prefers the middle":
        score = 2 + (score - 2) * 0.5
    elif habit == "uses the extremes":
        score = 2 + (score - 2) * 1.5
    score += c.rng.gauss(0, 0.45)
    return int(round(max(0.0, min(4.0, score))))


def _dont_know(c: _Context, extra: float = 0.0) -> bool:
    base = 0.06 if c.p.style["engagement"] == "rushed" else 0.03
    return c.rng.random() < base + extra


def _effects(c: _Context):
    ai, tasks = c.p.ai, c.m["tasks"]
    base = 0.9 + (ai["satisfaction_1_10"] - 1) / 9 * 2.6
    hours = ai["hours_saved_per_week"]
    analysis_busy = tasks["reporting"] in BUSY or tasks["audience_research"] in BUSY
    scores = [
        base + (0.5 if hours >= 3 else 0.2 if hours >= 1 else -0.5),
        base - 0.3 + (0.4 if tasks["segmentation"] in BUSY or tasks["audience_research"] in BUSY else -0.1),
        base + 0.35 + (0.2 if tasks["copywriting"] in BUSY else 0),
        base - 0.5 + (0.6 if analysis_busy else 0),
        base - 0.4 + (ai["trust_1_5"] - 3) * 0.3 - (0.3 if ai["attitude"] == "skeptic" else 0),
    ]
    dont_know_extra = [0, 0, 0, 0.12 if tasks["reporting"] in ("no", "never") else 0, 0]
    out = {}
    for row, score, extra in zip(c.q.rows, scores, dont_know_extra):
        out[row] = c.option(5 if _dont_know(c, extra) else _rate(c, score, agree_scale=True))
    return out


def _barriers(c: _Context):
    ai, m = c.p.ai, c.m
    concerns = {CONCERN_KEYS.get(x) for x in ai["concerns"]}
    base = {"enthusiast": 0.7, "pragmatist": 1.2, "cautious": 1.9, "skeptic": 2.2}[ai["attitude"]]
    if not c.uses_ai():
        base += 0.3
    policy = ai["employer_policy"] or ""
    scores = [
        base + (1.2 if concerns & {"accuracy", "misinfo"} else 0) + (3 - ai["trust_1_5"]) * 0.3,
        base + (1.2 if "privacy" in concerns else 0) + (0.3 if "approved" in policy or "discouraged" in policy else 0),
        base + (1.1 if concerns & {"copyright", "ai_act", "liability"} else 0),
        base + (1.2 if "bland" in concerns else 0) + (0.2 if c.p.profession_key in ("content_writer", "pr_comms") else 0),
        base - 0.6 + (1.2 if "bias" in concerns else 0),
        base + 0.1 + (1.0 if "policy" in concerns else 0) + (0.4 if m["ai_training"] != "yes" else 0)
        - (0.4 if ai["skill_level"] in ("advanced", "expert") else 0) + (0.5 if not c.uses_ai() else 0),
        base - 0.2 + (1.1 if "cost" in concerns else 0) + (0.3 if m["setting"] in ("own_business", "freelance") else 0),
    ]
    dont_know_extra = [0, 0, 0.03, 0, 0.12, 0, 0.03]
    out = {}
    for row, score, extra in zip(c.q.rows, scores, dont_know_extra):
        out[row] = c.option(5 if _dont_know(c, extra) else _rate(c, score, agree_scale=False))
    return out


# --------------------------------------------------------------------------- #
# Practices, training, open answer
# --------------------------------------------------------------------------- #

PRACTICES = ["human_review", "no_confidential_data", "fact_check", "approval", "training_guidelines", "disclosure",
             "none", "not_applicable"]


def _practices(c: _Context):
    practices = c.m["risk_practices"]
    if not c.uses_ai():
        practices = ["not_applicable"]
    elif practices == ["not_applicable"]:  # the persona does not use AI, but said "yes" to AI use
        practices = ["human_review", "none"]
    return [c.option(PRACTICES.index(x)) for x in PRACTICES if x in practices]


def _training(c: _Context):
    return c.option({"yes": 0, "planned": 1, "no": 2}[c.m["ai_training"]])


TASK_WORDS = {
    "EN": dict(audience_research="audience research", strategy="campaign planning", segmentation="personalisation",
               copywriting="posts and ad copy", visuals="visuals", ads="ad campaigns", community="replies to customers",
               reporting="reports"),
    "PL": dict(audience_research="analizie odbiorców", strategy="planowaniu kampanii", segmentation="personalizacji",
               copywriting="pisaniu postów i tekstów reklamowych", visuals="grafikach", ads="kampaniach reklamowych",
               community="odpowiedziach dla klientów", reporting="raportach"),
    "RU": dict(audience_research="анализе аудитории", strategy="планировании кампаний", segmentation="персонализации",
               copywriting="текстах для постов и рекламы", visuals="визуалах", ads="рекламных кампаниях",
               community="ответах клиентам", reporting="отчётах"),
}
CONCERN_WORDS = {
    "accuracy": {"EN": "it makes things up and sounds very sure about it",
                 "PL": "zmyśla fakty i brzmi przy tym bardzo pewnie", "RU": "он выдумывает факты и звучит очень уверенно"},
    "privacy": {"EN": "people paste client data into it without thinking",
                "PL": "ludzie wklejają dane klientów bez zastanowienia",
                "RU": "люди вставляют туда данные клиентов, не задумываясь"},
    "copyright": {"EN": "nobody really knows who owns the generated images",
                  "PL": "nie wiadomo, do kogo należą prawa do wygenerowanych grafik",
                  "RU": "непонятно, кому принадлежат права на сгенерированные картинки"},
    "bland": {"EN": "everything starts to sound the same, that generic AI tone",
              "PL": "wszystko zaczyna brzmieć tak samo, typowy styl AI",
              "RU": "всё начинает звучать одинаково, типичный ИИ-стиль"},
    "job": {"EN": "clients think junior work can now be had for free",
            "PL": "klienci myślą, że pracę juniora można teraz mieć za darmo",
            "RU": "клиенты думают, что работу джуниора теперь можно получить бесплатно"},
    "bias": {"EN": "the generated images are full of stereotypes", "PL": "wygenerowane obrazy są pełne stereotypów",
             "RU": "в сгенерированных картинках полно стереотипов"},
    "cost": {"EN": "the subscriptions keep getting more expensive", "PL": "abonamenty ciągle drożeją",
             "RU": "подписки постоянно дорожают"},
    "policy": {"EN": "there are no clear rules at work", "PL": "w pracy nie ma jasnych zasad",
               "RU": "на работе нет чётких правил"},
    "ai_act": {"EN": "nobody knows what the AI Act means for us in practice",
               "PL": "nikt nie wie, co AI Act oznacza dla nas w praktyce",
               "RU": "никто толком не знает, что AI Act значит для нас на практике"},
    "misinfo": {"EN": "fake content is getting harder to spot", "PL": "coraz trudniej odróżnić fałszywe treści",
                "RU": "фейковый контент всё сложнее отличить"},
    "deskilling": {"EN": "juniors stop learning to write themselves", "PL": "juniorzy przestają uczyć się pisać sami",
                   "RU": "джуниоры перестают учиться писать сами"},
    "pay": {"EN": "clients use AI as an argument to pay less", "PL": "klienci używają AI jako argumentu, żeby płacić mniej",
            "RU": "клиенты используют ИИ как повод платить меньше"},
    "dependence": {"EN": "we depend on a few big US companies", "PL": "jesteśmy zależni od kilku dużych firm z USA",
                   "RU": "мы зависим от нескольких крупных американских компаний"},
    "env": {"EN": "it uses a huge amount of energy", "PL": "zużywa ogromne ilości energii",
            "RU": "он тратит огромное количество энергии"},
}
NON_USE_WORDS = {
    "does not trust AI output for client work": {
        "EN": "I don't trust it for client work", "PL": "nie ufam temu przy pracy dla klientów",
        "RU": "не доверяю ему в работе для клиентов"},
    "prefers to write and design everything personally": {
        "EN": "I prefer to write everything myself", "PL": "wolę pisać wszystko sam(a)", "RU": "предпочитаю всё писать сам(а)"},
    "the employer does not allow AI tools": {
        "EN": "my employer doesn't allow it", "PL": "pracodawca na to nie pozwala", "RU": "работодатель это не разрешает"},
    "has not found the time to learn it": {
        "EN": "no time to learn it yet", "PL": "nie miałem/am jeszcze czasu się tego nauczyć",
        "RU": "пока не было времени разобраться"},
    "does not see the need in a business this small": {
        "EN": "not needed in a business this small", "PL": "w tak małej firmie nie jest mi to potrzebne",
        "RU": "в таком маленьком бизнесе это не нужно"},
    "worried about copyright and data protection": {
        "EN": "worried about copyright and data", "PL": "obawiam się o prawa autorskie i dane",
        "RU": "беспокоюсь об авторских правах и данных"},
}
OPEN_TEMPLATES = {
    "benefit": {
        "EN": ["Saves time on {task}.", "Faster first drafts for {task}, I still rewrite most of it.",
               "Speed. {tool} gives me a starting point for {task} and I edit from there, saves maybe {hours}h a week.",
               "More ideas in less time, especially when many versions of {task} are needed."],
        "PL": ["Oszczędność czasu przy {task}.", "Szybsze pierwsze wersje przy {task}, ale i tak dużo poprawiam.",
               "Szybkość. {tool} daje mi punkt wyjścia przy {task}, oszczędzam może {hours} godz. tygodniowo.",
               "Więcej pomysłów w krótszym czasie, zwłaszcza gdy potrzeba wielu wersji."],
        "RU": ["Экономия времени на {task}.", "Быстрее появляются черновики, но я всё равно многое переписываю.",
               "Скорость. {tool} даёт отправную точку, дальше редактирую сам(а), экономлю часа {hours} в неделю.",
               "Больше идей за меньшее время, особенно когда нужно много вариантов."],
    },
    "problem": {
        "EN": ["Problem: {concern}.", "My main issue is that {concern}.",
               "{concern_cap}. Everything has to be checked before it goes out."],
        "PL": ["Problem: {concern}.", "Największy problem to to, że {concern}.",
               "{concern_cap}. Wszystko trzeba sprawdzać przed publikacją."],
        "RU": ["Проблема: {concern}.", "Главная проблема в том, что {concern}.",
               "{concern_cap}. Всё приходится проверять перед публикацией."],
    },
    "condition": {
        "EN": ["A person always checks the final text.", "Never put client data into these tools.",
               "Fine as long as someone who knows the brand reviews everything and we are honest with clients about it.",
               "Clear rules in the team: what data we can use, who approves, when we say that AI was used."],
        "PL": ["Człowiek zawsze sprawdza finalny tekst.", "Nigdy nie wklejać danych klientów do tych narzędzi.",
               "OK, dopóki ktoś, kto zna markę, wszystko sprawdza i jesteśmy uczciwi wobec klientów.",
               "Jasne zasady w zespole: jakie dane wolno używać, kto zatwierdza, kiedy informujemy o użyciu AI."],
        "RU": ["Финальный текст всегда проверяет человек.", "Никогда не вводить данные клиентов в эти инструменты.",
               "Нормально, пока кто-то, кто знает бренд, всё проверяет и мы честны с клиентами.",
               "Чёткие правила в команде: какие данные можно использовать, кто утверждает, когда сообщаем об ИИ."],
    },
}


def _open_view(c: _Context):
    p, ai, rng = c.p, c.p.ai, c.rng
    if c.allow_skip and rng.random() < 0.35 + p.style.get("skip_optional_prob", 0.2):
        return None  # most respondents leave an optional open question at the end empty
    concern_key = next((CONCERN_KEYS.get(x) for x in ai["concerns"] if CONCERN_KEYS.get(x) in CONCERN_WORDS),
                       "accuracy")
    concern = c.text(CONCERN_WORDS[concern_key])
    if not c.uses_ai():
        reason = c.text(NON_USE_WORDS.get(ai.get("non_use_reason", ""), NON_USE_WORDS[work.AI_NON_USE_REASONS[0]]))
        text = {"EN": "I don't use AI, {r}. Also {c}.", "PL": "Nie korzystam z AI, {r}. Poza tym {c}.",
                "RU": "Я не использую ИИ, {r}. К тому же {c}."}
        return c.text(text).format(r=reason, c=concern)
    kind = {"enthusiast": "benefit", "skeptic": "problem", "cautious": "condition"}.get(ai["attitude"]) \
        or rng.choice(["benefit", "problem", "condition"])
    busy = [t for t in work.MARKETING_TASKS if c.m["tasks"][t] in BUSY] or ["copywriting"]
    slots = dict(task=c.text(TASK_WORDS)[rng.choice(busy)], tool=ai["primary_tool"],
                 hours=f"{max(1, ai['hours_saved_per_week']):g}".replace(".", "." if c.lang == "EN" else ","),
                 concern=concern,
                 concern_cap=concern[0].upper() + concern[1:])
    templates = c.text(OPEN_TEMPLATES[kind])
    verbosity = p.style.get("verbosity", "moderate")
    if verbosity == "terse":
        text = templates[0 if rng.random() < 0.6 else 1]
    else:
        text = rng.choice(templates[1:])
    if verbosity == "elaborate" and kind == "benefit":
        text += " " + rng.choice(c.text(OPEN_TEMPLATES["problem"]))
    return text.format(**slots)


HANDLERS = {
    "consent": _consent, "did_marketing": _did_marketing, "work_country": _work_country,
    "marketing_setting": _setting, "marketing_years": _years, "org_size": _org_size,
    "ai_use": _ai_use, "ai_frequency": _ai_frequency, "ai_tool_types": _tool_types, "ai_task_use": _task_use,
    "ai_effects": _effects, "ai_barriers": _barriers, "ai_risk_practices": _practices, "ai_training": _training,
    "ai_open_view": _open_view,
}
# Expected (number of options, number of rows) per topic; other shapes fall back to the generic heuristics.
SHAPES = {
    "consent": (2, 0), "did_marketing": (2, 0), "work_country": (0, 0), "marketing_setting": (5, 0),
    "marketing_years": (5, 0), "org_size": (6, 0), "ai_use": (2, 0), "ai_frequency": (5, 0), "ai_tool_types": (6, 0),
    "ai_task_use": (6, 8), "ai_effects": (6, 5), "ai_barriers": (6, 7), "ai_risk_practices": (8, 0),
    "ai_training": (3, 0), "ai_open_view": (0, 0),
}
