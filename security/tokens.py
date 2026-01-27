import logging
import jwt
from datetime import datetime, timedelta, timezone
from cachetools import TTLCache
from fastapi import HTTPException, status

from core.config import settings

logger = logging.getLogger("security.tokens")

TTL_BY_ROLE = {
    "monitoring": 20 * 60,
    "agent_reasoning": 2 * 60,
    "agent_fast": 1 * 60,
    "admin": 60 * 60,
    "user": 15 * 60,
    "agi": 30 * 60,
}

token_cache = TTLCache(
    maxsize=settings.TOKEN_CACHE_SIZE,
    ttl=settings.TOKEN_TTL_SECONDS,
)

def generate_token(username: str, role: str) -> tuple[str, int]:
    ttl = TTL_BY_ROLE.get(role)
    if not ttl:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    now = datetime.now(timezone.utc)
    iat = int(now.timestamp())
    exp = int((now + timedelta(seconds=ttl)).timestamp())

    payload = {
        "sub": username,
        "role": role,
        "iat": iat,
        "exp": exp,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    token_cache[token] = payload
    return token, exp


def verify_token(token: str) -> bool:
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return token in token_cache
    except jwt.PyJWTError as e:
        logger.warning("Token verification failed: %s", e)
        return False
