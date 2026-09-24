"""Deterministic generator of diverse European personas who use AI at work."""

from __future__ import annotations

import json
import random
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import geo, work

CURRENT_YEAR = 2026
TODAY = (9, 24)  # (month, day) the ages refer to
EU_REFERENCE_SALARY = 38000

AGE_BRACKETS = [((22, 24), 8), ((25, 29), 20), ((30, 34), 20), ((35, 39), 17), ((40, 44), 13),
                ((45, 49), 9), ((50, 54), 7), ((55, 59), 4), ((60, 64), 2)]

SENIORITY_FACTOR = {"junior": 0.72, "mid": 1.0, "senior": 1.3, "lead": 1.5, "head": 1.9,
                    "freelance": 1.0, "founder": 1.0, "owner": 1.0}

FREQUENCIES = ["several times a day", "daily", "a few times a week", "about once a week",
               "a few times a month"]

POLICIES = {
    "encouraged": "official AI tools are provided and actively encouraged",
    "guidelines": "allowed, with guidelines (no confidential or personal data)",
    "approved_only": "only company-approved AI tools are allowed",
    "no_policy": "no clear policy, everyone does their own thing",
    "discouraged": "officially discouraged or blocked, uses personal tools quietly anyway",
}

SENSITIVE_INDUSTRY_WORDS = ("Bank", "Insurance", "Law firm", "legal", "Public", "ministry", "administration",
                            "government", "hospital", "clinic", "Pharma", "EU institution", "agency")

GENERAL_CHATBOTS = {"ChatGPT", "Claude", "Gemini", "Microsoft Copilot", "Mistral Le Chat", "Perplexity",
                    "DeepSeek", "internal company AI assistant", "internal government AI assistant"}

# Translation/grammar helpers are rarely someone's *main* AI tool.
SUPPORT_TOOLS = {"DeepL", "DeepL Write", "Grammarly", "Google Translate"}

GENERIC_USES = ["drafting and polishing emails", "summarising long documents", "translating texts",
                "brainstorming ideas", "preparing for meetings", "explaining things I don't know yet"]

# Professions whose "freelance" variant is really running your own practice/business.
OWN_PRACTICE = {"physician", "psychologist", "pharmacist", "architect", "lawyer", "tradesperson", "agronomist",
                "finance", "small_business"}

OWN_PRACTICE_INDUSTRY = {
    "physician": "Private practice", "psychologist": "Private practice", "pharmacist": "Pharmacy",
    "architect": "Architecture firm", "lawyer": "Law firm", "finance": "Accounting firm",
    "tradesperson": "Construction & trades", "agronomist": "Agriculture",
}

SMALL_BUSINESS_FIELD = {
    "café": "Hospitality", "bakery": "Bakery", "brewery": "Food Technology", "hotel": "Hospitality",
    "hair salon": "Hairdressing", "florist": "Floristry", "bicycle shop": "Business Administration",
    "ceramics shop": "Design", "accounting office": "Accounting", "physiotherapy": "Physiotherapy",
    "driving school": "Business Administration",
}

INDUSTRY_SIZES = {
    "Private practice": work.SIZE_PRESETS["practice"], "Pharmacy": work.SIZE_PRESETS["practice"],
    "Public hospital": work.SIZE_PRESETS["hospital"], "Private clinic": work.w("11–50:2; 51–250:3; 251–1,000:1"),
    "Care home": work.w("11–50:3; 51–250:3"), "Home care": work.w("11–50:3; 51–250:2"),
    "University": work.SIZE_PRESETS["university"], "Research institute": work.w("51–250:2; 251–1,000:3; 1,001–5,000:1"),
    "Language school": work.w("2–10:2; 11–50:4; 51–250:1"), "Primary school": work.w("11–50:4; 51–250:3"),
    "Counselling service": work.w("2–10:2; 11–50:3; 51–250:1"),
}

SMALL_BUSINESS_USES = {
    "physiotherapy": ["exercise sheets for patients", "appointment reminder texts"],
    "driving school": ["practice theory questions for students", "job ads for new instructors"],
    "hair salon": ["appointment reminder texts", "ideas for seasonal offers"],
    "accounting office": ["explaining tax changes to clients in plain language", "drafting client letters"],
    "bicycle shop": ["repair price lists", "product descriptions for the web shop"],
    "driving": [],
}

# Fields that make sense as vocational training; others are replaced by a generic apprenticeship.
VOCATIONAL_FIELDS = {
    "Office Administration", "Logistics", "Information Technology", "Electronics", "Nursing", "Carpentry",
    "Plumbing", "Electrical Installation", "Heating & Ventilation", "Hospitality", "Hospitality Management",
    "Tourism", "Crafts", "Physiotherapy", "Bakery", "Hairdressing", "Floristry", "Media Design", "Graphic Design",
    "Real Estate Management", "Network Engineering", "Food Technology", "Agricultural Science", "Agronomy",
    "Accounting", "Film Studies", "Audio Engineering", "Mechatronics",
}

TITLE_FIELD = {
    "Electrician": "Electrical Installation", "Plumber": "Plumbing", "Carpenter": "Carpentry",
    "HVAC": "Heating & Ventilation", "Solar Panel": "Electrical Installation",
}

ORG_SUFFIXES = ("firm", "agency", "school", "service", "provider", "consultancy", "organisation", "practice",
                "hospital", "clinic", "home", "institute", "newspaper", "magazine")

SMALL_BUSINESS_INDUSTRY = {
    "café": "Food & hospitality", "bakery": "Food & hospitality", "brewery": "Food & hospitality",
    "hotel": "Tourism & hospitality", "hair salon": "Personal services", "florist": "Retail",
    "bicycle shop": "Retail", "ceramics shop": "E-commerce & retail", "accounting office": "Accounting services",
    "physiotherapy": "Healthcare", "driving school": "Education & training",
}

TONES = {
    "enthusiast": ["upbeat", "enthusiastic but practical", "casual and positive"],
    "pragmatist": ["matter-of-fact", "practical, no-nonsense", "relaxed and pragmatic"],
    "cautious": ["measured and careful", "thoughtful, a bit reserved", "balanced but wary"],
    "skeptic": ["critical and dry", "sceptical, a little sarcastic", "blunt"],
}

