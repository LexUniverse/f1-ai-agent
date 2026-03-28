import re
import unicodedata


_CANONICAL_ALIASES = {
    "driver:max_verstappen": ["макс ферстаппен", "max verstappen"],
    "team:ferrari": ["феррари", "scuderia ferrari", "ferrari"],
    "race:monaco_gp": [
        "гран-при монако",
        "monaco grand prix",
        "монако",
        "монако гран при",
        "гран при монако",
        "гран при монако 2000",
    ],
}

def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = normalized.replace("ё", "е")
    normalized = re.sub(r"[-_/]", " ", normalized)
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


_ALIAS_TO_CANONICAL = {
    _normalize(alias): canonical
    for canonical, aliases in _CANONICAL_ALIASES.items()
    for alias in aliases
}


def resolve_entities(query: str) -> tuple[str, list[str], list[str]]:
    normalized_query = _normalize(query)
    if not normalized_query:
        return normalized_query, [], []

    canonical_ids: list[str] = []
    entity_tags: list[str] = []

    for alias, canonical in _ALIAS_TO_CANONICAL.items():
        if normalized_query == alias or f" {alias} " in f" {normalized_query} ":
            if canonical not in canonical_ids:
                canonical_ids.append(canonical)
                entity_tags.append(canonical)

    return normalized_query, canonical_ids, entity_tags
