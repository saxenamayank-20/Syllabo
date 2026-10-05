# StudyAI — AI-Based Student Study Planner & Performance Tracker

Full-stack app: FastAPI + SQLAlchemy backend, React (Vite) + Tailwind frontend, Google Gemini for AI study plans.

> **Status:** feature-complete for the current scope. Deployment is prepared (Render + Vercel + Neon) and waits
> only on the accounts and keys listed in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Features

- Sign-up with **email verification** (6-digit code), login, **forgot/reset password**, change password
- Dashboard: today's tasks, days to next exam, overall progress, current grade, marks-vs-target chart,
  upcoming exams, recommendations for weak subjects
- Subjects & topics, exams, marks and study tasks — add, edit, delete, mark complete
- **AI study plans** (Gemini) with a preview before saving
- Settings: profile, timezone, password, study preferences
- Each user's "today" follows their own timezone

## Project layout

```
studyai/
  backend/        FastAPI app, Alembic migrations, tests, seed script
  frontend/       React (Vite) + Tailwind app
  docs/           UI mockup, deployment guide
  render.yaml     Render Blueprint for the backend
```

## Backend setup

Requires Python 3.11+.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # defaults work for local development
alembic upgrade head          # create tables
python -m app.seed            # optional: demo data
uvicorn app.main:app --reload # http://localhost:8000  (API docs at /docs)
```

### Environment variables (`backend/.env`)

| Variable | Description |
|---|---|
| `ENVIRONMENT` | `development` (default) or `production`. In production the server **refuses to start** if `JWT_SECRET`, `DATABASE_URL` or a real email provider is missing. |
| `DATABASE_URL` | PostgreSQL URL (e.g. Neon). `postgresql://…` and `postgres://…` both work. **Empty = local SQLite** (`backend/studyai.db`). |
| `JWT_SECRET` | Secret for signing login tokens (32+ random characters). Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_EXPIRE_MINUTES` | Login lifetime in minutes (default 1440 = 1 day). |
| `CORS_ORIGINS` | Comma-separated allowed frontend URLs (default `http://localhost:5173`). |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Google Gemini key and model name. Without them, AI plan generation shows a clear "not configured" message; everything else works. |
| `EMAIL_PROVIDER` | `console` (default — codes are printed in the backend terminal), `brevo` (recommended for production) or `smtp`. |
| `EMAIL_FROM` / `EMAIL_FROM_NAME` | Sender address and display name. With Brevo the address must be a verified sender. |
| `BREVO_API_KEY` | Brevo API key (when `EMAIL_PROVIDER=brevo`). |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | SMTP settings (when `EMAIL_PROVIDER=smtp`). For Gmail use an App Password. |
| `EMAIL_CHECK_DELIVERABILITY` | `true` (default) rejects emails whose domain can't receive mail. |
| `AUTH_RATE_LIMIT` / `AUTH_RATE_WINDOW_SECONDS` | Login/sign-up/code attempts allowed per IP (default 10 per 5 minutes). |

### Seed data

```bash
python -m app.seed
```

Creates (or resets) a demo account — **email** `demo@studyai.app`, **password** `demo1234` (already verified,
timezone Asia/Kolkata) — with 5 subjects, topics, exams, today's tasks, marks and study preferences.
Re-running it wipes and recreates only the demo user's data.

### Tests

```bash
pytest                                                        # in-memory SQLite
TEST_DATABASE_URL=postgresql://user:pass@host/testdb pytest   # same suite on PostgreSQL
```

Point `TEST_DATABASE_URL` only at an empty, throwaway database — tables are dropped between tests.

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
npm test               # Vitest + Testing Library
npm run build          # production bundle in frontend/dist/
```

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend base URL (default `http://localhost:8000`). Must be listed in the backend's `CORS_ORIGINS`. |

## Accounts & email

- **Sign-up** checks the address first: its domain must be able to receive mail (DNS MX lookup), and
  throwaway inboxes (mailinator, yopmail, temp-mail, …) are rejected. A 6-digit code is emailed and the
  account can't log in until it is verified.
