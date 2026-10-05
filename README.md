# StudyAI — AI-Based Student Study Planner & Performance Tracker

Full-stack app: FastAPI + SQLAlchemy backend, React (Vite) frontend, Google Gemini for AI study plans.

> **Status:** Phases 1–3 complete (backend, frontend core, AI study plans) plus email verification.

## Project layout

```
studyai/
  backend/    FastAPI app, Alembic migrations, tests, seed script
  frontend/   React (Vite) + Tailwind app
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
| `GEMINI_API_KEY` | Google Gemini API key (from Google AI Studio). Without it, AI plan generation returns a clear "not configured" error; everything else works. |
| `GEMINI_MODEL` | Gemini model name to use (read from env, never hardcoded). |
| `SMTP_HOST` / `SMTP_PORT` | Mail server for verification emails (default Gmail: `smtp.gmail.com` / `587`). |
| `SMTP_USER` | Sending address, e.g. `yourapp@gmail.com`. **Empty = dev mode:** codes are printed in the backend terminal. |
| `SMTP_PASSWORD` | Gmail **App Password** (16 characters), not the normal account password. |
| `SMTP_FROM_NAME` | Display name on outgoing mail (default `StudyAI`). |
| `EMAIL_CHECK_DELIVERABILITY` | `true` (default) rejects emails whose domain can't receive mail. |

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

## Frontend setup

Requires Node 18+.

```bash
cd frontend
cp .env.example .env   # VITE_API_URL, defaults to http://localhost:8000
npm install
npm run dev            # http://localhost:5173
```

Log in with the seeded demo account (`demo@studyai.app` / `demo1234`) or register a new one.
`npm run build` produces a production bundle in `frontend/dist/`.

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend base URL (default `http://localhost:8000`). Must be listed in the backend's `CORS_ORIGINS`. |

## API overview

All endpoints except `/auth/register`, `/auth/login` and `/health` require `Authorization: Bearer <token>`. Every query is scoped to the logged-in user; other users' records return 404.

| Method & path | Purpose |
|---|---|
| `POST /auth/register` | Creates an unverified account and emails a 6-digit code (no token yet) |
| `POST /auth/verify-email` | `{email, code}` → `{access_token, user}` |
| `POST /auth/resend-code` | `{email}` → sends a new code (once per 60 s) |
| `POST /auth/login` | `{access_token, user}`; 403 `email_not_verified` until the email is verified |
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
| `POST /ai/generate-plan` | `{start_date, end_date}` → validated plan **preview** from Gemini (nothing saved) |
| `POST /ai/save-plan` | Saves a previewed plan; replaces only *pending AI* tasks in that range |

## Email verification

New accounts must verify their email before they can log in.

- On sign-up the address is checked: its domain must be able to receive mail (DNS MX lookup) and
  throwaway inboxes (mailinator, yopmail, temp-mail, …) are rejected.
- A 6-digit code is emailed. It expires after 10 minutes, allows 5 wrong attempts, and can be resent once a
  minute. Codes are stored hashed.
- Logging in to an unverified account sends the user to the "Check your email" screen.

**Gmail setup:** turn on 2-Step Verification on the Gmail account, create an App Password
(Google Account → Security → App passwords), then set `SMTP_USER=you@gmail.com` and
`SMTP_PASSWORD=<16-char app password>` in `backend/.env` and restart the backend. Gmail allows roughly
500 emails/day on a free account; use Brevo/Resend/SendGrid SMTP (same settings, different host) for more.

Without `SMTP_USER`, the backend prints each code in its terminal, so you can test locally with no email account.

## AI study plans

On **My Study Plan**, set your daily minutes, study days and goal under *Study settings*, then click
**Generate AI Plan** and pick a date range (max 31 days). Gemini is called only when you click Generate.

1. The backend sends Gemini your subjects, pending topics, upcoming exams, weak subjects, preferences and the
   free minutes left on each study day (existing manual/completed tasks count against the daily limit),
   and asks for JSON only.
2. The response is validated with Pydantic; if it is malformed the request is retried once, then a clear
   error is returned. Rate limits (HTTP 429) produce a friendly "try again in a minute" message.
3. Subject/topic names are mapped back to your IDs. Anything that doesn't match, falls on a non-study day,
   or would exceed the daily minutes is skipped (and listed in the preview).
4. You review the preview and choose **Save**, **Regenerate** or **Cancel**. Saving stores the plan in
   `study_plans` and creates `study_tasks` with `source='ai'`, first deleting only the *pending AI* tasks in
   that date range — manual and completed tasks are never touched.
