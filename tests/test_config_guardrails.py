import unittest

from pydantic import ValidationError

from app.core.config import Settings


class SettingsGuardrailsTest(unittest.TestCase):
    def test_local_defaults_are_allowed_without_external_env(self):
        settings = Settings(_env_file=None)
        self.assertEqual(settings.JWT_SECRET, "local-dev-change-me")
        self.assertEqual(
            settings.JWT_REFRESH_SECRET,
            "local-dev-refresh-change-me",
        )

    def test_prod_rejects_placeholder_jwt_secret(self):
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                APP_ENV="prod",
                JWT_SECRET="local-dev-change-me",
                JWT_REFRESH_SECRET="local-dev-refresh-change-me",
            )

    def test_google_oauth_requires_id_and_secret_together(self):
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                GOOGLE_CLIENT_ID="client-id-only",
                GOOGLE_CLIENT_SECRET="",
            )
