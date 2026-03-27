import pytest

from src.live.gate import requires_live_data


@pytest.mark.parametrize(
    ("normalized", "raw", "expected"),
    [
        ("кто лидирует сейчас", "кто лидирует сейчас", True),
        ("current f1 standings", "current f1 standings", True),
        ("calendar next race", "calendar next race", True),
        ("who won monaco 1996", "who won monaco 1996", False),
        ("ferrari history", "ferrari history", False),
    ],
)
def test_requires_live_data_parametrized(normalized: str, raw: str, expected: bool) -> None:
    assert requires_live_data(normalized_query=normalized, raw_user_text=raw) is expected

