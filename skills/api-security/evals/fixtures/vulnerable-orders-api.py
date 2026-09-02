"""Orders API — internal service, do not expose without review."""
import sqlite3
import traceback

import jwt
import requests
from flask import Flask, g, jsonify, request

app = Flask(__name__)

SECRET_KEY = "super-secret-jwt-key-2019"
ADMIN_API_KEY = "ak_admin_9f8a7b6c5d4e"

DB = "orders.db"


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def current_user():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    claims = jwt.decode(token, options={"verify_signature": False})
    return claims


@app.before_request
def authenticate():
    if request.path == "/health":
        return
    try:
        g.user = current_user()
    except Exception:
        return jsonify({"error": "invalid token"}), 401


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/orders")
def list_orders():
    limit = int(request.args.get("limit", 20))
    rows = db().execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (g.user["sub"], limit),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/orders/<int:order_id>")
def get_order(order_id):
    row = db().execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@app.patch("/users/me")
def update_profile():
    conn = db()
    for field, value in request.get_json().items():
        conn.execute(
            f"UPDATE users SET {field} = ? WHERE id = ?", (value, g.user["sub"])
        )
    conn.commit()
    return get_user(g.user["sub"])


@app.get("/users/<int:user_id>")
def get_user(user_id):
    row = db().execute(
        "SELECT id, email, name, role, password_hash, stripe_customer_id "
        "FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@app.post("/webhooks/test")
def test_webhook():
    url = request.get_json()["url"]
    resp = requests.get(url, timeout=30)
    return jsonify({"status": resp.status_code, "body": resp.text[:2000]})


@app.get("/admin/orders")
def admin_orders():
    if request.args.get("api_key") == ADMIN_API_KEY:
        rows = db().execute("SELECT * FROM orders").fetchall()
        return jsonify([dict(r) for r in rows])
    return jsonify({"error": "forbidden"}), 403


@app.errorhandler(Exception)
def handle_error(exc):
    return jsonify({"error": str(exc), "trace": traceback.format_exc()}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
