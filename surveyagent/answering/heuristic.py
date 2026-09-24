"""Offline answering without an LLM.

Choice questions are matched against the persona profile (age, country, company
size, tools, frequency...), rating scales follow the persona's attitude and
survey habits, and open questions get short template answers. The result is
consistent and valid, but open answers are much less natural than in LLM mode.
It is also the fallback when an LLM answer is invalid for some question.
"""

from __future__ import annotations

import random
import re
from datetime import date

from ..personas.generator import Persona
from ..questionnaire import CHOICE_TYPES, GRID_TYPES, SCALE_TYPES, TEXT_TYPES, Question, Questionnaire
from . import topics

NEGATIVE_WORDS = ("worr", "concern", "risk", "threat", "replace", "afraid", "fear", "danger", "harm", "anxious",
                  "overhyped", "overrated", "mistrust", "distrust", "job loss", "lose my job", "stress", "difficult",
                  "frustrat", "inaccura", "unreliable", "ban", "problem", "negative")

POLARITY = [
    ("strongly disagree", -2), ("completely disagree", -2), ("strongly agree", 2), ("completely agree", 2),
    ("somewhat disagree", -1), ("somewhat agree", 1), ("disagree", -1), ("agree", 1),
    ("very dissatisfied", -2), ("very satisfied", 2), ("dissatisfied", -1), ("unsatisfied", -1), ("satisfied", 1),
    ("very unlikely", -2), ("very likely", 2), ("extremely likely", 2), ("unlikely", -1), ("likely", 1),
    ("not at all", -2), ("never", -2), ("rarely", -1), ("seldom", -1), ("sometimes", 0), ("occasionally", 0),
    ("often", 1), ("always", 2), ("very negative", -2), ("very positive", 2), ("negative", -1), ("positive", 1),
    ("much worse", -2), ("much better", 2), ("worse", -1), ("better", 1), ("the same", 0),
    ("significantly decrease", -2), ("significantly increase", 2), ("decrease", -1), ("increase", 1),
    ("very poor", -2), ("excellent", 2), ("poor", -1), ("good", 1), ("not important", -2), ("very important", 2),
    ("slightly", -1), ("moderately", 0), ("extremely", 2),
    ("neither", 0), ("neutral", 0), ("undecided", 0), ("mixed", 0), ("somewhat", 0),
]
NON_ANSWERS = ("prefer not", "don't know", "do not know", "not sure", "n/a", "not applicable", "rather not say")

FREQ_WORDS = {
    "several times a day": ["several times a day", "multiple times a day", "many times a day", "constantly", "hourly"],
    "daily": ["daily", "every day", "once a day", "every working day"],
    "a few times a week": ["few times a week", "several times a week", "2-3 times a week", "weekly", "a week"],
    "about once a week": ["once a week", "weekly", "a week"],
    "a few times a month": ["few times a month", "monthly", "a month", "rarely", "occasionally"],
}
COUNTRY_ALIASES = {
    "United Kingdom": ["uk", "united kingdom", "great britain", "britain", "england", "scotland", "wales"],
    "Netherlands": ["netherlands", "the netherlands", "holland"],
    "Czechia": ["czechia", "czech republic"],
    "Germany": ["germany", "deutschland"],
}
EDU_WORDS = [("phd", ["phd", "doctor", "doctorate"]), ("master", ["master", "msc", "ma ", "mba", "postgraduate"]),
             ("bachelor", ["bachelor", "bsc", "ba ", "undergraduate", "university degree"]),
             ("vocational", ["vocational", "apprentice", "trade", "technical"]),
             ("secondary", ["secondary", "high school", "a-level", "baccalaur", "abitur"])]
STOPWORDS = {"the", "and", "for", "with", "your", "you", "are", "what", "which", "how", "that", "this", "use", "using",
             "other", "from", "into", "about", "have", "does", "work", "most", "more", "than", "any", "all"}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9+#]+", text.lower()) if len(t) > 2 and t not in STOPWORDS}


