"""Automated tests verifying persistent user authentication, registration, login, and session restoration across server restarts."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import asyncio
from unittest.mock import MagicMock
from app.auth.repository import SqliteUserRepository
from app.auth.schemas import UserLoginRequest, UserRegisterRequest, UserSignupRequest
from app.auth.security import create_access_token, decode_access_token, hash_password, verify_password
from app.database.repository import SQLitePipelineRepository
from main import (
    app,
    demo_login,
    get_my_profile,
    list_pipelines,
    login,
    logout,
    register,
    signup,
)


class TestAuthPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db_path = str(Path(__file__).resolve().parent / "test_temp_auth.db")
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except OSError:
                pass

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except OSError:
                pass

    def setUp(self):
        # Connect repo to the persistent temp db file
        self.user_repo = SqliteUserRepository(self.temp_db_path)
        self.pipeline_repo = SQLitePipelineRepository(self.temp_db_path)
        self.mock_request = MagicMock()
        self.mock_request.app.state.user_repository = self.user_repo
        self.mock_request.app.state.pipeline_repository = self.pipeline_repo

    def test_01_user_registration_and_persistent_storage(self):
        """New user registers; password is securely hashed and record is saved in SQLite."""
        async def run_test():
            req = UserRegisterRequest(
                name="Sarah Connor",
                email="sarah.connor@cyberdyne.org",
                password="Resistance2026!",
            )
            res = await register(req, self.mock_request)
            self.assertIsNotNone(res.access_token)
            self.assertEqual(res.user.email, "sarah.connor@cyberdyne.org")
            self.assertEqual(res.user.name, "Sarah Connor")

            # Verify saved record directly in SQLite database
            db_user = await self.user_repo.get_by_email("sarah.connor@cyberdyne.org")
            self.assertIsNotNone(db_user)
            self.assertEqual(db_user["email"], "sarah.connor@cyberdyne.org")
            # Verify password was hashed and is never plain text
            self.assertNotEqual(db_user["password_hash"], "Resistance2026!")
            self.assertTrue(db_user["password_hash"].startswith("pbkdf2_sha256$100000$"))
            self.assertTrue(verify_password("Resistance2026!", db_user["password_hash"]))

        asyncio.run(run_test())

    def test_02_duplicate_email_registration_rejected(self):
        """Registering with an already existing email is rejected with 409 Conflict."""
        async def run_test():
            req = UserRegisterRequest(
                name="Sarah Clone",
                email="sarah.connor@cyberdyne.org",
                password="DifferentPassword123!",
            )
            with self.assertRaises(Exception) as ctx:
                await register(req, self.mock_request)
            self.assertIn("already exists", str(ctx.exception).lower())

        asyncio.run(run_test())

    def test_03_returning_user_login(self):
        """Registered user logs in with email and password, receiving a valid JWT."""
        async def run_test():
            login_req = UserLoginRequest(
                email="sarah.connor@cyberdyne.org",
                password="Resistance2026!",
            )
            res = await login(login_req, self.mock_request)
            self.assertIsNotNone(res.access_token)
            self.assertEqual(res.user.email, "sarah.connor@cyberdyne.org")
            self.assertEqual(res.user.name, "Sarah Connor")

            # Login with invalid password fails
            bad_req = UserLoginRequest(
                email="sarah.connor@cyberdyne.org",
                password="WrongPassword123!",
            )
            with self.assertRaises(Exception) as ctx:
                await login(bad_req, self.mock_request)
            self.assertIn("invalid email or password", str(ctx.exception).lower())

        asyncio.run(run_test())

    def test_04_session_persistence_across_server_restart(self):
        """Simulate a server restart: a new repository instance pointing to the DB file restores the session."""
        async def run_test():
            # Create a brand new repository instance to simulate rebooting the server
            restarted_user_repo = SqliteUserRepository(self.temp_db_path)
            restarted_request = MagicMock()
            restarted_request.app.state.user_repository = restarted_user_repo
            restarted_request.app.state.pipeline_repository = self.pipeline_repo

            # Verify the registered user is still present in the restarted repository
            user = await restarted_user_repo.get_by_email("sarah.connor@cyberdyne.org")
            self.assertIsNotNone(user, "User account was lost across simulated server restart!")
            self.assertEqual(user["email"], "sarah.connor@cyberdyne.org")

            # Generate a token as if the user logged in before the restart
            token = create_access_token({
                "sub": user["id"],
                "email": user["email"],
                "name": user["full_name"],
            })

            # Verify token decodes and resolves the user in restarted system
            decoded = decode_access_token(token)
            resolved_user = await restarted_user_repo.get_by_id(decoded["sub"])
            self.assertIsNotNone(resolved_user)
            self.assertEqual(resolved_user["email"], "sarah.connor@cyberdyne.org")

            # User can still log in again with their password on the restarted server
            login_res = await login(
                UserLoginRequest(email="sarah.connor@cyberdyne.org", password="Resistance2026!"),
                restarted_request,
            )
            self.assertEqual(login_res.user.email, "sarah.connor@cyberdyne.org")

        asyncio.run(run_test())

    def test_05_demo_access_persistence(self):
        """Instant demo access endpoint returns genuine signed JWT and saves demo lead."""
        async def run_test():
            res = await demo_login(self.mock_request)
            self.assertIsNotNone(res.access_token)
            self.assertEqual(res.user.email, "alex.morgan@swarm.dev")

            # Verify demo user is persisted in SQLite
            demo_user = await self.user_repo.get_by_email("alex.morgan@swarm.dev")
            self.assertIsNotNone(demo_user)
            self.assertEqual(demo_user["email"], "alex.morgan@swarm.dev")

            # Verify token decodes properly
            decoded = decode_access_token(res.access_token)
            self.assertEqual(decoded["sub"], demo_user["id"])
            self.assertEqual(decoded["email"], "alex.morgan@swarm.dev")

        asyncio.run(run_test())

    def test_06_logout_endpoint(self):
        """Logout endpoint acknowledges and returns 200 OK."""
        async def run_test():
            res = await logout(self.mock_request)
            self.assertEqual(res["message"], "Signed out successfully.")

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
