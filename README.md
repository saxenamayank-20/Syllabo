# Syllabo

Syllabo is a study planner for students. You add your subjects, topics, exams and marks, and it shows you where
you stand: what's on today, how many days are left until your next exam, how far through the syllabus you are,
and which subjects need more attention. When you want a plan, it can put together a day-by-day study schedule
with Google Gemini, built around your exams, your weak subjects and the time you actually have.

![Syllabo dashboard](docs/screenshot-dashboard.png)

## What it does

- **Dashboard** with today's tasks, a countdown to the next exam, overall progress, your current grade, a
  marks-vs-target chart per subject, upcoming exams and suggestions for subjects that are falling behind.
- **Subjects and topics** — tick topics off as you finish them.
- **Exams and marks** — record test results and see how they compare with the target you set for each subject.
- **My Study Plan** — tasks grouped by day. Add your own, or generate a plan with AI, review it, and save it
  only if you like it.
- **Accounts** — sign-up with email verification, password reset by email, and a settings page for your
  profile, timezone, password and study preferences.

## Built with

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL (SQLite for local development)
- **Frontend:** React (Vite), Tailwind CSS, React Router, Recharts
- **AI:** Google Gemini
- **Email:** Brevo (or any SMTP server)

## Running it locally

You'll need Python 3.11+ and Node 18+.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed          # optional: adds a demo account with sample data
uvicorn app.main:app --reload
```

The API runs at <http://localhost:8000>, and you can browse every endpoint at <http://localhost:8000/docs>.

You don't need any settings to run it locally. Without a `backend/.env` it uses a SQLite file instead of
PostgreSQL, and instead of sending emails it prints verification and reset codes in the terminal where the
backend is running.

### Frontend

In a second terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Then open <http://localhost:5173>.

### Demo account

If you ran the seed script, log in with **demo@syllabo.app** / **demo1234**. Running the seed script again
resets the demo data. Don't run it against a production database.

## Configuration

The backend reads its settings from `backend/.env` (or from environment variables on the server). The file
isn't committed, so create it yourself. These are the settings that matter most:

| Setting | What it's for |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string. Leave empty to use a local SQLite file. |
| `JWT_SECRET` | Secret used to sign logins. Use a long random value in production. |
| `CORS_ORIGINS` | The frontend address(es) allowed to call the API. |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Google Gemini key and model for AI study plans. Without them, everything else still works. |
| `EMAIL_PROVIDER` | `console` (print codes in the terminal), `brevo`, or `smtp`. |
| `BREVO_API_KEY`, `EMAIL_FROM` | Brevo key and the sender address verified in Brevo. |
| `ENVIRONMENT` | Set to `production` on the live server; it then refuses to start if anything important is missing. |

The frontend has just one setting, `VITE_API_URL`, which is the address of the backend.

## How the AI study plan works

On **My Study Plan**, set how many minutes a day you can study, which days, and your goal. Then click
**Generate AI Plan** and pick a date range. The app sends Gemini your subjects, unfinished topics, upcoming
exams, weak subjects and the free time left on each day. It asks for a plan that puts nearer exams and weaker
subjects first and never goes over your daily limit.

The answer is checked before you see it. Anything that doesn't match your subjects, lands on a day off, or
doesn't fit in the time available is left out, and the preview tells you what was skipped. Nothing is saved
until you click **Save**. Generating a new plan for the same dates only replaces earlier AI tasks you haven't
done yet. Your own tasks and anything you've completed are never touched.

## Accounts and email

New accounts get a 6-digit code by email and need to enter it before they can log in. Addresses on domains
that can't receive mail, and throwaway inboxes like mailinator, are turned away at sign-up. The same kind of
code is used for "Forgot password". Codes expire after 10 minutes, and login and sign-up attempts are
rate-limited. Changing or resetting a password signs you out everywhere else.

## Tests

```bash
cd backend && pytest
cd frontend && npm test
```

The backend tests use an in-memory database. To run them against PostgreSQL instead, set
`TEST_DATABASE_URL` to an empty test database.

## Project structure

```text
backend/
  app/
    core/        settings, database, security, rate limiting
    models/      database tables
    schemas/     request and response shapes
    routers/     API endpoints
    services/    business logic, Gemini and email
  alembic/       database migrations
  tests/
frontend/
  src/
    api/         API client
    components/  shared UI pieces
    context/     login state and notifications
    pages/       one file per screen
docs/            design mockup
render.yaml      backend hosting config (Render)
```