ATTITUDE_PHRASES = {
    "enthusiast": ["Genuinely excited about it and likes trying new tools.",
                   "Would not want to work without it anymore."],
    "pragmatist": ["Sees it as a useful tool, nothing more, nothing less.",
                   "Pragmatic: uses it where it saves time and checks the results."],
    "cautious": ["Uses it carefully and double-checks almost everything.",
                 "Finds it helpful but worries about getting things wrong."],
    "skeptic": ["Uses it because it is expected, but is openly sceptical of the hype.",
                "Thinks it is overrated, though admits it saves some time."],
}


@dataclass
class Persona:
    id: str
    first_name: str
    last_name: str
    gender: str
    age: int
    birth_year: int
    birth_date: str
    country: str
    country_code: str
    city: str
    nationality: str
    background: str
    native_languages: list[str]
    other_languages: list[str]
    english_level: str
    education: str
    field_of_study: str
    occupation: str
    profession_key: str
    job_title: str
    seniority: str
    employment_type: str
    industry: str
    company_size: str
    work_mode: str
    years_experience: int
    income_eur: int
    income_band: str
    household: str
    hobbies: list[str]
    email: str
    bio: str
    ai: dict = field(default_factory=dict)
    personality: dict = field(default_factory=dict)
    style: dict = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Persona":
        return cls(**data)


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def _pick(rng: random.Random, weights: dict[str, float]) -> str:
    items = [(k, v) for k, v in weights.items() if v > 0]
    total = sum(v for _, v in items)
    x = rng.uniform(0, total)
    for k, v in items:
        x -= v
        if x <= 0:
            return k
    return items[-1][0]


def _sample(rng: random.Random, weights: dict[str, float], k: int) -> list[str]:
    """Weighted sample without replacement."""
    pool = {key: val for key, val in weights.items() if val > 0}
    out: list[str] = []
    while pool and len(out) < k:
        choice = _pick(rng, pool)
        out.append(choice)
        del pool[choice]
    return out


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.replace("ø", "o").replace("Ø", "O").replace("ł", "l")
                                 .replace("Ł", "L").replace("ß", "ss").replace("đ", "d").replace("Đ", "D")
                                 .replace("ð", "d").replace("þ", "th").replace("æ", "ae").replace("ı", "i"))
    text = text.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", text.lower())


def _article(word: str) -> str:
    first = word.split()[0] if word.split() else word
    if first.isupper() and len(first) <= 4:  # acronyms: "an HR ...", "a UX ..."
        return "an" if first[0] in "AEFHILMNORSX" else "a"
    return "an" if word[:1].lower() in "aeiou" and not word.lower().startswith(("uni", "euro", "one")) else "a"


def _industry_phrase(industry: str) -> str:
    """Lower-case an industry label but keep acronyms/brands like SaaS, IT, FinTech."""
    return " ".join(w if any(ch.isupper() for ch in w[1:]) else w.lower() for w in industry.split())


def _country_phrase(name: str) -> str:
    return f"the {name}" if name in ("Netherlands", "United Kingdom", "United States") else name


def _allocate_countries(count: int) -> list[str]:
    """Quota allocation proportional to (population x AI adoption)^0.7.

    Every mid-sized/large country gets at least one persona when count allows it,
    so the sample stays diverse; micro-states only appear through remainders.
    """
    raw = {c: (d["pop"] * d["ai"]) ** 0.7 for c, d in geo.COUNTRIES.items()}
    core = [c for c, d in geo.COUNTRIES.items() if d["pop"] >= 1.3]
    minimum = {c: 1 for c in core} if count >= 2 * len(core) else {}
    remaining = count - sum(minimum.values())
    total = sum(raw.values())
    exact = {c: remaining * raw[c] / total for c in raw}
    quota = {c: minimum.get(c, 0) + int(exact[c]) for c in raw}
    leftover = count - sum(quota.values())
    for c in sorted(raw, key=lambda c: exact[c] - int(exact[c]), reverse=True)[:leftover]:
        quota[c] += 1
    out: list[str] = []
    for c, n in quota.items():
        out.extend([c] * n)
    return out


def _title_for(prof: dict, level: str, rng: random.Random) -> str:
    titles = prof["titles"]
    order = work.TITLE_LEVELS
    idx = order.index(level) if level in order else 1
    for offset in [0, -1, 1, -2, 2, -3, 3, -4, 4]:
        j = idx + offset
        if 0 <= j < len(order) and order[j] in titles:
            return rng.choice(titles[order[j]])
    return prof["label"]


def _income_band(value: int) -> str:
    if value >= 150000:
        return "€150,000+"
    if value >= 100000:
        lo = 100000 if value < 125000 else 125000
        return f"€{lo:,}–{lo + 25000:,}"
    step = 5000 if value < 30000 else 10000
    lo = value // step * step
    return f"€{lo:,}–{lo + step:,}"


# --------------------------------------------------------------------------- #
# Generator
# --------------------------------------------------------------------------- #

