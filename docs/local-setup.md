# Local reviewer setup

Follow the [README setup](../README.md#local-setup). Copy [the environment sample](../backend/.env.example) to `backend/.env` if you need custom settings. Leave MongoDB unset for a disposable session. Set `MONGODB_URI`, `MONGODB_DB`, and a stable `SECRET_KEY` to test persistence with an isolated database. Keep `SESSION_COOKIE_SECURE=1` for HTTPS environments. Set `GEMINI_API_KEY` only for a live AI check and use a scoped test key.

## Seed a sample project

With Flask running at localhost, use a fresh email or change the sample address on subsequent runs. Sign in through the UI with the same account. Add a section, save a revision, and load the project again. If using MongoDB, restart Flask and verify the manuscript persists.
