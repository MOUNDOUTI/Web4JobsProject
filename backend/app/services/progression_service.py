# =============================================================================
# CyberLearn — ProgressionService
# Fonctionnalité : UC10, UC13 — XP, niveaux, badges
# Diagramme d'état 8 : niveaux joueur Recrue → Agent Élite
# =============================================================================

from typing import Optional
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import Badge, BadgeCondition, UserBadge
from app.models.game_session import GameSession, SessionStatus
from app.models.user import User


# ─── Seuils XP par niveau (diagramme d'état 8) ───────────────────────────────
LEVEL_THRESHOLDS = {
    1: 0,
    2: 200,
    3: 500,
    4: 1000,
    5: 2000,
}

LEVEL_NAMES = {
    1: "Recrue",
    2: "Analyste Junior",
    3: "Investigateur Cyber",
    4: "Expert en Sécurité",
    5: "Agent Élite CSDF",
}

# Chapitres débloqués par niveau
LEVEL_UNLOCKS = {
    1: [1],
    2: [1, 2],
    3: [1, 2, 3, 4],
    4: [1, 2, 3, 4, 5, 6],
    5: [1, 2, 3, 4, 5, 6, 7],
}


def calculate_level(total_xp: int) -> int:
    """Calcule le niveau correspondant à un total XP."""
    level = 1
    for lvl, threshold in sorted(LEVEL_THRESHOLDS.items(), reverse=True):
        if total_xp >= threshold:
            level = lvl
            break
    return level


def get_xp_to_next_level(total_xp: int, current_level: int) -> int:
    """Calcule les XP restants pour atteindre le niveau suivant."""
    if current_level >= 5:
        return 0
    next_threshold = LEVEL_THRESHOLDS.get(current_level + 1, 0)
    return max(0, next_threshold - total_xp)


