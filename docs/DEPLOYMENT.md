# Deploying StudyAI

The app is ready to deploy. The backend runs on **Render**, the frontend on **Vercel**, the database on
**Neon** (PostgreSQL), emails are sent with **Brevo**, and AI plans use **Google Gemini**. All of them
have free plans that are enough to launch.

## 1. What the client needs to provide

| # | Account / item | Used for | Free plan | What to hand over |
|---|---|---|---|---|
| 1 | **GitHub** repository (or access to one) | Render and Vercel deploy from it | Yes | Repo access |
| 2 | **Render** account | Backend API | Yes | Account access (or do the steps below themselves) |
| 3 | **Vercel** account | Frontend website | Yes | Account access |
| 4 | **Neon** account | PostgreSQL database | Yes (0.5 GB) | Connection string |
| 5 | **Brevo** account + a sender email | Verification and password-reset emails | Yes (300 emails/day) | API key + the verified sender address |
| 6 | **Google Gemini** API key | AI study plans | Yes (rate-limited) | API key + chosen model name |
| 7 | *(optional)* Custom domain | e.g. `app.clientname.com` | — | DNS access |

The sender email for Brevo can be any inbox the client controls (e.g. `studyai.team@gmail.com` or
`hello@clientdomain.com`). Brevo sends a confirmation link to it once. With their own domain they can also
authenticate it in Brevo for better inbox placement — recommended but not required.

## 2. Collect the keys

**Neon** — create a project → *Connection Details* → copy the connection string
(`postgresql://…neon.tech/…?sslmode=require`).

**Brevo** — sign up → *Senders, domains & dedicated IPs* → add and verify the sender email →
*SMTP & API* → *API keys* → create a key.

**Gemini** — open Google AI Studio → *Get API key* → create a key. Pick the model to use from the model list
in AI Studio (the app reads it from `GEMINI_MODEL`, so it can be changed any time without code changes).

## 3. Deploy the backend (Render)

1. Push this repository to GitHub.
2. Render → **New → Blueprint** → select the repository. Render reads [`render.yaml`](../render.yaml).
3. Fill in the values it asks for:
   - `DATABASE_URL` — the Neon connection string
   - `BREVO_API_KEY`, `EMAIL_FROM` — from Brevo
   - `GEMINI_API_KEY`, `GEMINI_MODEL` — from Google AI Studio
   - `CORS_ORIGINS` — leave as `http://localhost:5173` for now; it's updated in step 5
   - `JWT_SECRET` is generated automatically.
4. Deploy. Migrations run automatically on start. Check `https://<service>.onrender.com/health`
   returns `{"status":"ok"}`.

If a required setting is missing, the service won't start and the Render log lists exactly what to fix
(e.g. `JWT_SECRET must be set…`).

## 4. Deploy the frontend (Vercel)

1. Vercel → **Add New → Project** → import the same repository.
2. **Root Directory:** `frontend` (framework preset: Vite — detected automatically).
3. Environment variable: `VITE_API_URL` = the Render URL, e.g. `https://studyai-api.onrender.com`
   (no trailing slash).
4. Deploy and note the site URL, e.g. `https://studyai.vercel.app`.

## 5. Connect them

In Render → the service → **Environment**, set `CORS_ORIGINS` to the Vercel URL
(comma-separate several, e.g. a custom domain too) and save — Render redeploys.

## 6. Smoke test

1. Open the Vercel URL and register with a real email address → the 6-digit code should arrive
   (check spam the first time).
2. Verify, add a subject with topics, an exam and a mark → the dashboard updates.
3. My Study Plan → **Generate AI Plan** → a preview appears → Save.
4. Log out → **Forgot password?** → reset with the emailed code.

## Good to know

- **Render free plan sleeps** after about 15 minutes without traffic; the first request afterwards takes
  up to a minute while it wakes. The app shows "the server may be waking up — try again". A paid instance
  removes this.
- The demo seed (`python -m app.seed`) is for local testing; don't run it against the production database.
- Emails: Brevo's free plan allows 300 per day. Gmail SMTP isn't used in production because Render's free
  tier blocks outgoing SMTP connections.
- Login tokens last 24 hours (`JWT_EXPIRE_MINUTES`). Changing `JWT_SECRET` logs everyone out.
