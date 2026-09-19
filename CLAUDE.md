# CLAUDE.md

## Project overview
Python FastAPI application.

## Dependency management
- Poetry (version 2.1.1) manages all dependencies.
- Add new dependencies through Poetry, not pip.

## Project structure
- `main.py` — FastAPI entrypoint, stays in the project root.
- `src/` — application code, organized directly into layers (no `app/` subdirectory):
  - `routes/` — HTTP/API layer. Handles request/response only; delegates business logic to services.
  - `services/` — business logic.
  - `repositories/` — data access and external API integrations.
  - `models/` — Pydantic/data models.
  - `consts/` — constants and enums.
  - `data/` — local/static data.
- `tests/` — all tests.

## API conventions
- All endpoints are exposed under the `/api` prefix.
- The `/api` prefix is centralized once in the main API router (`src/routes/__init__.py`), not repeated per route.

## Commands
- Install dependencies: `poetry install`
- Run the application locally: `poetry run uvicorn main:app --reload`
- Run tests: `poetry run pytest`