class ProgressionService:
    """
    Service de progression — gère XP, niveaux et badges.
    Fonctionnalité de conception : UC10 tableau de bord, UC13 badges
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def award_xp(self, user: User, xp: int) -> dict:
        """
        Attribue des XP à un joueur et recalcule son niveau.

        Returns:
            dict avec old_level, new_level, level_up (bool), xp_earned
        """
        old_level = user.level
        user.total_xp += xp
        new_level = calculate_level(user.total_xp)
        level_up = new_level > old_level

        if level_up:
            user.level = new_level
            logger.info(
                f"Joueur id={user.id} monte au niveau {new_level} "
                f"({LEVEL_NAMES[new_level]}) — total XP: {user.total_xp}"
            )

        await self.db.flush()

        return {
            "old_level": old_level,
            "new_level": new_level,
            "level_up": level_up,
            "xp_earned": xp,
            "total_xp": user.total_xp,
            "level_name": LEVEL_NAMES[new_level],
        }

    async def check_and_award_badges(self, user: User) -> list[dict]:
        """
        Vérifie toutes les conditions de badge pour un joueur
        et attribue ceux qui ne sont pas encore obtenus.

        Fonctionnalité de conception : UC13 — badges
        Returns: liste des nouveaux badges obtenus
        """
        # Récupérer tous les badges non encore obtenus
        already_earned_result = await self.db.execute(
            select(UserBadge.badge_id).where(UserBadge.user_id == user.id)
        )
        already_earned_ids = {row[0] for row in already_earned_result.fetchall()}

        all_badges_result = await self.db.execute(select(Badge))
        all_badges = all_badges_result.scalars().all()

        new_badges = []

        for badge in all_badges:
            if badge.id in already_earned_ids:
                continue

            if await self._check_badge_condition(user, badge):
                user_badge = UserBadge(user_id=user.id, badge_id=badge.id)
                self.db.add(user_badge)
                new_badges.append({
                    "id": badge.id,
                    "name": badge.name,
                    "description": badge.description,
                    "icon_url": badge.icon_url,
                })
                logger.info(f"Badge '{badge.name}' attribué au joueur id={user.id}")

        if new_badges:
            await self.db.flush()

        return new_badges

    async def _check_badge_condition(self, user: User, badge: Badge) -> bool:
        """Vérifie si un joueur remplit la condition d'un badge."""

        if badge.condition_type == BadgeCondition.first_mission:
            # Première mission complétée
            result = await self.db.execute(
                select(func.count(GameSession.id)).where(
                    GameSession.user_id == user.id,
                    GameSession.status == SessionStatus.completed,
                )
            )
            return (result.scalar() or 0) >= 1

        if badge.condition_type == BadgeCondition.mission_count:
            result = await self.db.execute(
                select(func.count(GameSession.id)).where(
                    GameSession.user_id == user.id,
                    GameSession.status == SessionStatus.completed,
                )
            )
            return (result.scalar() or 0) >= badge.condition_value

        if badge.condition_type == BadgeCondition.xp_total:
            return user.total_xp >= badge.condition_value

        if badge.condition_type == BadgeCondition.chapter_complete:
            # Toutes les missions du chapitre complétées
            from app.models.mission import Mission
            missions_result = await self.db.execute(
                select(func.count(Mission.id)).where(
                    Mission.chapter_id == badge.condition_chapter_id,
                    Mission.is_active == True,
                )
            )
            total_missions = missions_result.scalar() or 0
            if total_missions == 0:
                return False

            completed_result = await self.db.execute(
                select(func.count(GameSession.id)).join(
                    GameSession.mission
                ).where(
                    GameSession.user_id == user.id,
                    GameSession.status == SessionStatus.completed,
                    Mission.chapter_id == badge.condition_chapter_id,
                )
            )
            completed = completed_result.scalar() or 0
            return completed >= total_missions

        if badge.condition_type == BadgeCondition.perfect_score:
            result = await self.db.execute(
                select(func.count(GameSession.id)).where(
                    GameSession.user_id == user.id,
                    GameSession.status == SessionStatus.completed,
                    GameSession.score == 100,
                )
            )
            return (result.scalar() or 0) >= badge.condition_value

        if badge.condition_type == BadgeCondition.no_hint:
            result = await self.db.execute(
                select(func.count(GameSession.id)).where(
                    GameSession.user_id == user.id,
                    GameSession.status == SessionStatus.completed,
                    GameSession.hints_used == 0,
                )
            )
            return (result.scalar() or 0) >= badge.condition_value

        return False

    async def get_user_stats(self, user: User) -> dict:
        """Calcule les statistiques complètes d'un joueur."""
        from app.models.mission import Mission

        completed_result = await self.db.execute(
            select(func.count(GameSession.id)).where(
                GameSession.user_id == user.id,
                GameSession.status == SessionStatus.completed,
            )
        )
        missions_completed = completed_result.scalar() or 0

        abandoned_result = await self.db.execute(
            select(func.count(GameSession.id)).where(
                GameSession.user_id == user.id,
                GameSession.status == SessionStatus.abandoned,
            )
        )
        missions_abandoned = abandoned_result.scalar() or 0

        total_result = await self.db.execute(
            select(func.count(GameSession.id)).where(
                GameSession.user_id == user.id,
            )
        )
        total_sessions = total_result.scalar() or 0

        time_result = await self.db.execute(
            select(func.sum(GameSession.duration_seconds)).where(
                GameSession.user_id == user.id,
                GameSession.duration_seconds.isnot(None),
            )
        )
        total_time = time_result.scalar() or 0

        badges_result = await self.db.execute(
            select(func.count(UserBadge.badge_id)).where(
                UserBadge.user_id == user.id,
            )
        )
        badges_count = badges_result.scalar() or 0

        return {
            "user_id": user.id,
            "pseudo": user.pseudo,
            "level": user.level,
            "total_xp": user.total_xp,
            "xp_to_next_level": get_xp_to_next_level(user.total_xp, user.level),
            "missions_completed": missions_completed,
            "missions_abandoned": missions_abandoned,
            "total_sessions": total_sessions,
            "total_play_time_seconds": total_time,
            "badges_count": badges_count,
            "current_level_name": LEVEL_NAMES.get(user.level, "Recrue"),
        }
