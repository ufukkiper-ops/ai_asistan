# AGENTS.md

## Cursor Cloud specific instructions

### What this project is
- **KipGPT** is a Flask web app: a Gmail-style mail client (IMAP/SMTP) plus an AI chat assistant (OpenAI) and a JSON mobile API (`routes/mobile_api.py`) consumed by the native Android client in `android/`.
- Data is stored in flat JSON files at the repo root: `users.json` (accounts) and `data.json` (chats). These are created automatically from the `*.example` files / on first run and are gitignored.

### Services
- **Flask web app (primary):** run with `.venv/bin/python app.py` (dev mode, auto-reload, listens on `0.0.0.0:5001`). This also serves the mobile API. There is no separate frontend build step — templates and static assets are served directly.
- **Android client (`android/`):** a Kotlin/Gradle app that talks to the mobile API. Building it requires the Android SDK (`ANDROID_HOME` + `android/local.properties`), which is not installed by the update script. Not needed to run/test the web product.

### Running / dev notes
- The update script creates `.venv` and installs `requirements.txt`. Always use the venv interpreter (`.venv/bin/python`).
- The app runs without any secrets. Missing `OPENAI_API_KEY` only disables AI chat/translation replies; missing Google OAuth vars only disable "Sign in with Google" (email/password login still works).
- **Dev quick login:** username `q`, password `q` (see `users.py`, `DEV_QUICK_*`). This bypasses external auth and lands on `/mail`, making it the easiest way to exercise the app end to end.
- After login the site root `/` redirects to `/mail`. Other key routes: `/login`, `/register`, `/chat`, `/mail-version` (JSON health/version check).
- Adding a mail account (sidebar `+`) only validates and persists the form — it does not verify IMAP/SMTP connectivity, so accounts can be added without real credentials. Actually fetching/sending mail requires valid IMAP/SMTP credentials.
- Production (Render) uses `gunicorn app:app` (see `render.yaml`); for local development use `app.py` directly so debug + reloader are enabled.

### Tests / lint
- There is no automated test suite and no configured linter in this repo. Validate changes by running the app and exercising the affected route. `.venv/bin/python -c "import app"` is a quick import/smoke check.
