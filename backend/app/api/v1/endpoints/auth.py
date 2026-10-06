# =============================================================================
# CyberLearn — Endpoints Auth
# UC01: inscription, UC02: connexion, UC03: déconnexion, refresh token
# =============================================================================

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_refresh_token_user
from app.core.config import settings
from app.core.security import create_access_token
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="UC01 — Inscription avec vérification 18+",
)
async def register(
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Crée un nouveau compte utilisateur.

    - Vérifie que l'utilisateur a **18 ans ou plus** côté serveur (non contournable)
    - Hash le mot de passe avec bcrypt (coût 12)
    - Retourne un access token JWT + pose un cookie HttpOnly pour le refresh token

    Erreurs possibles:
    - 403: AgeVerificationError (mineur)
    - 409: EmailAlreadyExistsError ou PseudoAlreadyExistsError
    - 422: ValidationError (format invalide)
    """
    service = AuthService(db)
    user, access_token, refresh_token = await service.register(data)

    # Poser le refresh token en cookie HttpOnly (inaccessible au JS)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        pseudo=user.pseudo,
        role=user.role.value,
        level=user.level,
        total_xp=user.total_xp,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="UC02 — Connexion",
)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Authentifie un utilisateur.

    - Rate limiting : 5 tentatives max / 15 min par email
    - Retourne un access token JWT + pose un cookie refresh token

    Erreurs possibles:
    - 401: InvalidCredentialsError
    - 429: AccountLockedError (trop de tentatives)
    """
    service = AuthService(db)
    user, access_token, refresh_token = await service.login(data)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        pseudo=user.pseudo,
        role=user.role.value,
        level=user.level,
        total_xp=user.total_xp,
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Renouvellement de l'access token",
)
async def refresh_token(
    response: Response,
    user: User = Depends(get_refresh_token_user),
):
    """
    Renouvelle l'access token à partir du refresh token (cookie HttpOnly).

    Erreurs possibles:
    - 401: AuthRequiredError, InvalidTokenError
    """
    new_access_token = create_access_token(user.id, user.role.value)
    return RefreshResponse(access_token=new_access_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="UC03 — Déconnexion",
)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Déconnecte l'utilisateur.

    - Supprime le refresh token de Redis (révocation immédiate)
    - Efface le cookie refresh token
    """
    service = AuthService(db)
    await service.logout(current_user.id)

    response.delete_cookie(key="refresh_token", path="/api/v1/auth")

    return MessageResponse(message="Déconnexion réussie.")


@router.get(
    "/me",
    summary="Profil de l'utilisateur connecté",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retourne les informations de l'utilisateur authentifié."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "pseudo": current_user.pseudo,
        "level": current_user.level,
        "total_xp": current_user.total_xp,
        "role": current_user.role.value,
        "is_verified_18": current_user.is_verified_18,
        "avatar_url": current_user.avatar_url,
        "bio": current_user.bio,
        "created_at": current_user.created_at,
    }
