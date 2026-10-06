# =============================================================================
# CyberLearn — Modèle Mission (SQLAlchemy)
# Fonctionnalité : UC04-UC09 — jeu, terminal, quiz, validation
# La colonne config (JSONB) contient : solution_hash, terminal_commands, hints, questions
# =============================================================================

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text, func
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class MissionType(str, enum.Enum):
    terminal = "terminal"
    log_analysis = "log_analysis"
    quiz = "quiz"
    network_config = "network_config"
    code_review = "code_review"
    cryptography = "cryptography"
    incident_report = "incident_report"


class DifficultyLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)
    mission_type: Mapped[MissionType] = mapped_column(
        Enum(MissionType, name="mission_type"), nullable=False
    )
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    narrative_intro: Mapped[str | None] = mapped_column(Text, nullable=True)
    narrative_outro: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_targeted: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    xp_reward: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    time_limit_seconds: Mapped[int] = mapped_column(Integer, default=1800, nullable=False)

    # ─── Config JSONB ─────────────────────────────────────────────────────────
    # Contient selon le type :
    # terminal : { solution_hash, terminal_commands: {cmd: output}, hints: [], max_hints }
    # quiz     : { questions: [{text, options, correct, explanation}], time_per_question }
    # etc.
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ─── Relations ────────────────────────────────────────────────────────────
    chapter: Mapped["Chapter"] = relationship(  # noqa: F821
        "Chapter", back_populates="missions"
    )
    sessions: Mapped[list["GameSession"]] = relationship(  # noqa: F821
        "GameSession", back_populates="mission", lazy="select"
    )

    # ─── Méthodes métier ──────────────────────────────────────────────────────

    def get_solution_hash(self) -> str | None:
        """Retourne le hash SHA-256 de la solution (jamais la solution en clair)."""
        return self.config.get("solution_hash")

    def get_hint(self, hint_index: int) -> str | None:
        """Retourne un indice par son index (0-based)."""
        hints = self.config.get("hints", [])
        if 0 <= hint_index < len(hints):
            return hints[hint_index]
        return None

    def get_max_hints(self) -> int:
        """Retourne le nombre maximum d'indices disponibles."""
        return len(self.config.get("hints", []))

    def get_terminal_output(self, command: str) -> str:
        """
        Retourne l'output d'une commande dans le terminal simulé.
        Fonctionnalité : UC05 — Terminal simulé
        """
        commands = self.config.get("terminal_commands", {})
        cmd_lower = command.strip().lower()

        # Recherche exacte d'abord
        if cmd_lower in commands:
            return commands[cmd_lower]

        # Commandes génériques toujours disponibles
        generic = {
            "help": self._get_help_text(commands),
            "clear": "",
            "whoami": "agent_chen",
            "date": "Mon Sep 14 2026",
            "pwd": "/home/agent_chen/missions",
            "exit": "Impossible de quitter la mission en cours.",
        }
        if cmd_lower in generic:
            return generic[cmd_lower]

        return f"bash: {command}: commande introuvable. Tapez 'help' pour la liste des commandes."

    def _get_help_text(self, commands: dict) -> str:
        available = list(commands.keys()) + ["help", "clear", "whoami", "date", "pwd"]
        return "Commandes disponibles :\n  " + "\n  ".join(sorted(set(available)))

    def get_questions(self) -> list[dict]:
        """Retourne les questions pour les missions de type quiz."""
        return self.config.get("questions", [])

    def __repr__(self) -> str:
        return f"<Mission id={self.id} title={self.title} type={self.mission_type}>"
