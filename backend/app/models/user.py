# =============================================================================
# CyberLearn — Modèle User (SQLAlchemy)
# Fonctionnalité : UC01 inscription, UC02 connexion, UC10 progression
# =============================================================================

import enum
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    pseudo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_verified_18: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.user,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ─── Relations ────────────────────────────────────────────────────────────
    sessions: Mapped[list["GameSession"]] = relationship(  # noqa: F821
        "GameSession", back_populates="user", lazy="select"
    )
    user_badges: Mapped[list["UserBadge"]] = relationship(  # noqa: F821
        "UserBadge", back_populates="user", lazy="select"
    )

    # ─── Propriétés calculées ─────────────────────────────────────────────────

    @property
    def age(self) -> int:
        """Calcule l'âge exact du joueur à aujourd'hui."""
        today = date.today()
        age = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age

    @property
    def is_adult(self) -> bool:
        """Vérifie que le joueur a au moins 18 ans."""
        return self.age >= 18

    @property
    def is_admin(self) -> bool:
        """Vérifie que l'utilisateur a le rôle admin."""
        return self.role == UserRole.admin

    def __repr__(self) -> str:
        return f"<User id={self.id} pseudo={self.pseudo} level={self.level}>"
