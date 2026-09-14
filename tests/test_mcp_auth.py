import asyncio
from urllib.parse import parse_qs, urlparse

from mcp.server.auth.provider import AuthorizationParams
from mcp.shared.auth import OAuthClientInformationFull
from pydantic import AnyUrl

from mcp_server.oauth import oauth_provider


def _begin_authorization():
    client = OAuthClientInformationFull(
        client_id="test-mcp-client",
        client_name="Test MCP client",
        redirect_uris=[AnyUrl("http://127.0.0.1:54321/callback")],
        token_endpoint_auth_method="none",
    )
    params = AuthorizationParams(
        state="test-state",
        scopes=["ridgeline:mcp"],
        code_challenge="test-code-challenge",
        redirect_uri=AnyUrl("http://127.0.0.1:54321/callback"),
        redirect_uri_provided_explicitly=True,
        resource="http://127.0.0.1:5000/mcp",
    )
    authorization_url = asyncio.run(oauth_provider.authorize(client, params))
    return parse_qs(urlparse(authorization_url).query)["request_id"][0]


def test_mcp_authorization_requires_class_password(client):
    request_id = _begin_authorization()

    response = client.get(f"/oauth/authorize?request_id={request_id}")

    assert response.status_code == 200
    assert b"Enter the class password" in response.data


def test_mcp_authorization_form_renders_when_browser_is_logged_in(client, login):
    login("staff@example.test")
    request_id = _begin_authorization()

    response = client.get(f"/oauth/authorize?request_id={request_id}")

    assert response.status_code == 200
    assert b"Enter the class password" in response.data
    assert b'class="auth-screen"' in response.data


def test_mcp_authorization_rejects_wrong_class_password(client):
    request_id = _begin_authorization()

    response = client.post(
        f"/oauth/authorize?request_id={request_id}",
        data={"password": "wrong-password"},
    )

    assert response.status_code == 401
    assert b"That class password is not correct" in response.data


def test_mcp_authorization_issues_code_after_class_password(client):
    request_id = _begin_authorization()

    response = client.post(
        f"/oauth/authorize?request_id={request_id}",
        data={"password": "test-class-password"},
    )

    assert response.status_code == 302
    query = parse_qs(urlparse(response.headers["Location"]).query)
    assert query["state"] == ["test-state"]
    assert query["code"][0] in oauth_provider.codes
