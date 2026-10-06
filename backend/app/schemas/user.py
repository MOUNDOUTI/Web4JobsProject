# =============================================================================
# CyberLearn — Schémas User (Pydantic v2)
# =============================================================================

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    """Données publiques d'un utilisateur."""
    id: int
    pseudo: str
    avatar_url: Optional[str] = None
    level: int
    total_xp: int
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfile(BaseModel):
    """Profil complet de l'utilisateur connecté."""
    id: int
    email: str
    pseudo: str
    birth_date: date
    is_verified_18: bool
    total_xp: int
    level: int
    role: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """Données modifiables du profil."""
    pseudo: Optional[str] = Field(None, min_length=3, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)


class UserStats(BaseModel):
    """Statistiques de progression du joueur."""
    user_id: int
    pseudo: str
    level: int
    total_xp: int
    xp_to_next_level: int
    missions_completed: int
    missions_abandoned: int
    total_sessions: int
    total_play_time_seconds: int
    badges_count: int
    current_level_name: str

    model_config = {"from_attributes": True}
