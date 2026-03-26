from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, render_template_string, request, session, url_for

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from src.dashboard.auth import (
        DEFAULT_AUTH_DB_PATH,
        create_user,
        ensure_auth_db,
        get_user_by_username,
        verify_password,
    )
else:
    from src.dashboard.auth import (
        DEFAULT_AUTH_DB_PATH,
        create_user,
        ensure_auth_db,
        get_user_by_username,
        verify_password,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "clean" / "atm_logs.db"
VALID_ROLES = ("admin", "manager", "ops")
ROLE_LABELS = {
    "admin": "Admin",
    "manager": "Manager",
    "ops": "Ops",
}


def get_dashboard_endpoint(role: str) -> str:
    return {
        "admin": "admin_dashboard",
        "manager": "manager_dashboard",
        "ops": "ops_dashboard",
    }[role]


def render_dashboard_view(role: str):
    dashboard_html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
    dashboard_html = dashboard_html.replace('href="styles.css"', 'href="/styles.css"', 1)
    dashboard_html = dashboard_html.replace('<script src="app.js"></script>', '<script src="/app.js"></script>', 1)
    dashboard_html = dashboard_html.replace(
        "<body>",
        f'<body data-dashboard-role="{role}" data-dashboard-role-label="{ROLE_LABELS[role]}">',
        1,
    )
    dashboard_html = dashboard_html.replace(
        '<script src="/app.js"></script>',
        f'<script>window.__dashboardRole = "{role}"; window.__dashboardRoleLabel = "{ROLE_LABELS[role]}";</script>\n    <script src="/app.js"></script>',
        1,
    )
    return render_template_string(dashboard_html)


def create_app(db_path: Path | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(DASHBOARD_DIR),
        static_url_path="",
        template_folder=str(DASHBOARD_DIR / "templates"),
    )
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    app.config["DB_PATH"] = str(db_path or DEFAULT_DB_PATH)
    app.config["AUTH_DB_PATH"] = str(DEFAULT_AUTH_DB_PATH)
    ensure_auth_db(Path(app.config["AUTH_DB_PATH"]))

    @app.get("/")
    def index():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        selected_username = ""

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            selected_username = username

            if not username or not password:
                error = "Enter both username and password."
            else:
                user = get_user_by_username(username, Path(app.config["AUTH_DB_PATH"]))
                if not user or not verify_password(password, user["password_hash"]):
                    error = "Invalid username or password."
                else:
                    session["user_id"] = user["id"]
                    session["user_name"] = user["username"]
                    session["role"] = user["role"]
                    return redirect(url_for(get_dashboard_endpoint(user["role"])))

        return render_template(
            "login.html",
            error=error,
            selected_username=selected_username,
        )

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        error = None
        selected_username = ""
        selected_role = ""

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            role = request.form.get("role", "").strip().lower()

            selected_username = username
            selected_role = role

            if not username:
                error = "Enter a username."
            elif not password:
                error = "Enter a password."
            elif password != confirm_password:
                error = "Passwords do not match."
            elif role not in VALID_ROLES:
                error = "Select a valid role to continue."
            elif get_user_by_username(username, Path(app.config["AUTH_DB_PATH"])):
                error = "That username is already taken."
            elif not create_user(username, password, role, Path(app.config["AUTH_DB_PATH"])):
                error = "Unable to create account."
            else:
                return redirect(url_for("login", signup="success", username=username))

        return render_template(
            "signup.html",
            error=error,
            selected_username=selected_username,
            selected_role=selected_role,
        )

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    def serve_dashboard_for_role(expected_role: str):
        role = session.get("role")
        if role not in VALID_ROLES:
            return redirect(url_for("login"))
        if role != expected_role:
            return redirect(url_for(get_dashboard_endpoint(role)))
        return render_dashboard_view(expected_role)

    @app.get("/dashboard/admin")
    def admin_dashboard():
        return serve_dashboard_for_role("admin")

    @app.get("/dashboard/manager")
    def manager_dashboard():
        return serve_dashboard_for_role("manager")

    @app.get("/dashboard/ops")
    def ops_dashboard():
        return serve_dashboard_for_role("ops")

    @app.get("/health")
    def health():
        db_file = Path(app.config["DB_PATH"])
        auth_db_file = Path(app.config["AUTH_DB_PATH"])
        return jsonify(
            {
                "status": "ok",
                "role": session.get("role"),
                "database_present": db_file.exists(),
                "database_path": str(db_file.relative_to(PROJECT_ROOT)),
                "auth_database_present": auth_db_file.exists(),
                "auth_database_path": str(auth_db_file.relative_to(PROJECT_ROOT)),
            }
        )

    @app.get("/api/status")
    def api_status():
        db_file = Path(app.config["DB_PATH"])
        auth_db_file = Path(app.config["AUTH_DB_PATH"])
        response = {
            "database_present": db_file.exists(),
            "database_path": str(db_file.relative_to(PROJECT_ROOT)),
            "auth_database_present": auth_db_file.exists(),
            "auth_database_path": str(auth_db_file.relative_to(PROJECT_ROOT)),
            "role": session.get("role"),
            "tables": [],
            "auth_tables": [],
        }

        if not db_file.exists():
            if auth_db_file.exists():
                with sqlite3.connect(auth_db_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT name
                        FROM sqlite_master
                        WHERE type = 'table'
                        ORDER BY name
                        """
                    )
                    response["auth_tables"] = [row[0] for row in cursor.fetchall()]
            return jsonify(response)

        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            )
            response["tables"] = [row[0] for row in cursor.fetchall()]

        if auth_db_file.exists():
            with sqlite3.connect(auth_db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    ORDER BY name
                    """
                )
                response["auth_tables"] = [row[0] for row in cursor.fetchall()]

        return jsonify(response)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
