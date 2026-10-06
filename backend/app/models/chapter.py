# =============================================================================
# CyberLearn — Modèle Chapter (SQLAlchemy)
# Fonctionnalité : UC11 catalogue, structure narrative du jeu
# =============================================================================

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    narrative_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    unlock_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ─── Relations ────────────────────────────────────────────────────────────
    missions: Mapped[list["Mission"]] = relationship(  # noqa: F821
        "Mission",
        back_populates="chapter",
        order_by="Mission.order_num",
        lazy="select",
    )

    def is_unlocked_for(self, user_level: int) -> bool:
        """Vérifie si ce chapitre est débloqué pour un niveau donné."""
        return user_level >= self.unlock_level

    def __repr__(self) -> str:
        return f"<Chapter id={self.id} title={self.title} order={self.order_num}>"
