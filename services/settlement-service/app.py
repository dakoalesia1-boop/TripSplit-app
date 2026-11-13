import os
from flask import Flask, jsonify
from migration_runner import apply_migrations

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify(status="ok", service="settlement-service")

if __name__ == "__main__":
    apply_migrations()
    port = int(os.getenv("PORT", 8001))
    app.run(host="0.0.0.0", port=port)