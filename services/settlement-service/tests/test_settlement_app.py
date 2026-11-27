
import sys
from datetime import datetime
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
sys.path.remove(str(SERVICE_DIR))


@pytest.fixture
def client():
    settlement_app.app.config["TESTING"] = True
    with settlement_app.app.test_client() as client:
        yield client


@pytest.fixture
def health_database(monkeypatch):
    from unittest.mock import MagicMock

    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    cursor.fetchone.return_value = (1,)

    monkeypatch.setenv("DATABASE_URL", "mock-database")
    monkeypatch.setenv("APP_VERSION", "test-version")
    monkeypatch.setattr(
        settlement_app.pyodbc, "connect", lambda *args, **kwargs: conn
    )

    return conn, cursor


def test_health_returns_ok(client, health_database):
    conn, cursor = health_database

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["service"] == "settlement-service"
    assert response.json["db"] == "ok"
    assert response.json["version"] == "test-version"

    assert cursor.execute.call_count == 2
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()
    cursor.close.assert_called_once()
    conn.close.assert_called_once()


def test_health_returns_503_when_connection_fails(client, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mock-database")
    monkeypatch.setenv("APP_VERSION", "test-version")

    def fail_connection(*args, **kwargs):
        raise settlement_app.pyodbc.Error("Database unavailable")

    monkeypatch.setattr(
        settlement_app.pyodbc, "connect", fail_connection
    )

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json["status"] == "error"
    assert response.json["db"] == "unavailable"
    assert response.json["version"] == "test-version"


def test_health_returns_503_when_write_fails(client, health_database):
    conn, cursor = health_database

    cursor.execute.side_effect = [
        None,
        settlement_app.pyodbc.Error("Write denied")
    ]

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json["db"] == "unavailable"
    conn.commit.assert_not_called()
    cursor.close.assert_called_once()
    conn.close.assert_called_once()


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

def test_expense_and_settlement_services_integrate(
    client, monkeypatch
):
    # Import the Expense Service test app
    expense_test_dir = (
        Path(__file__).resolve().parents[2]
        / "expense-service"
        / "tests"
    )

    import importlib.util

    expense_test_file = expense_test_dir / "test_app.py"

    spec = importlib.util.spec_from_file_location(
        "expense_integration_test_app",
        expense_test_file
    )
    expense_test_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(expense_test_module)

    expense_app = expense_test_module.expense_app

    # Mock Expense Service database
    expense_conn = MagicMock()
    expense_cursor = MagicMock()
    expense_conn.cursor.return_value = expense_cursor

    group = (1, "Integration Test Trip")
    expense = (1, "Dinner", 60, "Food", 10, "Alex", datetime(2026, 11, 26, 19, 35, 29))

    expense_cursor.fetchone.side_effect = [
        group,
        None
    ]

    expense_cursor.fetchall.side_effect = [
        [expense],
        [(10,), (11,)]
    ]

    monkeypatch.setattr(
        expense_app,
        "get_connection",
        lambda: expense_conn
    )

    mock_settlement_database(monkeypatch)

    expense_client = expense_app.app.test_client()

    class FlaskResponseAdapter:
        def __init__(self, response):
            self.response = response

        def raise_for_status(self):
            if self.response.status_code >= 400:
                error = requests.HTTPError()
                error.response = type(
                    "Response",
                    (),
                    {"status_code": self.response.status_code}
                )()
                raise error

        def json(self):
            return self.response.get_json()

    def call_expense_service(url, **kwargs):
        response = expense_client.get(
            "/api/groups/1/snapshot"
        )
        return FlaskResponseAdapter(response)

    monkeypatch.setattr(
        settlement_app.requests,
        "get",
        call_expense_service
    )

    response = client.get("/api/groups/1/balances")

    assert response.status_code == 200
    assert response.json["group_id"] == 1

    balances = {
        item["participant_id"]: item["balance"]
        for item in response.json["balances"]
    }

    assert balances == {
        10: 30.0,
        11: -30.0
    }

def test_cors_allows_configured_origin(client, monkeypatch, health_database):
    monkeypatch.setattr(
        settlement_app,
        "CORS_ORIGINS",
        {"https://example.com"},
    )

    mock_settlement_database(monkeypatch)
    response = client.get(
        "/health",
        headers={"Origin": "https://example.com"},
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "https://example.com"
    assert response.headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"
