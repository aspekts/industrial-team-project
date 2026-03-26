from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, session, url_for


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "clean" / "atm_logs.db"
VALID_ROLES = ("admin", "manager", "ops")
ROLE_LABELS = {
    "admin": "Admin",
    "manager": "Manager",
    "ops": "Ops",
}
LOGIN_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Operations Hub Login</title>
    <style>
      :root {
        color-scheme: light;
        font-family: "Public Sans", system-ui, sans-serif;
      }

      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: linear-gradient(160deg, #f4efe7 0%, #d9e4dd 100%);
        color: #132a1f;
      }

      .login-shell {
        width: min(100%, 28rem);
        padding: 2rem;
        border-radius: 1.5rem;
        background: rgba(255, 252, 247, 0.92);
        box-shadow: 0 1rem 3rem rgba(19, 42, 31, 0.14);
      }

      h1 {
        margin: 0 0 0.75rem;
        font-size: 2rem;
      }

      p {
        margin: 0 0 1.25rem;
        line-height: 1.5;
      }

      fieldset {
        margin: 0;
        padding: 0;
        border: 0;
      }

      .role-option {
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        margin-bottom: 0.75rem;
        padding: 0.9rem 1rem;
        border: 1px solid #b9c7bd;
        border-radius: 1rem;
        background: #fff;
      }

      .role-option strong,
      .role-option span {
        display: block;
      }

      .error {
        margin-bottom: 1rem;
        color: #8f1d1d;
        font-weight: 600;
      }

      button {
        margin-top: 0.75rem;
        border: 0;
        border-radius: 999px;
        padding: 0.85rem 1.2rem;
        background: #173927;
        color: #fff;
        font: inherit;
        cursor: pointer;
      }
    </style>
  </head>
  <body>
    <main class="login-shell">
      <p>Operations Hub</p>
      <h1>Select a role</h1>
      <p>Choose the dashboard persona for this session.</p>
      {% if error %}
      <p class="error">{{ error }}</p>
      {% endif %}
      <form method="post">
        <fieldset>
          <legend class="sr-only">Role selection</legend>
          <label class="role-option">
            <input type="radio" name="role" value="admin" {% if selected_role == "admin" %}checked{% endif %} />
            <span>
              <strong>Admin</strong>
              <span>Platform-wide access and configuration oversight.</span>
            </span>
          </label>
          <label class="role-option">
            <input type="radio" name="role" value="manager" {% if selected_role == "manager" %}checked{% endif %} />
            <span>
              <strong>Manager</strong>
              <span>Operational review and summary-level monitoring.</span>
            </span>
          </label>
          <label class="role-option">
            <input type="radio" name="role" value="ops" {% if selected_role == "ops" %}checked{% endif %} />
            <span>
              <strong>Ops</strong>
              <span>Daily anomaly handling and frontline investigation.</span>
            </span>
          </label>
        </fieldset>
        <button type="submit">Continue</button>
      </form>
    </main>
  </body>
</html>
"""


def get_dashboard_endpoint(role: str) -> str:
    return {
        "admin": "admin_dashboard",
        "manager": "manager_dashboard",
        "ops": "ops_dashboard",
    }[role]


def render_dashboard_view(role: str):
    dashboard_html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
    dashboard_html = dashboard_html.replace(
        "<body>",
        f'<body data-dashboard-role="{role}" data-dashboard-role-label="{ROLE_LABELS[role]}">',
        1,
    )
    dashboard_html = dashboard_html.replace(
        '<script src="app.js"></script>',
        f'<script>window.__dashboardRole = "{role}"; window.__dashboardRoleLabel = "{ROLE_LABELS[role]}";</script>\n    <script src="app.js"></script>',
        1,
    )
    return render_template_string(dashboard_html)


def create_app(db_path: Path | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(DASHBOARD_DIR),
        static_url_path="",
    )
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    app.config["DB_PATH"] = str(db_path or DEFAULT_DB_PATH)

    @app.get("/")
    def index():
        role = session.get("role")
        if role in VALID_ROLES:
            return redirect(url_for(get_dashboard_endpoint(role)))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        selected_role = session.get("role", "")

        if request.method == "POST":
            role = request.form.get("role", "").strip().lower()
            if role not in VALID_ROLES:
                error = "Select a valid role to continue."
            else:
                session["role"] = role
                return redirect(url_for(get_dashboard_endpoint(role)))

        return render_template_string(LOGIN_TEMPLATE, error=error, selected_role=selected_role)

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
        return jsonify(
            {
                "status": "ok",
                "role": session.get("role"),
                "database_present": db_file.exists(),
                "database_path": str(db_file.relative_to(PROJECT_ROOT)),
            }
        )

    @app.get("/api/status")
    def api_status():
        db_file = Path(app.config["DB_PATH"])
        response = {
            "database_present": db_file.exists(),
            "database_path": str(db_file.relative_to(PROJECT_ROOT)),
            "role": session.get("role"),
            "tables": [],
        }

        if not db_file.exists():
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

        return jsonify(response)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
