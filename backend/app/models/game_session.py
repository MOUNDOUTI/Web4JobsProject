# =============================================================================
# CyberLearn — Modèle GameSession (SQLAlchemy)
# Fonctionnalité : UC04-UC09 — cycle de vie d'une session de jeu
# Diagramme d'état : IN_PROGRESS → COMPLETED / TIMEOUT / ABANDONED
# =============================================================================

import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey,
    Integer, SmallInteger, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.database import Base


class SessionStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"
    timeout = "timeout"


class GameSession(Base):
    __tablename__ = "game_sessions"

    # Contrainte : 1 seule session IN_PROGRESS par (user, mission)
    __table_args__ = (
        UniqueConstraint(
            "user_id", "mission_id",
            name="uq_active_session",
            # Cette contrainte est partielle — gérée au niveau applicatif
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("missions.id"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hints_used: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        default=SessionStatus.in_progress,
        nullable=False,
        index=True,
    )
    # État interne de la session : historique commandes, progression quiz, etc.
    session_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ─── Relations ────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="sessions")  # noqa: F821
    mission: Mapped["Mission"] = relationship("Mission", back_populates="sessions")  # noqa: F821

    # ─── Propriétés ───────────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        return self.status == SessionStatus.in_progress

    @property
    def elapsed_seconds(self) -> int:
        """Temps écoulé depuis le début de la session."""
        now = datetime.now(timezone.utc)
        start = self.started_at
        if start.tzinfo is None:
            from datetime import timezone as tz
            start = start.replace(tzinfo=tz.utc)
        return int((now - start).total_seconds())

    def __repr__(self) -> str:
        return (
            f"<GameSession id={self.id} user={self.user_id} "
            f"mission={self.mission_id} status={self.status}>"
        )
