from flask import Flask, request, jsonify
import pymysql
import os
import uuid
import hmac
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

ADMIN_PASSWORD = os.environ.get("FOODSHARE_ADMIN_PASSWORD")


def get_db():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        port=int(os.environ.get("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )


def now_utc():
    return datetime.now(timezone.utc)


def db_date(value):
    if not value:
        return None
    return value.replace(tzinfo=None)


def format_donation(donation):
    for field in ["created_at", "collected_at", "delete_after"]:
        value = donation.get(field)
        if value:
             donation[field] = value.isoformat()
    return donation


def admin_required():
    if not ADMIN_PASSWORD:
        return jsonify({"error": "Admin password is not configured"}), 503

    supplied = request.headers.get("X-Admin-Password", "")

    if not hmac.compare_digest(supplied, ADMIN_PASSWORD):
        return jsonify({"error": "Unauthorized"}), 401

    return None


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "FoodShare Backend is Running!",
        "status": "success"
    })
@app.route("/api/donate", methods=["POST"])
@app.route("/donate", methods=["POST"])
def donate():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid donation data"}), 400

    required_fields = ["name", "food", "quantity", "location", "contact"]

    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing {field}"}), 400

    donation = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "food": data["food"],
        "quantity": str(data["quantity"]),
        "location": data["location"],
        "contact": data["contact"],
        "status": "available",
        "created_at": now_utc(),
        "collected_at": None,
        "delete_after": None
    }

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO donations
                (id, name, food, quantity, location, contact,
                 status, created_at, collected_at, delete_after)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                donation["id"],
                donation["name"],
                donation["food"],
                donation["quantity"],
                donation["location"],
                donation["contact"],
                donation["status"],
                db_date(donation["created_at"]),
                None,
                None
            ))

        connection.commit()

    finally:
        connection.close()

    return jsonify({
        "message": "Donation submitted successfully!",
        "donation": format_donation(donation)
    }), 201


@app.route("/api/donations", methods=["GET"])
@app.route("/donations", methods=["GET"])
def get_donations():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM donations WHERE status = %s",
                ("available",)
            )
            donations = cursor.fetchall()
    finally:
        connection.close()

    available = []

    for donation in donations:
        donation.pop("contact", None)
        available.append(format_donation(donation))

    return jsonify(available), 200


@app.route("/api/admin/donations", methods=["GET"])
def admin_get_donations():
    auth_error = admin_required()

    if auth_error:
        return auth_error

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM donations")
            donations = cursor.fetchall()
    finally:
        connection.close()

    donations = [format_donation(d) for d in donations]

    return jsonify({
        "total_donations": len(donations),
        "donations": donations
    }), 200


@app.route("/api/admin/donations/<donation_id>/collect", methods=["PATCH"])
def collect_donation(donation_id):
    auth_error = admin_required()

    if auth_error:
        return auth_error

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            connection.begin()

            cursor.execute(
                "SELECT * FROM donations WHERE id = %s FOR UPDATE",
                (donation_id,)
            )

            donation = cursor.fetchone()

            if not donation:
                connection.rollback()
                return jsonify({"error": "Donation not found"}), 404

            if donation["status"] == "collected":
                connection.rollback()
                return jsonify({"error": "Already collected"}), 409

            collected_at = now_utc()
            delete_after = collected_at + timedelta(hours=24)

            cursor.execute("""
                UPDATE donations
                SET status = %s, collected_at = %s, delete_after = %s
                WHERE id = %s
            """, (
                "collected",
                db_date(collected_at),
                db_date(delete_after),
                donation_id
            ))

            connection.commit()

            donation["status"] = "collected"
            donation["collected_at"] = collected_at
            donation["delete_after"] = delete_after

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return jsonify({
        "message": "Donation marked as collected",
        "donation": format_donation(donation)
    }), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "application": "FoodShare Backend"
    }), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
