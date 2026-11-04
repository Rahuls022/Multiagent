"""Unit and service tests for user authentication, password hashing, and user data safety."""

import asyncio
import unittest
from unittest.mock import MagicMock

from app.auth.repository import InMemoryUserRepository
from app.auth.schemas import UserLoginRequest, UserRegisterRequest
from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from main import get_my_profile, login, register


class TestUserAuthentication(unittest.TestCase):
    def setUp(self):
        self.user_repo = InMemoryUserRepository()
        self.mock_request = MagicMock()
        self.mock_request.app.state.user_repository = self.user_repo

    def test_salted_password_hashing(self):
        password = "SuperSecretPassword123!"
        hashed = hash_password(password)

        self.assertTrue(hashed.startswith("pbkdf2_sha256$100000$"))
        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_jwt_token_generation_and_verification(self):
        payload = {"sub": "usr-12345", "email": "test@example.com", "name": "Test User"}
        token = create_access_token(payload)

        decoded = decode_access_token(token)
        self.assertEqual(decoded["sub"], "usr-12345")
        self.assertEqual(decoded["email"], "test@example.com")
        self.assertIn("exp", decoded)

    def test_auth_workflow(self):
        async def run_flow():
            test_email = "alex.devops@example.com"
            test_pw = "SecureSwarm2026!"

            # 1. Register new user
            reg_req = UserRegisterRequest(name="Alex DevOps", email=test_email, password=test_pw)
            reg_res = await register(reg_req, self.mock_request)
            self.assertIsNotNone(reg_res.access_token)
            self.assertEqual(reg_res.user.email, test_email)
            self.assertEqual(reg_res.user.name, "Alex DevOps")
            token = reg_res.access_token

            # 2. Duplicate registration throws error
            with self.assertRaises(Exception):
                await register(reg_req, self.mock_request)

            # 3. Login with correct credentials
            login_req = UserLoginRequest(email=test_email, password=test_pw)
            login_res = await login(login_req, self.mock_request)
            self.assertIsNotNone(login_res.access_token)
            self.assertEqual(login_res.user.id, reg_res.user.id)

            # 4. Login with invalid password fails
            bad_login = UserLoginRequest(email=test_email, password="WrongPassword!")
            with self.assertRaises(Exception):
                await login(bad_login, self.mock_request)

            # 5. Access profile with current_user
            current_user = {
                "id": reg_res.user.id,
                "name": "Alex DevOps",
                "email": test_email,
                "created_at": reg_res.user.created_at,
            }
            me_res = await get_my_profile(current_user=current_user)
            self.assertEqual(me_res.email, test_email)
            self.assertEqual(me_res.name, "Alex DevOps")

        asyncio.run(run_flow())

    def test_user_pipeline_data_isolation(self):
        """Verify that user pipeline history is isolated per user."""
        from app.database import InMemoryPipelineRepository
        from app.schemas import PipelineRequest
        from main import list_pipelines, start_development_pipeline

        pipe_repo = InMemoryPipelineRepository()
        self.mock_request.app.state.pipeline_repository = pipe_repo

        async def run_isolation_flow():
            user_a = {"id": "user-A", "email": "a@example.com", "name": "User A"}
            user_b = {"id": "user-B", "email": "b@example.com", "name": "User B"}
            await self.user_repo.create_user(user_a)
            await self.user_repo.create_user(user_b)

            # Create pipeline for User A
            req_a = MagicMock()
            req_a.app.state.pipeline_repository = pipe_repo
            req_a.app.state.user_repository = self.user_repo
            req_a.headers = {}
            payload_a = PipelineRequest(request="User A Mission", user_id=user_a["id"])
            await start_development_pipeline(payload_a, req_a)

            # Create pipeline for User B
            req_b = MagicMock()
            req_b.app.state.pipeline_repository = pipe_repo
            req_b.app.state.user_repository = self.user_repo
            req_b.headers = {}
            payload_b = PipelineRequest(request="User B Mission", user_id=user_b["id"])
            await start_development_pipeline(payload_b, req_b)

            # Query pipelines for User A
            list_req_a = MagicMock()
            list_req_a.app.state.pipeline_repository = pipe_repo
            list_req_a.app.state.user_repository = self.user_repo
            list_req_a.headers = {"authorization": f"Bearer {create_access_token({'sub': user_a['id'], 'email': user_a['email'], 'name': user_a['name']})}"}
            res_a = await list_pipelines(list_req_a)

            # User A should only see their own pipeline
            self.assertEqual(len(res_a["pipelines"]), 1)
            self.assertEqual(res_a["pipelines"][0]["task"]["user_id"], user_a["id"])
        from unittest.mock import patch
        from app.agents.development_supervisor import DevelopmentSupervisor

        with patch.object(DevelopmentSupervisor, "run_pipeline") as mock_run:
            async def fake_run(mission, task=None):
                res = {
                    "task": task or {"id": "test-id", "request": mission, "user_id": "test"},
                    "status": "completed",
                    "workflow_state": "COMPLETED",
                    "stages": [],
                    "logs": [],
                    "events": [],
                }
                await pipe_repo.create(res)
                return res

            mock_run.side_effect = fake_run
            asyncio.run(run_isolation_flow())


if __name__ == "__main__":
    unittest.main()
