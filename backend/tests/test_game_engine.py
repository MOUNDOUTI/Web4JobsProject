# =============================================================================
# CyberLearn — Tests Moteur de jeu
# Couvre : scoring, validation solutions, progression XP
# =============================================================================

import pytest
from app.services.scoring_service import ScoringService
from app.services.progression_service import calculate_level, get_xp_to_next_level, LEVEL_THRESHOLDS


class TestScoringService:
    """Tests du calcul de score."""

    def setup_method(self):
        self.scoring = ScoringService()

    def test_perfect_score_fast_no_hints(self):
        """Résolution rapide sans indice = score maximum."""
        score = self.scoring.calculate_score(
            elapsed_seconds=300,
            time_limit=1800,
            hints_used=0,
            attempts=1,
        )
        assert score > 100  # Bonus rapidité

    def test_score_with_hints_penalty(self):
        """Chaque indice enlève 10 pts."""
        score_no_hint = self.scoring.calculate_score(600, 1800, 0, 1)
        score_one_hint = self.scoring.calculate_score(600, 1800, 1, 1)
        assert score_no_hint - score_one_hint == 10

    def test_score_with_excess_attempts(self):
        """Au-delà de 3 tentatives, malus de 5 pts par tentative."""
        score_3 = self.scoring.calculate_score(600, 1800, 0, 3)
        score_5 = self.scoring.calculate_score(600, 1800, 0, 5)
        assert score_3 - score_5 == 10  # 2 tentatives excédentaires × 5

    def test_minimum_score_10(self):
        """Score minimum = 10 même avec beaucoup de malus."""
        score = self.scoring.calculate_score(
            elapsed_seconds=1800,
            time_limit=1800,
            hints_used=5,
            attempts=20,
        )
        assert score >= 10

    def test_xp_perfect_score(self):
        xp = self.scoring.calculate_xp(base_xp=40, score=105, hints_used=0)
        assert xp == 40  # 100% des XP de base

    def test_xp_good_score(self):
        xp = self.scoring.calculate_xp(base_xp=40, score=80, hints_used=0)
        assert xp == 30  # 75% des XP

    def test_xp_medium_score(self):
        xp = self.scoring.calculate_xp(base_xp=40, score=55, hints_used=0)
        assert xp == 20  # 50% des XP

    def test_xp_low_score(self):
        xp = self.scoring.calculate_xp(base_xp=40, score=30, hints_used=0)
        assert xp == 10  # 25% des XP

    def test_xp_minimum_1(self):
        xp = self.scoring.calculate_xp(base_xp=1, score=10, hints_used=5)
        assert xp >= 1


class TestProgressionService:
    """Tests du système de niveaux."""

    def test_level_1_at_0_xp(self):
        assert calculate_level(0) == 1

    def test_level_1_at_199_xp(self):
        assert calculate_level(199) == 1

    def test_level_2_at_200_xp(self):
        assert calculate_level(200) == 2

    def test_level_3_at_500_xp(self):
        assert calculate_level(500) == 3

    def test_level_4_at_1000_xp(self):
        assert calculate_level(1000) == 4

    def test_level_5_at_2000_xp(self):
        assert calculate_level(2000) == 5

    def test_level_5_stays_at_high_xp(self):
        assert calculate_level(99999) == 5

    def test_xp_to_next_level_1(self):
        """Depuis niveau 1 avec 100 XP → 100 XP restants pour niveau 2."""
        remaining = get_xp_to_next_level(100, 1)
        assert remaining == 100  # 200 - 100

    def test_xp_to_next_level_max(self):
        """Au niveau max → 0 XP restants."""
        remaining = get_xp_to_next_level(5000, 5)
        assert remaining == 0

    def test_no_regression(self):
        """On ne peut pas descendre de niveau (XP uniquement additifs)."""
        level = calculate_level(1999)
        assert level == 4
        level_after = calculate_level(1999)
        assert level_after >= level
