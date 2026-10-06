# =============================================================================
# CyberLearn — Sécurité : JWT, bcrypt, vérification âge 18+
# =============================================================================

import hashlib
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import (
    AgeVerificationError,
    InvalidTokenError,
    TokenExpiredError,
)

# ─── Contexte bcrypt ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Hachage mots de passe ───────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt (coût 12)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash stocké."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── Vérification de l'âge (PEGI 18+) ───────────────────────────────────────

def calculate_age(birth_date: date) -> int:
    """
    Calcule l'âge exact en années à la date d'aujourd'hui.
    Prend en compte le jour et le mois (pas seulement l'année).
    """
    today = date.today()
    age = today.year - birth_date.year
    # Soustraire 1 si l'anniversaire n'est pas encore passé cette année
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def verify_minimum_age(birth_date: date) -> int:
    """
    Vérifie que l'utilisateur a l'âge minimum requis (18 ans).
    Lève AgeVerificationError si l'utilisateur est mineur.
    Retourne l'âge calculé si la vérification réussit.

    Fonctionnalité de conception : UC01 — Vérification âge 18+ côté serveur
    """
    age = calculate_age(birth_date)
    if age < settings.minimum_age:
        raise AgeVerificationError()
    return age


# ─── Hachage SHA-256 solutions de jeu ────────────────────────────────────────

def hash_solution(solution: str) -> str:
    """
    Hash une solution de mission avec SHA-256.
    Utilisé pour stocker les solutions sans les exposer en clair.
    """
    return hashlib.sha256(solution.strip().lower().encode()).hexdigest()


def verify_solution(submitted: str, stored_hash: str) -> bool:
    """
    Vérifie qu'une solution soumise correspond au hash stocké.
    Insensible à la casse et aux espaces.

    Fonctionnalité de conception : UC06 — Validation solution côté serveur
    """
    submitted_hash = hash_solution(submitted)
    return submitted_hash == stored_hash


# ─── Tokens JWT ───────────────────────────────────────────────────────────────

def create_access_token(user_id: int, role: str) -> str:
    """
    Crée un JWT access token (durée : 1h par défaut).
    Payload : user_id, role, type=access, jti unique, exp.
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> tuple[str, str]:
    """
    Crée un JWT refresh token (durée : 7j par défaut).
    Retourne (token, jti) — le jti est stocké dans Redis.
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti


def decode_token(token: str) -> dict:
    """
    Décode et valide un JWT.
    Lève InvalidTokenError ou TokenExpiredError si invalide.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise TokenExpiredError()
        raise InvalidTokenError()


def get_token_jti(token: str) -> Optional[str]:
    """Extrait le JTI d'un token sans valider l'expiration."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False},
        )
        return payload.get("jti")
    except Exception:
        return None
