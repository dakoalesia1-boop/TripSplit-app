
import sys
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

import importlib.util

spec = importlib.util.spec_from_file_location(
    "expense_service_app", SERVICE_DIR / "app.py"
)
expense_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(expense_app)
sys.path.remove(str(SERVICE_DIR))


@pytest.fixture
def client():
    expense_app.app.config["TESTING"] = True
    with expense_app.app.test_client() as client:
        yield client


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["service"] == "expense-service"


@pytest.mark.parametrize("payload", [
    None,
    [],
    "not a JSON object",
])
def test_create_group_rejects_invalid_json(client, payload):
    response = client.post("/api/groups", json=payload)

    assert response.status_code == 400


@pytest.mark.parametrize("payload", [
    {},
    {"name": ""},
    {"name": "   "},
    {"name": 123},
])
def test_create_group_rejects_invalid_name(client, payload):
    response = client.post("/api/groups", json=payload)

    assert response.status_code == 400


def test_create_group_rejects_name_over_255_characters(client):
    response = client.post("/api/groups", json={"name": "A" * 256})

    assert response.status_code == 400


@pytest.mark.parametrize("payload", [
    {},
    {"name": ""},
    {"name": "   "},
    {"name": 123},
])
def test_create_participant_rejects_invalid_name(client, payload):
    response = client.post("/api/groups/1/participants", json=payload)

    assert response.status_code == 400


@pytest.mark.parametrize("payload", [
    {},
    {"description": "Dinner"},
    {"description": "Dinner", "amount": -10, "paid_by_id": 1,
     "shared_participants": [1]},
    {"description": "Dinner", "amount": 0, "paid_by_id": 1,
     "shared_participants": [1]},
    {"description": "Dinner", "amount": "invalid", "paid_by_id": 1,
     "shared_participants": [1]},
    {"description": "Dinner", "amount": 10, "paid_by_id": 1,
     "shared_participants": []},
    {"description": "Dinner", "amount": 10, "paid_by_id": 1,
     "shared_participants": [1, 1]},
    {"description": "Dinner", "amount": 10, "paid_by_id": 1,
     "shared_participants": ["invalid"]},
])
def test_create_expense_rejects_invalid_input(client, payload):
    response = client.post("/api/groups/1/expenses", json=payload)

    assert response.status_code == 400


def test_create_expense_rejects_description_over_200_characters(client):
    response = client.post(
        "/api/groups/1/expenses",
        json={
            "description": "A" * 201,
            "amount": 10,
            "paid_by_id": 1,
            "shared_participants": [1],
        },
    )

    assert response.status_code == 400


from unittest.mock import MagicMock


def mock_database(monkeypatch, fetchone=None, fetchall=None):
    conn = MagicMock()
    cursor = MagicMock()

    cursor.fetchone.side_effect = fetchone or []
    cursor.fetchall.side_effect = fetchall or []

    conn.cursor.return_value = cursor
    monkeypatch.setattr(expense_app, "get_connection", lambda: conn)

    return conn, cursor


def test_get_groups_success(client, monkeypatch):
    mock_database(monkeypatch, fetchall=[[(1, "Barcelona Trip")]])

    response = client.get("/api/groups")

    assert response.status_code == 200
    assert response.json == [{"id": 1, "name": "Barcelona Trip"}]


def test_create_group_success(client, monkeypatch):
    conn, _ = mock_database(monkeypatch, fetchone=[(5,)])

    response = client.post("/api/groups", json={"name": "New Trip"})

    assert response.status_code == 201
    assert response.json["id"] == 5
    assert response.json["name"] == "New Trip"
    conn.commit.assert_called_once()


def test_get_participants_success(client, monkeypatch):
    mock_database(
        monkeypatch,
        fetchone=[(1,)],
        fetchall=[[(10, "Alex", 1), (11, "Bob", 1)]],
    )

    response = client.get("/api/groups/1/participants")

    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]["name"] == "Alex"


def test_create_participant_success(client, monkeypatch):
    conn, _ = mock_database(
        monkeypatch,
        fetchone=[(1,), (12,)],
    )

    response = client.post(
        "/api/groups/1/participants",
        json={"name": "Charlie"},
    )

    assert response.status_code == 201
    assert response.json["id"] == 12
    assert response.json["name"] == "Charlie"
    conn.commit.assert_called_once()


def test_get_group_success(client, monkeypatch):
    mock_database(
        monkeypatch,
        fetchone=[(1, "Barcelona Trip")],
        fetchall=[[(10, "Alex"), (11, "Bob")]],
    )

    response = client.get("/api/groups/1")

    assert response.status_code == 200
    assert response.json["name"] == "Barcelona Trip"
    assert len(response.json["participants"]) == 2


def test_create_expense_success(client, monkeypatch):
    conn, _ = mock_database(
        monkeypatch,
        fetchone=[(1,), (10,), (25,)],
        fetchall=[[(10,), (11,)]],
    )

    response = client.post(
        "/api/groups/1/expenses",
        json={
            "description": "Dinner",
            "amount": 40,
            "paid_by_id": 10,
            "category": "Food",
            "shared_participants": [10, 11],
        },
    )

    assert response.status_code == 201
    assert response.json["id"] == 25
    assert response.json["amount"] == 40
    assert response.json["shared_participants"] == [10, 11]
    conn.commit.assert_called_once()


def test_get_group_snapshot_success(client, monkeypatch):
    mock_database(
        monkeypatch,
        fetchone=[(1, "Barcelona Trip")],
        fetchall=[
            [(25, "Dinner", 40, "Food", 10, "Alex")],
            [(10,), (11,)],
        ],
    )

    response = client.get("/api/groups/1/snapshot")

    assert response.status_code == 200
    assert response.json["group_name"] == "Barcelona Trip"
    assert response.json["expenses"][0]["description"] == "Dinner"
    assert response.json["expenses"][0]["shared_participants"] == [10, 11]

def test_cors_allows_configured_origin(client, monkeypatch):
    monkeypatch.setattr(
        expense_app,
        "CORS_ORIGINS",
        {"https://example.com"},
    )

    response = client.get(
        "/health",
        headers={"Origin": "https://example.com"},
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "https://example.com"
    assert response.headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"
