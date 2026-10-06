# =============================================================================
# CyberLearn — Configuration du logging (Loguru)
# =============================================================================

import sys
from loguru import logger
from app.core.config import settings


def setup_logging() -> None:
    """Configure Loguru pour l'application."""

    logger.remove()

    log_level = "DEBUG" if settings.is_development else "INFO"
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        colorize=True,
    )

    if settings.is_production:
        logger.add(
            "logs/cyberlearn_{time:YYYY-MM-DD}.log",
            level="INFO",
            format=log_format,
            rotation="1 day",
            retention="30 days",
            compression="gz",
        )

    logger.info(f"Logging configuré — niveau: {log_level} — env: {settings.app_env}")
