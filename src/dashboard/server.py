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

    def _db():
        return Path(app.config["DB_PATH"])

    def _connect():
        return sqlite3.connect(_db())

    def _table_exists(conn, name):
        cur = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        )
        return cur.fetchone() is not None

    @app.get("/api/summary")
    def api_summary():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "reason": "database not found"})

        with _connect() as conn:
            has_atma = _table_exists(conn, "ATMA")
            has_atmh = _table_exists(conn, "ATMH")
            has_kafk = _table_exists(conn, "KAFK")
            has_detections = _table_exists(conn, "analysis_detections")

            observed_atms = 0
            if has_atma:
                row = conn.execute("SELECT COUNT(DISTINCT atm_id) FROM ATMA").fetchone()
                observed_atms = row[0] if row else 0

            app_errors = 0
            if has_atma:
                row = conn.execute(
                    "SELECT COUNT(*) FROM ATMA WHERE event_type IN ('ERROR','TIMEOUT','NETWORK_DISCONNECT')"
                ).fetchone()
                app_errors = row[0] if row else 0

            hardware_alerts = 0
            if has_atmh:
                row = conn.execute(
                    "SELECT COUNT(*) FROM ATMH WHERE severity IN ('CRITICAL','WARNING')"
                ).fetchone()
                hardware_alerts = row[0] if row else 0

            avg_tps = 0.0
            if has_kafk:
                row = conn.execute(
                    "SELECT AVG(CAST(transaction_rate_tps AS REAL)) FROM KAFK"
                ).fetchone()
                avg_tps = round(row[0] or 0, 1)

            failure_windows = 0
            if has_detections:
                row = conn.execute(
                    "SELECT COUNT(*) FROM analysis_detections WHERE severity = 'CRITICAL'"
                ).fetchone()
                failure_windows = row[0] if row else 0

        return jsonify(
            {
                "status": "ok",
                "observed_atms": observed_atms,
                "app_errors": app_errors,
                "hardware_alerts": hardware_alerts,
                "avg_tps": avg_tps,
                "failure_windows": failure_windows,
            }
        )

    @app.get("/api/scale")
    def api_scale():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable"})

        source_names = ("ATMA", "ATMH", "GCP", "KAFK", "PROM", "TERM", "WINOS")
        with _connect() as conn:
            present = [n for n in source_names if _table_exists(conn, n)]
            sources = len(present)

            atms = 0
            if "ATMA" in present:
                row = conn.execute("SELECT COUNT(DISTINCT atm_id) FROM ATMA").fetchone()
                atms = row[0] if row else 0

            time_window = "N/A"
            if "KAFK" in present:
                row = conn.execute(
                    "SELECT MIN(timestamp), MAX(timestamp) FROM KAFK"
                ).fetchone()
                if row and row[0] and row[1]:
                    time_window = f"{row[0][:10]} \u2013 {row[1][:10]}"

            avg_tps = 0.0
            if "KAFK" in present:
                row = conn.execute(
                    "SELECT AVG(CAST(transaction_rate_tps AS REAL)) FROM KAFK"
                ).fetchone()
                avg_tps = round(row[0] or 0, 1)

        return jsonify(
            {
                "status": "ok",
                "sources": sources,
                "atms": atms,
                "time_window": time_window,
                "avg_tps": avg_tps,
            }
        )

    @app.get("/api/source-snapshot")
    def api_source_snapshot():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "sources": []})

        source_names = ("ATMA", "ATMH", "GCP", "KAFK", "PROM", "TERM", "WINOS")
        results = []
        with _connect() as conn:
            for name in source_names:
                if not _table_exists(conn, name):
                    results.append({"source": name, "signal": "absent", "status": "No data"})
                    continue

                row = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()
                count = row[0] if row else 0

                if count == 0:
                    signal, status = "empty", "0 records"
                else:
                    signal, status = "present", f"{count:,} records"

                results.append({"source": name, "signal": signal, "status": status})

        return jsonify({"status": "ok", "sources": results})

    @app.get("/api/atm-list")
    def api_atm_list():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "atms": []})

        with _connect() as conn:
            has_atma = _table_exists(conn, "ATMA")
            has_detections = _table_exists(conn, "analysis_detections")

            if not has_atma:
                return jsonify({"status": "ok", "atms": []})

            rows = conn.execute(
                """
                SELECT atm_id, location_code, MAX(timestamp) AS last_update
                FROM ATMA
                GROUP BY atm_id, location_code
                """
            ).fetchall()

            atm_issues = {}
            if has_detections:
                det_rows = conn.execute(
                    """
                    SELECT atm_id, severity, anomaly_name
                    FROM analysis_detections
                    ORDER BY CASE WHEN severity = 'CRITICAL' THEN 0 ELSE 1 END, detected_at DESC
                    """
                ).fetchall()
                for atm_id, severity, name in det_rows:
                    if atm_id and atm_id not in atm_issues:
                        atm_issues[atm_id] = (severity, name)

            atms = []
            for atm_id, location_code, last_update in rows:
                if atm_id in atm_issues:
                    severity, issue = atm_issues[atm_id]
                    status = "critical" if severity == "CRITICAL" else "warning"
                else:
                    issue = None
                    status = "ok"

                atms.append(
                    {
                        "atm_id": atm_id,
                        "location": location_code or "N/A",
                        "status": status,
                        "issue": issue,
                        "last_update": last_update,
                    }
                )

            atms.sort(
                key=lambda a: (
                    0 if a["status"] == "critical" else 1 if a["status"] == "warning" else 2
                )
            )

        return jsonify({"status": "ok", "atms": atms})

    @app.get("/api/alerts")
    def api_alerts():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "critical": [], "warning": []})

        with _connect() as conn:
            if not _table_exists(conn, "analysis_detections"):
                return jsonify({"status": "ok", "critical": [], "warning": []})

            rows = conn.execute(
                """
                SELECT anomaly_type, anomaly_name, severity, source, atm_id,
                       detection_timestamp, description, event_count
                FROM analysis_detections
                ORDER BY CASE WHEN severity = 'CRITICAL' THEN 0 ELSE 1 END, detected_at DESC
                """
            ).fetchall()

        critical = []
        warning = []
        for anomaly_type, anomaly_name, severity, source, atm_id, ts, desc, count in rows:
            entry = {
                "anomaly_type": anomaly_type,
                "anomaly_name": anomaly_name,
                "severity": severity,
                "source": source,
                "atm_id": atm_id,
                "detection_timestamp": ts,
                "description": desc,
                "event_count": count,
            }
            if severity == "CRITICAL":
                critical.append(entry)
            else:
                warning.append(entry)

        return jsonify({"status": "ok", "critical": critical, "warning": warning})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
