import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.core.security import hash_password
from app.modules.auth.application.auth_service import AuthService
from app.modules.auth.domain.entities import AuthTokens, AuthUser


class _FakeAuthRepository:
    def __init__(self):
        self.users_by_email: dict[str, AuthUser] = {}
        self.users_by_id: dict[str, AuthUser] = {}
        self.invite_codes: dict[str, dict] = {}
        self.patients: list[dict] = []
        self.patients_by_id: dict[str, dict] = {}
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

    async def get_invite_code(self, code: str) -> dict | None:
        return self.invite_codes.get(code)

    async def consume_invite_code(self, code: str, user_id: str) -> None:
        if code in self.invite_codes:
            self.invite_codes[code]["used_at"] = datetime.utcnow()
            self.invite_codes[code]["used_by_user_id"] = user_id

    async def create_patient_for_user(self, *, user_id: str, owner_id: str, name: str) -> None:
        self.patients.append({"user_id": user_id, "owner_id": owner_id, "name": name})

    async def link_user_to_patient(self, *, user_id: str, patient_id: str) -> bool:
        patient = self.patients_by_id.get(patient_id)
        if patient is None or patient.get("user_id") is not None:
            return False
        patient["user_id"] = user_id
        return True

    async def update_password_hash(self, user_id: str, password_hash: str) -> None:
        user = self.users_by_id.get(user_id)
        if user is None:
            return
        updated = AuthUser(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            password_hash=password_hash,
        )
        self.users_by_id[user.id] = updated
        self.users_by_email[user.email] = updated


class AuthServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_register_creates_user_with_normalized_email(self):
        repository = _FakeAuthRepository()
        repository.invite_codes["DEMO2026"] = {
            "code": "DEMO2026",
            "owner_id": "owner-1",
            "expires_at": None,
            "used_at": None,
        }
        service = AuthService(repository)

        user = await service.register(
            name="Maria",
            email=" Maria@Email.com ",
            password="secret123",
            invite_code="demo2026",
        )

        self.assertEqual(user.email, "maria@email.com")
        self.assertEqual(user.name, "Maria")
        self.assertEqual(user.role, "patient")
        self.assertNotEqual(user.password_hash, "secret123")
        self.assertEqual(len(repository.patients), 1)
        self.assertEqual(repository.patients[0]["owner_id"], "owner-1")
        self.assertIsNotNone(repository.invite_codes["DEMO2026"]["used_at"])

    async def test_register_with_a_patient_scoped_invite_links_the_existing_patient(self):
        repository = _FakeAuthRepository()
        repository.patients_by_id["chart-1"] = {
            "id": "chart-1",
            "name": "Juan Pérez",
            "user_id": None,
        }
        repository.invite_codes["LINK2026"] = {
            "code": "LINK2026",
            "owner_id": "owner-1",
            "patient_id": "chart-1",
            "expires_at": None,
            "used_at": None,
        }
        service = AuthService(repository)

        user = await service.register(
            name="Juan Pérez",
            email="juan@email.com",
            password="secret123",
            invite_code="link2026",
        )

        self.assertEqual(repository.patients_by_id["chart-1"]["user_id"], user.id)
        self.assertEqual(repository.patients, [])  # no duplicate patient created

    async def test_register_falls_back_to_a_new_patient_if_the_linked_chart_is_gone(self):
        repository = _FakeAuthRepository()
        repository.invite_codes["GONE2026"] = {
            "code": "GONE2026",
            "owner_id": "owner-1",
            "patient_id": "does-not-exist",
            "expires_at": None,
            "used_at": None,
        }
        service = AuthService(repository)

        await service.register(
            name="Maria",
            email="maria2@email.com",
            password="secret123",
            invite_code="gone2026",
        )

        self.assertEqual(len(repository.patients), 1)

    async def test_register_nutritionist_creates_a_nutritionist_user_without_invite_code(self):
        repository = _FakeAuthRepository()
        service = AuthService(repository)

        user = await service.register_nutritionist(
            name="Dra. Ruiz",
            email=" Dra.Ruiz@Email.com ",
            password="secret123",
        )

        self.assertEqual(user.email, "dra.ruiz@email.com")
        self.assertEqual(user.role, "nutritionist")
        self.assertEqual(repository.patients, [])  # no patient record created

    async def test_register_nutritionist_rejects_a_duplicate_email(self):
        repository = _FakeAuthRepository()
        service = AuthService(repository)
        await service.register_nutritionist(
            name="Dra. Ruiz", email="dra.ruiz@email.com", password="secret123"
        )

        with self.assertRaises(FileExistsError):
            await service.register_nutritionist(
                name="Otra", email="dra.ruiz@email.com", password="secret456"
            )

    async def test_register_rejects_unknown_invite_code(self):
        service = AuthService(_FakeAuthRepository())

        with self.assertRaises(LookupError):
            await service.register(
                name="Maria",
                email="maria@email.com",
                password="secret123",
                invite_code="NOPE",
            )

    async def test_register_rejects_already_used_invite_code(self):
        repository = _FakeAuthRepository()
        repository.invite_codes["USED"] = {
            "code": "USED",
            "owner_id": "owner-1",
            "expires_at": None,
            "used_at": datetime.utcnow(),
        }
        service = AuthService(repository)

        with self.assertRaises(LookupError):
            await service.register(
                name="Maria",
                email="maria@email.com",
                password="secret123",
                invite_code="USED",
            )

    async def test_register_rejects_expired_invite_code(self):
        repository = _FakeAuthRepository()
        repository.invite_codes["OLD"] = {
            "code": "OLD",
            "owner_id": "owner-1",
            "expires_at": datetime.utcnow() - timedelta(days=1),
            "used_at": None,
        }
        service = AuthService(repository)

        with self.assertRaises(LookupError):
            await service.register(
                name="Maria",
                email="maria@email.com",
                password="secret123",
                invite_code="OLD",
            )

    async def test_forgot_password_returns_none_for_unknown_email(self):
        service = AuthService(_FakeAuthRepository())

        token = await service.forgot_password(email="ghost@demo.com")

        self.assertIsNone(token)

    async def test_forgot_password_then_reset_password_updates_hash(self):
        repository = _FakeAuthRepository()
        repository.users_by_email["patient@demo.com"] = AuthUser(
            id="abc123",
            email="patient@demo.com",
            role="patient",
            password_hash=hash_password("old-secret"),
        )
        repository.users_by_id["abc123"] = repository.users_by_email["patient@demo.com"]
        service = AuthService(repository)

        token = await service.forgot_password(email="patient@demo.com")
        self.assertIsNotNone(token)

        await service.reset_password(token=token, new_password="new-secret")

        updated = repository.users_by_id["abc123"]
        self.assertNotEqual(updated.password_hash, hash_password("old-secret"))

        # El mismo token ya no debe funcionar dos veces (la guarda cambió).
        with self.assertRaises(PermissionError):
            await service.reset_password(token=token, new_password="another-secret")

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
