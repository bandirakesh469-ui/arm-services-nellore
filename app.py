"""
ARM SERVICES NELLORE — Website + Admin Portal
------------------------------------------------
A single Flask application that serves:
  1. The public marketing site (services, pricing, lead-capture form)
  2. An admin portal (login, dashboard with order stats + filters,
     order status management, and a "change password" flow)

Run locally:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000

Default admin login (change it immediately from the admin portal):
    username: Cuziamchaithu_1
    password: r%t@D213kK%Z

Deploy on Render:
    Build Command : pip install -r requirements.txt
    Start Command : gunicorn app:app
    Env Variable  : ARM_SECRET_KEY = (any strong random string)
"""

import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "arm_services.db")

# Seed admin credentials (used only the first time the DB is created).
# Change these from the admin portal's "Change Password" page after first login.
SEED_ADMIN_USERNAME = "Cuziamchaithu_1"
SEED_ADMIN_PASSWORD = "r%t@D213kK%Z"

SERVICE_CHOICES = [
    ("website", "Website Development"),
    ("social", "Social Media Promotion"),
    ("photos", "Business Photos / Content"),
    ("gbp", "Google Business Profile Setup"),
    ("whatsapp", "WhatsApp Business Integration"),
    ("ads", "Online Advertising"),
]

STATUS_CHOICES = ["pending", "accepted", "rejected"]

app = Flask(__name__)
app.secret_key = os.environ.get("ARM_SECRET_KEY", "change-this-secret-key-in-production")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    first_time = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_name TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            services TEXT,
            message TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    if first_time:
        conn.execute(
            "INSERT INTO admin (username, password_hash) VALUES (?, ?)",
            (SEED_ADMIN_USERNAME, generate_password_hash(SEED_ADMIN_PASSWORD)),
        )
        conn.commit()
    conn.close()


# Initialize DB on startup (works both locally and on Render/Gunicorn)
init_db()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Public site
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", services=SERVICE_CHOICES)


@app.route("/submit-order", methods=["POST"])
def submit_order():
    hotel_name = request.form.get("hotel_name", "").strip()
    contact_name = request.form.get("contact_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    services = request.form.getlist("services")
    message = request.form.get("message", "").strip()

    if not hotel_name or not contact_name or not phone:
        flash("Please fill in your name, business name and phone number.", "error")
        return redirect(url_for("index") + "#get-started")

    db = get_db()
    db.execute(
        """INSERT INTO orders (hotel_name, contact_name, phone, email, services, message, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
        (hotel_name, contact_name, phone, email, ", ".join(services), message,
         datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    db.commit()
    flash("Thanks! Your request has been received — our team will contact you shortly.", "success")
    return redirect(url_for("index") + "#get-started")


# ---------------------------------------------------------------------------
# Admin: auth
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        admin = db.execute("SELECT * FROM admin WHERE username = ?", (username,)).fetchone()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin/change-password", methods=["GET", "POST"])
@login_required
def admin_change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        db = get_db()
        admin = db.execute("SELECT * FROM admin WHERE id = ?", (session["admin_id"],)).fetchone()

        if not check_password_hash(admin["password_hash"], old_password):
            flash("Your current password is incorrect.", "error")
        elif len(new_password) < 8:
            flash("New password must be at least 8 characters long.", "error")
        elif new_password != confirm_password:
            flash("New password and confirmation do not match.", "error")
        else:
            db.execute(
                "UPDATE admin SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_password), admin["id"]),
            )
            db.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("admin_dashboard"))

    return render_template("admin_change_password.html")


# ---------------------------------------------------------------------------
# Admin: dashboard
# ---------------------------------------------------------------------------

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    db = get_db()
    status_filter = request.args.get("status", "all")

    counts = {
        "all": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "pending": db.execute("SELECT COUNT(*) FROM orders WHERE status='pending'").fetchone()[0],
        "accepted": db.execute("SELECT COUNT(*) FROM orders WHERE status='accepted'").fetchone()[0],
        "rejected": db.execute("SELECT COUNT(*) FROM orders WHERE status='rejected'").fetchone()[0],
    }

    if status_filter in STATUS_CHOICES:
        orders = db.execute(
            "SELECT * FROM orders WHERE status = ? ORDER BY id DESC", (status_filter,)
        ).fetchall()
    else:
        status_filter = "all"
        orders = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()

    return render_template(
        "admin_dashboard.html",
        orders=orders,
        counts=counts,
        active_status=status_filter,
        admin_username=session.get("admin_username"),
    )


@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    new_status = request.form.get("status")
    if new_status not in STATUS_CHOICES:
        flash("Invalid status.", "error")
    else:
        db = get_db()
        db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        db.commit()
        flash(f"Order #{order_id} marked as {new_status}.", "success")

    return redirect(url_for("admin_dashboard", status=request.args.get("status", "all")))


if __name__ == "__main__":
    # Local development only
    app.run(debug=True)