def _numbers(text: str) -> list[float]:
    text = text.replace(",", "").replace("’", "").replace("'", "")
    out = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(k\b|000\b)?", text.lower()):
        value = float(m.group(1))
        if m.group(2) == "k":
            value *= 1000
        out.append(value)
    return out


def _range_of(option: str) -> tuple[float, float] | None:
    """'25-34' -> (25, 34); '55+' / '55 or older' -> (55, inf); 'Under 25' -> (-inf, 24.99)."""
    low = option.lower()
    nums = _numbers(low)
    if not nums:
        if "just me" in low or "only me" in low or "self-employed" in low:
            return (1, 1)
        return None
    if len(nums) >= 2:
        return (nums[0], nums[1])
    n = nums[0]
    if re.search(r"(under|less than|below|fewer than|<|up to)", low):
        return (float("-inf"), n - 1e-9 if "up to" not in low else n)
    if re.search(r"(\+|or more|and more|and above|and over|over|more than|at least|older|>)", low):
        return (n, float("inf"))
    return (n, n)


def _pick_range(options: list[str], value: float) -> str | None:
    best = None
    for opt in options:
        r = _range_of(opt)
        if r and r[0] <= value <= r[1] + 0.999:
            return opt
        if r and best is None and value < r[0]:
            best = opt
    return best


def _polarity(option: str) -> int | None:
    low = option.lower()
    for phrase, value in POLARITY:
        if phrase in low:
            return value
    return None


def _ordered(options: list[str]) -> list[str] | None:
    """If options form an ordinal scale (agree..disagree etc.), return them from negative to positive."""
    real = [o for o in options if not any(n in o.lower() for n in NON_ANSWERS)]
    scored = [(o, _polarity(o)) for o in real]
    if len(real) < 3 or sum(p is not None for _, p in scored) < 0.6 * len(real):
        numeric = [o for o in real if re.fullmatch(r"\s*\d+\s*", o)]
        if len(numeric) == len(real) and len(real) >= 3:
            return sorted(real, key=lambda o: int(o))
        return None
    # keep original order for unknown ones, orient by the known polarities
    known = [p for _, p in scored if p is not None]
    if known[0] > known[-1]:
        real = list(reversed(real))
    return real


