"""Mechanical "human noise" for free-text answers: casing, punctuation and typos.

The LLM decides *what* a respondent says and in which voice; this module adds the
small slips people make when typing into a web form. It is deterministic for a
given random generator, so re-running produces the same text.
"""

from __future__ import annotations

import random
import re

COMMON_MISSPELLINGS = {
    "definitely": "definately", "separate": "seperate", "necessary": "neccessary", "receive": "recieve",
    "occasionally": "occasionaly", "environment": "enviroment", "tomorrow": "tommorow", "which": "wich",
    "because": "becuase", "really": "realy", "business": "buisness", "believe": "belive",
    "until": "untill", "different": "diffrent", "probably": "probaly", "actually": "acutally",
    "generally": "generaly", "especially": "especialy", "information": "infomation", "results": "resluts",
    "their": "thier", "writing": "writting", "useful": "usefull", "sometimes": "somtimes",
}

_WORD = re.compile(r"[A-Za-zÀ-ÿ]+")


def _typo(word: str, rng: random.Random) -> str:
    low = word.lower()
    if low in COMMON_MISSPELLINGS and rng.random() < 0.6:
        fixed = COMMON_MISSPELLINGS[low]
        return fixed.capitalize() if word[0].isupper() else fixed
    i = rng.randint(1, len(word) - 3)
    kind = rng.random()
    if kind < 0.45:  # swap two neighbouring letters
        return word[:i] + word[i + 1] + word[i] + word[i + 2:]
    if kind < 0.8:  # drop a letter
        return word[:i] + word[i + 1:]
    return word[:i] + word[i] + word[i:]  # double a letter


def add_typos(text: str, count: int, rng: random.Random) -> str:
    candidates = [m for m in _WORD.finditer(text)
                  if len(m.group()) >= 5 and not m.group().isupper() and not any(c.isdigit() for c in m.group())
                  and not m.group()[0].isupper()]  # leave names and brands alone
    if not candidates or count <= 0:
        return text
    chosen = sorted(rng.sample(candidates, min(count, len(candidates))), key=lambda m: m.start(), reverse=True)
    for m in chosen:
        text = text[:m.start()] + _typo(m.group(), rng) + text[m.end():]
    return text


def humanize(text: str, style: dict, rng: random.Random) -> str:
    """Apply a persona's typing habits to one free-text answer."""
    if not text or len(text) < 4 or "@" in text:
        return text
    words = len(text.split())
    typo_level = style.get("typos", "low")
    if words < 5:  # short factual answers (job title, city...) are typed carefully
        count = 0
    elif typo_level == "medium":
        count = sum(1 for _ in range(max(1, words // 12)) if rng.random() < 0.45)
    elif typo_level == "low":
        count = 1 if rng.random() < min(0.35, 0.04 * words) else 0
    else:
        count = 0
    text = add_typos(text, count, rng)
    if style.get("casing") == "mostly lowercase":
        text = re.sub(r"(?<![@\w.])([A-ZÀ-Þ])(?=[a-zß-ÿ])", lambda m: m.group(1).lower(), text)
        text = re.sub(r"\bI\b", "i", text) if rng.random() < 0.7 else text
    if not style.get("ends_with_full_stop", True) and text.endswith(".") and not text.endswith(".."):
        text = text[:-1]
    return text
