# =============================================================================
# CyberLearn — Service IA (FastAPI microservice)
# Fonctionnalité : UC14 — Recommandation content-based filtering
# Port : 8001
# =============================================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from loguru import logger

from app.recommendation_engine import RecommendationEngine

engine = RecommendationEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🤖 Démarrage du service IA CyberLearn...")
    try:
        await engine.fit()
        logger.info(f"✅ Modèle entraîné sur {engine.n_games} missions")
    except Exception as e:
        logger.warning(f"⚠️  Entraînement initial échoué : {e}")
    yield
    logger.info("🛑 Arrêt du service IA")


app = FastAPI(
    title="CyberLearn AI Service",
    version="1.0.0",
    description="Service de recommandation de missions",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "fitted": engine.is_fitted,
        "games_indexed": engine.n_games,
    }


@app.get("/api/recommend/{user_id}")
async def recommend_for_user(user_id: int, n: int = 5):
    """
    Recommandations personnalisées pour un joueur.
    Fonctionnalité : UC14
    """
    if not engine.is_fitted:
        return JSONResponse(status_code=503, content={"error": "Modèle non disponible"})
    try:
        game_ids = await engine.get_user_recommendations(user_id, n)
        return {"game_ids": game_ids, "user_id": user_id}
    except Exception as e:
        logger.error(f"Erreur recommandation user={user_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/similar/{mission_id}")
async def similar_missions(mission_id: int, n: int = 5):
    """Missions similaires à une mission donnée."""
    if not engine.is_fitted:
        return JSONResponse(status_code=503, content={"error": "Modèle non disponible"})
    try:
        game_ids = engine.get_similar(mission_id, n)
        return {"game_ids": game_ids, "mission_id": mission_id}
    except Exception as e:
        logger.error(f"Erreur similaires mission={mission_id}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/retrain")
async def retrain():
    """Ré-entraîne le modèle sur les données actuelles."""
    try:
        await engine.fit()
        return {"message": "Modèle ré-entraîné", "games_indexed": engine.n_games}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
