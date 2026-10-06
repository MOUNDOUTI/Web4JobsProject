# =============================================================================
# CyberLearn — GameEngine
# Fonctionnalité : UC04-UC09 — cœur du moteur de jeu
# Diagramme de séquence 4 : lancement → terminal → validation → résultats
# Diagramme d'état 7 : IN_PROGRESS → COMPLETED / TIMEOUT / ABANDONED
# =============================================================================

from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    MissionLockedError,
    MissionNotFoundError,
    NoHintsRemainingError,
    RateLimitSubmitError,
    SessionAccessDeniedError,
    SessionAlreadyActiveError,
    SessionNotActiveError,
    SessionNotFoundError,
)
from app.core.security import verify_solution
from app.db.redis import (
    delete_session_data,
    get_session_data,
    get_submit_attempts,
    increment_submit_attempts,
    set_session_data,
)
from app.models.game_session import GameSession, SessionStatus
from app.models.mission import Mission
from app.models.user import User
from app.services.progression_service import ProgressionService
from app.services.scoring_service import ScoringService


class GameEngine:
    """
    Moteur de jeu central de CyberLearn.
    Orchestre : démarrage session, terminal, validation, scoring, progression.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.scoring = ScoringService()
        self.progression = ProgressionService(db)

    # ─── UC04 — Démarrer une mission ─────────────────────────────────────────

    async def start_mission(self, user: User, mission_id: int) -> GameSession:
        """
        Démarre une session de jeu pour une mission.

        Fonctionnalité de conception : UC04 — Lancer une mission
        Vérifie : mission active, niveau suffisant, pas de session déjà active.
        """
        # 1. Récupérer la mission
        result = await self.db.execute(
            select(Mission).where(
                Mission.id == mission_id,
                Mission.is_active == True,
            )
        )
        mission = result.scalar_one_or_none()
        if not mission:
            raise MissionNotFoundError(mission_id)

        # 2. Vérifier que le chapitre est débloqué pour ce joueur
        chapter_result = await self.db.execute(
            select(Mission).where(Mission.id == mission_id)
        )
        from app.models.chapter import Chapter
        chapter_res = await self.db.execute(
            select(Chapter).where(Chapter.id == mission.chapter_id)
        )
        chapter = chapter_res.scalar_one_or_none()
        if chapter and not chapter.is_unlocked_for(user.level):
            raise MissionLockedError(required_level=chapter.unlock_level)

        # 3. Vérifier qu'il n'y a pas déjà une session active
        active_session_result = await self.db.execute(
            select(GameSession).where(
                GameSession.user_id == user.id,
                GameSession.mission_id == mission_id,
                GameSession.status == SessionStatus.in_progress,
            )
        )
        existing = active_session_result.scalar_one_or_none()
        if existing:
            raise SessionAlreadyActiveError(session_id=existing.id)

        # 4. Créer la session
        session = GameSession(
            user_id=user.id,
            mission_id=mission_id,
            status=SessionStatus.in_progress,
            score=0,
            hints_used=0,
            attempts=0,
            xp_earned=0,
            session_data={
                "terminal_history": [],
                "current_question_index": 0,
                "answered_questions": [],
            },
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        # 5. Stocker l'état initial dans Redis (accès rapide pendant le jeu)
        await set_session_data(session.id, {
            "user_id": user.id,
            "mission_id": mission_id,
            "terminal_history": [],
            "score": 0,
            "hints_used": 0,
            "attempts": 0,
            "started_at": session.started_at.isoformat(),
        })

        logger.info(
            f"Session démarrée : id={session.id} "
            f"user={user.id} mission={mission_id}"
        )
        return session

    # ─── UC05 — Commande terminal ─────────────────────────────────────────────

    async def process_terminal_command(
        self, session_id: int, user_id: int, command: str
    ) -> dict:
        """
        Traite une commande saisie dans le terminal simulé.

        Fonctionnalité de conception : UC05 — Terminal simulé
        La commande est recherchée dans la config JSONB de la mission.
        """
        session, mission = await self._get_active_session_and_mission(
            session_id, user_id
        )

        # Récupérer l'output contextuel depuis la config de la mission
        output = mission.get_terminal_output(command)

        # Mettre à jour l'historique dans Redis
        redis_data = await get_session_data(session_id) or {}
        history = redis_data.get("terminal_history", [])
        history.append({"cmd": command, "output": output})
        redis_data["terminal_history"] = history[-50:]  # Garder les 50 dernières
        await set_session_data(session_id, redis_data)

        # Synchroniser dans session_data PostgreSQL
        session.session_data = {
            **session.session_data,
            "terminal_history": redis_data["terminal_history"],
        }
        await self.db.flush()

        logger.debug(f"Terminal cmd='{command}' session={session_id}")
        return {
            "command": command,
            "output": output,
            "session_id": session_id,
        }

    # ─── UC06 — Soumission solution ───────────────────────────────────────────

    async def submit_solution(
        self, session_id: int, user_id: int, answer: str
    ) -> dict:
        """
        Valide une solution soumise par le joueur.

        Fonctionnalité de conception : UC06 — Soumettre une solution
        La validation est exclusivement côté serveur (SHA-256).
        La solution n'est jamais transmise au client.
        """
        session, mission = await self._get_active_session_and_mission(
            session_id, user_id
        )

        # Rate limiting : max 10 tentatives par session
        attempts_count = await get_submit_attempts(session_id)
        if attempts_count >= settings.rate_limit_submit_per_session:
            raise RateLimitSubmitError(max_attempts=settings.rate_limit_submit_per_session)

        # Vérification de la solution (SHA-256 côté serveur)
        solution_hash = mission.get_solution_hash()
        is_correct = False

        if solution_hash:
            is_correct = verify_solution(answer, solution_hash)
        elif mission.mission_type.value == "quiz":
            is_correct = await self._validate_quiz_answer(session, mission, answer)

        session.attempts += 1

        if not is_correct:
            # Incrémenter compteur Redis anti-brute force
            await increment_submit_attempts(session_id)
            await self.db.flush()
            logger.debug(
                f"Solution incorrecte — session={session_id} "
                f"tentative={session.attempts}"
            )
            return {
                "correct": False,
                "message": "Réponse incorrecte. Réessayez !",
                "explanation": None,
                "score": session.score,
                "attempts": session.attempts,
                "session_completed": False,
            }

        # Solution correcte — calculer le score final
        elapsed = session.elapsed_seconds
        score = self.scoring.calculate_score(
            elapsed_seconds=elapsed,
            time_limit=mission.time_limit_seconds,
            hints_used=session.hints_used,
            attempts=session.attempts,
        )
        session.score = score

        # Compléter la session
        result = await self._complete_session(session, mission, user_id)

        logger.info(
            f"Solution correcte — session={session_id} "
            f"score={score} xp={result['xp_earned']}"
        )
        return {
            "correct": True,
            "message": "Bravo ! Solution correcte !",
            "explanation": mission.config.get("explanation", ""),
            "score": score,
            "attempts": session.attempts,
            "session_completed": True,
            **result,
        }

    # ─── UC07 — Indice ────────────────────────────────────────────────────────

    async def use_hint(self, session_id: int, user_id: int) -> dict:
        """
        Fournit un indice au joueur (avec malus sur le score).

        Fonctionnalité de conception : UC07 — Demander un indice
        """
        session, mission = await self._get_active_session_and_mission(
            session_id, user_id
        )

        max_hints = mission.get_max_hints()
        if session.hints_used >= max_hints:
            raise NoHintsRemainingError()

        hint = mission.get_hint(session.hints_used)
        session.hints_used += 1
        await self.db.flush()

        hints_remaining = max_hints - session.hints_used
        logger.debug(
            f"Indice #{session.hints_used} utilisé — session={session_id}"
        )

        return {
            "hint": hint,
            "hint_index": session.hints_used - 1,
            "hints_remaining": hints_remaining,
            "score_penalty": 10,
        }

    # ─── Abandon de session ───────────────────────────────────────────────────

    async def abandon_session(self, session_id: int, user_id: int) -> dict:
        """
        Abandonne une session de jeu.

        Diagramme d'état : IN_PROGRESS → ABANDONED
        """
        session, mission = await self._get_active_session_and_mission(
            session_id, user_id
        )

        now = datetime.now(timezone.utc)
        elapsed = session.elapsed_seconds

        session.status = SessionStatus.abandoned
        session.completed_at = now
        session.duration_seconds = elapsed
        session.xp_earned = 0
        await self.db.flush()

        # Supprimer l'état Redis
        await delete_session_data(session_id)

        logger.info(f"Session abandonnée : id={session_id}")
        return {
            "session_id": session_id,
            "status": "abandoned",
            "message": "Session abandonnée.",
        }

    # ─── Résultats ────────────────────────────────────────────────────────────

    async def get_session_results(self, session_id: int, user_id: int) -> dict:
        """
        Retourne les résultats d'une session terminée — UC09.
        """
        result = await self.db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise SessionNotFoundError(session_id)
        if session.user_id != user_id:
            raise SessionAccessDeniedError()

        mission_result = await self.db.execute(
            select(Mission).where(Mission.id == session.mission_id)
        )
        mission = mission_result.scalar_one_or_none()

        return {
            "session_id": session.id,
            "mission_id": session.mission_id,
            "mission_title": mission.title if mission else "",
            "status": session.status.value,
            "score": session.score,
            "max_score": 100,
            "score_percentage": round(session.score, 1),
            "xp_earned": session.xp_earned,
            "hints_used": session.hints_used,
            "attempts": session.attempts,
            "duration_seconds": session.duration_seconds,
            "narrative_outro": mission.narrative_outro if mission else None,
            "new_badges": session.session_data.get("new_badges", []),
            "level_up": session.session_data.get("level_up"),
        }

    # ─── Méthodes privées ─────────────────────────────────────────────────────

    async def _get_active_session_and_mission(
        self, session_id: int, user_id: int
    ) -> tuple[GameSession, Mission]:
        """Récupère une session active et sa mission, avec vérifications."""
        result = await self.db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise SessionNotFoundError(session_id)
        if session.user_id != user_id:
            raise SessionAccessDeniedError()
        if session.status != SessionStatus.in_progress:
            raise SessionNotActiveError()

        mission_result = await self.db.execute(
            select(Mission).where(Mission.id == session.mission_id)
        )
        mission = mission_result.scalar_one_or_none()
        if not mission:
            raise MissionNotFoundError(session.mission_id)

        return session, mission

    async def _complete_session(
        self, session: GameSession, mission: Mission, user_id: int
    ) -> dict:
        """
        Complète une session : met à jour le statut, attribue XP et badges.
        Diagramme d'état : IN_PROGRESS → COMPLETED
        """
        now = datetime.now(timezone.utc)
        elapsed = session.elapsed_seconds

        session.status = SessionStatus.completed
        session.completed_at = now
        session.duration_seconds = elapsed

        # Calculer XP
        xp = self.scoring.calculate_xp(
            base_xp=mission.xp_reward,
            score=session.score,
            hints_used=session.hints_used,
        )
        session.xp_earned = xp

        # Récupérer le joueur et attribuer XP
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        progression_result = None
        new_badges = []

        if user:
            progression_result = await self.progression.award_xp(user, xp)
            new_badges = await self.progression.check_and_award_badges(user)

        # Sauvegarder les résultats dans session_data
        session.session_data = {
            **session.session_data,
            "new_badges": new_badges,
            "level_up": progression_result.get("new_level") if progression_result and progression_result.get("level_up") else None,
        }
        await self.db.flush()

        # Nettoyer Redis
        await delete_session_data(session.id)

        return {
            "xp_earned": xp,
            "new_badges": new_badges,
            "level_up": progression_result.get("new_level") if progression_result and progression_result.get("level_up") else None,
        }

    async def _validate_quiz_answer(
        self, session: GameSession, mission: Mission, answer: str
    ) -> bool:
        """Valide une réponse de quiz selon la config de la mission."""
        questions = mission.get_questions()
        answered = session.session_data.get("answered_questions", [])
        current_idx = len(answered)

        if current_idx >= len(questions):
            return True

        question = questions[current_idx]
        correct_index = question.get("correct", -1)
        options = question.get("options", [])

        # Accepte l'index (int sous forme str) ou le texte de la réponse
        try:
            submitted_index = int(answer)
            is_correct = submitted_index == correct_index
        except ValueError:
            is_correct = (
                answer.strip().lower() == options[correct_index].strip().lower()
                if 0 <= correct_index < len(options)
                else False
            )

        # Enregistrer la réponse
        answered.append({
            "question_id": current_idx,
            "answer": answer,
            "correct": is_correct,
        })
        session.session_data = {
            **session.session_data,
            "answered_questions": answered,
        }

        # Le quiz est complet quand toutes les questions ont été répondues
        all_answered = len(answered) >= len(questions)
        if all_answered:
            correct_count = sum(1 for a in answered if a["correct"])
            return correct_count >= len(questions) * 0.7  # 70% minimum

        return False
