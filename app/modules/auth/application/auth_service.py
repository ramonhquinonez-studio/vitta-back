from datetime import datetime

from jose import JWTError

from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_password_reset_token,
    decode_refresh,
    hash_password,
    password_reset_guard_matches,
    verify_password,
)

from ..domain.entities import AuthTokens, AuthUser
from ..domain.repositories import AuthRepository, PatientQuotaChecker


class AuthService:
    def __init__(self, repository: AuthRepository, quota_checker: PatientQuotaChecker | None = None):
        self._repository = repository
        self._quota_checker = quota_checker

    async def register(
        self, *, name: str, email: str, password: str, invite_code: str | None = None
    ) -> AuthUser:
        normalized_email = self._normalize_email(email)
        normalized_name = (name or "").strip()
        if not normalized_name:
            raise ValueError("Name is required")

        existing = await self._repository.get_user_by_email(normalized_email)
        if existing is not None:
            raise FileExistsError("Email already registered")

        # A blank/whitespace code is treated the same as "not provided" —
        # self-registration (030-back-patient-self-registration) — rather
        # than as an invalid-code error.
        cleaned_code = (invite_code or "").strip().upper()
        invite: dict | None = None
        if cleaned_code:
            invite = await self._repository.get_invite_code(cleaned_code)
            if invite is None:
                raise LookupError("Invalid invite code")
            if invite.get("used_at") is not None:
                raise LookupError("Invite code already used")
            expires_at = invite.get("expires_at")
            if expires_at is not None and expires_at < datetime.utcnow():
                raise LookupError("Invite code expired")

        # Only an invite with no already-existing `patient_id` will create a
        # brand-new patient below — that's the one case that actually grows
        # the nutritionist's roster, so it's the one checked against quota.
        # Checked before creating the user account: a failed quota check
        # here must not leave behind an orphan account with no patient chart.
        if invite is not None and not invite.get("patient_id") and self._quota_checker is not None:
            await self._quota_checker.check(invite["owner_id"])

        user = await self._repository.create_user(
            name=normalized_name,
            email=normalized_email,
            password_hash=hash_password(password),
            role="patient",
        )

        if invite is not None:
            patient_id = invite.get("patient_id")
            linked = False
            if patient_id:
                linked = await self._repository.link_user_to_patient(
                    user_id=user.id, patient_id=patient_id
                )
            if not linked:
                # Either this was an unscoped invite (no patient_id at all), or
                # the linked chart was claimed/removed between invite creation
                # and redemption — either way, the new account still needs a
                # patient record, not silently none at all.
                await self._repository.create_patient_for_user(
                    user_id=user.id,
                    owner_id=invite["owner_id"],
                    name=normalized_name,
                )
            await self._repository.consume_invite_code(invite["code"], user.id)
        else:
            # No nutritionist yet: create a self-owned chart with its own
            # connection code, so a nutritionist can claim this patient later
            # (`PatientsService.claim_patient`).
            await self._repository.create_unowned_patient_for_user(
                user_id=user.id, name=normalized_name
            )
        return user

    async def preview_invite_code(self, code: str) -> dict:
        """Read-only, unauthenticated lookup — lets the register screen react
        to what a code unlocks (a specific existing patient vs. a blank
        slate) before the patient types anything else."""
        invite = await self._repository.get_invite_code((code or "").strip().upper())
        if invite is None:
            return {"valid": False}
        if invite.get("used_at") is not None:
            return {"valid": False}
        expires_at = invite.get("expires_at")
        if expires_at is not None and expires_at < datetime.utcnow():
            return {"valid": False}

        patient_id = invite.get("patient_id")
        patient_name = None
        if patient_id:
            patient_name = await self._repository.get_patient_name(patient_id)

        nutritionist = await self._repository.get_user_by_id(invite["owner_id"])
        return {
            "valid": True,
            "scoped": patient_id is not None and patient_name is not None,
            "patient_name": patient_name,
            "nutritionist_name": nutritionist.name if nutritionist else None,
        }

    async def register_nutritionist(
        self, *, name: str, email: str, password: str
    ) -> AuthUser:
        normalized_email = self._normalize_email(email)
        normalized_name = (name or "").strip()
        if not normalized_name:
            raise ValueError("Name is required")

        existing = await self._repository.get_user_by_email(normalized_email)
        if existing is not None:
            raise FileExistsError("Email already registered")

        return await self._repository.create_user(
            name=normalized_name,
            email=normalized_email,
            password_hash=hash_password(password),
            role="nutritionist",
        )

    async def forgot_password(self, *, email: str) -> str | None:
        """Devuelve el token de reset si el correo existe; None si no (el
        router siempre responde con el mismo mensaje genérico para no
        revelar qué correos están registrados)."""
        normalized_email = self._normalize_email(email)
        user = await self._repository.get_user_by_email(normalized_email)
        if user is None:
            return None
        return create_password_reset_token(user.id, user.password_hash or "")

    async def reset_password(self, *, token: str, new_password: str) -> None:
        try:
            payload = decode_password_reset_token(token)
        except JWTError as exc:
            raise PermissionError("Invalid or expired token") from exc

        user_id = payload.get("sub")
        if not user_id:
            raise PermissionError("Invalid token payload")

        user = await self._repository.get_user_by_id(user_id)
        if user is None:
            raise PermissionError("Invalid token")
        if not password_reset_guard_matches(payload, user.password_hash or ""):
            raise PermissionError("Token already used")

        await self._repository.update_password_hash(user_id, hash_password(new_password))

    async def login(self, *, email: str, password: str) -> AuthTokens:
        normalized_email = self._normalize_email(email)
        user = await self._repository.get_user_by_email(normalized_email)
        if user is None or not verify_password(password, user.password_hash or ""):
            raise PermissionError("Invalid email or password")
        return self._issue_tokens(user.id, user.role)

    async def refresh(self, *, refresh_token: str) -> AuthTokens:
        try:
            data = decode_refresh(refresh_token)
        except JWTError as exc:
            raise PermissionError("Invalid token") from exc

        if data.get("type") != "refresh":
            raise PermissionError("Invalid token type")

        uid = data.get("sub")
        if not uid:
            raise PermissionError("Invalid token payload")

        role = data.get("role", "user")
        return self._issue_tokens(uid, role)

    def _issue_tokens(self, user_id: str, role: str) -> AuthTokens:
        return AuthTokens(
            access_token=create_access_token(user_id, role),
            refresh_token=create_refresh_token(user_id, role),
        )

    def _normalize_email(self, email: str) -> str:
        normalized = (email or "").strip().lower()
        if not normalized:
            raise ValueError("Email is required")
        return normalized
