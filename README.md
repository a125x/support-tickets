# Support Tickets Service

A small FastAPI service for creating and tracking support requests: clients open a
ticket, support replies to it and moves it through the statuses
`open` → `in_progress` → `closed`, and `/stats` shows a live count per status.
Intended as a minimal, fully testable CRUD + workflow API.

## Endpoints

- `POST /tickets` — create a new ticket (returns `201` with an id).
- `GET /tickets/{ticket_id}` — fetch one ticket by id (`404` if missing).
- `GET /tickets?status=open` — list tickets, optionally filtered by status.
- `POST /tickets/{ticket_id}/reply` — add a reply and update the status.
- `GET /stats` — count of tickets per status.
- `GET /` — service info.
- `GET /health` — liveness probe.
- `GET /version` — application version (read from the environment).

Interactive API docs are available at `http://127.0.0.1:8000/docs` (Swagger UI).

## Requirements

- Python 3.9+
- Dependencies: `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`
- Tests: `pytest`, `httpx`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
```

## Run

Normal (production) run — no auto-reload:

```bash
python -m uvicorn app_final:app
```

Development run with auto-reload:

```bash
python -m uvicorn app_final:app --reload
```

The app opens at `http://127.0.0.1:8000`. Try it:

```bash
curl http://127.0.0.1:8000/health    # -> {"status":"ok"}
curl http://127.0.0.1:8000/version   # -> {"app":"support-tickets","version":"1.0.0"}
```

## Tests

```bash
python -m pytest -v
```

All tests run in-process via `fastapi.testclient.TestClient`; no server needs to
be started manually.

## Environment variables

| Variable      | Default   | Description                                   |
| ------------- | --------- | --------------------------------------------- |
| `APP_VERSION` | `1.0.0`   | Version reported by `/version` and at startup. |
| `LOG_LEVEL`   | `INFO`    | Logging level: `DEBUG`, `INFO`, `WARNING`, …  |

Copy `.env.example` to `.env` to override the defaults. Never commit a real `.env`.

## Logs

The service logs its startup, every request (method, path, status, latency) and
each ticket state change. By default it writes to stdout. To capture logs to a
file:

```bash
python -m uvicorn app_final:app > server.log 2>&1
tail -f server.log
```

## Diagnostics / how to check the app

1. **Is it up?** `curl http://127.0.0.1:8000/health` should return `{"status":"ok"}`
   with HTTP `200`. Anything else means the server failed to start.
2. **Is the right version running?** `curl http://127.0.0.1:8000/version` — the
   `version` field should match your `APP_VERSION`.
3. **Can it do real work?** Create and fetch a ticket:
   ```bash
   curl -X POST http://127.0.0.1:8000/tickets \
        -H 'Content-Type: application/json' \
        -d '{"name":"Alice","email":"alice@example.com","message":"Cannot log in"}'
   ```
   Expect a `201` response with an `id`. Then `GET /tickets/<id>` should return it.
4. **Where to look when something fails**
   - **Startup crash** → the log shows the traceback; most often a missing
     dependency (`pip install -r requirements.txt`) or a Python < 3.9 issue.
   - **`422` on a route** → the request body or the `status` query value is invalid;
     the error `detail` names the accepted values.
   - **`404` on `GET /tickets/<id>`** → no ticket with that id exists (check `GET /tickets`).
   - **Empty `server.log`** → the process did not reach the logging setup; run
     `python -m uvicorn app_final:app` in the foreground to see the error.
5. **CI** → GitHub Actions runs `pytest -v` on every push and pull request and
   uploads the app files as an artifact when the run is green
   (see `.github/workflows/ci.yml`).
