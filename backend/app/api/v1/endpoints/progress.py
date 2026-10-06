# =============================================================================
# CyberLearn — Endpoints Progression
# UC10: tableau de bord, UC13: badges, historique sessions
# =============================================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import get_current_user
from app.db.database import get_db
from app.models.badge import Badge, UserBadge
from app.models.chapter import Chapter
from app.models.game_session import GameSession, SessionStatus
from app.models.mission import Mission
from app.models.user import User
from app.services.progression_service import (
    LEVEL_NAMES,
    LEVEL_THRESHOLDS,
    ProgressionService,
    get_xp_to_next_level,
)

router = APIRouter(prefix="/progress", tags=["Progression"])


@router.get(
    "/me",
    summary="UC10 — Tableau de bord de progression",
)
async def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retourne le tableau de bord complet du joueur :
    XP, niveau, badges, statistiques, prochains déblocages.
    """
    service = ProgressionService(db)
    stats = await service.get_user_stats(current_user)

    # Infos sur les niveaux
    next_level = current_user.level + 1 if current_user.level < 5 else None
    xp_to_next = get_xp_to_next_level(current_user.total_xp, current_user.level)

    return {
        **stats,
        "level_name": LEVEL_NAMES.get(current_user.level, "Recrue"),
        "next_level": next_level,
        "next_level_name": LEVEL_NAMES.get(next_level) if next_level else None,
        "xp_to_next_level": xp_to_next,
        "level_thresholds": LEVEL_THRESHOLDS,
    }


@router.get(
    "/me/badges",
    summary="UC13 — Badges obtenus par le joueur",
)
async def get_my_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retourne la liste des badges obtenus par le joueur
    avec leur date d'obtention.
    """
    result = await db.execute(
        select(UserBadge, Badge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == current_user.id)
        .order_by(UserBadge.earned_at.desc())
    )
    rows = result.fetchall()

    badges = []
    for user_badge, badge in rows:
        badges.append({
            "badge_id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "icon_url": badge.icon_url,
            "condition_type": badge.condition_type.value,
            "earned_at": user_badge.earned_at,
        })

    # Tous les badges disponibles (pour afficher ceux non encore obtenus)
    all_badges_result = await db.execute(select(Badge))
    all_badges = all_badges_result.scalars().all()
    earned_ids = {b["badge_id"] for b in badges}

    locked_badges = [
        {
            "badge_id": b.id,
            "name": b.name,
            "description": b.description,
            "icon_url": b.icon_url,
            "condition_type": b.condition_type.value,
            "condition_value": b.condition_value,
            "earned": False,
        }
        for b in all_badges if b.id not in earned_ids
    ]

    return {
        "earned_badges": badges,
        "earned_count": len(badges),
        "locked_badges": locked_badges,
        "total_badges": len(all_badges),
    }


@router.get(
    "/me/history",
    summary="Historique des sessions de jeu",
)
async def get_my_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    Retourne l'historique paginé des sessions de jeu du joueur.
    """
    result = await db.execute(
        select(GameSession, Mission, Chapter)
        .join(Mission, GameSession.mission_id == Mission.id)
        .join(Chapter, Mission.chapter_id == Chapter.id)
        .where(GameSession.user_id == current_user.id)
        .order_by(desc(GameSession.started_at))
        .limit(limit)
        .offset(offset)
    )
    rows = result.fetchall()

    history = []
    for session, mission, chapter in rows:
        history.append({
            "session_id": session.id,
            "mission_id": mission.id,
            "mission_title": mission.title,
            "chapter_title": chapter.title,
            "status": session.status.value,
            "score": session.score,
            "xp_earned": session.xp_earned,
            "hints_used": session.hints_used,
            "attempts": session.attempts,
            "duration_seconds": session.duration_seconds,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
        })

    return {
        "history": history,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/leaderboard",
    summary="Classement des joueurs",
)
async def get_leaderboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Retourne le classement des joueurs par XP total.
    """
    result = await db.execute(
        select(User)
        .where(User.is_active == True, User.is_verified_18 == True)
        .order_by(desc(User.total_xp))
        .limit(limit)
    )
    users = result.scalars().all()

    leaderboard = []
    for rank, user in enumerate(users, start=1):
        leaderboard.append({
            "rank": rank,
            "user_id": user.id,
            "pseudo": user.pseudo,
            "level": user.level,
            "level_name": LEVEL_NAMES.get(user.level, "Recrue"),
            "total_xp": user.total_xp,
            "avatar_url": user.avatar_url,
            "is_current_user": user.id == current_user.id,
        })

    # Position du joueur courant si pas dans le top
    current_user_in_top = any(e["is_current_user"] for e in leaderboard)
    current_user_rank = None
    if not current_user_in_top:
        rank_result = await db.execute(
            select(User)
            .where(
                User.is_active == True,
                User.total_xp > current_user.total_xp,
            )
        )
        current_user_rank = len(rank_result.scalars().all()) + 1

    return {
        "leaderboard": leaderboard,
        "current_user_rank": current_user_rank,
        "current_user_xp": current_user.total_xp,
    }
