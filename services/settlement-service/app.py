import os
import pyodbc
import requests
import logging
import time

from flask import Flask, jsonify, request, g
from migration_runner import apply_migrations, get_connection


app = Flask(__name__)

CORS_ORIGINS = {
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
}

@app.before_request
def start_request_timer():
    g.request_started_at = time.perf_counter()


@app.after_request
def log_request(response):
    duration = time.perf_counter() - g.request_started_at

    app.logger.info(
        "%s %s - %s - %.4f seconds",
        request.method,
        request.path,
        response.status_code,
        duration
    )

    origin = request.headers.get("Origin")

    if origin and origin in CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Max-Age"] = "600"
        response.headers.add("Vary", "Origin")

    return response

EXPENSE_SERVICE_URL = os.getenv(
    "EXPENSE_SERVICE_URL",
    "http://expense-service:8000"
)


@app.route("/api/groups/<int:group_id>/balances", methods=["GET"])
def get_balances(group_id):
    try:
        response = requests.get(
            f"{EXPENSE_SERVICE_URL}/api/groups/{group_id}/snapshot",
            timeout=5
        )
        response.raise_for_status()
        snapshot = response.json()

    except requests.HTTPError as error:
        if error.response.status_code == 404:
            return jsonify(error="Group not found"), 404

        return jsonify(error="Could not retrieve group expenses"), 502

    except requests.RequestException:
        return jsonify(error="Could not retrieve group expenses"), 502

    if not snapshot.get("group_id"):
        return jsonify(error="Group not found"), 404

    balances = {}

    for expense in snapshot.get("expenses", []):
        amount = float(expense["amount"])
        payer_id = expense["paid_by_id"]
        shared_participants = expense.get("shared_participants", [])

        if not shared_participants:
            continue

        split_amount = amount / len(shared_participants)

        balances[payer_id] = balances.get(payer_id, 0) + amount

        for participant_id in shared_participants:
            balances[participant_id] = (
                balances.get(participant_id, 0) - split_amount
            )

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT payer_id, receiver_id, amount
                FROM settlements
                WHERE group_id = ?
                """,
                group_id
            )

            for payer_id, receiver_id, amount in cursor.fetchall():
                balances[payer_id] = (
                    balances.get(payer_id, 0) + float(amount)
                )
                balances[receiver_id] = (
                    balances.get(receiver_id, 0) - float(amount)
                )

    except pyodbc.Error:
        return jsonify(error="Could not retrieve settlements"), 500

    result = [
        {
            "participant_id": participant_id,
            "balance": round(balance, 2)
        }
        for participant_id, balance in sorted(balances.items())
    ]

    return jsonify(group_id=group_id, balances=result)

@app.route("/health")
def health():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")

        return jsonify(
            status="ok",
            service="settlement-service",
            db="ok"
        ), 200

    except Exception:
        app.logger.exception("Settlement Service database health check failed")

        return jsonify(
            status="error",
            service="settlement-service",
            db="unavailable"
        ), 503

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/groups/<int:group_id>/settlements", methods=["POST"])
def create_settlement(group_id):
    data = request.get_json(silent=True) or {}

    payer_id = data.get("payer_id")
    receiver_id = data.get("receiver_id")
    amount = data.get("amount")

    if payer_id is None or receiver_id is None or amount is None:
        return jsonify(error="payer_id, receiver_id and amount are required"), 400

    try:
        payer_id = int(payer_id)
        receiver_id = int(receiver_id)
        amount = float(amount)

        if payer_id <= 0 or receiver_id <= 0:
            raise ValueError

        if payer_id == receiver_id:
            return jsonify(error="Payer and receiver must be different"), 400

        if not amount > 0 or not __import__("math").isfinite(amount):
            raise ValueError

    except (ValueError, TypeError):
        return jsonify(error="Invalid settlement details"), 400

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO settlements (payer_id, receiver_id, amount, group_id)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?)
                """,
                payer_id,
                receiver_id,
                amount,
                group_id
            )

            settlement_id = cursor.fetchone()[0]
            conn.commit()

    except pyodbc.Error:
        return jsonify(error="Could not save settlement"), 500

    return jsonify(
        id=settlement_id,
        group_id=group_id,
        payer_id=payer_id,
        receiver_id=receiver_id,
        amount=round(amount, 2)
    ), 201

if __name__ == "__main__":
    apply_migrations()
    port = int(os.getenv("PORT", 8001))
    app.run(host="0.0.0.0", port=port)