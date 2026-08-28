import requests
from google_auth_oauthlib.flow import Flow

from app.core.config import settings


class GoogleOAuthClient:
    """Thin wrapper around `google_auth_oauthlib`'s `Flow` and Google's token
    revocation endpoint — the only piece of this module that actually talks
    to Google, kept separate from `GoogleOAuthService`'s orchestration logic
    the same way `StripeBillingProvider` isolates the Stripe SDK from
    `BillingService`.
    """

    def _flow(self) -> Flow:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=settings.GOOGLE_SCOPES,
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        return flow

    def build_authorization_url(self, *, state: str) -> str:
        flow = self._flow()
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
        return auth_url

    def fetch_credentials(self, *, authorization_response: str):
        flow = self._flow()
        flow.fetch_token(authorization_response=authorization_response)
        return flow.credentials

    def revoke(self, token: str) -> None:
        try:
            requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": token},
                headers={"content-type": "application/x-www-form-urlencoded"},
                timeout=5,
            )
        except Exception:
            # No interrumpas por errores de red — el token local se borra
            # igual; en el peor caso queda vivo del lado de Google hasta
            # que expire por su cuenta.
            pass
