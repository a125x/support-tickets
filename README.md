## Support tickets app

Fastapi app for support tickets management.

## Endpoints

- POST /tickets — create a new ticket (returns 201 with an id).
- GET /tickets/{ticket_id} — fetch one ticket by id (404 if missing).
- GET /tickets?status=open — list tickets, optionally filtered by status.
- POST /tickets/{ticket_id}/reply — add a reply and update the status.
- GET /stats — count of tickets per status.
- / — service info, /health — liveness probe, /version — version from env.

## Requirements

python 3.9, uvicorn, pydantic, fastapi, python-dotenv

## Setup

```python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
```

and tests:
```python
python -m pytest -v
```

## Run
```python
#for regular usage
python -m uvicorn app_final:app

for dev
source .venv/bin/activate
python -m uvicorn app_final:app --reload
```

opens at http://127.0.0.1:8000

usage examples:
```python
curl http://127.0.0.1:8000/health     # -> {"status":"ok"}
curl http://127.0.0.1:8000/version    # -> {"app":"support-tickets","version":"1.0.0"}
```
## Logs
```python
python -m uvicorn app_final:app > server.log 2>&1
tail -f server.log
```
