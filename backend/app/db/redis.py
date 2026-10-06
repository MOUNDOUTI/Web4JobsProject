# =============================================================================
# CyberLearn — Client Redis async
# Utilisé pour : sessions de jeu, JWT blacklist, rate limiting, cache
# =============================================================================

from typing import Optional
import redis.asyncio as aioredis
from loguru import logger
from app.core.config import settings

# ─── Instance globale ─────────────────────────────────────────────────────────
_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Retourne le client Redis (singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Ferme la connexion Redis proprement."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Connexion Redis fermée")


async def check_redis_connection() -> bool:
    """Vérifie que Redis est accessible."""
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception:
        return False


# ─── Helpers JWT blacklist ────────────────────────────────────────────────────

async def blacklist_token(jti: str, expire_seconds: int) -> None:
    """Ajoute un token à la blacklist Redis (révocation au logout)."""
    client = await get_redis()
    await client.setex(f"blacklist:{jti}", expire_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    """Vérifie si un token est blacklisté."""
    client = await get_redis()
    return await client.exists(f"blacklist:{jti}") == 1


# ─── Helpers sessions de jeu ─────────────────────────────────────────────────

async def set_session_data(session_id: int, data: dict, ttl: int = 7200) -> None:
    """Stocke l'état d'une session de jeu active (TTL 2h par défaut)."""
    import json
    client = await get_redis()
    await client.setex(
        f"session:{session_id}",
        ttl,
        json.dumps(data),
    )


async def get_session_data(session_id: int) -> Optional[dict]:
    """Récupère l'état d'une session de jeu depuis Redis."""
    import json
    client = await get_redis()
    raw = await client.get(f"session:{session_id}")
    if raw:
        return json.loads(raw)
    return None


async def delete_session_data(session_id: int) -> None:
    """Supprime l'état d'une session de jeu (après complétion/abandon)."""
    client = await get_redis()
    await client.delete(f"session:{session_id}")


# ─── Helpers rate limiting auth ───────────────────────────────────────────────

async def increment_login_attempts(email: str) -> int:
    """Incrémente le compteur de tentatives de connexion. Retourne le nombre actuel."""
    client = await get_redis()
    key = f"login_attempts:{email}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, 900)  # 15 minutes
    return count


async def get_login_attempts(email: str) -> int:
    """Retourne le nombre de tentatives de connexion échouées."""
    client = await get_redis()
    val = await client.get(f"login_attempts:{email}")
    return int(val) if val else 0


async def reset_login_attempts(email: str) -> None:
    """Réinitialise le compteur après une connexion réussie."""
    client = await get_redis()
    await client.delete(f"login_attempts:{email}")


# ─── Helpers rate limiting soumissions ───────────────────────────────────────

async def increment_submit_attempts(session_id: int) -> int:
    """Incrémente le compteur de soumissions incorrectes pour une session."""
    client = await get_redis()
    key = f"submit_attempts:{session_id}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, 3600)  # 1h
    return count


async def get_submit_attempts(session_id: int) -> int:
    """Retourne le nombre de soumissions incorrectes pour une session."""
    client = await get_redis()
    val = await client.get(f"submit_attempts:{session_id}")
    return int(val) if val else 0


# ─── Helpers refresh token ───────────────────────────────────────────────────

async def store_refresh_token(user_id: int, jti: str, expire_days: int) -> None:
    """Stocke le JTI du refresh token pour un utilisateur."""
    client = await get_redis()
    await client.setex(
        f"refresh:{user_id}",
        expire_days * 86400,
        jti,
    )


async def get_stored_refresh_jti(user_id: int) -> Optional[str]:
    """Récupère le JTI du refresh token actif d'un utilisateur."""
    client = await get_redis()
    return await client.get(f"refresh:{user_id}")


async def delete_refresh_token(user_id: int) -> None:
    """Supprime le refresh token d'un utilisateur (logout)."""
    client = await get_redis()
    await client.delete(f"refresh:{user_id}")
