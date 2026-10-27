import pytest
from fastapi.testclient import TestClient

from app_final import app, tickets

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_tickets():
    tickets.clear()
    import app_final

    app_final._next_id = 1
    yield
    tickets.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_matches_env():
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "support-tickets"
    assert body["version"] == app.version


def test_create_and_get_ticket():
    created = client.post(
        "/tickets",
        json={"name": "Alice", "email": "alice@example.com", "message": "Cannot log in"},
    )
    assert created.status_code == 201
    ticket_id = created.json()["id"]
    assert created.json()["status"] == "open"

    fetched = client.get(f"/tickets/{ticket_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == ticket_id
    assert fetched.json()["email"] == "alice@example.com"


def test_get_ticket_not_found():
    response = client.get("/tickets/9999")
    assert response.status_code == 404


def test_list_filter_by_status():
    client.post("/tickets", json={"name": "A", "email": "a@x.com", "message": "m"})
    ticket2 = client.post(
        "/tickets", json={"name": "B", "email": "b@x.com", "message": "m"}
    ).json()

    all_tickets = client.get("/tickets").json()
    assert len(all_tickets) == 2

    client.post(f"/tickets/{ticket2['id']}/reply", json={"message": "ok", "status": "closed"})

    open_only = client.get("/tickets", params={"status": "open"}).json()
    assert len(open_only) == 1
    assert open_only[0]["id"] != ticket2["id"]


def test_reply_updates_status():
    created = client.post(
        "/tickets", json={"name": "C", "email": "c@x.com", "message": "m"}
    ).json()
    response = client.post(
        f"/tickets/{created['id']}/reply", json={"message": "on it", "status": "in_progress"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert len(response.json()["replies"]) == 1


def test_stats_counts_by_status():
    created = client.post(
        "/tickets", json={"name": "D", "email": "d@x.com", "message": "m"}
    ).json()
    client.post(f"/tickets/{created['id']}/reply", json={"message": "ok", "status": "closed"})

    response = client.get("/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["by_status"]["closed"] == 1
