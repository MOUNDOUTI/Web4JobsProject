# =============================================================================
# CyberLearn — AuthService
# Fonctionnalité : UC01 inscription 18+, UC02 connexion, UC03 déconnexion
# Diagramme de séquence : inscription avec double vérification âge
# =============================================================================

from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountLockedError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    PseudoAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_minimum_age,
    verify_password,
)
from app.db.redis import (
    delete_refresh_token,
    get_login_attempts,
    increment_login_attempts,
    reset_login_attempts,
    store_refresh_token,
)
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest


class AuthService:
    """
    Service d'authentification CyberLearn.
    Gère l'inscription avec vérification d'âge, la connexion et la déconnexion.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── UC01 — Inscription ───────────────────────────────────────────────────

    async def register(self, data: RegisterRequest) -> tuple[User, str, str]:
        """
        Inscrit un nouvel utilisateur avec vérification d'âge 18+ côté serveur.

        Fonctionnalité de conception : UC01 — S'inscrire avec vérification 18+
        Diagramme de séquence 3 : flux complet inscription

        Returns:
            (user, access_token, refresh_token)
        Raises:
            AgeVerificationError si âge < 18 ans
            EmailAlreadyExistsError si email déjà utilisé
            PseudoAlreadyExistsError si pseudo déjà utilisé
        """
        # 1. Vérification âge CÔTÉ SERVEUR (non contournable)
        age = verify_minimum_age(data.birth_date)
        logger.info(f"Inscription — âge vérifié : {age} ans ✓")

        # 2. Vérification unicité email
        existing_email = await self.db.execute(
            select(User).where(User.email == data.email.lower())
        )
        if existing_email.scalar_one_or_none():
            raise EmailAlreadyExistsError()

        # 3. Vérification unicité pseudo
        existing_pseudo = await self.db.execute(
            select(User).where(User.pseudo == data.pseudo)
        )
        if existing_pseudo.scalar_one_or_none():
            raise PseudoAlreadyExistsError()

        # 4. Hash du mot de passe (bcrypt coût 12)
        hashed = hash_password(data.password)

        # 5. Création du compte
        user = User(
            email=data.email.lower(),
            pseudo=data.pseudo,
            password_hash=hashed,
            birth_date=data.birth_date,
            is_verified_18=True,   # Positionné après vérification serveur
            total_xp=0,
            level=1,
            role=UserRole.user,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()   # Pour obtenir l'id sans commit
        await self.db.refresh(user)

        # 6. Génération des tokens JWT
        access_token = create_access_token(user.id, user.role.value)
        refresh_token, refresh_jti = create_refresh_token(user.id)

        # 7. Stockage refresh token dans Redis
        await store_refresh_token(
            user.id,
            refresh_jti,
            settings.jwt_refresh_token_expire_days,
        )

        logger.info(f"Nouvel utilisateur créé : id={user.id} pseudo={user.pseudo}")
        return user, access_token, refresh_token

    # ─── UC02 — Connexion ─────────────────────────────────────────────────────

    async def login(self, data: LoginRequest) -> tuple[User, str, str]:
        """
        Authentifie un utilisateur avec rate limiting.

        Fonctionnalité de conception : UC02 — Se connecter
        Raises:
            AccountLockedError après trop de tentatives
            InvalidCredentialsError si email/MDP incorrect
        """
        email = data.email.lower()

        # 1. Vérification rate limiting (max 5 tentatives / 15 min)
        attempts = await get_login_attempts(email)
        if attempts >= settings.rate_limit_auth_per_minute:
            raise AccountLockedError(minutes=15)

        # 2. Recherche de l'utilisateur
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            # Incrémenter les tentatives échouées
            await increment_login_attempts(email)
            remaining = settings.rate_limit_auth_per_minute - (attempts + 1)
            logger.warning(f"Tentative connexion échouée pour {email} ({attempts + 1}/5)")
            raise InvalidCredentialsError()

        # 3. Connexion réussie — reset tentatives
        await reset_login_attempts(email)

        # 4. Génération tokens
        access_token = create_access_token(user.id, user.role.value)
        refresh_token, refresh_jti = create_refresh_token(user.id)

        # 5. Stockage refresh token Redis
        await store_refresh_token(
            user.id,
            refresh_jti,
            settings.jwt_refresh_token_expire_days,
        )

        logger.info(f"Connexion réussie : id={user.id} pseudo={user.pseudo}")
        return user, access_token, refresh_token

    # ─── UC03 — Déconnexion ───────────────────────────────────────────────────

    async def logout(self, user_id: int) -> None:
        """
        Déconnecte l'utilisateur en supprimant le refresh token de Redis.

        Fonctionnalité de conception : UC03 — Se déconnecter
        """
        await delete_refresh_token(user_id)
        logger.info(f"Déconnexion utilisateur id={user_id}")

    # ─── Refresh token ────────────────────────────────────────────────────────

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Récupère un utilisateur par son id."""
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update_profile(self, user: User, pseudo: Optional[str] = None,
                             bio: Optional[str] = None,
                             avatar_url: Optional[str] = None) -> User:
        """Met à jour le profil d'un utilisateur."""
        if pseudo and pseudo != user.pseudo:
            existing = await self.db.execute(
                select(User).where(User.pseudo == pseudo)
            )
            if existing.scalar_one_or_none():
                raise PseudoAlreadyExistsError()
            user.pseudo = pseudo
        if bio is not None:
            user.bio = bio
        if avatar_url is not None:
            user.avatar_url = avatar_url
        await self.db.flush()
        await self.db.refresh(user)
        return user
