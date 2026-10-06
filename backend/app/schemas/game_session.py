# =============================================================================
# CyberLearn — Schémas GameSession (Pydantic v2)
# Fonctionnalité : UC04-UC09 — session, terminal, submit, résultats
# =============================================================================

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SessionStartResponse(BaseModel):
    """Réponse au démarrage d'une session — UC04."""
    session_id: int
    mission_id: int
    mission_title: str
    mission_type: str
    narrative_intro: str
    time_limit_seconds: int
    max_hints: int
    started_at: datetime

    model_config = {"from_attributes": True}


class TerminalCommandRequest(BaseModel):
    """Commande envoyée au terminal simulé — UC05."""
    command: str = Field(..., min_length=1, max_length=200)


class TerminalCommandResponse(BaseModel):
    """Réponse du terminal simulé."""
    command: str
    output: str
    session_id: int


class SubmitSolutionRequest(BaseModel):
    """Soumission d'une solution — UC06."""
    answer: str = Field(..., min_length=1, max_length=500)


class SubmitSolutionResponse(BaseModel):
    """Retour après soumission d'une solution."""
    correct: bool
    message: str
    explanation: Optional[str] = None    # Explication pédagogique si correct
    score: int                            # Score actuel
    attempts: int                         # Nombre de tentatives
    session_completed: bool = False       # True si la mission est terminée


class HintResponse(BaseModel):
    """Indice demandé — UC07."""
    hint: str
    hint_index: int
    hints_remaining: int
    score_penalty: int                    # Points perdus (-10 par indice)


class SessionResultResponse(BaseModel):
    """Résultats finaux d'une session — UC09."""
    session_id: int
    mission_id: int
    mission_title: str
    status: str
    score: int
    max_score: int = 100
    score_percentage: float
    xp_earned: int
    hints_used: int
    attempts: int
    duration_seconds: Optional[int]
    narrative_outro: Optional[str]        # Texte narratif post-mission
    new_badges: List[Dict[str, Any]] = [] # Badges débloqués durant cette session
    level_up: Optional[int] = None        # Nouveau niveau si montée de niveau

    model_config = {"from_attributes": True}


class SessionHistoryItem(BaseModel):
    """Élément de l'historique des sessions."""
    session_id: int
    mission_id: int
    mission_title: str
    chapter_title: str
    status: str
    score: int
    xp_earned: int
    started_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}
