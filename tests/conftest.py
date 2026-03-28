import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.chat import PROCESS_CALLS
from src.auth.limiter import AuthLimiter
from src.auth.service import AuthService
from src.main import app
from src.sessions.store import SessionStore


@pytest.fixture(autouse=True)
def reset_state():
    # Fast deterministic Chroma embeddings in tests (production uses F1_EMBEDDING_MODEL / RoSBERTa).
    os.environ["F1_CHROMA_DEFAULT_EMBEDDINGS"] = "1"
    os.environ["AUTH_ALLOWLIST_CODES"] = "ABC123,XYZ789"
    app.state.session_store = SessionStore()
    app.state.auth_service = AuthService(limiter=AuthLimiter(max_failures=5, window_seconds=300, cooldown_seconds=600))
    PROCESS_CALLS["count"] = 0
    yield


@pytest.fixture
def client():
    return TestClient(app)


def assert_error_envelope(payload: dict, code: str):
    assert "error" in payload
    assert payload["error"]["code"] == code
    assert "message" in payload["error"]
    assert "details" in payload["error"]
