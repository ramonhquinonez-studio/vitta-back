import unittest
from unittest.mock import patch

from app.core.security import hash_password
from app.modules.auth.application.auth_service import AuthService
from app.modules.auth.domain.entities import AuthTokens, AuthUser


class _FakeAuthRepository:
    def __init__(self):
        self.users_by_email: dict[str, AuthUser] = {}
        self.users_by_id: dict[str, AuthUser] = {}
        self.sequence = 0

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        return self.users_by_email.get(email)

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        return self.users_by_id.get(user_id)

    async def create_user(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role: str,
    ) -> AuthUser:
        self.sequence += 1
        user = AuthUser(
            id=str(self.sequence),
            email=email,
            name=name,
            role=role,
            password_hash=password_hash,
        )
        self.users_by_email[email] = user
        self.users_by_id[user.id] = user
        return user


class AuthServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_register_creates_user_with_normalized_email(self):
        repository = _FakeAuthRepository()
        service = AuthService(repository)

        user = await service.register(
            name="Maria",
            email=" Maria@Email.com ",
            password="secret123",
        )

        self.assertEqual(user.email, "maria@email.com")
        self.assertEqual(user.name, "Maria")
        self.assertEqual(user.role, "user")
        self.assertNotEqual(user.password_hash, "secret123")

    async def test_login_returns_token_pair_for_valid_credentials(self):
        repository = _FakeAuthRepository()
        repository.users_by_email["patient@demo.com"] = AuthUser(
            id="abc123",
            email="patient@demo.com",
            role="user",
            password_hash=hash_password("secret123"),
        )
        service = AuthService(repository)

        with patch(
            "app.modules.auth.application.auth_service.create_access_token",
            return_value="access-token",
        ), patch(
            "app.modules.auth.application.auth_service.create_refresh_token",
            return_value="refresh-token",
        ):
            tokens = await service.login(
                email="patient@demo.com",
                password="secret123",
            )

        self.assertEqual(
            tokens,
            AuthTokens(
                access_token="access-token",
                refresh_token="refresh-token",
            ),
        )

    async def test_refresh_reissues_tokens_from_refresh_claims(self):
        service = AuthService(_FakeAuthRepository())

        with patch(
            "app.modules.auth.application.auth_service.decode_refresh",
            return_value={"sub": "user-1", "type": "refresh", "role": "patient"},
        ), patch(
            "app.modules.auth.application.auth_service.create_access_token",
            return_value="fresh-access",
        ), patch(
            "app.modules.auth.application.auth_service.create_refresh_token",
            return_value="fresh-refresh",
        ):
            tokens = await service.refresh(refresh_token="valid-refresh-token")

        self.assertEqual(tokens.access_token, "fresh-access")
        self.assertEqual(tokens.refresh_token, "fresh-refresh")
        self.assertEqual(tokens.token_type, "bearer")

    async def test_refresh_rejects_missing_subject(self):
        service = AuthService(_FakeAuthRepository())

        with patch(
            "app.modules.auth.application.auth_service.decode_refresh",
            return_value={"type": "refresh"},
        ):
            with self.assertRaises(PermissionError):
                await service.refresh(refresh_token="invalid")
