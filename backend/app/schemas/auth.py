# =============================================================================
# CyberLearn — Schémas Auth (Pydantic v2)
# Fonctionnalité : UC01 inscription, UC02 connexion, UC03 déconnexion
# =============================================================================

import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    """Données d'inscription — UC01."""
    email: EmailStr
    pseudo: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str
    birth_date: date
    accept_terms: bool

    @field_validator("pseudo")
    @classmethod
    def pseudo_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError("Le pseudo ne peut contenir que des lettres, chiffres, _ et -")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un caractère spécial")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.password_confirm:
            raise ValueError("Les mots de passe ne correspondent pas")
        return self

    @field_validator("accept_terms")
    @classmethod
    def must_accept_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Vous devez accepter les conditions d'utilisation")
        return v


class LoginRequest(BaseModel):
    """Données de connexion — UC02."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Réponse après inscription/connexion réussie."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    pseudo: str
    role: str
    level: int
    total_xp: int


class RefreshResponse(BaseModel):
    """Réponse après renouvellement du token."""
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Réponse générique avec message."""
    message: str
