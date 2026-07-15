# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
KipGPT is a Turkish-language Flask app with two client surfaces backed by one backend:
- **Flask web app (primary product)** — `app.py` registers four blueprints: `auth` (local + Google OAuth login), `chat` (ChatGPT-style assistant at `/`), `mail` (Gmail-style webmail at `/mail`), and `mobile_api` (JSON REST API under `/api/v1`).
- **Android app (secondary client)** — `android/` is a Kotlin/Jetpack Compose client that talks to `/api/v1`. Building it requires the Android SDK + JDK 17 (not installed by the update script); the web app is fully usable on its own.

Persistence is flat JSON files (`users.json`, `data.json`), auto-created on startup. There is no database, and no test suite or lint config in the repo.

### Running the web app (dev)
- Start: `python3 app.py` — serves on `0.0.0.0:5001` with Flask debug + auto-reloader on (reloader is disabled only when the `RENDER` env var is set). Chat UI at `/`, webmail at `/mail`.
- Dev quick login: username `q`, password `q` (see `users.py`). New local accounts can also be created at `/register`.
- Python dependencies are installed by the update script (`pip install -r requirements.txt`) into the user site (`~/.local`).

### Credentials / gotchas
- The app boots and login works with **no** external credentials. `.env` is optional (git-ignored); copy `.env.example` to `.env` to configure keys locally.
- **AI features require `OPENAI_API_KEY`.** Without it, chat / file analysis / mail AI reply / translation return a graceful in-UI error (`"...OPENAI_API_KEY ayarlı değil."`) rather than crashing. Set `OPENAI_API_KEY` (optionally `OPENAI_MODEL`, default `gpt-4.1`) in `.env` to enable them.
- **Mail features require real IMAP/SMTP accounts** added through the `/mail` UI (Gmail/Outlook/Yahoo/custom); credentials are stored in `users.json`.
- **Google OAuth is optional** (`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI`, or a `google_client_secret.json`). Sign-in-with-Google buttons are hidden until it is configured.
