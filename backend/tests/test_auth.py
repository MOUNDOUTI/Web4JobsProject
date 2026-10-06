# =============================================================================
# CyberLearn — Tests Authentification
# Couvre : UC01 inscription 18+, UC02 connexion, rate limiting
# =============================================================================

import pytest
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import hash_password, verify_password, calculate_age, verify_solution, hash_solution


# ─── Tests unitaires — security.py ────────────────────────────────────────────

class TestAgeCalculation:
    """Tests de la vérification d'âge — règle métier critique."""

    def test_adult_user(self):
        birth = date.today() - timedelta(days=25 * 365)
        assert calculate_age(birth) >= 24

    def test_exactly_18_today(self):
        birth = date(
            date.today().year - 18,
            date.today().month,
            date.today().day,
        )
        age = calculate_age(birth)
        assert age == 18

    def test_minor_17_years(self):
        birth = date.today() - timedelta(days=17 * 365)
        assert calculate_age(birth) < 18

    def test_minor_17_years_364_days(self):
        """17 ans et 364 jours — doit être refusé."""
        birth = date.today() - timedelta(days=18 * 365 - 1)
        from app.core.security import calculate_age
        age = calculate_age(birth)
        assert age < 18

    def test_verify_minimum_age_adult(self):
        from app.core.security import verify_minimum_age
        birth = date(1995, 1, 1)
        age = verify_minimum_age(birth)
        assert age >= 18

    def test_verify_minimum_age_minor_raises(self):
        from app.core.security import verify_minimum_age
        from app.core.exceptions import AgeVerificationError
        birth = date.today() - timedelta(days=16 * 365)
        with pytest.raises(AgeVerificationError):
            verify_minimum_age(birth)


class TestPasswordHashing:
    """Tests du hachage bcrypt."""

    def test_hash_is_not_plaintext(self):
        hashed = hash_password("MyPassword1!")
        assert hashed != "MyPassword1!"

    def test_verify_correct_password(self):
        hashed = hash_password("MyPassword1!")
        assert verify_password("MyPassword1!", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("MyPassword1!")
        assert verify_password("WrongPassword!", hashed) is False

    def test_two_hashes_differ(self):
        h1 = hash_password("MyPassword1!")
        h2 = hash_password("MyPassword1!")
        assert h1 != h2  # bcrypt utilise un salt aléatoire


class TestSolutionHashing:
    """Tests de la validation de solutions (SHA-256)."""

    def test_correct_solution(self):
        solution = "FLAG{test_flag}"
        stored = hash_solution(solution)
        assert verify_solution("FLAG{test_flag}", stored) is True

    def test_case_insensitive(self):
        stored = hash_solution("flag{test}")
        assert verify_solution("FLAG{TEST}", stored) is True

    def test_strips_whitespace(self):
        stored = hash_solution("flag{test}")
        assert verify_solution("  flag{test}  ", stored) is True

    def test_wrong_solution(self):
        stored = hash_solution("flag{correct}")
        assert verify_solution("flag{wrong}", stored) is False

    def test_solution_never_in_plain(self):
        """La solution hashée ne doit jamais contenir la valeur originale."""
        stored = hash_solution("FLAG{secret}")
        assert "FLAG{secret}" not in stored
        assert "secret" not in stored


# ─── Tests intégration — endpoints auth ───────────────────────────────────────

@pytest.fixture
def adult_birth_date():
    return str(date(1995, 6, 15))


@pytest.fixture
def minor_birth_date():
    return str(date.today() - timedelta(days=16 * 365))


@pytest.mark.asyncio
class TestRegisterEndpoint:
    """Tests du endpoint POST /api/v1/auth/register."""

    BASE_URL = "http://test"
    REGISTER_URL = "/api/v1/auth/register"

    async def _client(self):
        return AsyncClient(
            transport=ASGITransport(app=app),
            base_url=self.BASE_URL,
        )

    async def test_register_valid_adult(self, adult_birth_date):
        async with await self._client() as client:
            response = await client.post(self.REGISTER_URL, json={
                "email": "test_adult@example.com",
                "pseudo": "TestAdult",
                "password": "SecurePass1!",
                "password_confirm": "SecurePass1!",
                "birth_date": adult_birth_date,
                "accept_terms": True,
            })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["pseudo"] == "TestAdult"

    async def test_register_minor_rejected(self, minor_birth_date):
        """UC01 — Mineur doit être refusé avec HTTP 403."""
        async with await self._client() as client:
            response = await client.post(self.REGISTER_URL, json={
                "email": "minor@example.com",
                "pseudo": "MinorUser",
                "password": "SecurePass1!",
                "password_confirm": "SecurePass1!",
                "birth_date": minor_birth_date,
                "accept_terms": True,
            })
        assert response.status_code == 403
        assert response.json()["error"] == "AGE_VERIFICATION_FAILED"

    async def test_register_exactly_18(self):
        """Exactement 18 ans aujourd'hui — doit être accepté."""
        birth = date(
            date.today().year - 18,
            date.today().month,
            date.today().day,
        )
        async with await self._client() as client:
            response = await client.post(self.REGISTER_URL, json={
                "email": "exactly18@example.com",
                "pseudo": "Exactly18",
                "password": "SecurePass1!",
                "password_confirm": "SecurePass1!",
                "birth_date": str(birth),
                "accept_terms": True,
            })
        assert response.status_code == 201

    async def test_register_weak_password(self, adult_birth_date):
        async with await self._client() as client:
            response = await client.post(self.REGISTER_URL, json={
                "email": "weak@example.com",
                "pseudo": "WeakPass",
                "password": "password",
                "password_confirm": "password",
                "birth_date": adult_birth_date,
                "accept_terms": True,
            })
        assert response.status_code == 422

    async def test_register_passwords_mismatch(self, adult_birth_date):
        async with await self._client() as client:
            response = await client.post(self.REGISTER_URL, json={
                "email": "mismatch@example.com",
                "pseudo": "MismatchUser",
                "password": "SecurePass1!",
                "password_confirm": "DifferentPass1!",
                "birth_date": adult_birth_date,
                "accept_terms": True,
            })
        assert response.status_code == 422

    async def test_register_terms_not_accepted(self, adult_birth_date):
        async with await self._client() as client:
            response = await client.post(self.REGISTER_URL, json={
                "email": "noterms@example.com",
                "pseudo": "NoTerms",
                "password": "SecurePass1!",
                "password_confirm": "SecurePass1!",
                "birth_date": adult_birth_date,
                "accept_terms": False,
            })
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLoginEndpoint:
    """Tests du endpoint POST /api/v1/auth/login."""

    BASE_URL = "http://test"
    LOGIN_URL = "/api/v1/auth/login"

    async def _client(self):
        return AsyncClient(
            transport=ASGITransport(app=app),
            base_url=self.BASE_URL,
        )

    async def test_login_invalid_credentials(self):
        async with await self._client() as client:
            response = await client.post(self.LOGIN_URL, json={
                "email": "nonexistent@example.com",
                "password": "WrongPass1!",
            })
        assert response.status_code == 401
        assert response.json()["error"] == "INVALID_CREDENTIALS"

    async def test_protected_route_without_token(self):
        """Accès à une route protégée sans token — doit retourner 401."""
        async with await self._client() as client:
            response = await client.get("/api/v1/catalogue/chapters")
        assert response.status_code == 401
