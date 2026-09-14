"""Combined ASGI entry point for the Flask site and hosted MCP server."""
import os

from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.routing import Mount

from app import create_app
from mcp_server.server import server as mcp_server


def _comma_separated_env(name):
    return [
        value.strip()
        for value in os.environ.get(name, "").split(",")
        if value.strip()
    ]


def _transport_security():
    """Allow local development, Render, and explicitly configured custom domains."""
    allowed_hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    allowed_origins = [
        "http://127.0.0.1:*",
        "http://localhost:*",
        "http://[::1]:*",
    ]

    render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if render_hostname:
        allowed_hosts.extend([render_hostname, f"{render_hostname}:*"])
        allowed_origins.append(f"https://{render_hostname}")

    allowed_hosts.extend(_comma_separated_env("MCP_ALLOWED_HOSTS"))
    allowed_origins.extend(_comma_separated_env("MCP_ALLOWED_ORIGINS"))

    return TransportSecuritySettings(
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


flask_app = create_app()
if not flask_app.config.get("MCP_CLASS_PASSWORD"):
    raise RuntimeError("MCP_CLASS_PASSWORD must be set to host the MCP endpoint.")

# Keep the MCP app at the top level so its lifespan starts its session manager.
# Its /mcp route is registered before the catch-all Flask mount.
app = mcp_server.streamable_http_app(
    stateless_http=True,
    transport_security=_transport_security(),
)
app.routes.append(Mount("/", app=WSGIMiddleware(flask_app)))
