# =============================================================================
# CyberLearn — Endpoints Sessions de Jeu
# UC04: démarrer, UC05: terminal, UC06: soumettre, UC07: indice, UC09: résultats
# =============================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.game_session import (
    HintResponse,
    SessionResultResponse,
    SessionStartResponse,
    SubmitSolutionRequest,
    SubmitSolutionResponse,
    TerminalCommandRequest,
    TerminalCommandResponse,
)
from app.services.game_engine import GameEngine

router = APIRouter(prefix="/sessions", tags=["Sessions de jeu"])


@router.post(
    "/missions/{mission_id}/start",
    response_model=SessionStartResponse,
    status_code=201,
    summary="UC04 — Démarrer une mission",
)
async def start_mission(
    mission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Démarre une session de jeu pour la mission spécifiée.

    - Vérifie que le chapitre est débloqué (niveau joueur suffisant)
    - Vérifie qu'il n'y a pas de session déjà active pour cette mission
    - Crée la session et initialise l'état dans Redis

    Erreurs possibles:
    - 403: MissionLockedError (niveau insuffisant)
    - 404: MissionNotFoundError
    - 409: SessionAlreadyActiveError
    """
    engine = GameEngine(db)
    session = await engine.start_mission(current_user, mission_id)

    from sqlalchemy import select
    from app.models.mission import Mission
    mission_result = await db.execute(
        select(Mission).where(Mission.id == mission_id)
    )
    mission = mission_result.scalar_one_or_none()

    return SessionStartResponse(
        session_id=session.id,
        mission_id=mission.id,
        mission_title=mission.title,
        mission_type=mission.mission_type.value,
        narrative_intro=mission.narrative_intro or "",
        time_limit_seconds=mission.time_limit_seconds,
        max_hints=mission.get_max_hints(),
        started_at=session.started_at,
    )


@router.post(
    "/{session_id}/command",
    response_model=TerminalCommandResponse,
    summary="UC05 — Envoyer une commande au terminal simulé",
)
async def send_command(
    session_id: int,
    data: TerminalCommandRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Traite une commande saisie dans le terminal simulé.

    - Lookup dans la config JSONB de la mission
    - Retourne l'output contextuel préenregistré
    - La solution n'est jamais dans les outputs

    Erreurs possibles:
    - 403: SessionAccessDeniedError
    - 404: SessionNotFoundError
    - 400: SessionNotActiveError
    """
    engine = GameEngine(db)
    result = await engine.process_terminal_command(
        session_id=session_id,
        user_id=current_user.id,
        command=data.command,
    )
    return TerminalCommandResponse(**result)


@router.post(
    "/{session_id}/submit",
    response_model=SubmitSolutionResponse,
    summary="UC06 — Soumettre une solution",
)
async def submit_solution(
    session_id: int,
    data: SubmitSolutionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Valide la solution soumise par le joueur.

    - Validation EXCLUSIVEMENT côté serveur (SHA-256)
    - La solution correcte n'est JAMAIS transmise au client
    - Rate limiting : 10 tentatives max par session

    Erreurs possibles:
    - 403: SessionAccessDeniedError
    - 404: SessionNotFoundError
    - 400: SessionNotActiveError
    - 429: RateLimitSubmitError
    """
    engine = GameEngine(db)
    result = await engine.submit_solution(
        session_id=session_id,
        user_id=current_user.id,
        answer=data.answer,
    )
    return SubmitSolutionResponse(**result)


@router.post(
    "/{session_id}/hint",
    response_model=HintResponse,
    summary="UC07 — Demander un indice",
)
async def get_hint(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fournit un indice au joueur (malus de -10 pts sur le score max).

    Erreurs possibles:
    - 403: SessionAccessDeniedError
    - 404: SessionNotFoundError
    - 400: NoHintsRemainingError, SessionNotActiveError
    """
    engine = GameEngine(db)
    result = await engine.use_hint(
        session_id=session_id,
        user_id=current_user.id,
    )
    return HintResponse(**result)


@router.patch(
    "/{session_id}/abandon",
    response_model=MessageResponse,
    summary="Abandonner une session",
)
async def abandon_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Abandonne la session de jeu en cours.
    Diagramme d'état : IN_PROGRESS → ABANDONED (xp=0)
    """
    engine = GameEngine(db)
    result = await engine.abandon_session(
        session_id=session_id,
        user_id=current_user.id,
    )
    return MessageResponse(message=result["message"])


@router.get(
    "/{session_id}/results",
    response_model=SessionResultResponse,
    summary="UC09 — Résultats d'une session",
)
async def get_results(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retourne les résultats complets d'une session terminée.
    Inclut : score, XP gagné, badges débloqués, narration post-mission.
    """
    engine = GameEngine(db)
    result = await engine.get_session_results(
        session_id=session_id,
        user_id=current_user.id,
    )
    return SessionResultResponse(**result)
