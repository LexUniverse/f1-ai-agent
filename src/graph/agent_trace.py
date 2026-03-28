"""Console trace for multi-agent flow (enable with F1_LOG_AGENT_TRACE=1)."""

from __future__ import annotations

import os
import sys


def agent_trace(tag: str, message: str) -> None:
    if os.environ.get("F1_LOG_AGENT_TRACE", "").strip().lower() not in ("1", "true", "yes", "on"):
        return
    print(f"[F1 trace] {tag}: {message}", file=sys.stderr, flush=True)