class HeuristicAnswerer:
    def __init__(self, questionnaire: Questionnaire, seed: int = 0):
        self.questionnaire = questionnaire
        self.seed = seed

    def answer(self, persona: Persona) -> dict:
        """Answers along the form's path; questions the logic skips are None."""
        rng = random.Random(f"{self.seed}:{persona.id}")
        answers: dict = {}
        for q in self.questionnaire.iter_path(answers):
            answers[q.id] = self.answer_question(q, persona, rng, context=answers)
        return {q.id: answers.get(q.id) for q in self.questionnaire.questions}

    # ------------------------------------------------------------------ #
    def answer_question(self, q: Question, p: Persona, rng: random.Random, allow_skip: bool = True,
                        context: dict | None = None):
        """`context` holds the answers given so far (used by topic-based questions)."""
        skip = p.style.get("skip_optional_prob", 0.2)
        if q.type == "email":
            return p.email
        if q.topic:
            value = topics.answer(q, p, rng, context or {}, self.questionnaire, allow_skip)
            if value is not topics.UNKNOWN:
                return value
        if not q.required and allow_skip:
            if q.type in TEXT_TYPES and rng.random() < skip:
                return None
            if q.type not in TEXT_TYPES and rng.random() < skip / 6:
                return None
        if q.type in TEXT_TYPES:
            return self._text(q, p, rng) or (None if not q.required else "-")
        if q.type in CHOICE_TYPES:
            return self._choice(q, p, rng)
        if q.type == "checkboxes":
            return self._checkboxes(q, p, rng)
        if q.type in SCALE_TYPES:
            return self._scale_value(q.scale_values, self._sentiment(q.title + " " + " ".join(q.scale_labels), p),
                                     p, rng)
        if q.type in GRID_TYPES:
            ordered = _ordered(q.options) or q.options
            out = {}
            for row in q.rows:
                target = self._sentiment(f"{q.title} {row}", p)
                col = self._scale_value(ordered, target, p, rng)
                out[row] = [col] if q.type == "checkbox_grid" else col
            return out
        if q.type == "date":
            if "birth" in q.title.lower():
                return p.birth_date
            return date.today().isoformat()
        if q.type == "time":
            return f"{rng.randint(8, 17):02d}:{rng.choice(['00', '15', '30', '45'])}"
        return None

    # -- sentiment / scales --------------------------------------------- #
    def _sentiment(self, text: str, p: Persona) -> float:
        """Target position on a negative(0)..positive(1) scale for this question."""
        low = text.lower()
        ai = p.ai
        if "satisf" in low:
            base = (ai["satisfaction_1_10"] - 1) / 9
        elif "trust" in low or "reliab" in low or "accura" in low:
            base = (ai["trust_1_5"] - 1) / 4
        elif "recommend" in low:
            base = (ai["satisfaction_1_10"] - 1) / 9 - 0.05
        elif "productiv" in low or "save" in low or "time" in low or "efficien" in low:
            base = min(1.0, 0.35 + ai["hours_saved_per_week"] / 10)
        elif "skill" in low or "confident" in low or "proficien" in low or "familiar" in low:
            base = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.75, "expert": 0.95}[ai["skill_level"]]
        elif re.search(r"rules|polic|guideline", low) and "employer" in low:
            policy = ai["employer_policy"] or ""
            base = 0.5 if not policy else 0.2 if "no clear" in policy else 0.4 if "discouraged" in policy else 0.8
        elif "often" in low or "frequen" in low:
            base = {"several times a day": 1.0, "daily": 0.8, "a few times a week": 0.6, "about once a week": 0.4,
                    "a few times a month": 0.2}.get(ai["frequency"], 0.0)
        else:
            base = {"enthusiast": 0.85, "pragmatist": 0.65, "cautious": 0.45, "skeptic": 0.25}[ai["attitude"]]
            if any(w in low for w in NEGATIVE_WORDS):
                base = 1 - base
                if any(word in " ".join(ai["concerns"]) for word in ("job", "privacy", "hallucination")
                       if word in low):
                    base = min(1.0, base + 0.15)
        return max(0.0, min(1.0, base))

    def _scale_value(self, values: list, target: float, p: Persona, rng: random.Random):
        habit = p.style.get("scale_habit", "none")
        if habit == "tends to agree":
            target += 0.1
        elif habit == "prefers the middle":
            target = 0.5 + (target - 0.5) * 0.5
        elif habit == "uses the extremes":
            target = 0.5 + (target - 0.5) * 1.6
        target += rng.gauss(0, 0.08)
        target = max(0.0, min(1.0, target))
        return values[round(target * (len(values) - 1))]

    # -- choices -------------------------------------------------------- #
    def _choice(self, q: Question, p: Persona, rng: random.Random):
        title = f"{q.title} {q.description}".lower()
        opts = q.options
        picked = self._match_known(q, title, p)
        if picked is not None:
            return picked
        ordered = _ordered(opts)
        if ordered:
            return self._scale_value(ordered, self._sentiment(title, p), p, rng)
        yes = next((o for o in opts if o.strip().lower() in ("yes", "yes.", "ja", "oui", "sí", "si")), None)
        no = next((o for o in opts if o.strip().lower() in ("no", "no.", "nein", "non")), None)
        if yes and no:
            return yes if self._yes_no(title, p, rng) else no
        scores = self._overlap_scores(opts, p)
        best = max(scores.values()) if scores else 0
        if best > 0:
            return rng.choice([o for o, s in scores.items() if s == best])
        real = [o for o in opts if not any(n in o.lower() for n in NON_ANSWERS)] or opts
        return rng.choice(real)

    def _match_known(self, q: Question, title: str, p: Persona):
        ai = p.ai
        opts = q.options
        if re.search(r"\bage\b|how old|age group|age range|year of birth", title):
            return _pick_range(opts, p.age)
        if "gender" in title or re.search(r"\bsex\b", title):
            words = {"female": ("female", "woman", "women"), "male": ("male", "man", "men"),
                     "non-binary": ("non-binary", "nonbinary", "non binary", "diverse", "other")}[p.gender]
            for o in opts:
                low = o.lower()
                if p.gender == "male" and ("female" in low or "woman" in low):
                    continue
                if any(re.search(rf"\b{re.escape(w)}\b", low) for w in words):
                    return o
            return None
        if "country" in title or re.search(r"where (do|are) you (live|based|located|reside)", title):
            aliases = COUNTRY_ALIASES.get(p.country, [p.country.lower()])
            for o in opts:
                if o.lower().strip() in aliases or p.country.lower() in o.lower():
                    return o
            if "europe" in " ".join(opts).lower():
                return next(o for o in opts if "europe" in o.lower())
            return {"other": p.country} if q.has_other else None
        if "education" in title or "degree" in title or "qualification" in title:
            level = next((k for k in ("phd", "master", "bachelor", "vocational", "secondary")
                          if k in p.education.lower() or (k == "phd" and "doctor" in p.education.lower())), "secondary")
            if "medical degree" in p.education.lower():
                level = "master"
            for key, words in EDU_WORDS:
                if key == level:
                    for o in opts:
                        if any(w in o.lower() + " " for w in words):
                            return o
            return None
        if re.search(r"employees|company size|organi[sz]ation size|size of (your|the) (company|organi)|how many people", title):
            lo, hi = {"1 (just me)": (1, 1), "2–10": (2, 10), "11–50": (11, 50), "51–250": (51, 250),
                      "251–1,000": (251, 1000), "1,001–5,000": (1001, 5000), "5,000+": (5001, 20000)}[p.company_size]
            return _pick_range(opts, (lo + hi) / 2 if hi < 20000 else 8000)
        if "experience" in title and "year" in title:
            if re.search(r"\bai\b|artificial|chatgpt|tools", title):
                return _pick_range(opts, 2026 - (ai["since_year"] or 2026) + 0.5)
            return _pick_range(opts, p.years_experience)
        if re.search(r"income|salary|earn", title):
            if not p.style.get("discloses_income", True):
                no_say = next((o for o in opts if "prefer not" in o.lower() or "rather not" in o.lower()), None)
                if no_say:
                    return no_say
            return _pick_range(opts, p.income_eur)
        if re.search(r"(time|hours).*(sav|free)|sav.*(time|hours)", title):
            hours = ai["hours_saved_per_week"]
            if hours == 0:
                zero = next((o for o in opts if re.search(r"\b(none|no time|nothing)\b", o.lower())), None)
                if zero:
                    return zero
            return _pick_range(opts, hours)
        if re.search(r"employer|company|organi[sz]ation", title) and re.search(r"allow|permit|polic|rules", title):
            policy = ai["employer_policy"]
            lows = {o: o.lower() for o in opts}
            if policy is None:
                return next((o for o, l in lows.items() if "not applicable" in l or "self-employed" in l), None)
            if "no clear policy" in policy:
                return next((o for o, l in lows.items() if "no clear" in l or "no policy" in l or "not sure" in l), None)
            wanted = "no" if "discouraged" in policy else "yes"
            return next((o for o, l in lows.items() if l.strip(" .") == wanted), None)
        if re.search(r"how often|how frequently|frequency", title):
            for o in opts:
                if any(w in o.lower() for w in FREQ_WORDS.get(ai["frequency"], ["never"])):
                    return o
            return None
        if re.search(r"how long have you|since when|when did you (start|begin)", title):
            months = (2026 - (ai["since_year"] or 2026)) * 12 + 6
            for o in opts:
                r = _range_of(o)
                if r:
                    scale = 1 if "month" in o.lower() else 12
                    if r[0] * scale <= months <= (r[1] + 0.999) * scale:
                        return o
            return None
        if "remote" in " ".join(opts).lower() and ("where" in title or "work" in title):
            for o in opts:
                if p.work_mode in o.lower():
                    return o
        if re.search(r"main|primary|most often|favou?rite", title) and re.search(r"tool|assistant|app", title):
            for o in opts:
                if o.lower() in p.ai["primary_tool"].lower() or p.ai["primary_tool"].lower() in o.lower():
                    return o
        if re.search(r"industry|sector", title):
            scores = {o: len(_tokens(o) & _tokens(p.industry + " " + p.occupation)) for o in opts}
            best = max(scores.values())
            if best:
                return max(scores, key=scores.get)
            return {"other": p.industry} if q.has_other else None
        if re.search(r"role|position|job|occupation|profession", title):
            scores = {o: len(_tokens(o) & _tokens(p.job_title + " " + p.occupation)) for o in opts}
            best = max(scores.values())
            if best:
                return max(scores, key=scores.get)
            return None
        return None

    def _yes_no(self, title: str, p: Persona, rng: random.Random) -> bool:
        ai = p.ai
        if re.search(r"use[ds]? (any )?(ai|artificial intelligence|genai|generative)", title):
            return p.uses_ai
        if re.search(r"(employer|company|organi[sz]ation).*(provide|pay|licen)", title):
            return "employer pays" in ai["access"]
        if re.search(r"pay .*(yourself|personally|own)", title):
            return "pays personally" in ai["access"]
        if "policy" in title or "guideline" in title:
            return bool(ai["employer_policy"]) and "no clear policy" not in ai["employer_policy"]
        if "training" in title:
            return "no training" not in ai["training"] and "self-taught" not in ai["training"]
        positive = {"enthusiast": 0.85, "pragmatist": 0.65, "cautious": 0.4, "skeptic": 0.25}[ai["attitude"]]
        if any(w in title for w in NEGATIVE_WORDS):
            positive = 1 - positive
        return rng.random() < positive

    def _profile_text(self, p: Persona) -> str:
        ai = p.ai
        return " ".join([p.job_title, p.occupation, p.industry, " ".join(ai["tools"]), " ".join(ai["use_cases"]),
                         " ".join(ai["concerns"]), ai["good_experience"], ai["access"]])

    def _overlap_scores(self, opts: list[str], p: Persona) -> dict[str, int]:
        profile = _tokens(self._profile_text(p))
        return {o: len(_tokens(o) & profile) for o in opts}

    def _checkboxes(self, q: Question, p: Persona, rng: random.Random):
        title = f"{q.title} {q.description}".lower()
        ai = p.ai
        chosen: list = []
        if re.search(r"tool|assistant|app|product|model|service", title):
            tools_low = [t.lower() for t in ai["tools"]]
            for o in q.options:
                ol = o.lower()
                if any(ol in t or t in ol or (len(ol) > 3 and ol.split()[0] in t) for t in tools_low):
                    chosen.append(o)
            extras = [t for t in ai["tools"] if not any(t.lower() in c.lower() or c.lower() in t.lower() for c in chosen)]
            if extras and q.has_other and rng.random() < 0.6:
                chosen.append({"other": extras[0]})
        elif re.search(r"concern|worr|risk|challenge|barrier|problem|downside|obstacle", title):
            source = _tokens(" ".join(ai["concerns"]) + " " + ai["bad_experience"] + " " + ai["pet_peeve"])
            chosen = [o for o in q.options if len(_tokens(o) & source) >= 1]
        else:
            source = _tokens(" ".join(ai["use_cases"]) + " " + ai["good_experience"] + " " + p.job_title)
            chosen = [o for o in q.options if len(_tokens(o) & source) >= 1]
        chosen = [c for c in chosen if isinstance(c, dict) or not any(n in c.lower() for n in NON_ANSWERS)]
        limit = {"terse": 3, "moderate": 4, "elaborate": 6}[p.style.get("verbosity", "moderate")]
        chosen = chosen[:limit]
        if not chosen:
            real = [o for o in q.options if not any(n in o.lower() for n in NON_ANSWERS + ("none",))] or q.options
            chosen = rng.sample(real, min(len(real), rng.randint(1, 2)))
        return chosen

    # -- open text ------------------------------------------------------ #
    def _text(self, q: Question, p: Persona, rng: random.Random) -> str | None:
        title = f"{q.title} {q.description}".lower()
        ai = p.ai
        if not p.uses_ai and not re.search(r"e-?mail|name|\bage\b|how old|country|city|town|job title|industry|sector",
                                           title):
            return f"I don't use AI at work, {ai['non_use_reason']}."
        verbose = p.style.get("verbosity", "moderate")
        short = len(q.title) < 70  # factual one-liners like "Your job title?"
        if re.search(r"e-?mail", title):
            return p.email
        if re.search(r"(first|your) name|full name|\bname\b", title) and "company" not in title:
            return p.first_name if "first" in title else p.full_name
        if short and re.search(r"\bage\b|how old", title):
            return str(p.age)
        if short and "country" in title:
            return p.country
        if short and ("city" in title or "town" in title):
            return p.city
        if short and re.search(r"job title|your (current )?(role|position|occupation|profession)|what do you do", title):
            return p.job_title
        if short and ("industry" in title or "sector" in title):
            return p.industry
        if re.search(r"company name|employer name|organi[sz]ation name", title):
            return None if not q.required else "prefer not to say"
        if re.search(r"phone|telephone|mobile number", title):
            return None if not q.required else "-"
        if re.search(r"concern|worr|risk|challenge|problem|dislike|frustrat|downside|negative|bad experience", title):
            parts = {"terse": [ai["concerns"][0]],
                     "moderate": [ai["concerns"][0], f"once {ai['bad_experience']}"],
                     "elaborate": [ai["concerns"][0], f"once {ai['bad_experience']}", f"also {ai['pet_peeve']}"]}[verbose]
            return ". ".join(s[0].upper() + s[1:] for s in parts) + "."
        if re.search(r"benefit|advantage|like (most|best)|positive|value|helpful|example|success", title):
            if verbose == "terse":
                return f"saves time, about {ai['hours_saved_per_week']:g}h a week"
            return (f"It saves me roughly {ai['hours_saved_per_week']:g} hours a week. "
                    f"Best example: {ai['good_experience']}.")
        if re.search(r"improve|wish|feature|missing|suggest|change", title):
            wishes = ["Fewer made-up facts and clear sources", "Better integration with the tools we already use",
                      f"Better quality in {p.native_languages[0]}", "Clear rules from my employer",
                      "Cheaper licences", "Remembering context between sessions"]
            return rng.choice(wishes) + ("" if verbose == "terse" else ".")
        if re.search(r"future|next year|expect|predict|in \d+ years", title):
            return ai["outlook"][0].upper() + ai["outlook"][1:] + "."
        if re.search(r"anything else|comments?\b|feedback|\badd\b", title):
            return None if rng.random() < 0.6 else rng.choice(["No, thanks", "Nothing to add", "Interesting survey!"])
        if re.search(r"which (ai )?tools|what (ai )?tools", title):
            return ", ".join(ai["tools"])
        if re.search(r"\buse\b|\busing\b|tasks|use cases|what for|purpose", title):
            uses = ai["use_cases"][: {"terse": 2, "moderate": 3, "elaborate": 4}[verbose]]
            text = ", ".join(uses)
            return text if verbose == "terse" else f"Mostly {text}."
        if ai["attitude"] in ("enthusiast", "pragmatist"):
            return f"Overall positive. I use {ai['primary_tool']} {ai['frequency']} and it helps with {ai['use_cases'][0]}."
        return f"Mixed feelings. Useful for {ai['use_cases'][0]}, but {ai['concerns'][0]} is a real issue."
