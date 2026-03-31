from __future__ import annotations

import os
import sqlite3
import sys
from datetime import date
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

    def _get_filter_date():
        raw_value = request.args.get("date", "").strip()
        if not raw_value:
            return None

        try:
            return date.fromisoformat(raw_value).isoformat()
        except ValueError:
            return None

    def _invalid_date_response():
        return jsonify({"status": "invalid", "reason": "date must be in YYYY-MM-DD format"}), 400

    @app.get("/api/summary")
    def api_summary():
        filter_date = _get_filter_date()
        if request.args.get("date") and not filter_date:
            return _invalid_date_response()

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
                if filter_date:
                    row = conn.execute(
                        "SELECT COUNT(DISTINCT atm_id) FROM ATMA WHERE substr(timestamp, 1, 10) = ?",
                        (filter_date,),
                    ).fetchone()
                else:
                    row = conn.execute("SELECT COUNT(DISTINCT atm_id) FROM ATMA").fetchone()
                observed_atms = row[0] if row else 0

            app_errors = 0
            if has_atma:
                if filter_date:
                    row = conn.execute(
                        """
                        SELECT COUNT(*)
                        FROM ATMA
                        WHERE event_type IN ('ERROR','TIMEOUT','NETWORK_DISCONNECT')
                          AND substr(timestamp, 1, 10) = ?
                        """,
                        (filter_date,),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM ATMA WHERE event_type IN ('ERROR','TIMEOUT','NETWORK_DISCONNECT')"
                    ).fetchone()
                app_errors = row[0] if row else 0

            hardware_alerts = 0
            if has_atmh:
                if filter_date:
                    row = conn.execute(
                        """
                        SELECT COUNT(*)
                        FROM ATMH
                        WHERE severity IN ('CRITICAL','WARNING')
                          AND substr(timestamp, 1, 10) = ?
                        """,
                        (filter_date,),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM ATMH WHERE severity IN ('CRITICAL','WARNING')"
                    ).fetchone()
                hardware_alerts = row[0] if row else 0

            avg_tps = 0.0
            if has_kafk:
                if filter_date:
                    row = conn.execute(
                        """
                        SELECT AVG(CAST(transaction_rate_tps AS REAL))
                        FROM KAFK
                        WHERE substr(timestamp, 1, 10) = ?
                        """,
                        (filter_date,),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT AVG(CAST(transaction_rate_tps AS REAL)) FROM KAFK"
                    ).fetchone()
                avg_tps = round(row[0] or 0, 1)

            failure_windows = 0
            if has_detections:
                if filter_date:
                    row = conn.execute(
                        """
                        SELECT COUNT(*)
                        FROM analysis_detections
                        WHERE severity = 'CRITICAL'
                          AND substr(detection_timestamp, 1, 10) = ?
                        """,
                        (filter_date,),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM analysis_detections WHERE severity = 'CRITICAL'"
                    ).fetchone()
                failure_windows = row[0] if row else 0

        return jsonify(
            {
                "status": "ok",
                "filter_date": filter_date,
                "observed_atms": observed_atms,
                "app_errors": app_errors,
                "hardware_alerts": hardware_alerts,
                "avg_tps": avg_tps,
                "failure_windows": failure_windows,
            }
        )

    @app.get("/api/scale")
    def api_scale():
        filter_date = _get_filter_date()
        if request.args.get("date") and not filter_date:
            return _invalid_date_response()

        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable"})

        source_names = ("ATMA", "ATMH", "GCP", "KAFK", "PROM", "TERM", "WINOS")
        with _connect() as conn:
            present = [n for n in source_names if _table_exists(conn, n)]
            sources = len(present)

            atms = 0
            if "ATMA" in present:
                if filter_date:
                    row = conn.execute(
                        "SELECT COUNT(DISTINCT atm_id) FROM ATMA WHERE substr(timestamp, 1, 10) = ?",
                        (filter_date,),
                    ).fetchone()
                else:
                    row = conn.execute("SELECT COUNT(DISTINCT atm_id) FROM ATMA").fetchone()
                atms = row[0] if row else 0

            time_window = "N/A"
            if "KAFK" in present:
                if filter_date:
                    row = conn.execute(
                        "SELECT MIN(timestamp), MAX(timestamp) FROM KAFK WHERE substr(timestamp, 1, 10) = ?",
                        (filter_date,),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT MIN(timestamp), MAX(timestamp) FROM KAFK"
                    ).fetchone()
                if row and row[0] and row[1]:
                    time_window = f"{row[0][:10]} \u2013 {row[1][:10]}"

            avg_tps = 0.0
            if "KAFK" in present:
                if filter_date:
                    row = conn.execute(
                        """
                        SELECT AVG(CAST(transaction_rate_tps AS REAL))
                        FROM KAFK
                        WHERE substr(timestamp, 1, 10) = ?
                        """,
                        (filter_date,),
                    ).fetchone()
                else:
                    row = conn.execute(
                        "SELECT AVG(CAST(transaction_rate_tps AS REAL)) FROM KAFK"
                    ).fetchone()
                avg_tps = round(row[0] or 0, 1)

        return jsonify(
            {
                "status": "ok",
                "filter_date": filter_date,
                "sources": sources,
                "atms": atms,
                "time_window": time_window,
                "avg_tps": avg_tps,
            }
        )

    @app.get("/api/source-snapshot")
    def api_source_snapshot():
        filter_date = _get_filter_date()
        if request.args.get("date") and not filter_date:
            return _invalid_date_response()

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

                if filter_date:
                    row = conn.execute(
                        f"SELECT COUNT(*) FROM [{name}] WHERE substr(timestamp, 1, 10) = ?",
                        (filter_date,),
                    ).fetchone()
                else:
                    row = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()
                count = row[0] if row else 0

                if count == 0:
                    signal, status = "empty", "0 records"
                else:
                    signal, status = "present", f"{count:,} records"

                results.append({"source": name, "signal": signal, "status": status})

        return jsonify({"status": "ok", "filter_date": filter_date, "sources": results})

    @app.get("/api/atm-list")
    def api_atm_list():
        filter_date = _get_filter_date()
        if request.args.get("date") and not filter_date:
            return _invalid_date_response()

        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "atms": []})

        with _connect() as conn:
            has_atma = _table_exists(conn, "ATMA")
            has_detections = _table_exists(conn, "analysis_detections")

            if not has_atma:
                return jsonify({"status": "ok", "atms": []})

            if filter_date:
                rows = conn.execute(
                    """
                    SELECT atm_id, location_code, MAX(timestamp) AS last_update
                    FROM ATMA
                    WHERE substr(timestamp, 1, 10) = ?
                    GROUP BY atm_id, location_code
                    """,
                    (filter_date,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT atm_id, location_code, MAX(timestamp) AS last_update
                    FROM ATMA
                    GROUP BY atm_id, location_code
                    """
                ).fetchall()

            atm_issues = {}
            if has_detections:
                if filter_date:
                    det_rows = conn.execute(
                        """
                        SELECT atm_id, severity, anomaly_name
                        FROM analysis_detections
                        WHERE substr(detection_timestamp, 1, 10) = ?
                        ORDER BY CASE WHEN severity = 'CRITICAL' THEN 0 ELSE 1 END, detected_at DESC
                        """,
                        (filter_date,),
                    ).fetchall()
                else:
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

        return jsonify({"status": "ok", "filter_date": filter_date, "atms": atms})

    @app.get("/api/alerts")
    def api_alerts():
        filter_date = _get_filter_date()
        if request.args.get("date") and not filter_date:
            return _invalid_date_response()

        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "critical": [], "warning": []})

        with _connect() as conn:
            if not _table_exists(conn, "analysis_detections"):
                return jsonify({"status": "ok", "critical": [], "warning": []})

            if filter_date:
                rows = conn.execute(
                    """
                    SELECT anomaly_type, anomaly_name, severity, source, atm_id,
                           detection_timestamp, description, event_count
                    FROM analysis_detections
                    WHERE substr(detection_timestamp, 1, 10) = ?
                    ORDER BY CASE WHEN severity = 'CRITICAL' THEN 0 ELSE 1 END, detected_at DESC
                    """,
                    (filter_date,),
                ).fetchall()
            else:
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

        return jsonify({"status": "ok", "filter_date": filter_date, "critical": critical, "warning": warning})

    @app.get("/api/trend")
    def api_trend():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "points": []})

        with _connect() as conn:
            if not _table_exists(conn, "ATMA"):
                return jsonify({"status": "ok", "points": [], "peak_hour": None, "peak_errors": 0})

            rows = conn.execute(
                """
                SELECT
                    strftime('%H', timestamp) AS hour,
                    COUNT(*) AS total_events,
                    COUNT(CASE WHEN event_type IN ('ERROR','TIMEOUT','NETWORK_DISCONNECT')
                               THEN 1 END) AS error_count
                FROM ATMA
                GROUP BY hour
                ORDER BY hour
                """
            ).fetchall()

        points = [{"hour": row[0], "total": row[1], "errors": row[2] or 0} for row in rows if row[0]]
        peak = max(points, key=lambda p: p["errors"], default=None)
        return jsonify({
            "status": "ok",
            "points": points,
            "peak_hour": peak["hour"] if peak else None,
            "peak_errors": peak["errors"] if peak else 0,
        })

    @app.get("/api/source-checks")
    def api_source_checks():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "checks": []})

        checks = []
        with _connect() as conn:
            if _table_exists(conn, "KAFK"):
                row = conn.execute(
                    "SELECT COUNT(*) FROM KAFK WHERE failure_count > 0"
                ).fetchone()
                kafk_failures = row[0] if row else 0
                checks.append({
                    "key": "kafk_failures",
                    "label": "KAFK transaction failures",
                    "value": kafk_failures,
                    "detail": f"{kafk_failures} windows with failure_count > 0" if kafk_failures else "No failure windows detected",
                    "severity": "critical" if kafk_failures > 0 else "ok",
                })
            else:
                checks.append({"key": "kafk_failures", "label": "KAFK transaction failures",
                                "value": 0, "detail": "KAFK table not present", "severity": "absent"})

            if _table_exists(conn, "TERM"):
                row = conn.execute(
                    "SELECT COUNT(*) FROM TERM WHERE log_level IN ('ERROR','FATAL')"
                ).fetchone()
                term_errors = row[0] if row else 0
                checks.append({
                    "key": "term_errors",
                    "label": "Terminal handler runtime",
                    "value": term_errors,
                    "detail": f"{term_errors} ERROR/FATAL events in terminal handler" if term_errors else "No error-level events detected",
                    "severity": "warning" if term_errors > 0 else "ok",
                })
            else:
                checks.append({"key": "term_errors", "label": "Terminal handler runtime",
                                "value": 0, "detail": "TERM table not present", "severity": "absent"})

            if _table_exists(conn, "WINOS"):
                row = conn.execute(
                    "SELECT COUNT(*), MAX(cpu_usage_percent) FROM WINOS WHERE cpu_usage_percent > 80"
                ).fetchone()
                pressure_count = row[0] if row else 0
                peak_cpu = int(row[1]) if row and row[1] else 0
                checks.append({
                    "key": "winos_pressure",
                    "label": "Windows host health",
                    "value": pressure_count,
                    "detail": f"{pressure_count} samples above 80% CPU (peak {peak_cpu}%)" if pressure_count else "CPU within normal range",
                    "severity": "critical" if pressure_count > 0 else "ok",
                })
            else:
                checks.append({"key": "winos_pressure", "label": "Windows host health",
                                "value": 0, "detail": "WINOS table not present", "severity": "absent"})

        return jsonify({"status": "ok", "checks": checks})

    @app.get("/api/priority-summary")
    def api_priority_summary():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable"})

        with _connect() as conn:
            if not _table_exists(conn, "analysis_detections"):
                return jsonify({"status": "ok", "has_critical": False, "anomaly_name": None})

            top_row = conn.execute(
                """
                SELECT anomaly_type, anomaly_name, severity, source, atm_id,
                       detection_timestamp, description, event_count
                FROM analysis_detections
                WHERE severity = 'CRITICAL'
                ORDER BY detected_at DESC
                LIMIT 1
                """
            ).fetchone()

            if not top_row:
                top_row = conn.execute(
                    """
                    SELECT anomaly_type, anomaly_name, severity, source, atm_id,
                           detection_timestamp, description, event_count
                    FROM analysis_detections
                    ORDER BY detected_at DESC
                    LIMIT 1
                    """
                ).fetchone()

            if not top_row:
                return jsonify({"status": "ok", "has_critical": False, "anomaly_name": None})

            anomaly_type, anomaly_name, severity, source, atm_id, ts, desc, event_count = top_row

            corr_row = conn.execute(
                "SELECT GROUP_CONCAT(DISTINCT source) FROM analysis_detections WHERE atm_id = ?",
                (atm_id,),
            ).fetchone()
            correlated_sources = corr_row[0] if corr_row and corr_row[0] else source

            crit_count = conn.execute(
                "SELECT COUNT(*) FROM analysis_detections WHERE severity = 'CRITICAL'"
            ).fetchone()
            total_critical = crit_count[0] if crit_count else 0

        return jsonify({
            "status": "ok",
            "has_critical": severity == "CRITICAL",
            "anomaly_name": anomaly_name,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "source": source,
            "atm_id": atm_id or "N/A",
            "detection_timestamp": ts,
            "description": desc or "",
            "event_count": event_count or 0,
            "correlated_sources": correlated_sources,
            "total_critical": total_critical,
            "primary_signal": f"{anomaly_name} ({anomaly_type}) — {source}",
            "secondary_signal": f"{event_count} events on {atm_id or 'multiple ATMs'} since {(ts or '')[:10]}",
            "impact": f"{total_critical} critical detection group{'s' if total_critical != 1 else ''} active",
            "next_review_area": f"Cross-reference {correlated_sources} for {atm_id or 'affected ATMs'}",
            "next_best_action": f"Open anomaly groups for {atm_id or 'affected ATMs'} and review {source} evidence",
        })

    @app.get("/api/me")
    def api_me():
        username = session.get("user_name", "")
        role = session.get("role", "")
        if not username:
            return jsonify({"status": "unauthenticated", "username": "", "role": ""})
        return jsonify({"status": "ok", "username": username, "role": role})

    @app.get("/api/winos-trend")
    def api_winos_trend():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "points": []})

        with _connect() as conn:
            if not _table_exists(conn, "WINOS"):
                return jsonify({"status": "ok", "points": [], "peak_hour": None, "peak_cpu": 0})

            rows = conn.execute(
                """
                SELECT
                    strftime('%H', timestamp) AS hour,
                    AVG(CAST(cpu_usage_percent AS REAL)) AS avg_cpu,
                    MAX(CAST(cpu_usage_percent AS REAL)) AS max_cpu
                FROM WINOS
                GROUP BY hour
                ORDER BY hour
                """
            ).fetchall()

        points = [
            {"hour": row[0], "avg_cpu": round(row[1] or 0, 1), "max_cpu": round(row[2] or 0, 1)}
            for row in rows
            if row[0]
        ]
        peak = max(points, key=lambda p: p["max_cpu"], default=None)
        return jsonify({
            "status": "ok",
            "points": points,
            "peak_hour": peak["hour"] if peak else None,
            "peak_cpu": peak["max_cpu"] if peak else 0,
        })

    @app.get("/api/atm-detail/<atm_id>")
    def api_atm_detail(atm_id):
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable"})

        with _connect() as conn:
            if not _table_exists(conn, "ATMA"):
                return jsonify({"status": "not_found", "atm_id": atm_id})

            atma_row = conn.execute(
                """
                SELECT location_code, MAX(timestamp) AS last_ts, atm_status,
                       COUNT(CASE WHEN event_type IN ('ERROR','TIMEOUT','NETWORK_DISCONNECT')
                                  THEN 1 END) AS error_count
                FROM ATMA WHERE atm_id = ?
                GROUP BY location_code, atm_status
                ORDER BY last_ts DESC LIMIT 1
                """,
                (atm_id,),
            ).fetchone()

            if not atma_row:
                return jsonify({"status": "not_found", "atm_id": atm_id})

            location_code, last_ts, atm_status, error_count = atma_row

            timeline_rows = conn.execute(
                """
                SELECT timestamp, event_type, component, message, error_code
                FROM ATMA WHERE atm_id = ?
                ORDER BY timestamp DESC LIMIT 6
                """,
                (atm_id,),
            ).fetchall()

            detections = []
            if _table_exists(conn, "analysis_detections"):
                det_rows = conn.execute(
                    """
                    SELECT anomaly_type, anomaly_name, severity, source, description, event_count
                    FROM analysis_detections WHERE atm_id = ?
                    ORDER BY CASE WHEN severity='CRITICAL' THEN 0 ELSE 1 END, detected_at DESC
                    """,
                    (atm_id,),
                ).fetchall()
                detections = [
                    {"anomaly_type": r[0], "anomaly_name": r[1], "severity": r[2],
                     "source": r[3], "description": r[4], "event_count": r[5]}
                    for r in det_rows
                ]

            kafk_summary = None
            if _table_exists(conn, "KAFK"):
                kafk_row = conn.execute(
                    """
                    SELECT SUM(failure_count), AVG(CAST(transaction_rate_tps AS REAL)),
                           GROUP_CONCAT(DISTINCT transaction_failure_reason)
                    FROM KAFK WHERE atm_id = ? AND failure_count > 0
                    """,
                    (atm_id,),
                ).fetchone()
                if kafk_row and kafk_row[0]:
                    kafk_summary = {
                        "total_failures": int(kafk_row[0]),
                        "avg_tps": round(kafk_row[1] or 0, 1),
                        "failure_reasons": kafk_row[2] or "None",
                    }

            winos_summary = None
            if _table_exists(conn, "WINOS"):
                winos_row = conn.execute(
                    """
                    SELECT cpu_usage_percent, memory_usage_percent, network_errors
                    FROM WINOS WHERE atm_id = ?
                    ORDER BY timestamp DESC LIMIT 1
                    """,
                    (atm_id,),
                ).fetchone()
                if winos_row:
                    winos_summary = {
                        "cpu_pct": winos_row[0],
                        "mem_pct": winos_row[1],
                        "net_errors": winos_row[2],
                    }

            atmh_count = 0
            if _table_exists(conn, "ATMH"):
                row = conn.execute(
                    "SELECT COUNT(*) FROM ATMH WHERE atm_id = ? AND severity IN ('CRITICAL','WARNING')",
                    (atm_id,),
                ).fetchone()
                atmh_count = row[0] if row else 0

            all_sources = list({d["source"] for d in detections})

        return jsonify({
            "status": "ok",
            "atm_id": atm_id,
            "location_code": location_code or "N/A",
            "last_update": last_ts,
            "atm_status": atm_status or "Unknown",
            "error_count": error_count or 0,
            "hw_alerts": atmh_count,
            "top_detection": detections[0] if detections else None,
            "detections": detections,
            "kafk_summary": kafk_summary,
            "winos_summary": winos_summary,
            "correlated_sources": ", ".join(all_sources) if all_sources else "N/A",
            "timeline": [
                {"timestamp": r[0], "event_type": r[1], "component": r[2],
                 "message": r[3], "error_code": r[4]}
                for r in timeline_rows
            ],
        })

    @app.get("/api/incidents")
    def api_incidents():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "incidents": []})
        with _connect() as conn:
            if not _table_exists(conn, "incidents"):
                return jsonify({"status": "ok", "incidents": [], "total": 0})
            rows = conn.execute(
                """
                SELECT incident_id, correlation_id, atm_ids, sources, anomaly_types,
                       severity, event_count, earliest_ts, latest_ts, description, strategy
                FROM incidents
                ORDER BY CASE WHEN severity='CRITICAL' THEN 0 ELSE 1 END, earliest_ts DESC
                """
            ).fetchall()
        cols = ["incident_id", "correlation_id", "atm_ids", "sources", "anomaly_types",
                "severity", "event_count", "earliest_ts", "latest_ts", "description", "strategy"]
        incidents = [dict(zip(cols, r)) for r in rows]
        return jsonify({"status": "ok", "incidents": incidents, "total": len(incidents)})

    @app.get("/api/ml-summary")
    def api_ml_summary():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable"})
        with _connect() as conn:
            if not _table_exists(conn, "ml_anomaly_scores"):
                return jsonify({"status": "ok", "total_scored": 0, "total_anomalies": 0, "model_version": None, "sources": []})
            row = conn.execute(
                "SELECT COUNT(*), SUM(is_anomaly), MAX(model_version) FROM ml_anomaly_scores"
            ).fetchone()
            source_rows = conn.execute(
                "SELECT source, COUNT(*), SUM(is_anomaly) FROM ml_anomaly_scores GROUP BY source"
            ).fetchall()
        return jsonify({
            "status": "ok",
            "total_scored": row[0] or 0,
            "total_anomalies": int(row[1] or 0),
            "model_version": row[2],
            "sources": [{"source": r[0], "scored": r[1], "anomalies": int(r[2] or 0)} for r in source_rows],
        })

    @app.get("/api/trend")
    def api_trend():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "points": []})

        with _connect() as conn:
            if not _table_exists(conn, "ATMA"):
                return jsonify({"status": "ok", "points": [], "peak_hour": None, "peak_errors": 0})

            rows = conn.execute(
                """
                SELECT
                    strftime('%H', timestamp) AS hour,
                    COUNT(*) AS total_events,
                    COUNT(CASE WHEN event_type IN ('ERROR','TIMEOUT','NETWORK_DISCONNECT')
                               THEN 1 END) AS error_count
                FROM ATMA
                GROUP BY hour
                ORDER BY hour
                """
            ).fetchall()

        points = [{"hour": row[0], "total": row[1], "errors": row[2] or 0} for row in rows if row[0]]
        peak = max(points, key=lambda p: p["errors"], default=None)
        return jsonify({
            "status": "ok",
            "points": points,
            "peak_hour": peak["hour"] if peak else None,
            "peak_errors": peak["errors"] if peak else 0,
        })

    @app.get("/api/source-checks")
    def api_source_checks():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "checks": []})

        checks = []
        with _connect() as conn:
            if _table_exists(conn, "KAFK"):
                row = conn.execute(
                    "SELECT COUNT(*) FROM KAFK WHERE failure_count > 0"
                ).fetchone()
                kafk_failures = row[0] if row else 0
                checks.append({
                    "key": "kafk_failures",
                    "label": "KAFK transaction failures",
                    "value": kafk_failures,
                    "detail": f"{kafk_failures} windows with failure_count > 0" if kafk_failures else "No failure windows detected",
                    "severity": "critical" if kafk_failures > 0 else "ok",
                })
            else:
                checks.append({"key": "kafk_failures", "label": "KAFK transaction failures",
                                "value": 0, "detail": "KAFK table not present", "severity": "absent"})

            if _table_exists(conn, "TERM"):
                row = conn.execute(
                    "SELECT COUNT(*) FROM TERM WHERE log_level IN ('ERROR','FATAL')"
                ).fetchone()
                term_errors = row[0] if row else 0
                checks.append({
                    "key": "term_errors",
                    "label": "Terminal handler runtime",
                    "value": term_errors,
                    "detail": f"{term_errors} ERROR/FATAL events in terminal handler" if term_errors else "No error-level events detected",
                    "severity": "warning" if term_errors > 0 else "ok",
                })
            else:
                checks.append({"key": "term_errors", "label": "Terminal handler runtime",
                                "value": 0, "detail": "TERM table not present", "severity": "absent"})

            if _table_exists(conn, "WINOS"):
                row = conn.execute(
                    "SELECT COUNT(*), MAX(cpu_usage_percent) FROM WINOS WHERE cpu_usage_percent > 80"
                ).fetchone()
                pressure_count = row[0] if row else 0
                peak_cpu = int(row[1]) if row and row[1] else 0
                checks.append({
                    "key": "winos_pressure",
                    "label": "Windows host health",
                    "value": pressure_count,
                    "detail": f"{pressure_count} samples above 80% CPU (peak {peak_cpu}%)" if pressure_count else "CPU within normal range",
                    "severity": "critical" if pressure_count > 0 else "ok",
                })
            else:
                checks.append({"key": "winos_pressure", "label": "Windows host health",
                                "value": 0, "detail": "WINOS table not present", "severity": "absent"})

        return jsonify({"status": "ok", "checks": checks})

    @app.get("/api/priority-summary")
    def api_priority_summary():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable"})

        with _connect() as conn:
            if not _table_exists(conn, "analysis_detections"):
                return jsonify({"status": "ok", "has_critical": False, "anomaly_name": None})

            top_row = conn.execute(
                """
                SELECT anomaly_type, anomaly_name, severity, source, atm_id,
                       detection_timestamp, description, event_count
                FROM analysis_detections
                WHERE severity = 'CRITICAL'
                ORDER BY detected_at DESC
                LIMIT 1
                """
            ).fetchone()

            if not top_row:
                top_row = conn.execute(
                    """
                    SELECT anomaly_type, anomaly_name, severity, source, atm_id,
                           detection_timestamp, description, event_count
                    FROM analysis_detections
                    ORDER BY detected_at DESC
                    LIMIT 1
                    """
                ).fetchone()

            if not top_row:
                return jsonify({"status": "ok", "has_critical": False, "anomaly_name": None})

            anomaly_type, anomaly_name, severity, source, atm_id, ts, desc, event_count = top_row

            corr_row = conn.execute(
                "SELECT GROUP_CONCAT(DISTINCT source) FROM analysis_detections WHERE atm_id = ?",
                (atm_id,),
            ).fetchone()
            correlated_sources = corr_row[0] if corr_row and corr_row[0] else source

            crit_count = conn.execute(
                "SELECT COUNT(*) FROM analysis_detections WHERE severity = 'CRITICAL'"
            ).fetchone()
            total_critical = crit_count[0] if crit_count else 0

        return jsonify({
            "status": "ok",
            "has_critical": severity == "CRITICAL",
            "anomaly_name": anomaly_name,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "source": source,
            "atm_id": atm_id or "N/A",
            "detection_timestamp": ts,
            "description": desc or "",
            "event_count": event_count or 0,
            "correlated_sources": correlated_sources,
            "total_critical": total_critical,
            "primary_signal": f"{anomaly_name} ({anomaly_type}) — {source}",
            "secondary_signal": f"{event_count} events on {atm_id or 'multiple ATMs'} since {(ts or '')[:10]}",
            "impact": f"{total_critical} critical detection group{'s' if total_critical != 1 else ''} active",
            "next_review_area": f"Cross-reference {correlated_sources} for {atm_id or 'affected ATMs'}",
            "next_best_action": f"Open anomaly groups for {atm_id or 'affected ATMs'} and review {source} evidence",
        })

    @app.get("/api/me")
    def api_me():
        username = session.get("user_name", "")
        role = session.get("role", "")
        if not username:
            return jsonify({"status": "unauthenticated", "username": "", "role": ""})
        return jsonify({"status": "ok", "username": username, "role": role})

    @app.get("/api/winos-trend")
    def api_winos_trend():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "points": []})

        with _connect() as conn:
            if not _table_exists(conn, "WINOS"):
                return jsonify({"status": "ok", "points": [], "peak_hour": None, "peak_cpu": 0})

            rows = conn.execute(
                """
                SELECT
                    strftime('%H', timestamp) AS hour,
                    AVG(CAST(cpu_usage_percent AS REAL)) AS avg_cpu,
                    MAX(CAST(cpu_usage_percent AS REAL)) AS max_cpu
                FROM WINOS
                GROUP BY hour
                ORDER BY hour
                """
            ).fetchall()

        points = [
            {"hour": row[0], "avg_cpu": round(row[1] or 0, 1), "max_cpu": round(row[2] or 0, 1)}
            for row in rows
            if row[0]
        ]
        peak = max(points, key=lambda p: p["max_cpu"], default=None)
        return jsonify({
            "status": "ok",
            "points": points,
            "peak_hour": peak["hour"] if peak else None,
            "peak_cpu": peak["max_cpu"] if peak else 0,
        })

    @app.get("/api/atm-detail/<atm_id>")
    def api_atm_detail(atm_id):
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable"})

        with _connect() as conn:
            if not _table_exists(conn, "ATMA"):
                return jsonify({"status": "not_found", "atm_id": atm_id})

            atma_row = conn.execute(
                """
                SELECT location_code, MAX(timestamp) AS last_ts, atm_status,
                       COUNT(CASE WHEN event_type IN ('ERROR','TIMEOUT','NETWORK_DISCONNECT')
                                  THEN 1 END) AS error_count
                FROM ATMA WHERE atm_id = ?
                GROUP BY location_code, atm_status
                ORDER BY last_ts DESC LIMIT 1
                """,
                (atm_id,),
            ).fetchone()

            if not atma_row:
                return jsonify({"status": "not_found", "atm_id": atm_id})

            location_code, last_ts, atm_status, error_count = atma_row

            timeline_rows = conn.execute(
                """
                SELECT timestamp, event_type, component, message, error_code
                FROM ATMA WHERE atm_id = ?
                ORDER BY timestamp DESC LIMIT 6
                """,
                (atm_id,),
            ).fetchall()

            detections = []
            if _table_exists(conn, "analysis_detections"):
                det_rows = conn.execute(
                    """
                    SELECT anomaly_type, anomaly_name, severity, source, description, event_count
                    FROM analysis_detections WHERE atm_id = ?
                    ORDER BY CASE WHEN severity='CRITICAL' THEN 0 ELSE 1 END, detected_at DESC
                    """,
                    (atm_id,),
                ).fetchall()
                detections = [
                    {"anomaly_type": r[0], "anomaly_name": r[1], "severity": r[2],
                     "source": r[3], "description": r[4], "event_count": r[5]}
                    for r in det_rows
                ]

            kafk_summary = None
            if _table_exists(conn, "KAFK"):
                kafk_row = conn.execute(
                    """
                    SELECT SUM(failure_count), AVG(CAST(transaction_rate_tps AS REAL)),
                           GROUP_CONCAT(DISTINCT transaction_failure_reason)
                    FROM KAFK WHERE atm_id = ? AND failure_count > 0
                    """,
                    (atm_id,),
                ).fetchone()
                if kafk_row and kafk_row[0]:
                    kafk_summary = {
                        "total_failures": int(kafk_row[0]),
                        "avg_tps": round(kafk_row[1] or 0, 1),
                        "failure_reasons": kafk_row[2] or "None",
                    }

            winos_summary = None
            if _table_exists(conn, "WINOS"):
                winos_row = conn.execute(
                    """
                    SELECT cpu_usage_percent, memory_usage_percent, network_errors
                    FROM WINOS WHERE atm_id = ?
                    ORDER BY timestamp DESC LIMIT 1
                    """,
                    (atm_id,),
                ).fetchone()
                if winos_row:
                    winos_summary = {
                        "cpu_pct": winos_row[0],
                        "mem_pct": winos_row[1],
                        "net_errors": winos_row[2],
                    }

            atmh_count = 0
            if _table_exists(conn, "ATMH"):
                row = conn.execute(
                    "SELECT COUNT(*) FROM ATMH WHERE atm_id = ? AND severity IN ('CRITICAL','WARNING')",
                    (atm_id,),
                ).fetchone()
                atmh_count = row[0] if row else 0

            all_sources = list({d["source"] for d in detections})

        return jsonify({
            "status": "ok",
            "atm_id": atm_id,
            "location_code": location_code or "N/A",
            "last_update": last_ts,
            "atm_status": atm_status or "Unknown",
            "error_count": error_count or 0,
            "hw_alerts": atmh_count,
            "top_detection": detections[0] if detections else None,
            "detections": detections,
            "kafk_summary": kafk_summary,
            "winos_summary": winos_summary,
            "correlated_sources": ", ".join(all_sources) if all_sources else "N/A",
            "timeline": [
                {"timestamp": r[0], "event_type": r[1], "component": r[2],
                 "message": r[3], "error_code": r[4]}
                for r in timeline_rows
            ],
        })

    @app.get("/api/incidents")
    def api_incidents():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable", "incidents": []})
        with _connect() as conn:
            if not _table_exists(conn, "incidents"):
                return jsonify({"status": "ok", "incidents": [], "total": 0})
            rows = conn.execute(
                """
                SELECT incident_id, correlation_id, atm_ids, sources, anomaly_types,
                       severity, event_count, earliest_ts, latest_ts, description, strategy
                FROM incidents
                ORDER BY CASE WHEN severity='CRITICAL' THEN 0 ELSE 1 END, earliest_ts DESC
                """
            ).fetchall()
        cols = ["incident_id", "correlation_id", "atm_ids", "sources", "anomaly_types",
                "severity", "event_count", "earliest_ts", "latest_ts", "description", "strategy"]
        incidents = [dict(zip(cols, r)) for r in rows]
        return jsonify({"status": "ok", "incidents": incidents, "total": len(incidents)})

    @app.get("/api/ml-summary")
    def api_ml_summary():
        db_file = _db()
        if not db_file.exists():
            return jsonify({"status": "unavailable"})
        with _connect() as conn:
            if not _table_exists(conn, "ml_anomaly_scores"):
                return jsonify({"status": "ok", "total_scored": 0, "total_anomalies": 0, "model_version": None, "sources": []})
            row = conn.execute(
                "SELECT COUNT(*), SUM(is_anomaly), MAX(model_version) FROM ml_anomaly_scores"
            ).fetchone()
            source_rows = conn.execute(
                "SELECT source, COUNT(*), SUM(is_anomaly) FROM ml_anomaly_scores GROUP BY source"
            ).fetchall()
        return jsonify({
            "status": "ok",
            "total_scored": row[0] or 0,
            "total_anomalies": int(row[1] or 0),
            "model_version": row[2],
            "sources": [{"source": r[0], "scored": r[1], "anomalies": int(r[2] or 0)} for r in source_rows],
        })

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
