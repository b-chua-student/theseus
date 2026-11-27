# Local reviewer setup

Follow the [README setup](../README.md#local-setup). Copy [the environment sample](../backend/.env.example) to `backend/.env` if you need custom settings. Leave MongoDB unset for a disposable session. Set `MONGODB_URI`, `MONGODB_DB`, and a stable `SECRET_KEY` to test persistence with an isolated database. Keep `SESSION_COOKIE_SECURE=1` for HTTPS environments. Set `GEMINI_API_KEY` only for a live AI check and use a scoped test key.

## Run with Docker

Start Docker and run these commands from the repository root. The build downloads dependencies and the MiniLM model. The container serves the UI and API together.

```sh
docker build -t theseus:local .
docker run --rm -p 127.0.0.1:5000:5000 theseus:local
```

Open [http://localhost:5000](http://localhost:5000). From a second terminal, verify that the API responds.

```sh
curl --fail http://localhost:5000/api/health
```

Press Ctrl+C to stop the container. Data stored in memory is lost when it stops. If port 5000 is already in use, publish `127.0.0.1:5001:5000` and use port 5001 in the browser and health check.

For persistence or live Gemini calls, create `backend/.env` from the sample if it does not already exist, configure it as described above, and pass it to Docker at runtime.

```sh
docker run --rm --env-file backend/.env -p 127.0.0.1:5000:5000 theseus:local
```

Keep `PORT=5000` or leave it unset for this mapping, and leave `SESSION_COOKIE_SECURE` unset when testing over local HTTP. Set `MONGODB_URI` to an address reachable from the container. For MongoDB running on the Docker Desktop host, use `host.docker.internal` in the URI. On Linux Docker Engine, add `--add-host=host.docker.internal:host-gateway` before the image name and ensure MongoDB listens on a host interface reachable from the container.

## Seed a sample project

With the app running, sign in or register a disposable test account. Create a project named **Demo workspace**, then create **Demo manuscript** and add a section titled **Introduction**. Give it a sample paragraph and save a revision. Reload the project and verify that the manuscript and revision are still available. If using MongoDB, restart the backend and repeat the verification.

These steps work with either the native dev server or the Docker container.

## Verify the writing assistant

Set `GEMINI_API_KEY` in `backend/.env` and restart the app. For Docker, start it with the `--env-file` command above. Use sample text you can send to Gemini.

1. In **Demo workspace**, open **Source Library** and choose **+ Add text**. Title the source **Trial notes**, paste “The greenhouse trial used 37 basil seedlings. The team watered them every Tuesday.” into **Content**, and choose **Create**.
2. Open **Demo manuscript** and launch **Theseus Scholar AI**. Open the context dropdown, select **Trial notes** when it appears among the indexed sources, and clear **Web** and **Manuscript**.
3. Ask “How many basil seedlings did the greenhouse trial use?” Check that the answer gives **37** and that any source citation points to **Trial notes**. If the source is unavailable, reopen the dropdown after indexing has had time to finish. While signed in, check `GET /api/projects/{project_id}/indexed-sources` for the source ID in `source_ids`. If it is missing, check the backend logs for indexing or provider errors.
