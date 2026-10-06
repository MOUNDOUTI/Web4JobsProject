# =============================================================================
# CyberLearn — Endpoints Catalogue
# UC11: carte du jeu, UC12: statut des missions
# =============================================================================

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import get_current_user
from app.db.database import get_db
from app.models.chapter import Chapter
from app.models.game_session import GameSession, SessionStatus
from app.models.mission import Mission
from app.models.user import User
from app.services.progression_service import LEVEL_UNLOCKS

router = APIRouter(prefix="/catalogue", tags=["Catalogue"])


@router.get(
    "/chapters",
    summary="UC11 — Carte du jeu (liste des chapitres)",
)
async def get_chapters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retourne tous les chapitres avec leur statut de progression pour le joueur.
    Indique quels chapitres sont débloqués selon le niveau du joueur.
    """
    result = await db.execute(
        select(Chapter)
        .where(Chapter.is_active == True)
        .order_by(Chapter.order_num.asc())
        .options(selectinload(Chapter.missions))
    )
    chapters = result.scalars().all()

    # Récupérer les missions complétées par le joueur
    completed_result = await db.execute(
        select(GameSession.mission_id).where(
            GameSession.user_id == current_user.id,
            GameSession.status == SessionStatus.completed,
        )
    )
    completed_mission_ids = {row[0] for row in completed_result.fetchall()}

    # Récupérer les meilleures sessions par mission
    best_scores_result = await db.execute(
        select(
            GameSession.mission_id,
            func.max(GameSession.score).label("best_score"),
        )
        .where(
            GameSession.user_id == current_user.id,
            GameSession.status == SessionStatus.completed,
        )
        .group_by(GameSession.mission_id)
    )
    best_scores = {row[0]: row[1] for row in best_scores_result.fetchall()}

    chapters_data = []
    for chapter in chapters:
        is_unlocked = chapter.is_unlocked_for(current_user.level)
        active_missions = [m for m in chapter.missions if m.is_active]
        completed_in_chapter = sum(
            1 for m in active_missions if m.id in completed_mission_ids
        )

        missions_data = []
        for mission in sorted(active_missions, key=lambda m: m.order_num):
            missions_data.append({
                "id": mission.id,
                "title": mission.title,
                "order_num": mission.order_num,
                "mission_type": mission.mission_type.value,
                "difficulty": mission.difficulty.value,
                "xp_reward": mission.xp_reward,
                "time_limit_seconds": mission.time_limit_seconds,
                "skills_targeted": mission.skills_targeted,
                "is_unlocked": is_unlocked,
                "is_completed": mission.id in completed_mission_ids,
                "best_score": best_scores.get(mission.id),
            })

        chapters_data.append({
            "id": chapter.id,
            "title": chapter.title,
            "order_num": chapter.order_num,
            "description": chapter.description,
            "narrative_context": chapter.narrative_context,
            "unlock_level": chapter.unlock_level,
            "cover_image_url": chapter.cover_image_url,
            "is_unlocked": is_unlocked,
            "missions_count": len(active_missions),
            "completed_count": completed_in_chapter,
            "completion_percentage": round(
                (completed_in_chapter / len(active_missions) * 100)
                if active_missions else 0,
                1,
            ),
            "missions": missions_data,
        })

    return {
        "chapters": chapters_data,
        "player_level": current_user.level,
        "total_xp": current_user.total_xp,
    }


@router.get(
    "/missions/{mission_id}",
    summary="Fiche détaillée d'une mission",
)
async def get_mission_detail(
    mission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retourne la fiche complète d'une mission.
    La config sensible (solution_hash) est filtrée — jamais transmise au client.
    """
    result = await db.execute(
        select(Mission, Chapter)
        .join(Chapter, Mission.chapter_id == Chapter.id)
        .where(Mission.id == mission_id, Mission.is_active == True)
    )
    row = result.first()
    if not row:
        from app.core.exceptions import MissionNotFoundError
        raise MissionNotFoundError(mission_id)

    mission, chapter = row

    # Vérifier si débloquée pour ce joueur
    is_unlocked = chapter.is_unlocked_for(current_user.level)

    # Récupérer la meilleure session du joueur
    best_session_result = await db.execute(
        select(GameSession)
        .where(
            GameSession.user_id == current_user.id,
            GameSession.mission_id == mission_id,
            GameSession.status == SessionStatus.completed,
        )
        .order_by(GameSession.score.desc())
        .limit(1)
    )
    best_session = best_session_result.scalar_one_or_none()

    # Config publique — SANS le solution_hash
    public_config = {}
    if mission.mission_type.value == "quiz":
        questions = mission.get_questions()
        # Ne pas envoyer la réponse correcte au client
        public_config["questions"] = [
            {
                "id": i,
                "text": q.get("text"),
                "options": q.get("options", []),
                # "correct" est EXCLU intentionnellement
            }
            for i, q in enumerate(questions)
        ]
        public_config["time_per_question"] = mission.config.get("time_per_question", 30)
    elif mission.mission_type.value == "terminal":
        public_config["available_commands"] = list(
            mission.config.get("terminal_commands", {}).keys()
        ) + ["help", "clear", "whoami", "date", "pwd"]

    return {
        "id": mission.id,
        "title": mission.title,
        "order_num": mission.order_num,
        "mission_type": mission.mission_type.value,
        "difficulty": mission.difficulty.value,
        "description": mission.description,
        "narrative_intro": mission.narrative_intro,
        "skills_targeted": mission.skills_targeted,
        "xp_reward": mission.xp_reward,
        "time_limit_seconds": mission.time_limit_seconds,
        "max_hints": mission.get_max_hints(),
        "chapter_id": chapter.id,
        "chapter_title": chapter.title,
        "is_unlocked": is_unlocked,
        "is_completed": best_session is not None,
        "best_score": best_session.score if best_session else None,
        "public_config": public_config,
    }
