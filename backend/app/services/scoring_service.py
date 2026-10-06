# =============================================================================
# CyberLearn — ScoringService
# Calcul du score final et des XP selon les performances du joueur
# =============================================================================


class ScoringService:
    """
    Calcule le score et les XP selon :
    - Temps de résolution vs temps limite
    - Nombre d'indices utilisés (malus)
    - Nombre de tentatives incorrectes (malus)
    """

    BASE_SCORE = 100
    HINT_PENALTY = 10        # Points perdus par indice utilisé
    ATTEMPT_PENALTY = 5      # Points perdus par tentative incorrecte (au-delà de 3)
    SPEED_BONUS_MAX = 20     # Bonus max si résolution rapide

    def calculate_score(
        self,
        elapsed_seconds: int,
        time_limit: int,
        hints_used: int,
        attempts: int,
    ) -> int:
        """
        Calcule le score final d'une session.

        Formule :
        score = BASE (100)
              + bonus_rapidité (0 à 20)
              - malus_indices (hints_used × 10)
              - malus_tentatives ((attempts - 3) × 5 si attempts > 3)
        Score minimum : 10 (on ne peut pas scorer 0 si on a réussi)
        """
        score = self.BASE_SCORE

        # Bonus rapidité : proportionnel au temps restant
        if time_limit > 0 and elapsed_seconds < time_limit:
            time_ratio = 1 - (elapsed_seconds / time_limit)
            speed_bonus = int(self.SPEED_BONUS_MAX * time_ratio)
            score += speed_bonus

        # Malus indices
        score -= hints_used * self.HINT_PENALTY

        # Malus tentatives (les 3 premières sont tolérées)
        excess_attempts = max(0, attempts - 3)
        score -= excess_attempts * self.ATTEMPT_PENALTY

        # Clamper entre 10 et 120
        return max(10, min(120, score))

    def calculate_xp(
        self,
        base_xp: int,
        score: int,
        hints_used: int,
    ) -> int:
        """
        Calcule les XP attribués selon le score obtenu.

        - Score parfait (>= 100) : 100% des XP de base
        - Bon score (>= 70)      : 75% des XP
        - Score moyen (>= 50)    : 50% des XP
        - Score faible (< 50)    : 25% des XP
        """
        if score >= 100:
            xp_ratio = 1.0
        elif score >= 70:
            xp_ratio = 0.75
        elif score >= 50:
            xp_ratio = 0.5
        else:
            xp_ratio = 0.25

        xp = int(base_xp * xp_ratio)
        return max(1, xp)  # Minimum 1 XP si la mission est complétée
