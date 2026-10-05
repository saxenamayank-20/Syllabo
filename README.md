# StudyAI — AI-Based Student Study Planner & Performance Tracker

Full-stack app: FastAPI + SQLAlchemy backend, React (Vite) frontend, Google Gemini for AI study plans.

> **Status:** Phase 1 (backend foundation) complete. Frontend and AI plan generation come in Phases 2–3.

## Project layout

```
studyai/
  backend/    FastAPI app, Alembic migrations, tests, seed script
  frontend/   React (Vite) app — Phase 2
  docs/       UI mockup (mockup-dashboard.jpg)
```

## Backend setup

Requires Python 3.11+.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit values
alembic upgrade head          # create tables
python -m app.seed            # optional: demo data
uvicorn app.main:app --reload # http://localhost:8000  (API docs at /docs)
```

### Environment variables (`backend/.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL URL (e.g. Neon). `postgresql://…` and `postgres://…` are accepted and use the psycopg driver. **Leave empty to use local SQLite** (`backend/studyai.db`). |
| `JWT_SECRET` | Secret used to sign access tokens. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes (default 1440). |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins (default `http://localhost:5173`). |
| `GEMINI_API_KEY` | Google Gemini API key (Phase 3). |
| `GEMINI_MODEL` | Gemini model name (Phase 3) — not hardcoded. |

### Seed data

```bash
python -m app.seed
```

Creates (or resets) a demo account — **email** `demo@studyai.app`, **password** `demo1234` — with 5 subjects, topics, exams, today's tasks, marks and study preferences. Re-running it wipes and recreates only the demo user's data.

### Tests

```bash
pytest
```

Tests use an isolated in-memory SQLite database.

### Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## API overview

All endpoints except `/auth/register`, `/auth/login` and `/health` require `Authorization: Bearer <token>`. Every query is scoped to the logged-in user; other users' records return 404.

| Method & path | Purpose |
|---|---|
| `POST /auth/register`, `POST /auth/login` | Returns `{access_token, user}` |
| `GET /auth/me` | Current user |
| `GET/POST /subjects`, `GET/PATCH/DELETE /subjects/{id}` | Subjects (GET includes nested topics) |
| `GET/POST /subjects/{id}/topics` | Topics of a subject |
| `PATCH /topics/{id}` | Empty body toggles status; or send `{"status": ...}` / `{"name": ...}` |
| `DELETE /topics/{id}` | Delete topic |
| `GET /exams?upcoming=true`, `POST /exams`, `PATCH/DELETE /exams/{id}` | Exams sorted by date |
| `GET/PUT /preferences` | Daily minutes, study days, goal note |
| `GET /tasks?date=YYYY-MM-DD`, `POST /tasks`, `PATCH /tasks/{id}/status`, `DELETE /tasks/{id}` | Study tasks |
| `GET /marks?subject_id=`, `POST /marks`, `DELETE /marks/{id}` | Assessment marks |
| `GET /dashboard/summary` | Stats for the dashboard |
