# =============================================================================
# CyberLearn — Modèles Badge et UserBadge (SQLAlchemy)
# Fonctionnalité : UC13 — badges, système de récompenses
# =============================================================================

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class BadgeCondition(str, enum.Enum):
    mission_count = "mission_count"       # Nombre total de missions complétées
    chapter_complete = "chapter_complete" # Chapitre spécifique complété
    xp_total = "xp_total"                # XP total atteint
    perfect_score = "perfect_score"       # Score parfait sur N missions
    no_hint = "no_hint"                   # N missions sans indice
    first_mission = "first_mission"       # Première mission (onboarding)


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    condition_type: Mapped[BadgeCondition] = mapped_column(
        Enum(BadgeCondition, name="badge_condition"), nullable=False
    )
    # Valeur associée à la condition (ex: 5 pour "5 missions complétées")
    condition_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Pour chapter_complete : chapter_id cible
    condition_chapter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ─── Relations ────────────────────────────────────────────────────────────
    user_badges: Mapped[list["UserBadge"]] = relationship(
        "UserBadge", back_populates="badge"
    )

    def __repr__(self) -> str:
        return f"<Badge id={self.id} name={self.name}>"


class UserBadge(Base):
    """Table d'association User ↔ Badge avec date d'obtention."""
    __tablename__ = "user_badges"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True, nullable=False
    )
    badge_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("badges.id"),
        primary_key=True, nullable=False
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ─── Relations ────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="user_badges")  # noqa: F821
    badge: Mapped["Badge"] = relationship("Badge", back_populates="user_badges")

    def __repr__(self) -> str:
        return f"<UserBadge user={self.user_id} badge={self.badge_id}>"
