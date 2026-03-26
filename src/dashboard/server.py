from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, jsonify, send_from_directory


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "clean" / "atm_logs.db"


def create_app(db_path: Path | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(DASHBOARD_DIR),
        static_url_path="",
    )
    app.config["DB_PATH"] = str(db_path or DEFAULT_DB_PATH)

    @app.get("/")
    def index():
        return send_from_directory(DASHBOARD_DIR, "index.html")

    @app.get("/health")
    def health():
        db_file = Path(app.config["DB_PATH"])
        return jsonify(
            {
                "status": "ok",
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
