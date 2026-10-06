# =============================================================================
# CyberLearn — Schémas Badge (Pydantic v2)
# Fonctionnalité : UC13 — badges et récompenses
# =============================================================================

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BadgePublic(BaseModel):
    """Badge visible par le joueur."""
    id: int
    name: str
    description: str
    icon_url: Optional[str] = None
    condition_type: str
    condition_value: int

    model_config = {"from_attributes": True}


class UserBadgeResponse(BaseModel):
    """Badge obtenu par un joueur avec date d'obtention."""
    badge_id: int
    name: str
    description: str
    icon_url: Optional[str] = None
    earned_at: datetime

    model_config = {"from_attributes": True}


class BadgeCreate(BaseModel):
    """Création d'un badge (admin)."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str
    icon_url: Optional[str] = None
    condition_type: str
    condition_value: int = Field(..., ge=1)
    condition_chapter_id: Optional[int] = None
