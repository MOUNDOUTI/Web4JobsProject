# =============================================================================
# CyberLearn — RecommendationService
# Fonctionnalité : UC14 — Recommandations de missions adaptées
# =============================================================================

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter import Chapter
from app.models.game_session import GameSession, SessionStatus
from app.models.mission import Mission
from app.models.user import User


class RecommendationService:
    """
    Service de recommandation de missions.
    Stratégie : progression linéaire + révision adaptative si faible score.
    Fonctionnalité de conception : UC14
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recommendations(self, user: User, limit: int = 5) -> list[dict]:
        """
        Retourne les missions recommandées pour un joueur.

        Logique :
        1. Priorité : mission en cours (reprise)
        2. Prochaine mission non complétée dans le chapitre courant
        3. Missions avec faible score (révision)
        4. Prochaine mission débloquée dans l'ordre narratif
        """
        recommendations = []

        # 1. Session en cours → reprendre
        active = await self._get_active_session(user.id)
        if active:
            recommendations.append({
                "mission_id": active["mission_id"],
                "mission_title": active["mission_title"],
                "chapter_title": active["chapter_title"],
                "reason": "Reprendre votre mission en cours",
                "priority": 1,
                "session_id": active["session_id"],
            })

        # 2. Missions avec faible score → révision
        low_score = await self._get_low_score_missions(user.id, user.level)
        for m in low_score[:2]:
            if m["mission_id"] not in [r["mission_id"] for r in recommendations]:
                recommendations.append({
                    "mission_id": m["mission_id"],
                    "mission_title": m["mission_title"],
                    "chapter_title": m["chapter_title"],
                    "reason": f"Améliorez votre score ({m['best_score']}/100)",
                    "priority": 2,
                    "session_id": None,
                })

        # 3. Prochaine mission débloquée non complétée
        next_missions = await self._get_next_unlocked_missions(user.id, user.level)
        for m in next_missions:
            if len(recommendations) >= limit:
                break
            if m["mission_id"] not in [r["mission_id"] for r in recommendations]:
                recommendations.append({
                    "mission_id": m["mission_id"],
                    "mission_title": m["mission_title"],
                    "chapter_title": m["chapter_title"],
                    "reason": "Prochaine mission de votre parcours",
                    "priority": 3,
                    "session_id": None,
                })

        return recommendations[:limit]

    async def _get_active_session(self, user_id: int) -> dict | None:
        """Récupère la session de jeu en cours si elle existe."""
        result = await self.db.execute(
            select(GameSession, Mission, Chapter)
            .join(Mission, GameSession.mission_id == Mission.id)
            .join(Chapter, Mission.chapter_id == Chapter.id)
            .where(
                GameSession.user_id == user_id,
                GameSession.status == SessionStatus.in_progress,
            )
            .limit(1)
        )
        row = result.first()
        if not row:
            return None
        session, mission, chapter = row
        return {
            "session_id": session.id,
            "mission_id": mission.id,
            "mission_title": mission.title,
            "chapter_title": chapter.title,
        }

    async def _get_low_score_missions(
        self, user_id: int, user_level: int
    ) -> list[dict]:
        """Missions complétées avec un score < 70 (candidates à révision)."""
        result = await self.db.execute(
            select(
                Mission.id,
                Mission.title,
                Chapter.title.label("chapter_title"),
                func.max(GameSession.score).label("best_score"),
            )
            .join(GameSession, GameSession.mission_id == Mission.id)
            .join(Chapter, Mission.chapter_id == Chapter.id)
            .where(
                GameSession.user_id == user_id,
                GameSession.status == SessionStatus.completed,
                Chapter.unlock_level <= user_level,
                Mission.is_active == True,
            )
            .group_by(Mission.id, Mission.title, Chapter.title)
            .having(func.max(GameSession.score) < 70)
            .order_by(func.max(GameSession.score).asc())
            .limit(3)
        )
        return [
            {
                "mission_id": row.id,
                "mission_title": row.title,
                "chapter_title": row.chapter_title,
                "best_score": row.best_score,
            }
            for row in result.fetchall()
        ]

    async def _get_next_unlocked_missions(
        self, user_id: int, user_level: int
    ) -> list[dict]:
        """Prochaines missions débloquées non complétées dans l'ordre narratif."""
        completed_result = await self.db.execute(
            select(GameSession.mission_id)
            .where(
                GameSession.user_id == user_id,
                GameSession.status == SessionStatus.completed,
            )
        )
        completed_ids = {row[0] for row in completed_result.fetchall()}

        result = await self.db.execute(
            select(Mission, Chapter)
            .join(Chapter, Mission.chapter_id == Chapter.id)
            .where(
                Chapter.unlock_level <= user_level,
                Chapter.is_active == True,
                Mission.is_active == True,
            )
            .order_by(Chapter.order_num.asc(), Mission.order_num.asc())
        )
        missions = []
        for mission, chapter in result.fetchall():
            if mission.id not in completed_ids:
                missions.append({
                    "mission_id": mission.id,
                    "mission_title": mission.title,
                    "chapter_title": chapter.title,
                })
        return missions[:5]