class PersonaGenerator:
    def __init__(self, seed: int = 42, email_domain: str = "example.com"):
        self.rng = random.Random(seed)
        self.email_domain = email_domain
        self.prof_weights = {p["key"]: p["weight"] for p in work.PROFESSIONS}
        self.city_use: dict[tuple[str, str], int] = {}
        self.used_names: set[str] = set()
        self.used_surnames: set[tuple[str, str]] = set()
        self.used_emails: set[str] = set()

    # -- public ------------------------------------------------------------ #
    def generate(self, count: int = 100) -> list[Persona]:
        countries = _allocate_countries(count)
        self.rng.shuffle(countries)
        return [self._persona(i + 1, cc) for i, cc in enumerate(countries)]

    # -- one persona --------------------------------------------------------- #
    def _persona(self, number: int, cc: str) -> Persona:
        rng = self.rng
        country = geo.COUNTRIES[cc]

        prof_key = _pick(rng, self.prof_weights)
        self.prof_weights[prof_key] *= 0.55  # keep the mix diverse
        prof = work.PROFESSIONS_BY_KEY[prof_key]

        city, local_language, pool_key = self._city(cc)
        age = self._age(prof)
        gender = self._gender(prof)
        origin = self._origin(cc)
        personality = {t: max(1, min(5, round(rng.gauss(3, 0.9))))
                       for t in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")}

        first, last = self._name(origin, pool_key, gender, age)
        nationality, background, native, other_langs, english = self._languages(
            cc, country, city, local_language, origin, age, last)

        edu_key = self._education_level(prof, age)
        years = self._experience(prof, edu_key, age)
        employment = self._employment(prof, years)
        seniority, title = self._role(prof, employment, years, age)
        industry = self._industry(prof, cc, title, employment)
        field_of_study = self._field(prof, title, industry, edu_key)
        if prof_key == "teacher":
            title = self._teacher_title(industry, field_of_study, seniority, title)
        if prof_key == "lawyer":  # law-firm vs in-house job titles
            in_house = industry.startswith(("In-house", "Public"))
            title = {("General Counsel", False): "Partner", ("Partner", True): "General Counsel",
                     ("Associate", True): "Legal Counsel", ("Senior Associate", True): "Senior Legal Counsel",
                     ("Legal Counsel", False): "Associate", ("Senior Legal Counsel", False): "Senior Associate",
                     }.get((title, in_house), title)
        education = self._education_label(edu_key, field_of_study, title)
        size = self._company_size(prof, employment, industry)
        work_mode = self._work_mode(prof, employment)
        income = self._income(country, prof, seniority, employment)

        attitude = self._attitude(prof, age, personality)
        ai = self._ai_profile(prof, cc, native, attitude, employment, size, industry, title)
        style = self._style(personality, attitude, age, native, english, cc, origin)

        household = self._household(age)
        hobbies = _sample(rng, {h: 1 for h in work.HOBBIES}, 2)
        if cc in geo.COUNTRY_HOBBIES and rng.random() < 0.4:
            hobbies[-1] = rng.choice(geo.COUNTRY_HOBBIES[cc])

        birth_date = self._birth_date(age)
        persona = Persona(
            id=f"P{number:03d}", first_name=first, last_name=last, gender=gender, age=age,
            birth_year=int(birth_date[:4]), birth_date=birth_date,
            country=country["name"], country_code=cc, city=city, nationality=nationality,
            background=background, native_languages=native, other_languages=other_langs,
            english_level=english, education=education, field_of_study=field_of_study,
            occupation=prof["label"], profession_key=prof_key, job_title=title, seniority=seniority,
            employment_type=employment, industry=industry, company_size=size, work_mode=work_mode,
            years_experience=years, income_eur=income, income_band=_income_band(income),
            household=household, hobbies=hobbies, email=self._email(first, last), bio="",
            ai=ai, personality=personality, style=style,
        )
        persona.bio = self._bio(persona)
        return persona

    # -- pieces ----------------------------------------------------------- #
    def _city(self, cc: str) -> tuple[str, str, str]:
        country = geo.COUNTRIES[cc]
        weights: dict[int, float] = {}
        for i, entry in enumerate(country["cities"]):
            used = self.city_use.get((cc, entry[0]), 0)
            weights[i] = entry[1] * (0.45 ** used)
        idx = int(_pick(self.rng, {str(k): v for k, v in weights.items()}))
        entry = country["cities"][idx]
        self.city_use[(cc, entry[0])] = self.city_use.get((cc, entry[0]), 0) + 1
        if len(entry) == 4:
            return entry[0], entry[2], entry[3]
        return entry[0], country["language"], geo.DEFAULT_POOL[cc]

    def _age(self, prof: dict) -> int:
        rng = self.rng
        for _ in range(50):
            lo, hi = AGE_BRACKETS[int(_pick(rng, {str(i): wt for i, (_, wt) in enumerate(AGE_BRACKETS)}))][0]
            age = rng.randint(lo, hi)
            if age >= prof["min_age"]:
                return age
        return prof["min_age"] + rng.randint(0, 10)

    def _birth_date(self, age: int) -> str:
        """A birth date consistent with `age` on TODAY (month, day)."""
        month = self.rng.randint(1, 12)
        day = self.rng.randint(1, 28)
        year = CURRENT_YEAR - age if (month, day) <= TODAY else CURRENT_YEAR - age - 1
        return f"{year:04d}-{month:02d}-{day:02d}"

    def _gender(self, prof: dict) -> str:
        r = self.rng.random()
        if r < 0.015:
            return "non-binary"
        return "female" if self.rng.random() < prof["female"] else "male"

    def _origin(self, cc: str) -> tuple[str, str] | None:
        """Returns (origin_key, kind) or None for people without migration background."""
        if cc not in geo.MIGRATION:
            return None
        prob, options = geo.MIGRATION[cc]
        if self.rng.random() >= prob:
            return None
        weights = {f"{o}|{kind}": wt for o, wt, kind in options}
        key, kind = _pick(self.rng, weights).split("|")
        return key, kind

    def _name(self, origin, pool_key: str, gender: str, age: int) -> tuple[str, str]:
        rng = self.rng
        for _ in range(100):
            first_pool = sur_pool = pool_key
            if origin:
                okey, kind = origin
                origin_pool = geo.DEFAULT_POOL.get(okey, okey)
                sur_pool = origin_pool
                # Second-generation people often have a "local" first name.
                first_pool = pool_key if (kind == "heritage" and rng.random() < 0.3) else origin_pool
            name_gender = gender if gender != "non-binary" else rng.choice(["male", "female"])
            first = rng.choice(geo.NAME_POOLS[first_pool][name_gender])
            last = self._surname(sur_pool, name_gender, age)
            family = (sur_pool, last.split()[0][:5])  # "Kowalski"/"Kowalska" count as the same family name
            if f"{first} {last}" not in self.used_names and (family not in self.used_surnames or _ > 30):
                self.used_names.add(f"{first} {last}")
                self.used_surnames.add(family)
                return first, last
        return first, last

    def _surname(self, pool_key: str, gender: str, age: int) -> str:
        rng = self.rng
        pool = geo.NAME_POOLS[pool_key]["surnames"]

        def form(entry) -> str:
            if isinstance(entry, str):
                return entry
            if gender == "female":
                if len(entry) == 3:  # Lithuanian: married vs maiden form
                    return entry[2] if (age < 30 or rng.random() < 0.35) else entry[1]
                return entry[1]
            return entry[0]

        last = form(rng.choice(pool))
        if pool_key == "ES" and rng.random() < 0.55:
            second = form(rng.choice(pool))
            if second != last:
                last = f"{last} {second}"
        elif pool_key in ("PT", "BR") and rng.random() < 0.4:
            second = form(rng.choice(pool))
            if second != last:
                last = f"{second} {last}"
        return last

    def _languages(self, cc, country, city, local_language, origin, age, surname=""):
        rng = self.rng
        nationality = country["nationality"]
        english = _pick(rng, country["english"])
        native = [local_language]
        other: list[str] = []
        background = f"{nationality}, grew up in {_country_phrase(country['name'])}"

        if cc in ("CH", "BE") and rng.random() < 0.5:
            second_local = {"German": "French", "French": "German" if cc == "CH" else "Dutch",
                            "Dutch": "French", "Italian": "German"}[local_language]
            other.append(f"{second_local} ({_pick(rng, {'B1': 2, 'B2': 3, 'C1': 2})})")
        if city in geo.CITY_SECOND_LANGUAGE:
            lang = geo.CITY_SECOND_LANGUAGE[city]
            if lang in ("Catalan", "Valencian", "Basque") and rng.random() < 0.5:
                native.append(lang)
            elif cc == "LU":
                native = ["Luxembourgish"]
                other.extend(["French (C1)", "German (C1)"])
            elif rng.random() < 0.15:
                native.append(lang)

        if origin:
            okey, kind = origin
            if okey in geo.COUNTRIES:
                o = geo.COUNTRIES[okey]
                o_name, o_nat, o_lang, o_eng = o["name"], o["nationality"], o["language"], o["english"]
            else:
                o = geo.EXTRA_ORIGINS[okey]
                o_name = rng.choice(o.get("alt_names", [o["name"]]))
                o_nat, o_lang, o_eng = o["nationality"], o["language"], o["english"]
                if "alt_languages" in o:
                    o_lang = geo.SURNAME_LANGUAGE.get(surname) or rng.choice(o["alt_languages"])
                if o_name != o["name"]:
                    o_nat = {"Pakistan": "Pakistani", "Bangladesh": "Bangladeshi", "Algeria": "Algerian",
                             "Tunisia": "Tunisian", "Iraq": "Iraqi", "Lebanon": "Lebanese",
                             "Egypt": "Egyptian"}.get(o_name, o_nat)
            if kind == "heritage":
                if okey == "RU":
                    native = ["Russian"]
                    other.insert(0, f"{local_language} (C1)")
                    background = f"{nationality}, Russian-speaking, born and raised in {_country_phrase(country['name'])}"
                else:
                    heritage_lang = o_lang
                    if okey == "SOUTH_ASIAN":
                        heritage_lang = geo.SURNAME_LANGUAGE.get(surname) or rng.choice(
                            geo.EXTRA_ORIGINS["SOUTH_ASIAN"]["heritage_languages"])
                        o_nat = {"Pakistan": "Pakistani", "Bangladesh": "Bangladeshi"}.get(o_name, "Indian")
                    if heritage_lang != local_language:
                        other.insert(0, f"{heritage_lang} (heritage speaker)")
                    background = f"{nationality}, born in {_country_phrase(country['name'])} to {o_nat} parents"
            else:  # expat
                nationality = o_nat
                native = [o_lang]
                english = _pick(rng, o_eng)
                if english in ("B1",):
                    english = "B2"
                max_years = max(1, min(15, age - 22))
                moved = CURRENT_YEAR - rng.randint(1, max_years)
                background = f"{o_nat}, moved from {_country_phrase(o_name)} to {_country_phrase(country['name'])} in {moved}"
                if local_language not in ("English",) and local_language != o_lang:
                    years_here = CURRENT_YEAR - moved
                    lvl = "A2" if years_here < 3 else ("B1" if years_here < 6 else _pick(rng, {"B2": 2, "C1": 2}))
                    other.insert(0, f"{local_language} ({lvl})")

        if "English" in native:
            english = "native"
        elif english == "native":
            native.append("English")
        if english != "native":
            other.insert(0, f"English ({english})")
        if rng.random() < 0.3:
            extra_w = {"French": 3, "German": 3, "Spanish": 3, "Italian": 1.5, "Russian": 0.4, "Swedish": 0.3,
                       "Dutch": 0.3, "Portuguese": 0.5}
            if cc in ("UA", "BG", "RS", "PL", "CZ", "SK", "LT", "LV", "EE") and age >= 35:
                extra_w["Russian"] = 3
            extra = _pick(rng, extra_w)
            other.append(f"{extra} ({_pick(rng, {'A2': 2, 'B1': 3, 'B2': 1})})")
        # One entry per language, never repeating a native language.
        seen = set(native)
        cleaned = []
        for entry in other:
            lang = entry.split(" (")[0]
            if lang not in seen:
                seen.add(lang)
                cleaned.append(entry)
        return nationality, background, native, cleaned, english

    def _education_level(self, prof: dict, age: int) -> str:
        key = _pick(self.rng, prof["education"])
        downgrade = {"phd": "master", "master": "bachelor", "medicine": "medicine", "bachelor": "vocational"}
        while work.EDUCATION_END_AGE[key][0] > age - 1 and key in downgrade and downgrade[key] != key:
            key = downgrade[key]
        return key

    def _field(self, prof: dict, title: str, industry: str, edu_key: str) -> str:
        """Field of study, kept consistent with the job title and the type of education."""
        field_of_study = self._field_for_title(prof, title, industry)
        if edu_key == "vocational" and field_of_study not in VOCATIONAL_FIELDS:
            if prof["key"] in ("software_engineer", "devops", "qa", "it_support", "security", "ml_engineer", "game_dev"):
                return "IT specialist"
            if prof["key"] in ("engineer", "lab_scientist", "architect"):
                return "Technician"
            return "Commercial apprenticeship"
        return field_of_study

    def _field_for_title(self, prof: dict, title: str, industry: str) -> str:
        rng = self.rng
        if prof["key"] == "small_business":
            for word, field_of_study in SMALL_BUSINESS_FIELD.items():
                if word in title:
                    return field_of_study
        if prof["key"] == "teacher" and industry == "Language school":
            return rng.choice(["English", "Modern Languages"])
        for word, field_of_study in TITLE_FIELD.items():
            if word in title:
                return field_of_study
        title_words = {t.lower() for t in re.findall(r"[A-Za-z]{5,}", title)}
        matching = [f for f in prof["fields"] if title_words & {t.lower() for t in re.findall(r"[A-Za-z]{5,}", f)}]
        if matching and rng.random() < 0.85:
            return rng.choice(matching)
        return rng.choice(prof["fields"])

    @staticmethod
    def _education_label(key: str, field_of_study: str, title: str) -> str:
        if title == "PhD Candidate" and key == "phd":
            key = "master"
        label = work.EDUCATION_LABELS[key]
        if key in ("bachelor", "master", "phd"):
            label = f"{label} in {field_of_study}"
        elif key == "vocational":
            label = f"Vocational training ({field_of_study})"
        if title == "PhD Candidate" and key == "master":
            label += " (PhD in progress)"
        return label

    def _experience(self, prof: dict, edu_key: str, age: int) -> int:
        rng = self.rng
        lo, hi = work.EDUCATION_END_AGE[edu_key]
        gap = _pick(rng, {"0": 3, "1": 2.5, "2": 2, "3": 1, "5": 0.6})
        start = rng.randint(lo, hi) + int(gap)
        years = max(0, age - start)
        changer_prob = 0.12 + max(0, age - 40) * 0.01
        if years > 6 and rng.random() < changer_prob:  # career changer
            years = int(years * rng.uniform(0.3, 0.8))
        cap = prof.get("max_years")
        if cap and years > cap:
            years = rng.randint(cap // 2, cap)
        return years

    def _employment(self, prof: dict, years: int) -> str:
        employment = _pick(self.rng, prof["employment"])
        if employment == "freelancer" and prof["key"] in OWN_PRACTICE:
            employment = "self_employed"
        if employment in ("freelancer", "self_employed") and years < 3 and prof["key"] != "small_business":
            employment = "employee"
        if employment == "employee" and "employee" not in prof["employment"]:
            employment = next(iter(prof["employment"]))
        return employment

    def _role(self, prof, employment, years, age) -> tuple[str, str]:
        rng = self.rng
        if employment == "founder":
            if prof["key"] == "founder":
                return "founder", rng.choice(prof["titles"]["mid"])
            return "founder", rng.choice(["Founder", "Co-founder", "Co-founder & CTO" if prof["key"] in (
                "software_engineer", "ml_engineer") else "Co-founder & CEO"])
        if employment in ("freelancer", "self_employed"):
            if prof["key"] == "small_business":
                return "owner", rng.choice(prof["titles"]["mid"])
            if prof["key"] == "tradesperson":
                return "owner", f"Self-employed {rng.choice(prof['titles']['mid'])}"
            title = prof.get("freelance_title") or f"Freelance {prof['titles'].get('mid', [prof['label']])[0]}"
            return ("owner" if employment == "self_employed" else "freelance"), title
        if years < 2:
            level = "junior"
        elif years < 5:
            level = _pick(rng, {"junior": 3, "mid": 7})
        elif years < 9:
            level = _pick(rng, {"mid": 5.5, "senior": 4.5})
        elif years < 15:
            level = _pick(rng, {"mid": 2, "senior": 5, "lead": 2, "head": 1})
        else:
            level = _pick(rng, {"mid": 1.5, "senior": 4.5, "lead": 2.5, "head": 1.8})
        if level == "head" and age < 32:
            level = "lead"
        title = _title_for(prof, level, rng)
        return level, title

    def _teacher_title(self, industry: str, field_of_study: str, seniority: str, title: str) -> str:
        if seniority in ("lead", "head", "junior"):
            return title
        if industry == "Primary school":
            return "Primary School Teacher"
        if industry == "Vocational school":
            return "Vocational School Teacher"
        if industry == "Language school":
            return "Language Teacher"
        if field_of_study == "Education":
            return "Secondary School Teacher"
        subject = {"Mathematics": "Maths"}.get(field_of_study, field_of_study)
        return f"{subject} Teacher"

    def _industry(self, prof: dict, cc: str, title: str, employment: str) -> str:
        if prof["key"] == "small_business":
            for word, industry in SMALL_BUSINESS_INDUSTRY.items():
                if word in title:
                    return industry
            return "Small business"
        if employment == "self_employed" and prof["key"] in OWN_PRACTICE_INDUSTRY:
            return OWN_PRACTICE_INDUSTRY[prof["key"]]
        weights = dict(prof["industries"])
        if "EU institution" in weights:
            weights["EU institution"] *= 4 if cc in ("BE", "LU") else 0.3
        return _pick(self.rng, weights)

    def _company_size(self, prof: dict, employment: str, industry: str = "") -> str:
        if employment == "freelancer":
            return "1 (just me)"
        if employment == "founder":
            return _pick(self.rng, work.w("2–10:5; 11–50:4; 51–250:1"))
        if employment == "self_employed":
            if prof["key"] == "small_business":
                return _pick(self.rng, work.w("2–10:6; 11–50:2; 1 (just me):1"))
            return _pick(self.rng, work.w("1 (just me):3; 2–10:5; 11–50:1"))
        for word, preset in INDUSTRY_SIZES.items():
            if word in industry:
                return _pick(self.rng, preset)
        return _pick(self.rng, work.SIZE_PRESETS[prof["sizes"]])

    def _work_mode(self, prof: dict, employment: str) -> str:
        weights = dict(prof["work"])
        if employment == "freelancer" and "remote" in weights:
            weights["remote"] *= 3
        return _pick(self.rng, weights)

    def _income(self, country: dict, prof: dict, seniority: str, employment: str) -> int:
        rng = self.rng
        level = country["salary"]
        g = prof["globalized"]
        base = max(level, level ** (1 - g) * EU_REFERENCE_SALARY ** g)
        value = base * prof["salary"] * SENIORITY_FACTOR[seniority] * rng.uniform(0.85, 1.15)
        value *= {"freelancer": rng.uniform(0.7, 1.4), "founder": rng.uniform(0.5, 1.5),
                  "self_employed": rng.uniform(0.6, 1.3)}.get(employment, 1.0)
        return int(round(value / 500) * 500)

    def _attitude(self, prof: dict, age: int, personality: dict) -> str:
        weights = dict(prof["attitudes"])
        if age >= 50:
            weights["cautious"] = weights.get("cautious", 0) * 1.3
            weights["skeptic"] = weights.get("skeptic", 0) * 1.3
            weights["enthusiast"] = weights.get("enthusiast", 0) * 0.8
        elif age < 30:
            weights["enthusiast"] = weights.get("enthusiast", 0) * 1.2
        weights["enthusiast"] = weights.get("enthusiast", 0) * (0.7 + 0.15 * personality["openness"])
        return _pick(self.rng, weights)

    def _ai_profile(self, prof, cc, native, attitude, employment, size, industry, title="") -> dict:
        rng = self.rng
        employee = employment == "employee"
        big = size in ("251–1,000", "1,001–5,000", "5,000+")

        adoption = {"enthusiast": "2022:4; 2023:4.5; 2024:1.5", "pragmatist": "2022:1; 2023:4.5; 2024:3.5; 2025:1",
                    "cautious": "2023:3; 2024:4.5; 2025:2.5", "skeptic": "2023:2; 2024:4; 2025:3.5; 2026:0.5"}
        since = int(_pick(rng, work.w(adoption[attitude])))

        score = prof["intensity"] * 2 + {"enthusiast": 1.0, "pragmatist": 0.5, "cautious": 0.0,
                                         "skeptic": -0.4}[attitude] + rng.gauss(0, 0.45)
        freq = FREQUENCIES[0 if score > 2.1 else 1 if score > 1.5 else 2 if score > 0.9 else 3 if score > 0.4 else 4]

        skill_score = {"enthusiast": 2.6, "pragmatist": 1.9, "cautious": 1.3, "skeptic": 1.2}[attitude] \
            + prof["intensity"] * 0.8 + rng.gauss(0, 0.4)
        skill = "beginner" if skill_score < 1.6 else "intermediate" if skill_score < 2.4 else \
            "advanced" if skill_score < 3.1 else "expert"

        tool_weights = dict(prof["tools"])
        if "English" not in native:
            tool_weights["DeepL"] = tool_weights.get("DeepL", 0) + 1.5
        elif "DeepL" in tool_weights and prof["key"] != "translator":
            tool_weights["DeepL"] *= 0.3
        tool_weights["Mistral Le Chat"] = tool_weights.get("Mistral Le Chat", 0) + (1.5 if cc == "FR" else 0.2)
        if not (employee and big):
            tool_weights.pop("internal company AI assistant", None)
        if not employee:
            tool_weights.pop("internal government AI assistant", None)
        if employee and big and "Microsoft Copilot" in tool_weights:
            tool_weights["Microsoft Copilot"] *= 2
        n_tools = {"beginner": rng.randint(1, 2), "intermediate": rng.randint(2, 3),
                   "advanced": rng.randint(3, 4), "expert": rng.randint(4, 6)}[skill]
        tools = _sample(rng, tool_weights, n_tools)
        if not GENERAL_CHATBOTS.intersection(tools) and rng.random() < 0.5:
            tools.append("ChatGPT")
        primary = _pick(rng, {t: tool_weights.get(t, 1) * (0.25 if t in SUPPORT_TOOLS and prof["key"] != "translator"
                                                           else 1) for t in tools})
        tools.remove(primary)
        tools.insert(0, primary)

        use_pool = list(prof["uses"])
        if prof["key"] == "small_business":
            for word, extra_uses in SMALL_BUSINESS_USES.items():
                if word in title:
                    use_pool = [u for u in use_pool if "menu" not in u] + extra_uses
        if "AI medical scribe" not in tools:
            use_pool = [u for u in use_pool if "AI scribe" not in u]
        n_uses = min(len(use_pool), rng.randint(2, 3) + (1 if skill in ("advanced", "expert") else 0))
        uses = rng.sample(use_pool, n_uses)
        if rng.random() < 0.35:
            extra = rng.choice([u for u in GENERIC_USES if u not in uses])
            uses.append(extra)

        base_hours = {FREQUENCIES[0]: (3, 10), FREQUENCIES[1]: (2, 7), FREQUENCIES[2]: (1, 4),
                      FREQUENCIES[3]: (0.5, 2), FREQUENCIES[4]: (0, 1)}[freq]
        hours = rng.uniform(*base_hours) * (0.7 if attitude == "skeptic" else 1.0)
        hours = round(hours * 2) / 2

        company_pays = employee and ((big and rng.random() < 0.65) or (size == "51–250" and rng.random() < 0.35))
        paid_tools = [t for t in tools if t in work.ENTERPRISE_TOOLS]
        access_parts = []
        if company_pays and paid_tools:
            access_parts.append(f"employer pays for {', '.join(paid_tools[:2])}")
        personal_prob = {"employee": 0.3, "freelancer": 0.7, "founder": 0.8, "self_employed": 0.5}[employment]
        if attitude in ("enthusiast", "pragmatist") and rng.random() < personal_prob:
            chatbot = next((t for t in tools if t in ("ChatGPT", "Claude", "Gemini", "Perplexity", "Midjourney",
                                                      "Cursor", "GitHub Copilot", "Mistral Le Chat")), None)
            if chatbot and not (company_pays and chatbot in paid_tools[:2]):
                access_parts.append(f"pays personally for {chatbot} (about €20/month)"
                                    + (" as a business expense" if employment != "employee" else ""))
        if not access_parts:
            access_parts.append("free versions only")
        access = "; ".join(access_parts)

        policy = None
        if employee:
            pw = {"encouraged": 2, "guidelines": 3, "approved_only": 2, "no_policy": 2, "discouraged": 0.7}
            if size in ("1,001–5,000", "5,000+"):
                pw.update(encouraged=3, approved_only=3, no_policy=0.6)
            elif size in ("2–10", "11–50"):
                pw.update(no_policy=5, approved_only=0.8, encouraged=1.6)
            if any(word.lower() in industry.lower() for word in SENSITIVE_INDUSTRY_WORDS):
                pw.update(approved_only=pw["approved_only"] * 2, discouraged=pw["discouraged"] * 2,
                          encouraged=pw["encouraged"] * 0.6)
            if company_pays:
                pw.update(no_policy=0, discouraged=0)
            policy = POLICIES[_pick(rng, pw)]

        if employee:
            training = _pick(rng, {
                "no training from the employer, self-taught": 4.5 if not big else 3,
                "a short e-learning module from the employer": 3,
                "a hands-on workshop organised by the employer": 2 if big else 1,
                "an internal AI champions programme": 0.7 if big else 0.1})
        else:
            training = "self-taught (YouTube, newsletters, trial and error)"

        satisfaction = {"enthusiast": (8, 10), "pragmatist": (6, 9), "cautious": (5, 8), "skeptic": (3, 7)}[attitude]
        trust = {"enthusiast": (3, 5), "pragmatist": (3, 4), "cautious": (2, 3), "skeptic": (1, 3)}[attitude]

        concern_weights = {k: v for k, v in prof["concerns"].items()}
        for k, v in {"privacy": 1, "accuracy": 1, "env": 0.5, "dependence": 0.5, "ai_act": 0.3, "cost": 0.4}.items():
            concern_weights[k] = concern_weights.get(k, 0) + v
        n_concerns = rng.randint(2, 4) if attitude in ("cautious", "skeptic") else rng.randint(1, 3)
        concerns = [work.CONCERNS[c] for c in _sample(rng, concern_weights, n_concerns)]

        peeves = list(work.PET_PEEVES)
        if "English" not in native:
            peeves.append(work.PET_PEEVE_NON_ENGLISH.format(language=native[0]))
        outlook = _pick(rng, {
            "enthusiast": {"expects to use AI much more next year": 6, "expects to use it a bit more": 3},
            "pragmatist": {"expects to use it a bit more": 5, "expects about the same": 3,
                           "expects to use AI much more next year": 1.5},
            "cautious": {"expects about the same": 5, "expects to use it a bit more": 3,
                         "would rather use it less": 1},
            "skeptic": {"expects about the same": 4, "would rather use it less": 3,
                        "expects to use it a bit more (because work demands it)": 2},
        }[attitude])
        job_impact = _pick(rng, {
            "enthusiast": {"it has already changed my job a lot": 5, "it changes some tasks but not the job": 3},
            "pragmatist": {"it changes some tasks but not the job": 6, "it has already changed my job a lot": 2},
            "cautious": {"it changes some tasks but not the job": 5, "worried it will replace parts of my job": 2},
            "skeptic": {"hardly changes the job itself": 4, "worried it will replace parts of my job": 3,
                        "it changes some tasks but not the job": 2},
        }[attitude])

        return dict(
            attitude=attitude, tools=tools, primary_tool=primary, frequency=freq, since_year=since,
            use_cases=uses, skill_level=skill, hours_saved_per_week=hours, access=access,
            employer_policy=policy, training=training,
            satisfaction_1_10=rng.randint(*satisfaction), trust_1_5=rng.randint(*trust),
            concerns=concerns, good_experience=rng.choice(prof["wins"]), bad_experience=rng.choice(prof["fails"]),
            pet_peeve=rng.choice(peeves), outlook=outlook, job_impact=job_impact,
        )

    def _style(self, p: dict, attitude: str, age: int, native, english, cc, origin) -> dict:
        rng = self.rng
        c = p["conscientiousness"]
        engagement = _pick(rng, {"careful": max(0.3, 3 + (c - 3) * 1.5), "normal": 5,
                                 "rushed": max(0.3, 2 - (c - 3) * 0.8)})
        v_score = (p["extraversion"] + p["openness"]) / 2 + {"careful": 0.6, "normal": 0, "rushed": -0.8}[engagement] \
            + (0.3 if attitude in ("enthusiast", "skeptic") else 0) + rng.gauss(0, 0.5)
        verbosity = "terse" if v_score < 2.6 else "moderate" if v_score < 3.6 else "elaborate"
        tone = rng.choice(TONES[attitude])
        if p["agreeableness"] <= 2 and "blunt" not in tone:
            tone += ", a bit blunt"
        if p["neuroticism"] >= 4:
            tone += ", slightly anxious"
        scale_habit = _pick(rng, {"none": 5.5, "tends to agree": 1.5, "prefers the middle": 1.5 + (1 if engagement == "rushed" else 0),
                                  "uses the extremes": 1.5})
        typo_w = {"none": 3.0, "low": 5.0, "medium": 2.0}
        if engagement == "rushed":
            typo_w["medium"] *= 2
        if c >= 4:
            typo_w["none"] *= 2
        typos = _pick(rng, typo_w)
        casing = "mostly lowercase" if rng.random() < (0.18 if age < 35 else 0.06) else "normal"
        full_stops = rng.random() > (0.35 if casing != "normal" or engagement == "rushed" else 0.15)
        skip = {"careful": 0.05, "normal": 0.2, "rushed": 0.5}[engagement]

        lang = native[0]
        notes = geo.L1_WRITING_NOTES.get(lang, "sometimes drops articles")
        if english == "native":
            spelling = "American" if cc == "US" or (origin and origin[0] == "US" and origin[1] == "expat") else "British"
            writing = f"native English speaker, {spelling} spelling"
        elif english == "C2":
            writing = f"near-native English ({lang} L1); {notes}, but very rarely"
        elif english == "C1":
            writing = f"fluent non-native English ({lang} L1); {notes}, occasionally"
        elif english == "B2":
            writing = f"good but clearly non-native English ({lang} L1); {notes}"
        else:
            writing = f"simple non-native English ({lang} L1); short sentences, basic vocabulary; {notes}"
        return dict(engagement=engagement, verbosity=verbosity, tone=tone, scale_habit=scale_habit, typos=typos,
                    casing=casing, ends_with_full_stop=full_stops, skip_optional_prob=skip,
                    discloses_income=rng.random() < 0.85, writing=writing)

    def _household(self, age: int) -> str:
        if age < 27:
            opts = {"single": 4, "living with partner": 3.5, "shares a flat with friends": 2, "married": 0.5}
        elif age < 35:
            opts = {"single": 2.5, "living with partner": 3.5, "married": 2.5, "married, one young child": 1.5,
                    "living with partner and a baby": 0.7}
        elif age < 50:
            kids = self.rng.choice(["one child", "two children", "two kids", "three kids"])
            opts = {"single": 1.2, "living with partner": 1.5, f"married, {kids}": 4.5, "divorced, shares custody of one child": 0.8,
                    "married, no kids": 1.2, f"living with partner and {kids}": 0.8}
        else:
            opts = {"married, children are teenagers": 2.5, "married, children have moved out": 2.5,
                    "divorced": 1.5, "single": 1, "living with partner": 0.8, "married, grandchildren": 0.7 if age > 55 else 0}
        return _pick(self.rng, opts)

    def _email(self, first: str, last: str) -> str:
        base = f"{_slug(first)}.{_slug(last.split()[0])}"
        email = f"{base}@{self.email_domain}"
        n = 2
        while email in self.used_emails:
            email = f"{base}{n}@{self.email_domain}"
            n += 1
        self.used_emails.add(email)
        return email

    def _bio(self, p: Persona) -> str:
        rng = self.rng
        if p.employment_type == "freelancer":
            where = f"works freelance from {p.city}, {p.country} ({_industry_phrase(p.industry)})"
        elif p.employment_type == "self_employed" and p.profession_key == "agronomist":
            where = f"runs a farm near {p.city}, {p.country}"
        elif p.employment_type == "self_employed":
            where = f"runs their own business in {p.city}, {p.country}"
        else:
            size = p.company_size
            size_word = {"2–10": "tiny", "11–50": "small", "51–250": "mid-sized", "251–1,000": "large",
                         "1,001–5,000": "large", "5,000+": "very large"}.get(size, "")
            if p.industry in work.ORG_PHRASES:
                org = work.ORG_PHRASES[p.industry]
            elif p.industry.lower().endswith(ORG_SUFFIXES):
                org = f"{_article(size_word)} {size_word} {_industry_phrase(p.industry)} ({size} employees)"
            elif p.employment_type == "founder":
                kind = p.industry.split("(")[-1].rstrip(")") + " startup" if p.industry.startswith("Startup") \
                    else _industry_phrase(p.industry) + " company"
                org = f"a {size}-person {kind}"
            else:
                org = f"{_article(size_word)} {size_word} company ({size} employees) in {p.industry}"
            where = f"works at {org} in {p.city}, {p.country}"
        low = p.job_title.lower()
        if low.startswith("owner"):
            role = f"the {low}"
        elif low.startswith(("founder", "co-founder")):
            role = ("the " if low.startswith("founder") else "a ") + low.replace(" & ", " and ").replace("ceo", "CEO").replace("cto", "CTO")
        else:
            role = f"{_article(p.job_title)} {p.job_title}"
        uses = p.ai["use_cases"][:2]
        sentence_ai = (f"Uses AI at work {p.ai['frequency']} since {p.ai['since_year']}, "
                       f"mainly {p.ai['primary_tool']}, for {uses[0]}"
                       + (f" and {uses[1]}" if len(uses) > 1 else "") + ".")
        return (f"{p.first_name} ({p.age}) is {role} and {where}. {p.background}. "
                f"{sentence_ai} {rng.choice(ATTITUDE_PHRASES[p.ai['attitude']])}")


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def generate_personas(count: int = 100, seed: int = 42, email_domain: str = "example.com") -> list[Persona]:
    return PersonaGenerator(seed=seed, email_domain=email_domain).generate(count)


def save_personas(personas: list[Persona], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([p.to_dict() for p in personas], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def load_personas(path: str | Path) -> list[Persona]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Persona.from_dict(d) for d in data]


def persona_card(p: Persona) -> str:
    """Human-readable profile used in LLM prompts."""
    ai, st, per = p.ai, p.style, p.personality
    lines = [
        f"Name: {p.full_name} ({p.gender}, {p.age} years old, born {p.birth_year})",
        f"Lives in: {p.city}, {p.country}. Background: {p.background}.",
        f"Languages: {', '.join(l + ' (native)' for l in p.native_languages)}"
        + (f"; {', '.join(p.other_languages)}" if p.other_languages else ""),
        f"Household: {p.household}. Hobbies: {', '.join(p.hobbies)}.",
        f"Education: {p.education}.",
        f"Job: {p.job_title} ({p.occupation}); {p.employment_type.replace('_', '-')}, seniority {p.seniority}, "
        f"{p.years_experience} years of experience in the field.",
        f"Organisation: {p.industry}; {p.company_size} people; works {p.work_mode}.",
        f"Income: about €{p.income_eur:,} gross per year ({p.income_band}).",
        f"Contact e-mail (use only if a question requires an e-mail): {p.email}",
        "AI at work:",
        f"- tools: {', '.join(ai['tools'])} (main: {ai['primary_tool']}); uses them {ai['frequency']}, since {ai['since_year']}",
        f"- used for: {'; '.join(ai['use_cases'])}",
        f"- skill level: {ai['skill_level']}; saves roughly {ai['hours_saved_per_week']} h per week",
        f"- access/payment: {ai['access']}",
        f"- employer policy: {ai['employer_policy'] or 'not applicable (own rules)'}; training: {ai['training']}",
        f"- attitude: {ai['attitude']}; satisfaction {ai['satisfaction_1_10']}/10; trust in outputs {ai['trust_1_5']}/5",
        f"- concerns: {'; '.join(ai['concerns'])}",
        f"- a good experience: {ai['good_experience']}",
        f"- a bad experience: {ai['bad_experience']}",
        f"- pet peeve: {ai['pet_peeve']}",
        f"- outlook: {ai['outlook']}; impact on job: {ai['job_impact']}",
        f"Personality (1-5): openness {per['openness']}, conscientiousness {per['conscientiousness']}, "
        f"extraversion {per['extraversion']}, agreeableness {per['agreeableness']}, neuroticism {per['neuroticism']}",
        "How this person fills in surveys:",
        f"- engagement: {st['engagement']}; open answers are {st['verbosity']}; tone: {st['tone']}",
        f"- rating-scale habit: {st['scale_habit']}; skips optional open questions with probability {st['skip_optional_prob']}",
        f"- {'answers income questions' if st['discloses_income'] else 'prefers not to disclose income if that option exists'}",
        f"- writing: {st['writing']}",
    ]
    return "\n".join(lines)