- **Forgot password** emails a reset code. Resetting (or changing) a password logs out every other session.
- Codes expire after 10 minutes, allow 5 wrong attempts, can be resent once a minute, and are stored hashed.
- Login, sign-up and code endpoints are rate-limited per IP. The limiter is in-memory, which fits a single
  server instance; running several instances would need a shared store such as Redis.
- **Local development:** with `EMAIL_PROVIDER=console`, codes appear in the backend terminal, so no email
  account is needed.
- **Production:** Brevo's HTTP API is recommended because Render's free tier blocks outgoing SMTP.
  Gmail via SMTP also works on hosts that allow it (`EMAIL_PROVIDER=smtp`, App Password, ~500 emails/day).

## AI study plans

On **My Study Plan**, set your daily minutes, study days and goal under *Study settings* (also on the
Settings page), then click **Generate AI Plan** and pick a date range (max 31 days). Gemini is called only
when you click Generate.

1. The backend sends Gemini your subjects, pending topics, upcoming exams, weak subjects, preferences and the
   free minutes left on each study day (existing manual/completed tasks count against the daily limit),
   and asks for JSON only.
2. The response is validated with Pydantic; if it is malformed the request is retried once, then a clear
   error is returned. Rate limits produce a friendly "try again in a minute" message.
3. Subject/topic names are mapped back to your IDs. Anything that doesn't match, falls on a non-study day,
   or would exceed the daily minutes is skipped (and listed in the preview).
4. You review the preview and choose **Save**, **Regenerate** or **Cancel**. Saving stores the plan in
   `study_plans` and creates `study_tasks` with `source='ai'`, first deleting only the *pending AI* tasks in
   that date range — manual and completed tasks are never touched. Editing an AI task turns it into a
   manual task, so regenerating never overwrites your edits.

## API overview

All endpoints except the public `/auth/*` ones and `/health` require `Authorization: Bearer <token>`.
Every query is scoped to the logged-in user; other users' records return 404. Interactive docs: `/docs`.

| Method & path | Purpose |
|---|---|
| `POST /auth/register` | Creates an unverified account and emails a code (no token yet) |
| `POST /auth/verify-email` | `{email, code}` → `{access_token, user}` |
| `POST /auth/resend-code` | `{email}` → new verification code (once per 60 s) |
| `POST /auth/login` | `{access_token, user}`; 403 `email_not_verified` until verified |
| `POST /auth/forgot-password` | `{email}` → emails a reset code (same response whether or not the account exists) |
| `POST /auth/reset-password` | `{email, code, new_password}` → `{access_token, user}` |
| `GET/PATCH /auth/me` | Current user; update name / timezone |
| `POST /auth/change-password` | `{current_password, new_password}` → fresh token, other sessions logged out |
| `GET/POST /subjects`, `GET/PATCH/DELETE /subjects/{id}` | Subjects (GET includes nested topics) |
| `GET/POST /subjects/{id}/topics`, `PATCH/DELETE /topics/{id}` | Topics (empty PATCH body toggles status) |
| `GET /exams?upcoming=true`, `POST /exams`, `PATCH/DELETE /exams/{id}` | Exams sorted by date |
| `GET/PUT /preferences` | Daily minutes, study days, goal note |
| `GET /tasks?date=YYYY-MM-DD`, `POST /tasks`, `PATCH/DELETE /tasks/{id}`, `PATCH /tasks/{id}/status` | Study tasks |
| `GET /marks?subject_id=`, `POST /marks`, `PATCH/DELETE /marks/{id}` | Assessment marks |
| `GET /dashboard/summary` | Stats for the dashboard |
| `POST /ai/generate-plan` | `{start_date, end_date}` → validated plan **preview** (nothing saved) |
| `POST /ai/save-plan` | Saves a previewed plan; replaces only *pending AI* tasks in that range |

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the step-by-step guide and the list of accounts/keys needed.
