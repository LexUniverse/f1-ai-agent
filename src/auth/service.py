import hmac
import logging

from src.auth.allowlist import parse_allowlist
from src.auth.errors import AUTH_COOLDOWN, AUTH_INVALID_CODE, AUTH_MISSING_CODE
from src.auth.limiter import AuthLimiter
from src.models.auth import AuthDecision

logger = logging.getLogger(__name__)

RUSSIAN_MESSAGES = {
    AUTH_MISSING_CODE: "Код доступа не указан.",
    AUTH_INVALID_CODE: "Неверный код доступа.",
    AUTH_COOLDOWN: "Слишком много попыток. Попробуйте позже.",
}


def mask_code(value: str) -> str:
    if len(value) <= 4:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


class AuthService:
    def __init__(self, limiter: AuthLimiter | None = None) -> None:
        self.limiter = limiter or AuthLimiter()

    def validate_access_code(self, access_code: str | None, limiter_key: str) -> AuthDecision:
        cooldown_state = self.limiter.get_cooldown_state(limiter_key)
        if cooldown_state.locked:
            return AuthDecision(
                ok=False,
                code=AUTH_COOLDOWN,
                message=RUSSIAN_MESSAGES[AUTH_COOLDOWN],
                retry_after_seconds=cooldown_state.retry_after_seconds,
            )

        normalized = (access_code or "").strip()
        if not normalized:
            self.limiter.record_failure(limiter_key)
            return AuthDecision(ok=False, code=AUTH_MISSING_CODE, message=RUSSIAN_MESSAGES[AUTH_MISSING_CODE])

        allowlist = parse_allowlist()
        for allowed in allowlist:
            if hmac.compare_digest(allowed.strip(), normalized):
                self.limiter.reset(limiter_key)
                return AuthDecision(ok=True)

        self.limiter.record_failure(limiter_key)
        logger.warning("auth_failure_invalid_code key=%s code=%s", limiter_key, mask_code(normalized))
        return AuthDecision(ok=False, code=AUTH_INVALID_CODE, message=RUSSIAN_MESSAGES[AUTH_INVALID_CODE])
