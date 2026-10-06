"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2025-07-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Énumérations ──────────────────────────────────────────────────────────
    op.execute("CREATE TYPE user_role AS ENUM ('user', 'admin')")
    op.execute("""
        CREATE TYPE mission_type AS ENUM (
            'terminal', 'log_analysis', 'quiz',
            'network_config', 'code_review', 'cryptography', 'incident_report'
        )
    """)
    op.execute("""
        CREATE TYPE difficulty_level AS ENUM (
            'beginner', 'intermediate', 'advanced', 'expert'
        )
    """)
    op.execute("""
        CREATE TYPE session_status AS ENUM (
            'in_progress', 'completed', 'abandoned', 'timeout'
        )
    """)
    op.execute("""
        CREATE TYPE badge_condition AS ENUM (
            'mission_count', 'chapter_complete', 'xp_total',
            'perfect_score', 'no_hint', 'first_mission'
        )
    """)

    # ── Table users ───────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("pseudo", sa.String(50), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("birth_date", sa.Date, nullable=False),
        sa.Column("is_verified_18", sa.Boolean, default=False, nullable=False),
        sa.Column("total_xp", sa.Integer, default=0, nullable=False),
        sa.Column("level", sa.Integer, default=1, nullable=False),
        sa.Column("role", sa.Enum("user", "admin", name="user_role"), default="user", nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("bio", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_pseudo", "users", ["pseudo"])

    # ── Table chapters ────────────────────────────────────────────────────────
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("order_num", sa.Integer, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("narrative_context", sa.Text, nullable=True),
        sa.Column("unlock_level", sa.Integer, default=1, nullable=False),
        sa.Column("cover_image_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Table missions ────────────────────────────────────────────────────────
    op.create_table(
        "missions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("chapter_id", sa.Integer, sa.ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("order_num", sa.Integer, nullable=False),
        sa.Column("mission_type", sa.Enum(
            "terminal", "log_analysis", "quiz", "network_config",
            "code_review", "cryptography", "incident_report",
            name="mission_type"
        ), nullable=False),
        sa.Column("difficulty", sa.Enum(
            "beginner", "intermediate", "advanced", "expert",
            name="difficulty_level"
        ), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("narrative_intro", sa.Text, nullable=True),
        sa.Column("narrative_outro", sa.Text, nullable=True),
        sa.Column("skills_targeted", ARRAY(sa.String), nullable=True),
        sa.Column("xp_reward", sa.Integer, default=20, nullable=False),
        sa.Column("time_limit_seconds", sa.Integer, default=1800, nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_missions_chapter_id", "missions", ["chapter_id"])

    # ── Table game_sessions ───────────────────────────────────────────────────
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mission_id", sa.Integer, sa.ForeignKey("missions.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Integer, default=0, nullable=False),
        sa.Column("hints_used", sa.SmallInteger, default=0, nullable=False),
        sa.Column("attempts", sa.Integer, default=0, nullable=False),
        sa.Column("xp_earned", sa.Integer, default=0, nullable=False),
        sa.Column("status", sa.Enum(
            "in_progress", "completed", "abandoned", "timeout",
            name="session_status"
        ), default="in_progress", nullable=False),
        sa.Column("session_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("duration_seconds", sa.Integer, nullable=True),
    )
    op.create_index("ix_game_sessions_user_id", "game_sessions", ["user_id"])
    op.create_index("ix_game_sessions_mission_id", "game_sessions", ["mission_id"])
    op.create_index("ix_game_sessions_status", "game_sessions", ["status"])

    # ── Table badges ──────────────────────────────────────────────────────────
    op.create_table(
        "badges",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("icon_url", sa.String(500), nullable=True),
        sa.Column("condition_type", sa.Enum(
            "mission_count", "chapter_complete", "xp_total",
            "perfect_score", "no_hint", "first_mission",
            name="badge_condition"
        ), nullable=False),
        sa.Column("condition_value", sa.Integer, default=1, nullable=False),
        sa.Column("condition_chapter_id", sa.Integer, nullable=True),
    )

    # ── Table user_badges ─────────────────────────────────────────────────────
    op.create_table(
        "user_badges",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("badge_id", sa.Integer, sa.ForeignKey("badges.id"), primary_key=True),
        sa.Column("earned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Extension full-text search ────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def downgrade() -> None:
    op.drop_table("user_badges")
    op.drop_table("badges")
    op.drop_table("game_sessions")
    op.drop_table("missions")
    op.drop_table("chapters")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS badge_condition")
    op.execute("DROP TYPE IF EXISTS session_status")
    op.execute("DROP TYPE IF EXISTS difficulty_level")
    op.execute("DROP TYPE IF EXISTS mission_type")
    op.execute("DROP TYPE IF EXISTS user_role")
