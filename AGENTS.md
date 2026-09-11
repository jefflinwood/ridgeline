# Repository Guidelines

## Project Structure & Module Organization

Ridgeline Coffee is a small Flask demo application. `run.py` is the local and Gunicorn entry point, while `config.py` reads database and secret settings from the environment. Application code lives in `app/`: each business area (`orders.py`, `catalog.py`, `roasting.py`, and similar) is a Flask blueprint, `models.py` defines SQLAlchemy entities, and `demo_data.py` supplies shared seed records. Keep Jinja templates under `app/templates/<blueprint>/` and browser styles in `app/static/css/style.css`. The separate `mcp_server/` package is a stdio client for the app's `/api/*` endpoints. Deployment configuration is in `Procfile` and `render.yaml`.

## Build, Test, and Development Commands

Create and activate a virtual environment before installing dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py
python run.py
```

`python seed.py` destructively recreates `ridgeline.db`; do not run it against data you need to preserve. The app is then available at `http://127.0.0.1:5000`. For MCP development, install `mcp_server/requirements.txt` separately and run `python mcp_server/server.py` with the Flask app available.

## Coding Style & Naming Conventions

Use four-space indentation and follow PEP 8. Prefer `snake_case` for functions, variables, modules, routes, and template directories; use `PascalCase` for models and configuration classes. Keep route handlers thin, put shared data logic in dedicated modules, and register new blueprints in `app/__init__.py`. Match the existing import grouping: standard library, Flask/third-party packages, then local `app` imports. No formatter or linter is configured, so keep changes consistent with nearby code.

## Testing Guidelines

This checkout has no automated test suite or coverage threshold. For changes, add focused `pytest` tests under `tests/` using names such as `test_orders.py` and `test_customer_cannot_view_other_order`. Until a suite is added, smoke-test login, role authorization, the affected workflow, and relevant `/api/*` responses. Verify a clean startup after reseeding.

## Commit & Pull Request Guidelines

Git history is not included in this checkout, so no repository-specific commit convention can be inferred. Use short, imperative subjects such as `Validate roast batch weights`, and keep unrelated changes separate. Pull requests should explain behavior changes, list verification performed, link the relevant issue, and include screenshots for template or CSS updates. Call out schema, seed-data, API, or environment-variable changes explicitly.

## Security & Configuration

Never commit `ridgeline.db`, credentials, or production secrets. Set `SECRET_KEY`, `RIDGELINE_API_KEY`, and optionally `DATABASE_URL` through the environment. The default credentials and API key are for local demonstrations only.
