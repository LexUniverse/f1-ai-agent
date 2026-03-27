import re

RU_LIVE_SUBSTRINGS = (
    "сейчас",
    "актуальн",
    "текущ",
    "последн",
    "календар",
    "следующ",
    "график",
    "на данный момент",
)

EN_LIVE_PHRASES = ("next race", "this season", "current season")

_EN_LIVE_WORDS = re.compile(r"\b(current|now|latest|standings|schedule|calendar)\b", re.IGNORECASE)


def requires_live_data(*, normalized_query: str, raw_user_text: str) -> bool:
    haystack = f"{normalized_query}\n{raw_user_text}"
    haystack_lower = haystack.lower()
    if any(s in haystack_lower for s in RU_LIVE_SUBSTRINGS):
        return True
    if any(phrase in haystack_lower for phrase in EN_LIVE_PHRASES):
        return True
    if _EN_LIVE_WORDS.search(haystack_lower):
        return True
    return False
