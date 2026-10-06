# =============================================================================
# CyberLearn — Endpoints Recommandation
# UC14: recommandations de missions adaptées
# =============================================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommandations"])


@router.get(
    "/me",
    summary="UC14 — Missions recommandées pour le joueur",
)
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=5, ge=1, le=10),
):
    """
    Retourne les missions recommandées pour le joueur courant.

    Logique de recommandation :
    1. Session en cours → reprendre
    2. Missions avec faible score → révision
    3. Prochaine mission dans l'ordre narratif
    """
    service = RecommendationService(db)
    recommendations = await service.get_recommendations(current_user, limit=limit)

    return {
        "recommendations": recommendations,
        "player_level": current_user.level,
        "total_xp": current_user.total_xp,
    }
