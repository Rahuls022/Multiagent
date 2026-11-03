import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure backend is on sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from dotenv import load_dotenv

load_dotenv(Path(backend_dir) / ".env")
os.environ.setdefault("AUTH_SECRET_KEY", "test-auth-secret-key-12345")

from starlette.testclient import TestClient
from app.auth import decode_access_token, hash_password, verify_password
from app.database import InMemoryPipelineRepository, SqliteUserRepository
from main import app


class AuthenticationTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temp sqlite file for test isolation
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(cls.temp_db_fd)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except OSError:
                pass

    def setUp(self):
        # Use fresh test client and repositories
        self.user_repo = SqliteUserRepository(self.temp_db_path)
        self.pipeline_repo = InMemoryPipelineRepository()
        app.state.user_repository = self.user_repo
        app.state.pipeline_repository = self.pipeline_repo
        self.client = TestClient(app)

    def test_01_successful_account_creation(self):
        """Test 1: User can register successfully with valid credentials."""
        payload = {
            "full_name": "Test Engineer",
            "email": "engineer@swarm.local",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        response = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["email"], "engineer@swarm.local")
        self.assertEqual(data["user"]["full_name"], "Test Engineer")
        self.assertIn("id", data["user"])

    def test_02_duplicate_email_registration_rejected(self):
        """Test 2: Registering an already existing email address returns 409 Conflict."""
        payload = {
            "full_name": "Duplicate User",
            "email": "engineer@swarm.local",
            "password": "AnotherPassword123!",
            "confirm_password": "AnotherPassword123!",
        }
        response = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertIn("already exists", response.json()["detail"].lower())

    def test_03_invalid_email_format_rejected(self):
        """Test 3: Signup with an invalid email address format fails validation."""
        payload = {
            "full_name": "Invalid Email",
            "email": "invalid-email-format",
            "password": "Password123!",
            "confirm_password": "Password123!",
        }
        response = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_04_password_shorter_than_8_chars_rejected(self):
        """Test 4: Password with fewer than 8 characters is rejected."""
        payload = {
            "full_name": "Short Pass",
            "email": "shortpass@swarm.local",
            "password": "short",
            "confirm_password": "short",
        }
        response = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_05_mismatched_passwords_rejected(self):
        """Test 5: Password and confirm password must match."""
        payload = {
            "full_name": "Mismatch Pass",
            "email": "mismatch@swarm.local",
            "password": "Password123!",
            "confirm_password": "Password456!",
        }
        response = self.client.post("/api/auth/signup", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_06_successful_login(self):
        """Test 6: User can sign in with valid credentials and receive an access token."""
        payload = {
            "email": "engineer@swarm.local",
            "password": "Password123!",
            "remember_me": True,
        }
        response = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "engineer@swarm.local")
        self.assertGreater(data["expires_in"], 86400)  # remember_me gives extended duration

    def test_07_incorrect_password_rejected(self):
        """Test 7: Signing in with wrong password returns 401 Unauthorized."""
        payload = {
            "email": "engineer@swarm.local",
            "password": "WrongPassword999!",
        }
        response = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("invalid", response.json()["detail"].lower())

    def test_08_unknown_email_rejected(self):
        """Test 8: Signing in with non-existent email returns 401 Unauthorized."""
        payload = {
            "email": "nonexistent@swarm.local",
            "password": "Password123!",
        }
        response = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("invalid", response.json()["detail"].lower())

    def test_09_session_persistence_via_me_endpoint(self):
        """Test 9: Stored access token verifies session across page refreshes via GET /api/auth/me."""
        # Log in to get token
        login_res = self.client.post("/api/auth/login", json={
            "email": "engineer@swarm.local",
            "password": "Password123!",
        })
        token = login_res.json()["access_token"]

        # Call /api/auth/me with Bearer token
        me_res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        user_info = me_res.json()
        self.assertEqual(user_info["email"], "engineer@swarm.local")
        self.assertEqual(user_info["full_name"], "Test Engineer")

    def test_10_logout_and_revocation_access(self):
        """Test 10: Authenticated user can call logout endpoint."""
        login_res = self.client.post("/api/auth/login", json={
            "email": "engineer@swarm.local",
            "password": "Password123!",
        })
        token = login_res.json()["access_token"]

        logout_res = self.client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn("message", logout_res.json())

    def test_11_unauthorized_api_requests_rejected(self):
        """Test 11: Unauthenticated requests to protected dashboard routes are rejected with 401."""
        endpoints = [
            ("GET", "/api/pipelines"),
            ("GET", "/api/failures"),
            ("GET", "/api/auth/me"),
            ("POST", "/api/pipelines"),
            ("POST", "/api/pipelines/simulate-failure"),
        ]
        for method, endpoint in endpoints:
            if method == "GET":
                res = self.client.get(endpoint)
            else:
                res = self.client.post(endpoint, json={"request": "Test mission"})
            self.assertEqual(res.status_code, 401, f"{method} {endpoint} should require authentication")

        # Invalid token should also return 401
        invalid_res = self.client.get("/api/pipelines", headers={"Authorization": "Bearer fake.invalid.token"})
        self.assertEqual(invalid_res.status_code, 401)

    def test_12_password_security_and_hashing(self):
        """Test 12: Verify passwords are never stored in plaintext and use PBKDF2 with salt."""
        raw_pwd = "SuperSecretPassword123!"
        hashed = hash_password(raw_pwd)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertNotIn(raw_pwd, hashed)
        self.assertTrue(verify_password(raw_pwd, hashed))
        self.assertFalse(verify_password("WrongPassword123!", hashed))

    def test_13_case_insensitive_email_and_whitespace_handling(self):
        """Test 13: Email matching is case-insensitive and trims surrounding whitespace."""
        payload = {
            "email": "  ENGINEER@SWARM.LOCAL  ",
            "password": "Password123!",
        }
        response = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["email"], "engineer@swarm.local")

    def test_14_database_persistence_across_reconnects(self):
        """Test 14: Permanent database persistence across new repository connections."""
        # Create a brand new connection to the same SQLite file
        new_repo = SqliteUserRepository(self.temp_db_path)
        import asyncio
        user = asyncio.run(new_repo.get_by_email("engineer@swarm.local"))
        self.assertIsNotNone(user)
        self.assertEqual(user["full_name"], "Test Engineer")
        self.assertTrue(user["password_hash"].startswith("pbkdf2_sha256$"))

    def test_15_duplicate_email_repository_mapping_and_500_preservation(self):
        """Test 15: create_user duplicate errors map to 409 by type; unrelated errors map to 500."""
        from unittest.mock import AsyncMock
        import sqlite3
        from app.database import DuplicateUserError

        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None
        app.state.user_repository = mock_repo

        # Case 1: DuplicateUserError -> 409
        mock_repo.create_user.side_effect = DuplicateUserError("Already exists")
        res1 = self.client.post("/api/auth/signup", json={
            "full_name": "User One", "email": "unique1@swarm.local", "password": "Password123!", "confirm_password": "Password123!"
        })
        self.assertEqual(res1.status_code, 409)

        # Case 2: sqlite3.IntegrityError without 'duplicate' text -> 409
        mock_repo.create_user.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: users.email")
        res2 = self.client.post("/api/auth/signup", json={
            "full_name": "User Two", "email": "unique2@swarm.local", "password": "Password123!", "confirm_password": "Password123!"
        })
        self.assertEqual(res2.status_code, 409)

        # Case 3: Unrelated error -> 500
        mock_repo.create_user.side_effect = OSError("Disk write failed")
        res3 = self.client.post("/api/auth/signup", json={
            "full_name": "User Three", "email": "unique3@swarm.local", "password": "Password123!", "confirm_password": "Password123!"
        })
        self.assertEqual(res3.status_code, 500)


if __name__ == "__main__":
    unittest.main()
