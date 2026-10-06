# Project: StudyAI — AI-Based Student Study Planner & Performance Tracker

You are building a full-stack web app for a client. Build it in PHASES. After each phase: run the app, fix errors, write a short summary of what was done, and STOP and wait for my confirmation before starting the next phase. Do not add features outside this spec. If something is ambiguous, pick the simplest reasonable option and note it in the summary.

## Tech stack (fixed — do not change)
- Frontend: React (Vite) + Tailwind CSS + React Router + Axios + Recharts
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0 (ORM), Alembic (migrations), Pydantic v2
- Database: PostgreSQL (hosted on Neon). Use SQLite automatically if DATABASE_URL is not set, for local dev.
- Auth: JWT (access token), passwords hashed with bcrypt
- AI: Google Gemini via the official `google-genai` Python SDK. Read the model name from env var GEMINI_MODEL; do not hardcode it.
- All secrets in `.env` (never committed). Provide `.env.example`.

## Folder structure
```
studyai/
  backend/
    app/
      main.py
      core/        (config.py, security.py, database.py)
      models/      (SQLAlchemy models)
      schemas/     (Pydantic schemas)
      routers/     (auth, subjects, topics, exams, tasks, marks, dashboard, ai)
      services/    (business logic, gemini_service.py)
    alembic/
    tests/
    requirements.txt
  frontend/
    src/
      api/         (axios client with JWT interceptor)
      components/
      pages/
      context/     (AuthContext)
  docs/
    mockup-dashboard.jpg
  README.md
```

## Database schema
- users: id, name, email (unique), password_hash, created_at
- subjects: id, user_id (FK), name, color, target_score (0–100, default 75)
- topics: id, subject_id (FK), name, status ('pending' | 'completed'), completed_at
- exams: id, user_id (FK), subject_id (FK, nullable), title, syllabus (text), exam_date
- study_preferences: id, user_id (FK, unique), daily_study_minutes, study_days (e.g. "Mon,Tue,Wed,Thu,Fri,Sat"), goal_note (text)
- study_tasks: id, user_id (FK), subject_id (FK), topic_id (FK, nullable), title, scheduled_date, start_time, duration_mins, status ('pending' | 'completed'), source ('manual' | 'ai'), plan_id (FK, nullable)
- marks: id, user_id (FK), subject_id (FK), assessment_name, score, max_score, assessment_date
- study_plans: id, user_id (FK), generated_at, start_date, end_date, raw_json (JSON/text)

Every query must be scoped to the logged-in user. A user must never see another user's data.

---

## PHASE 1 — Backend foundation
1. Project setup, config, DB connection, Alembic initial migration with all tables above.
2. Auth: POST /auth/register, POST /auth/login (returns JWT), GET /auth/me. Add a `get_current_user` dependency.
3. CRUD endpoints (all protected):
   - /subjects (with nested topics on GET)
   - /subjects/{id}/topics, PATCH /topics/{id} (toggle status)
   - /exams (list sorted by date, upcoming only via ?upcoming=true)
   - /preferences (GET, PUT)
   - /tasks (filter by ?date=YYYY-MM-DD), PATCH /tasks/{id}/status
   - /marks
4. GET /dashboard/summary returning:
   - today_tasks_total, today_tasks_completed
   - days_to_next_exam + next_exam (null if none)
   - overall_progress = completed topics / total topics × 100
   - progress_change_this_week = percentage points of topics completed in the last 7 days
   - current_grade from average mark percentage: A ≥ 80, B ≥ 65, C ≥ 50, D ≥ 35, else F (null if no marks)
   - subject_performance: list of {subject, avg_percentage, target_score}
   - weak_subjects: subjects where avg_percentage < target_score
5. Proper error handling (404, 401, 422), CORS enabled for the frontend dev URL.
6. Basic pytest tests for auth and one CRUD flow.
7. A seed script (`python -m app.seed`) that creates a demo user with sample subjects, topics, exams, tasks and marks.

## PHASE 2 — Frontend core (match the mockup style)

**Reference mockup: `docs/mockup-dashboard.jpg` (also attached in chat if available).** Use it as the visual reference for the layout, sidebar, stat cards, Today's Study Plan list, Performance Overview chart, Upcoming Exams card and AI Recommendations card. Match its style (colors, spacing, rounded cards, typography) as closely as practical, but:
- Ignore everything outside the laptop screen (desk, mugs, notebook, quote posters)
- Ignore the "Discipline today, a brighter tomorrow" quote and the sidebar quote
- All numbers, names and tasks in the mockup are sample data; render real data from the API
- Small layout changes are fine if they improve responsiveness

Design: clean light dashboard, white cards with soft shadows and rounded corners, blue primary color, left sidebar, top bar with search and notification icon. Fully responsive (sidebar collapses on mobile).
1. Login and Register pages, AuthContext, protected routes, token stored in memory + localStorage, auto-logout on 401.
2. Layout: sidebar with Dashboard, My Study Plan, Subjects, Performance, AI Assistant, Calendar, Notes, Settings. Pages not built yet show a clean "Coming soon" placeholder. User name/email at the bottom of the sidebar.
3. Dashboard page:
   - Greeting ("Good Morning/Afternoon/Evening, {name}") + today's date
   - 4 stat cards: Today's Tasks (x completed), Days to Exam, Overall Progress (+change this week), Current Grade
   - Today's Study Plan list with checkboxes (toggling calls the API and updates the stats)
   - Performance Overview bar chart (Recharts): marks vs target per subject
   - Upcoming Exams card (next 3)
   - AI Recommendations card: for now show the weak_subjects from the API as simple rule-based suggestions
4. Subjects page: add/edit/delete subjects; add topics and mark them complete.
5. Performance page: add marks via a form, table of past marks, the same chart.
6. My Study Plan page: tasks grouped by date, add a manual task, mark complete.
7. Loading states, empty states ("No exams added yet"), and error toasts everywhere.

## PHASE 3 — AI study plan generation
1. Settings section (inside My Study Plan page): set daily study minutes, study days, goal note.
2. POST /ai/generate-plan with body {start_date, end_date}:
   - Collect the user's subjects, pending topics, upcoming exams, preferences and weak subjects.
   - Send a structured prompt to Gemini asking for a JSON response ONLY, in the format:
     {"days":[{"date":"YYYY-MM-DD","tasks":[{"subject":"...","topic":"...","title":"...","start_time":"HH:MM","duration_mins":60}]}]}
   - Rules for the plan: prioritize subjects with nearer exams and weak subjects, never exceed the daily study minutes, only schedule on chosen study days.
   - Validate the response with a Pydantic model. If parsing fails, retry once, then return a clear error.
   - Save the plan in study_plans and create study_tasks with source='ai'. Map subject/topic names back to IDs; skip anything that doesn't match.
   - Generating a new plan for an overlapping date range deletes only the previous pending AI tasks in that range (never manual or completed tasks).
3. Frontend: "Generate AI Plan" button with a date range picker, loading state, and a preview of the generated plan before it's saved (Save / Regenerate / Cancel).
4. Gemini is called ONLY when the user clicks generate — never on page load. Handle rate-limit errors with a friendly message.

---

## STOP after Phase 3. Do NOT build yet:
AI chat assistant, AI-written recommendations, Calendar, Notes, notifications, search, deployment.

## Quality rules
- Clean, readable code with type hints; no unused files
- Keep business logic in services/, not in routers
- Update README with setup steps (backend + frontend), env variables and how to run the seed script
- Commit after each phase with a clear message


