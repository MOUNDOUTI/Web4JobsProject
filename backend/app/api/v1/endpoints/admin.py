# =============================================================================
# CyberLearn — Endpoints Admin
# UC-A1: CRUD missions/chapitres, UC-A2: statistiques
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_admin
from app.db.database import get_db
from app.models.badge import Badge
from app.models.chapter import Chapter
from app.models.game_session import GameSession, SessionStatus
from app.models.mission import Mission
from app.models.user import User
from app.schemas.badge import BadgeCreate
from app.schemas.mission import ChapterCreate, ChapterUpdate, MissionCreate, MissionUpdate

router = APIRouter(prefix="/admin", tags=["Administration"])


# ─── Chapitres ────────────────────────────────────────────────────────────────

@router.post("/chapters", status_code=201, summary="UC-A1 — Créer un chapitre")
async def create_chapter(
    data: ChapterCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    chapter = Chapter(**data.model_dump())
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)
    return {"id": chapter.id, "title": chapter.title, "message": "Chapitre créé."}


@router.put("/chapters/{chapter_id}", summary="UC-A1 — Modifier un chapitre")
async def update_chapter(
    chapter_id: int,
    data: ChapterUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre introuvable.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(chapter, field, value)
    await db.flush()
    return {"message": "Chapitre mis à jour."}


@router.delete("/chapters/{chapter_id}", summary="UC-A1 — Désactiver un chapitre")
async def delete_chapter(
    chapter_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapitre introuvable.")
    chapter.is_active = False
    await db.flush()
    return {"message": "Chapitre désactivé."}


# ─── Missions ─────────────────────────────────────────────────────────────────

@router.post("/missions", status_code=201, summary="UC-A1 — Créer une mission")
async def create_mission(
    data: MissionCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # Vérifier que le chapitre existe
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.id == data.chapter_id)
    )
    if not chapter_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapitre introuvable.")

    mission = Mission(**data.model_dump())
    db.add(mission)
    await db.flush()
    await db.refresh(mission)
    return {"id": mission.id, "title": mission.title, "message": "Mission créée."}


@router.put("/missions/{mission_id}", summary="UC-A1 — Modifier une mission")
async def update_mission(
    mission_id: int,
    data: MissionUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission introuvable.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(mission, field, value)
    await db.flush()
    return {"message": "Mission mise à jour."}


@router.delete("/missions/{mission_id}", summary="UC-A1 — Désactiver une mission")
async def delete_mission(
    mission_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission introuvable.")
    mission.is_active = False
    await db.flush()
    return {"message": "Mission désactivée."}


# ─── Badges ───────────────────────────────────────────────────────────────────

@router.post("/badges", status_code=201, summary="Créer un badge")
async def create_badge(
    data: BadgeCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    badge = Badge(**data.model_dump())
    db.add(badge)
    await db.flush()
    await db.refresh(badge)
    return {"id": badge.id, "name": badge.name, "message": "Badge créé."}


# ─── Statistiques ─────────────────────────────────────────────────────────────

@router.get("/stats", summary="UC-A2 — Statistiques de la plateforme")
async def get_platform_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retourne les statistiques globales de la plateforme."""
    total_users = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    total_sessions = await db.execute(select(func.count(GameSession.id)))
    completed_sessions = await db.execute(
        select(func.count(GameSession.id)).where(
            GameSession.status == SessionStatus.completed
        )
    )
    total_missions = await db.execute(
        select(func.count(Mission.id)).where(Mission.is_active == True)
    )
    total_xp_distributed = await db.execute(
        select(func.sum(GameSession.xp_earned))
    )

    return {
        "total_users": total_users.scalar() or 0,
        "total_sessions": total_sessions.scalar() or 0,
        "completed_sessions": completed_sessions.scalar() or 0,
        "total_missions": total_missions.scalar() or 0,
        "total_xp_distributed": total_xp_distributed.scalar() or 0,
    }


@router.get("/users", summary="Liste des utilisateurs")
async def list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(100)
    )
    users = result.scalars().all()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "pseudo": u.pseudo,
                "level": u.level,
                "total_xp": u.total_xp,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at,
            }
            for u in users
        ]
    }
