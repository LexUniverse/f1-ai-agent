import os


def parse_allowlist(raw_value: str | None = None) -> list[str]:
    env_value = raw_value if raw_value is not None else os.getenv("AUTH_ALLOWLIST_CODES", "")
    return [item.strip() for item in env_value.split(",") if item.strip()]
