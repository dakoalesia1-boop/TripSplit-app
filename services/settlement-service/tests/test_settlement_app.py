
import sys
from pathlib import Path

import pytest
import requests

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

sys.modules.pop("migration_runner", None)
import importlib.util

spec = importlib.util.spec_from_file_location(
    "settlement_service_app", SERVICE_DIR / "app.py"
)
settlement_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settlement_app)


@pytest.fixture
def client():
    settlement_app.app.config["TESTING"] = True
    with settlement_app.app.test_client() as client:
        yield client


def test_health_returns_ok(client, monkeypatch):
    mock_settlement_database(monkeypatch)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["service"] == "settlement-service"


@pytest.mark.parametrize("payload", [
    {},
    {"payer_id": 1, "receiver_id": 2},
    {"payer_id": 1, "amount": 20},
    {"receiver_id": 2, "amount": 20},
])
def test_settlement_rejects_missing_fields(client, payload):
    response = client.post("/api/groups/1/settlements", json=payload)

    assert response.status_code == 400


@pytest.mark.parametrize("payload", [
    {"payer_id": 1, "receiver_id": 2, "amount": -10},
    {"payer_id": 1, "receiver_id": 2, "amount": 0},
    {"payer_id": 1, "receiver_id": 2, "amount": "invalid"},
    {"payer_id": 1, "receiver_id": 1, "amount": 10},
    {"payer_id": 0, "receiver_id": 2, "amount": 10},
    {"payer_id": 1, "receiver_id": -2, "amount": 10},
])
def test_settlement_rejects_invalid_details(client, payload):
    response = client.post("/api/groups/1/settlements", json=payload)

    assert response.status_code == 400


def test_balances_returns_404_when_expense_service_reports_missing_group(
    client, monkeypatch
):
    class FakeResponse:
        def raise_for_status(self):
            error = requests.HTTPError()
            error.response = type("Response", (), {"status_code": 404})()
            raise error

    monkeypatch.setattr(
        settlement_app.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    response = client.get("/api/groups/999/balances")

    assert response.status_code == 404
    assert response.json["error"] == "Group not found"


def test_balances_returns_502_when_expense_service_is_unavailable(
    client, monkeypatch
):
    def unavailable(*args, **kwargs):
        raise requests.ConnectionError("Service unavailable")

    monkeypatch.setattr(settlement_app.requests, "get", unavailable)

    response = client.get("/api/groups/1/balances")

    assert response.status_code == 502
    assert response.json["error"] == "Could not retrieve group expenses"


from unittest.mock import MagicMock


def mock_settlement_database(monkeypatch, settlements=None, new_id=1):
    conn = MagicMock()
    conn.__enter__.return_value = conn

    cursor = MagicMock()
    cursor.fetchall.return_value = settlements or []
    cursor.fetchone.return_value = (new_id,)
    conn.cursor.return_value = cursor

    monkeypatch.setattr(
        settlement_app, "get_connection", lambda: conn
    )

    return conn, cursor


def test_balances_calculates_and_applies_settlements(client, monkeypatch):
    snapshot = {
        "group_id": 1,
        "expenses": [
            {
                "amount": 40,
                "paid_by_id": 10,
                "shared_participants": [10, 11],
            }
        ],
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return snapshot

    monkeypatch.setattr(
        settlement_app.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    mock_settlement_database(
        monkeypatch,
        settlements=[(11, 10, 20)],
    )

    response = client.get("/api/groups/1/balances")

    assert response.status_code == 200
    balances = {
        item["participant_id"]: item["balance"]
        for item in response.json["balances"]
    }
    assert balances == {10: 0, 11: 0}


def test_balances_without_expenses_returns_empty_list(client, monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"group_id": 1, "expenses": []}

    monkeypatch.setattr(
        settlement_app.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    mock_settlement_database(monkeypatch)

    response = client.get("/api/groups/1/balances")

    assert response.status_code == 200
    assert response.json["balances"] == []


def test_create_settlement_success(client, monkeypatch):
    conn, _ = mock_settlement_database(monkeypatch, new_id=15)

    response = client.post(
        "/api/groups/1/settlements",
        json={
            "payer_id": 11,
            "receiver_id": 10,
            "amount": 20,
        },
    )

    assert response.status_code == 201
    assert response.json["id"] == 15
    assert response.json["group_id"] == 1
    assert response.json["amount"] == 20
    conn.commit.assert_called_once()
