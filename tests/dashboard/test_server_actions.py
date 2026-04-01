from pathlib import Path

from src.dashboard.server import create_app


def build_client(tmp_path: Path):
    db_path = tmp_path / "atm_logs.db"
    app = create_app(db_path)
    app.config.update(TESTING=True)
    return app.test_client()


def test_manager_can_record_and_read_actions(tmp_path):
    client = build_client(tmp_path)

    with client.session_transaction() as session:
        session["role"] = "manager"
        session["user_name"] = "casey"

    response = client.post(
        "/api/actions",
        json={
            "action_label": "Assign for review",
            "anomaly_type": "A1",
            "anomaly_name": "Cash dispenser fault",
            "atm_id": "ATM-GB-0001",
            "notes": "Branch team notified.",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["action"]["action_label"] == "Assign for review"
    assert payload["action"]["user_role"] == "manager"
    assert payload["action"]["username"] == "casey"

    history_response = client.get("/api/actions")
    assert history_response.status_code == 200
    history_payload = history_response.get_json()
    assert history_payload["status"] == "ok"
    assert len(history_payload["actions"]) == 1
    assert history_payload["actions"][0]["atm_id"] == "ATM-GB-0001"


def test_admin_cannot_record_actions(tmp_path):
    client = build_client(tmp_path)

    with client.session_transaction() as session:
        session["role"] = "admin"
        session["user_name"] = "alex"

    response = client.post("/api/actions", json={"action_label": "Acknowledge issue"})

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["status"] == "error"
    assert payload["reason"] == "forbidden"
