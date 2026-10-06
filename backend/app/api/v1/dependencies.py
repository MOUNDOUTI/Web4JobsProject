# =============================================================================
# CyberLearn — Dépendances FastAPI
# Injection : utilisateur courant, vérification rôles, DB, Redis
# =============================================================================

from fastapi import Depends, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.exceptions import AuthRequiredError, AdminRequiredError, InvalidTokenError
from app.core.security import decode_token
from app.db.database import get_db
from app.db.redis import is_token_blacklisted, get_stored_refresh_jti
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dépendance : retourne l'utilisateur authentifié depuis le JWT Bearer.
    Lève AuthRequiredError si pas de token ou token invalide.
    """
    if not credentials:
        raise AuthRequiredError()

    token = credentials.credentials
    payload = decode_token(token)  # Lève InvalidTokenError ou TokenExpiredError

    # Vérifier que c'est bien un access token
    if payload.get("type") != "access":
        raise InvalidTokenError()

    # Vérifier que le token n'est pas blacklisté
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise InvalidTokenError()

    user_id = int(payload.get("sub", 0))
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AuthRequiredError()

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dépendance : vérifie que l'utilisateur a le rôle admin.
    Lève AdminRequiredError sinon.
    """
    if not current_user.is_admin:
        raise AdminRequiredError()
    return current_user


async def get_refresh_token_user(
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dépendance : retourne l'utilisateur depuis le refresh token (cookie HttpOnly).
    """
    if not refresh_token:
        raise AuthRequiredError()

    from app.core.security import decode_token
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise InvalidTokenError()

    user_id = int(payload.get("sub", 0))
    jti = payload.get("jti")

    # Vérifier que le JTI correspond à celui stocké dans Redis
    stored_jti = await get_stored_refresh_jti(user_id)
    if not stored_jti or stored_jti != jti:
        raise InvalidTokenError()

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AuthRequiredError()

    return user
