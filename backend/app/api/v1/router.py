# =============================================================================
# CyberLearn — Router principal API v1
# =============================================================================

from fastapi import APIRouter

from app.api.v1.endpoints import auth, sessions, catalogue, progress, recommend, admin

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(sessions.router)
api_router.include_router(catalogue.router)
api_router.include_router(progress.router)
api_router.include_router(recommend.router)
api_router.include_router(admin.router)
