# =============================================================================
# CyberLearn — Moteur de recommandation (content-based filtering)
# TF-IDF sur description + one-hot difficulty/type
# =============================================================================

import os
from typing import Optional
import asyncpg
import numpy as np
from loguru import logger

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from scipy.sparse import hstack, csr_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn non disponible — mode fallback activé")


class RecommendationEngine:
    def __init__(self):
        self.is_fitted = False
        self.n_games = 0
        self._mission_ids: list[int] = []
        self._similarity_matrix: Optional[np.ndarray] = None
        self._tfidf = TfidfVectorizer(max_features=300, stop_words=None) if SKLEARN_AVAILABLE else None

    async def fit(self) -> None:
        """Entraîne le modèle TF-IDF sur toutes les missions actives."""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn absent — recommandation désactivée")
            return

        db_url = os.getenv("DATABASE_URL", "")
        # Convertir URL asyncpg
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

        try:
            conn = await asyncpg.connect(db_url)
            rows = await conn.fetch("""
                SELECT m.id, m.title, m.description, m.mission_type, m.difficulty,
                       COALESCE(array_to_string(m.skills_targeted, ' '), '') as skills
                FROM missions m
                WHERE m.is_active = true
                ORDER BY m.id
            """)
            await conn.close()
        except Exception as e:
            logger.error(f"Erreur connexion DB pour IA : {e}")
            return

        if not rows:
            logger.warning("Aucune mission en base pour entraîner le modèle")
            return

        self._mission_ids = [r["id"] for r in rows]
        self.n_games = len(rows)

        # Feature engineering
        texts = [
            f"{r['title']} {r['description']} {r['skills']} {r['mission_type']} {r['difficulty']}"
            for r in rows
        ]

        # TF-IDF
        tfidf_matrix = self._tfidf.fit_transform(texts)

        # One-hot difficulty (pondération 1.5)
        difficulties = ["beginner", "intermediate", "advanced", "expert"]
        diff_matrix = np.array([
            [1.5 if r["difficulty"] == d else 0 for d in difficulties]
            for r in rows
        ])

        # One-hot mission type (pondération 1.5)
        types = ["terminal", "log_analysis", "quiz", "network_config", "code_review", "cryptography", "incident_report"]
        type_matrix = np.array([
            [1.5 if r["mission_type"] == t else 0 for t in types]
            for r in rows
        ])

        # Combinaison des features
        feature_matrix = hstack([
            tfidf_matrix,
            csr_matrix(diff_matrix),
            csr_matrix(type_matrix),
        ])

        self._similarity_matrix = cosine_similarity(feature_matrix, feature_matrix)
        self.is_fitted = True
        logger.info(f"Modèle entraîné sur {self.n_games} missions")

    def get_similar(self, mission_id: int, n: int = 5) -> list[int]:
        """Retourne les N missions les plus similaires à mission_id."""
        if not self.is_fitted or mission_id not in self._mission_ids:
            return []
        idx = self._mission_ids.index(mission_id)
        scores = self._similarity_matrix[idx]
        sorted_indices = np.argsort(scores)[::-1]
        result = []
        for i in sorted_indices:
            if self._mission_ids[i] != mission_id:
                result.append(self._mission_ids[i])
            if len(result) >= n:
                break
        return result

    async def get_user_recommendations(self, user_id: int, n: int = 5) -> list[int]:
        """
        Recommandations personnalisées basées sur l'historique du joueur.
        Calcule un profil moyen des missions jouées et trouve les plus similaires.
        """
        if not self.is_fitted:
            return []

        db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")

        try:
            conn = await asyncpg.connect(db_url)
            played = await conn.fetch("""
                SELECT DISTINCT mission_id FROM game_sessions
                WHERE user_id = $1 AND status = 'completed'
            """, user_id)
            await conn.close()
        except Exception as e:
            logger.error(f"Erreur DB recommandations user={user_id}: {e}")
            return self._get_popular()

        played_ids = {r["mission_id"] for r in played}

        if not played_ids:
            # Pas d'historique → missions débutant dans l'ordre
            return [
                mid for mid in self._mission_ids[:n]
                if mid not in played_ids
            ]

        # Profil utilisateur = moyenne des vecteurs des missions jouées
        valid_indices = [
            self._mission_ids.index(mid)
            for mid in played_ids
            if mid in self._mission_ids
        ]

        if not valid_indices:
            return self._get_popular()

        user_profile = np.mean(
            [self._similarity_matrix[i] for i in valid_indices], axis=0
        )

        sorted_indices = np.argsort(user_profile)[::-1]
        result = []
        for i in sorted_indices:
            mid = self._mission_ids[i]
            if mid not in played_ids:
                result.append(mid)
            if len(result) >= n:
                break

        return result

    def _get_popular(self) -> list[int]:
        """Fallback : retourne les premières missions (ordre narratif)."""
        return self._mission_ids[:5] if self._mission_ids else []
