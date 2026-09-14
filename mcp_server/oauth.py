"""Small in-process OAuth provider for the classroom MCP deployment."""
import os
import secrets
import time
from dataclasses import dataclass

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyHttpUrl


MCP_SCOPES = ["ridgeline:mcp"]


def public_base_url():
    configured_url = os.environ.get("MCP_PUBLIC_BASE_URL")
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if configured_url or render_url:
        return (configured_url or render_url).rstrip("/")

    port = os.environ.get("PORT", "5000")
    return f"http://127.0.0.1:{port}"


def auth_settings():
    base_url = public_base_url()
    return AuthSettings(
        issuer_url=AnyHttpUrl(base_url),
        resource_server_url=AnyHttpUrl(f"{base_url}/mcp"),
        required_scopes=MCP_SCOPES,
        client_registration_options=ClientRegistrationOptions(
            enabled=True,
            valid_scopes=MCP_SCOPES,
            default_scopes=MCP_SCOPES,
        ),
        validate_token_resource=True,
    )


@dataclass
class PendingAuthorization:
    client: OAuthClientInformationFull
    params: AuthorizationParams
    expires_at: float


class RidgelineOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """OAuth authorization-code provider backed by short-lived memory stores."""

    def __init__(self):
        self.clients = {}
        self.pending_authorizations = {}
        self.codes = {}
        self.access_tokens = {}

    async def get_client(self, client_id):
        return self.clients.get(client_id)

    async def register_client(self, client_info):
        self.clients[client_info.client_id] = client_info

    async def authorize(self, client, params):
        request_id = secrets.token_urlsafe(32)
        self.pending_authorizations[request_id] = PendingAuthorization(
            client=client,
            params=params,
            expires_at=time.time() + 300,
        )
        return f"{public_base_url()}/oauth/authorize?request_id={request_id}"

    def approve_authorization(self, request_id, subject):
        pending = self.pending_authorizations.pop(request_id, None)
        if pending is None or pending.expires_at < time.time():
            raise ValueError("The authorization request is invalid or has expired.")

        client_id = pending.client.client_id
        if client_id is None:
            raise ValueError("The OAuth client is missing its client id.")

        params = pending.params
        code = AuthorizationCode(
            code=f"code_{secrets.token_urlsafe(32)}",
            client_id=client_id,
            scopes=params.scopes or MCP_SCOPES,
            expires_at=time.time() + 300,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=params.resource,
            subject=subject,
        )
        self.codes[code.code] = code
        return construct_redirect_uri(
            str(params.redirect_uri),
            code=code.code,
            state=params.state,
        )

    async def load_authorization_code(self, client, authorization_code):
        return self.codes.get(authorization_code)

    async def exchange_authorization_code(self, client, authorization_code):
        access_token = f"access_{secrets.token_urlsafe(32)}"
        self.access_tokens[access_token] = AccessToken(
            token=access_token,
            client_id=authorization_code.client_id,
            scopes=authorization_code.scopes,
            expires_at=int(time.time()) + 28800,
            resource=authorization_code.resource,
            subject=authorization_code.subject,
        )
        self.codes.pop(authorization_code.code, None)
        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=28800,
            scope=" ".join(authorization_code.scopes),
        )

    async def load_access_token(self, token):
        return self.access_tokens.get(token)

    async def load_refresh_token(self, client, refresh_token):
        return None

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        raise NotImplementedError("Refresh tokens are not issued by this server.")

    async def revoke_token(self, token):
        self.access_tokens.pop(token.token, None)


oauth_provider = RidgelineOAuthProvider()
