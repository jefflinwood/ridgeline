import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    MCP_CLASS_PASSWORD = os.environ.get("MCP_CLASS_PASSWORD")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'ridgeline.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTO_SEED = True
