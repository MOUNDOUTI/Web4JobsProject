# =============================================================================
# CyberLearn — Schémas Mission et Chapter (Pydantic v2)
# Fonctionnalité : UC04, UC11, UC12 — catalogue et jeu
# =============================================================================

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─── Chapter ──────────────────────────────────────────────────────────────────

class ChapterBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    order_num: int = Field(..., ge=1)
    description: str
    narrative_context: Optional[str] = None
    unlock_level: int = Field(default=1, ge=1, le=5)
    cover_image_url: Optional[str] = None


class ChapterCreate(ChapterBase):
    pass


class ChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    narrative_context: Optional[str] = None
    unlock_level: Optional[int] = Field(None, ge=1, le=5)
    cover_image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ChapterPublic(ChapterBase):
    id: int
    is_active: bool
    missions_count: int = 0
    completed_count: int = 0     # Missions complétées par le joueur
    is_unlocked: bool = False    # Débloqué pour le joueur courant
    created_at: datetime

    model_config = {"from_attributes": True}


class ChapterWithMissions(ChapterPublic):
    missions: List["MissionPublic"] = []


# ─── Mission ──────────────────────────────────────────────────────────────────

class MissionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    order_num: int = Field(..., ge=1)
    mission_type: str
    difficulty: str
    description: str
    narrative_intro: Optional[str] = None
    narrative_outro: Optional[str] = None
    skills_targeted: Optional[List[str]] = None
    xp_reward: int = Field(default=20, ge=1, le=500)
    time_limit_seconds: int = Field(default=1800, ge=60)


class MissionCreate(MissionBase):
    chapter_id: int
    config: Dict[str, Any] = Field(default_factory=dict)


class MissionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    narrative_intro: Optional[str] = None
    narrative_outro: Optional[str] = None
    xp_reward: Optional[int] = None
    time_limit_seconds: Optional[int] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class MissionPublic(MissionBase):
    id: int
    chapter_id: int
    is_active: bool
    is_unlocked: bool = False      # Débloqué pour le joueur courant
    is_completed: bool = False     # Complété par le joueur courant
    best_score: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MissionDetail(MissionPublic):
    """Fiche complète d'une mission (sans la config sensible)."""
    chapter_title: str = ""
    # La config est filtrée — pas de solution_hash côté client !
    public_config: Dict[str, Any] = {}


# ─── Mise à jour des références circulaires ───────────────────────────────────
ChapterWithMissions.model_rebuild()
