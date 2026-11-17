
import os
import math
import pyodbc
from flask import Flask, jsonify, request
from migration_runner import apply_migrations, get_connection

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify(status="ok", service="expense-service")

@app.route("/api/groups", methods=["GET"])
def get_groups():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name
            FROM groups
            ORDER BY id
        """)

        rows = cursor.fetchall()

        groups = [
            {"id": row[0], "name": row[1]}
            for row in rows
        ]

        return jsonify(groups), 200

    except (pyodbc.Error, RuntimeError) as e:
        print(f"Error retrieving groups: {e}")
        return jsonify(error="Could not retrieve groups"), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/groups", methods=["POST"])
def create_group():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="A JSON object is required"), 400

    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify(error="Group name is required"), 400

    name = name.strip()

    if len(name) > 255:
        return jsonify(error="Group name cannot exceed 255 characters"), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO groups (name)
            OUTPUT INSERTED.id
            VALUES (?)
        """, name)

        new_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            "id": new_id,
            "name": name
        }), 201

    except (pyodbc.Error, RuntimeError) as e:
        if conn:
            conn.rollback()

        print(f"Error creating group: {e}")
        return jsonify(error="Could not create group"), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/groups/<int:group_id>/participants", methods=["GET"])
def get_participants(group_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            group_id
        )

        if cursor.fetchone() is None:
            return jsonify(error="Group not found"), 404

        cursor.execute("""
            SELECT id, name, group_id
            FROM participants
            WHERE group_id = ?
            ORDER BY id
        """, group_id)

        rows = cursor.fetchall()

        participants = [
            {
                "id": row[0],
                "name": row[1],
                "group_id": row[2]
            }
            for row in rows
        ]

        return jsonify(participants), 200

    except (pyodbc.Error, RuntimeError) as e:
        print(f"Error retrieving participants: {e}")
        return jsonify(error="Could not retrieve participants"), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/groups/<int:group_id>/participants", methods=["POST"])
def create_participant(group_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="A JSON object is required"), 400

    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify(error="Participant name is required"), 400

    name = name.strip()

    if len(name) > 255:
        return jsonify(error="Participant name cannot exceed 255 characters"), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            group_id
        )

        if cursor.fetchone() is None:
            return jsonify(error="Group not found"), 404

        cursor.execute("""
            INSERT INTO participants (name, group_id)
            OUTPUT INSERTED.id
            VALUES (?, ?)
        """, name, group_id)

        new_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            "id": new_id,
            "name": name,
            "group_id": group_id
        }), 201

    except (pyodbc.Error, RuntimeError) as e:
        if conn:
            conn.rollback()

        print(f"Error creating participant: {e}")
        return jsonify(error="Could not create participant"), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/groups/<int:group_id>/expenses", methods=["POST"])
