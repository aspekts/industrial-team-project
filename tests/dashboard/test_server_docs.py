from pathlib import Path

from src.dashboard.server import create_app


def build_client(tmp_path: Path):
    db_path = tmp_path / "atm_logs.db"
    app = create_app(db_path)
    app.config.update(TESTING=True)
    return app.test_client()


def test_swagger_ui_is_available(tmp_path):
    client = build_client(tmp_path)

    response = client.get("/api/docs/")

    assert response.status_code == 200
    assert b"swagger" in response.data.lower()


def test_openapi_spec_lists_key_routes(tmp_path):
    client = build_client(tmp_path)

    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["info"]["title"] == "ATM Monitoring Dashboard API"
    assert "/api/status" in payload["paths"]
    assert "/api/summary" in payload["paths"]
    assert "/api/atm-detail/{atm_id}" in payload["paths"]
