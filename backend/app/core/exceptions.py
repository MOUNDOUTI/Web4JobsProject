# =============================================================================
# CyberLearn — Exceptions métier
# Toutes les exceptions de l'application avec codes HTTP et messages clairs
# =============================================================================

from fastapi import HTTPException, status


class CyberLearnException(HTTPException):
    """Exception de base pour toutes les erreurs métier CyberLearn."""

    def __init__(self, status_code: int, error_code: str, message: str, details: dict = None):
        super().__init__(status_code=status_code, detail={
            "error": error_code,
            "message": message,
            "details": details or {},
        })
        self.error_code = error_code
        self.message = message
        self.details = details or {}


# ─── Authentification ─────────────────────────────────────────────────────────

class AgeVerificationError(CyberLearnException):
    """Levée quand l'utilisateur a moins de 18 ans (vérification serveur)."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AGE_VERIFICATION_FAILED",
            message="Accès refusé. Ce jeu est réservé aux personnes de 18 ans et plus.",
        )


class InvalidCredentialsError(CyberLearnException):
    """Levée quand email ou mot de passe incorrect."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_CREDENTIALS",
            message="Email ou mot de passe incorrect.",
        )


class TokenExpiredError(CyberLearnException):
    """Levée quand le JWT est expiré."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="TOKEN_EXPIRED",
            message="Session expirée. Veuillez vous reconnecter.",
        )


class InvalidTokenError(CyberLearnException):
    """Levée quand le JWT est invalide ou blacklisté."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_TOKEN",
            message="Token d'authentification invalide.",
        )


class AuthRequiredError(CyberLearnException):
    """Levée quand l'accès nécessite une authentification."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_REQUIRED",
            message="Authentification requise pour accéder à cette ressource.",
        )


class AccountLockedError(CyberLearnException):
    """Levée après trop de tentatives de connexion (rate limiting)."""
    def __init__(self, minutes: int = 15):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="ACCOUNT_LOCKED",
            message=f"Trop de tentatives. Compte temporairement verrouillé pour {minutes} minutes.",
            details={"retry_after_minutes": minutes},
        )


class AdminRequiredError(CyberLearnException):
    """Levée quand une action nécessite le rôle admin."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="ADMIN_REQUIRED",
            message="Accès réservé aux administrateurs.",
        )


# ─── Conflits ─────────────────────────────────────────────────────────────────

class EmailAlreadyExistsError(CyberLearnException):
    """Levée quand l'email est déjà utilisé."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="EMAIL_ALREADY_EXISTS",
            message="Cette adresse email est déjà associée à un compte.",
        )


class PseudoAlreadyExistsError(CyberLearnException):
    """Levée quand le pseudo est déjà utilisé."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="PSEUDO_ALREADY_EXISTS",
            message="Ce pseudo est déjà utilisé. Veuillez en choisir un autre.",
        )


# ─── Ressources introuvables ──────────────────────────────────────────────────

class MissionNotFoundError(CyberLearnException):
    def __init__(self, mission_id: int = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="MISSION_NOT_FOUND",
            message=f"Mission {'#' + str(mission_id) if mission_id else ''} introuvable.",
        )


class ChapterNotFoundError(CyberLearnException):
    def __init__(self, chapter_id: int = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="CHAPTER_NOT_FOUND",
            message=f"Chapitre {'#' + str(chapter_id) if chapter_id else ''} introuvable.",
        )


class SessionNotFoundError(CyberLearnException):
    def __init__(self, session_id: int = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SESSION_NOT_FOUND",
            message=f"Session de jeu {'#' + str(session_id) if session_id else ''} introuvable.",
        )


class UserNotFoundError(CyberLearnException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="USER_NOT_FOUND",
            message="Utilisateur introuvable.",
        )


# ─── Règles métier du jeu ─────────────────────────────────────────────────────

class MissionLockedError(CyberLearnException):
    """Levée quand le joueur n'a pas le niveau requis pour accéder à la mission."""
    def __init__(self, required_level: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="MISSION_LOCKED",
            message=f"Mission verrouillée. Niveau {required_level} requis.",
            details={"required_level": required_level},
        )


class SessionAlreadyActiveError(CyberLearnException):
    """Levée quand une session est déjà en cours pour cette mission."""
    def __init__(self, session_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="SESSION_ALREADY_ACTIVE",
            message="Une session est déjà en cours pour cette mission.",
            details={"active_session_id": session_id},
        )


class SessionNotActiveError(CyberLearnException):
    """Levée quand on tente d'agir sur une session qui n'est pas IN_PROGRESS."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="SESSION_NOT_ACTIVE",
            message="Cette session n'est plus active.",
        )


class SessionAccessDeniedError(CyberLearnException):
    """Levée quand un joueur tente d'accéder à la session d'un autre."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="SESSION_ACCESS_DENIED",
            message="Accès à cette session refusé.",
        )


class RateLimitSubmitError(CyberLearnException):
    """Levée après trop de tentatives de soumission sur une mission."""
    def __init__(self, max_attempts: int = 10):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_SUBMIT",
            message=f"Trop de tentatives ({max_attempts} max). Attendez avant de réessayer.",
            details={"max_attempts": max_attempts},
        )


class NoHintsRemainingError(CyberLearnException):
    """Levée quand tous les indices ont été utilisés."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="NO_HINTS_REMAINING",
            message="Vous avez utilisé tous les indices disponibles pour cette mission.",
        )