def create_expense(group_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="A JSON object is required"), 400

    description = data.get("description")
    amount = data.get("amount")
    paid_by_id = data.get("paid_by_id")
    category = data.get("category", "General")
    shared_participants = data.get("shared_participants")

    if not isinstance(description, str) or not description.strip():
        return jsonify(error="Expense description is required"), 400

    description = description.strip()

    if len(description) > 200:
        return jsonify(error="Description cannot exceed 200 characters"), 400

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify(error="A valid amount is required"), 400

    if amount <= 0 or not math.isfinite(amount):
        return jsonify(error="Amount must be greater than zero"), 400

    try:
        paid_by_id = int(paid_by_id)
    except (TypeError, ValueError):
        return jsonify(error="A valid paid_by_id is required"), 400

    if not isinstance(category, str) or not category.strip():
        return jsonify(error="Category must be a non-empty string"), 400

    category = category.strip()

    if len(category) > 50:
        return jsonify(error="Category cannot exceed 50 characters"), 400

    if not isinstance(shared_participants, list) or not shared_participants:
        return jsonify(error="At least one shared participant is required"), 400

    try:
        shared_participants = [int(pid) for pid in shared_participants]
    except (TypeError, ValueError):
        return jsonify(error="Participant IDs must be integers"), 400

    if len(shared_participants) != len(set(shared_participants)):
        return jsonify(error="Duplicate shared participants are not allowed"), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM groups WHERE id = ?",
            group_id
        )

        if cursor.fetchone() is None:
            return jsonify(error="Group not found"), 404

        cursor.execute(
            "SELECT id FROM participants WHERE id = ? AND group_id = ?",
            paid_by_id, group_id
        )

        if cursor.fetchone() is None:
            return jsonify(error="Paying participant not found in this group"), 400

        placeholders = ",".join("?" for _ in shared_participants)

        cursor.execute(
            f"""
            SELECT id FROM participants
            WHERE group_id = ? AND id IN ({placeholders})
            """,
            group_id, *shared_participants
        )

        valid_ids = {row[0] for row in cursor.fetchall()}

        if valid_ids != set(shared_participants):
            return jsonify(error="One or more shared participants do not belong to this group"), 400

        cursor.execute("""
            INSERT INTO expenses (description, amount, category, paid_by_id, group_id)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?)
        """, description, amount, category, paid_by_id, group_id)

        expense_id = cursor.fetchone()[0]

        for participant_id in shared_participants:
            cursor.execute("""
                INSERT INTO expense_shares (expense_id, participant_id)
                VALUES (?, ?)
            """, expense_id, participant_id)

        conn.commit()

        return jsonify({
            "id": expense_id,
            "description": description,
            "amount": amount,
            "category": category,
            "paid_by_id": paid_by_id,
            "group_id": group_id,
            "shared_participants": shared_participants
        }), 201

    except (pyodbc.Error, RuntimeError) as e:
        if conn:
            conn.rollback()

        print(f"Error creating expense: {e}")
        return jsonify(error="Could not create expense"), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/groups/<int:group_id>", methods=["GET"])
def get_group(group_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name FROM groups WHERE id = ?",
            group_id
        )

        group = cursor.fetchone()

        if group is None:
            return jsonify(error="Group not found"), 404

        cursor.execute("""
            SELECT id, name
            FROM participants
            WHERE group_id = ?
            ORDER BY id
        """, group_id)

        participants = [
            {"id": row[0], "name": row[1]}
            for row in cursor.fetchall()
        ]

        return jsonify({
            "id": group[0],
            "name": group[1],
            "participants": participants
        }), 200

    except (pyodbc.Error, RuntimeError) as e:
        print(f"Error retrieving group: {e}")
        return jsonify(error="Could not retrieve group"), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/groups/<int:group_id>/snapshot", methods=["GET"])
def get_group_snapshot(group_id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name FROM groups WHERE id = ?",
            group_id
        )

        group = cursor.fetchone()

        if group is None:
            return jsonify(error="Group not found"), 404

        cursor.execute("""
            SELECT
                e.id,
                e.description,
                e.amount,
                e.category,
                e.paid_by_id,
                p.name
            FROM expenses e
            JOIN participants p ON e.paid_by_id = p.id
            WHERE e.group_id = ?
            ORDER BY e.id
        """, group_id)

        expense_rows = cursor.fetchall()

        expenses = []

        for row in expense_rows:
            expense_id = row[0]

            cursor.execute("""
                SELECT participant_id
                FROM expense_shares
                WHERE expense_id = ?
                ORDER BY participant_id
            """, expense_id)

            shared_participants = [
                share[0] for share in cursor.fetchall()
            ]

            expenses.append({
                "id": row[0],
                "description": row[1],
                "amount": float(row[2]),
                "category": row[3],
                "paid_by_id": row[4],
                "paid_by_name": row[5],
                "shared_participants": shared_participants
            })

        return jsonify({
            "group_id": group[0],
            "group_name": group[1],
            "expenses": expenses
        }), 200

    except (pyodbc.Error, RuntimeError) as e:
        print(f"Error retrieving group snapshot: {e}")
        return jsonify(error="Could not retrieve group snapshot"), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    apply_migrations()
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
