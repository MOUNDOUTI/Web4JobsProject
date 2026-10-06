# =============================================================================
# CyberLearn — Point d'entrée FastAPI
# Configure : middlewares, CORS, exception handlers, routes, lifecycle
# =============================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import CyberLearnException
from app.core.logging import setup_logging
from app.db.database import check_db_connection, engine
from app.db.redis import check_redis_connection, close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ───────────────────────────────────────────────────────────────
    setup_logging()
    logger.info(f"🎮 Démarrage de {settings.app_name} v{settings.app_version}")
    logger.info(f"   Environnement : {settings.app_env}")

    db_ok = await check_db_connection()
    if not db_ok:
        logger.error("❌ PostgreSQL non disponible — arrêt")
        raise RuntimeError("PostgreSQL non disponible")
    logger.info("✅ PostgreSQL connecté")

    redis_ok = await check_redis_connection()
    if redis_ok:
        try:
            from fastapi_limiter import FastAPILimiter
            redis = await get_redis()
            await FastAPILimiter.init(redis)
            logger.info("✅ Redis connecté + rate limiter initialisé")
        except Exception as e:
            logger.warning(f"⚠️  Rate limiter non initialisé : {e}")
    else:
        logger.warning("⚠️  Redis non disponible")

    logger.info(f"🚀 API disponible sur http://{settings.api_host}:{settings.api_port}")
    logger.info(f"📚 Swagger : http://{settings.api_host}:{settings.api_port}/docs")

    yield

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    logger.info("🛑 Arrêt de l'application...")
    await close_redis()
    await engine.dispose()
    logger.info("✅ Ressources libérées")


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Jeu narratif d'apprentissage de la cybersécurité — PEGI 18+",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["X-Process-Time"],
)


# ── Middleware timing ─────────────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    import time
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{duration:.2f}ms"
    logger.debug(f"{request.method} {request.url.path} → {response.status_code} ({duration:.1f}ms)")
    return response


# ── Middleware sécurité ───────────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ── Exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(CyberLearnException)
async def cyberlearn_exception_handler(request: Request, exc: CyberLearnException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "NOT_FOUND", "message": "Ressource introuvable"},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception(f"Erreur interne : {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "Erreur interne du serveur"},
    )


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["System"])
async def health_check():
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()
    status = "healthy" if (db_ok and redis_ok) else "degraded"
    return JSONResponse(
        status_code=200 if status == "healthy" else 503,
        content={
            "status": status,
            "version": settings.app_version,
            "environment": settings.app_env,
            "services": {
                "database": "up" if db_ok else "down",
                "redis": "up" if redis_ok else "down",
            },
        },
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
