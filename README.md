# Support Tickets Service

FastAPI service for creating and tracking support requests. Tickets move through
statuses `open`, `in_progress`, `closed`. Interactive docs at `/docs`.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```
python -m uvicorn app_final:app
```

Opens at http://127.0.0.1:8000. For dev add `--reload`.

## Tests

```
python -m pytest -v
```

## Environment variables

`APP_VERSION` (default `1.0.0`) sets the version reported by `/version`.
`LOG_LEVEL` (default `INFO`) controls logging verbosity: `DEBUG`, `INFO`, `WARNING`.

Never commit `.env`.

## Endpoints

POST `/tickets` — create a ticket (201).
GET `/tickets/{id}` — get one ticket (404 if missing).
GET `/tickets?status=open` — list tickets, optional status filter.
POST `/tickets/{id}/reply` — add reply and update status.
GET `/stats` — ticket counts per status.
GET `/health` — liveness probe.
GET `/version` — app version.

## Logs

Logs go to stdout: startup, every request, ticket state changes. Capture to file:

```
python -m uvicorn app_final:app > server.log 2>&1
```

## Diagnostics

`curl http://127.0.0.1:8000/health` returns `{"status":"ok"}`.
`curl http://127.0.0.1:8000/version` returns the version from `APP_VERSION`.
If the app doesn't start, run without `> server.log` to see the traceback.
422 means invalid input (check the `detail` field). 404 means ticket not found.
CI runs `pytest -v` on every push and uploads an artifact on success.
