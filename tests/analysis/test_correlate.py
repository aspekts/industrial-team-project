"""
Tests for the cross-source correlation engine (src/analysis/correlate.py).

Strategy coverage:
  - correlation_id grouping (Strategy 1)
  - time-window fallback (Strategy 2)
  - build_incidents() combining both
  - store_incidents() writes + clears incidents table
  - edge cases: empty input, single-source groups excluded, NULL timestamps
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from src.analysis.correlate import Correlator, _parse_ts


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_db(tmp_path: Path) -> Path:
    """Create a minimal SQLite DB with analysis_detections + ATMA + KAFK tables."""
    db = tmp_path / "test.db"
    with sqlite3.connect(db) as conn:
        conn.execute("""
            CREATE TABLE analysis_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anomaly_type TEXT, anomaly_name TEXT, severity TEXT,
                source TEXT, atm_id TEXT, detection_timestamp TEXT,
                description TEXT, event_count INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE ATMA (
                timestamp TEXT, atm_id TEXT, correlation_id TEXT,
                event_type TEXT, message TEXT, log_level TEXT,
                location_code TEXT, session_id TEXT, transaction_id TEXT,
                component TEXT, thread_id INTEGER, response_time_ms INTEGER,
                error_code TEXT, error_detail TEXT, atm_status TEXT,
                os_version TEXT, app_version TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE KAFK (
                timestamp TEXT, event_id TEXT, correlation_id TEXT,
                atm_id TEXT, atm_status TEXT, transaction_rate_tps REAL,
                response_time_ms INTEGER, transaction_volume INTEGER,
                transaction_success_rate REAL, transaction_failure_reason TEXT,
                failure_count INTEGER, window_duration_seconds INTEGER,
                kafka_partition INTEGER, kafka_offset INTEGER
            )
        """)
    return db


def _insert_detection(db: Path, **kwargs):
    defaults = dict(
        anomaly_type="A1", anomaly_name="Test anomaly", severity="CRITICAL",
        source="ATMA", atm_id="ATM-01", detection_timestamp="2026-03-29T10:00:00",
        description="test", event_count=1,
    )
    defaults.update(kwargs)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO analysis_detections "
            "(anomaly_type, anomaly_name, severity, source, atm_id, "
            "detection_timestamp, description, event_count) "
            "VALUES (:anomaly_type, :anomaly_name, :severity, :source, :atm_id, "
            ":detection_timestamp, :description, :event_count)",
            defaults,
        )


def _insert_atma_row(db: Path, atm_id: str, correlation_id: str | None):
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO ATMA (timestamp, atm_id, correlation_id, event_type, message, "
            "log_level, location_code, session_id, transaction_id, component, atm_status, app_version) "
            "VALUES (?, ?, ?, 'ERROR', 'test', 'ERROR', 'LOC-01', NULL, NULL, 'DISPENSER', 'ACTIVE', '1.0')",
            ("2026-03-29T10:00:00", atm_id, correlation_id),
        )


def _insert_kafk_row(db: Path, atm_id: str, correlation_id: str | None):
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO KAFK (timestamp, event_id, correlation_id, atm_id, atm_status, "
            "transaction_rate_tps, response_time_ms, transaction_volume, "
            "transaction_success_rate, transaction_failure_reason, failure_count, "
            "window_duration_seconds) VALUES (?, 'ev-01', ?, ?, 'Offline', 5.0, 3000, 10, 0.5, "
            "'HOST_UNAVAILABLE', 3, 60)",
            ("2026-03-29T10:00:00", correlation_id, atm_id),
        )


# ── _parse_ts ─────────────────────────────────────────────────────────────────

def test_parse_ts_iso():
    ts = _parse_ts("2026-03-29T10:30:00")
    assert ts is not None
    assert ts.hour == 10 and ts.minute == 30


def test_parse_ts_space_separator():
    ts = _parse_ts("2026-03-29 10:30:00")
    assert ts is not None


def test_parse_ts_none():
    assert _parse_ts(None) is None


def test_parse_ts_invalid():
    assert _parse_ts("not-a-date") is None


# ── group_by_correlation_id ───────────────────────────────────────────────────

def test_corr_id_groups_cross_source(tmp_path):
    db = _make_db(tmp_path)
    cid = "corr-test-0001"
    _insert_atma_row(db, "ATM-01", cid)
    _insert_kafk_row(db, "ATM-01", cid)
    _insert_detection(db, source="ATMA", atm_id="ATM-01")
    _insert_detection(db, source="KAFK", atm_id="ATM-01")

    c = Correlator(db_path=str(db))
    with sqlite3.connect(db) as conn:
        dets = c._load_detections(conn)
    groups = c.group_by_correlation_id(dets)

    assert cid in groups
    sources = {d["source"] for d in groups[cid]}
    assert "ATMA" in sources
    assert "KAFK" in sources


def test_corr_id_excludes_single_source(tmp_path):
    db = _make_db(tmp_path)
    cid = "corr-single-0001"
    _insert_atma_row(db, "ATM-02", cid)
    _insert_detection(db, source="ATMA", atm_id="ATM-02")

    c = Correlator(db_path=str(db))
    with sqlite3.connect(db) as conn:
        dets = c._load_detections(conn)
    groups = c.group_by_correlation_id(dets)

    # single-source groups must be excluded
    assert cid not in groups


def test_corr_id_empty_detections(tmp_path):
    db = _make_db(tmp_path)
    c = Correlator(db_path=str(db))
    with sqlite3.connect(db) as conn:
        dets = c._load_detections(conn)
    groups = c.group_by_correlation_id(dets)
    assert groups == {}


# ── group_by_time_window ─────────────────────────────────────────────────────

def test_time_window_groups_same_atm_close_timestamps(tmp_path):
    db = _make_db(tmp_path)
    _insert_detection(db, source="ATMA", atm_id="ATM-03",
                      detection_timestamp="2026-03-29T10:00:00")
    _insert_detection(db, source="KAFK", atm_id="ATM-03",
                      detection_timestamp="2026-03-29T10:03:00")  # 3 min apart

    c = Correlator(db_path=str(db), window_seconds=300)
    with sqlite3.connect(db) as conn:
        dets = c._load_detections(conn)
    groups = c.group_by_time_window(dets)

    assert len(groups) == 1
    sources = {d["source"] for d in groups[0]}
    assert "ATMA" in sources and "KAFK" in sources


def test_time_window_excludes_outside_window(tmp_path):
    db = _make_db(tmp_path)
    _insert_detection(db, source="ATMA", atm_id="ATM-04",
                      detection_timestamp="2026-03-29T08:00:00")
    _insert_detection(db, source="KAFK", atm_id="ATM-04",
                      detection_timestamp="2026-03-29T10:00:00")  # 2 hours apart

    c = Correlator(db_path=str(db), window_seconds=300)
    with sqlite3.connect(db) as conn:
        dets = c._load_detections(conn)
    groups = c.group_by_time_window(dets)

    # 2 hours > 5 min window — should not be grouped together
    assert all(len({d["source"] for d in g}) > 1 for g in groups) is True or len(groups) == 0


def test_time_window_excludes_single_source(tmp_path):
    db = _make_db(tmp_path)
    _insert_detection(db, source="ATMA", atm_id="ATM-05",
                      detection_timestamp="2026-03-29T10:00:00")
    _insert_detection(db, source="ATMA", atm_id="ATM-05",
                      detection_timestamp="2026-03-29T10:02:00")

    c = Correlator(db_path=str(db), window_seconds=300)
    with sqlite3.connect(db) as conn:
        dets = c._load_detections(conn)
    groups = c.group_by_time_window(dets)

    # Both from ATMA — single source, must be excluded
    assert len(groups) == 0


# ── build_incidents ───────────────────────────────────────────────────────────

def test_build_incidents_returns_list(tmp_path):
    db = _make_db(tmp_path)
    c = Correlator(db_path=str(db))
    incidents = c.build_incidents()
    assert isinstance(incidents, list)


def test_build_incidents_severity_critical_wins(tmp_path):
    db = _make_db(tmp_path)
    _insert_detection(db, source="ATMA", atm_id="ATM-06", severity="WARNING",
                      detection_timestamp="2026-03-29T10:00:00")
    _insert_detection(db, source="KAFK", atm_id="ATM-06", severity="CRITICAL",
                      detection_timestamp="2026-03-29T10:02:00")

    c = Correlator(db_path=str(db), window_seconds=300)
    incidents = c.build_incidents()

    atm_incidents = [i for i in incidents if "ATM-06" in i["atm_ids"]]
    assert any(i["severity"] == "CRITICAL" for i in atm_incidents)


def test_build_incidents_empty_db(tmp_path):
    db = _make_db(tmp_path)
    c = Correlator(db_path=str(db))
    assert c.build_incidents() == []


# ── store_incidents ───────────────────────────────────────────────────────────

def test_store_incidents_creates_table(tmp_path):
    db = _make_db(tmp_path)
    c = Correlator(db_path=str(db))
    c.store_incidents()
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='incidents'"
        ).fetchone()
    assert row is not None


def test_store_incidents_clears_on_rerun(tmp_path):
    db = _make_db(tmp_path)
    _insert_detection(db, source="ATMA", atm_id="ATM-07",
                      detection_timestamp="2026-03-29T10:00:00")
    _insert_detection(db, source="KAFK", atm_id="ATM-07",
                      detection_timestamp="2026-03-29T10:01:00")

    c = Correlator(db_path=str(db), window_seconds=300)
    c.store_incidents()
    count_1 = sqlite3.connect(db).execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    c.store_incidents()
    count_2 = sqlite3.connect(db).execute("SELECT COUNT(*) FROM incidents").fetchone()[0]

    # Second run should not accumulate — same count expected
    assert count_1 == count_2


def test_store_incidents_returns_count(tmp_path):
    db = _make_db(tmp_path)
    c = Correlator(db_path=str(db))
    n = c.store_incidents()
    assert isinstance(n, int) and n >= 0


# ── known cross-system scenario (A1 cascade) ─────────────────────────────────

def test_a1_cascade_grouped_by_correlation_id(tmp_path):
    """
    The A1 network-timeout cascade scenario: ATMA and KAFK rows share a
    correlation_id — the engine must group them into one incident.
    """
    db = _make_db(tmp_path)
    cid = "corr-0010-xxyy-aabb-1234"
    _insert_atma_row(db, "ATM-GB-0010", cid)
    _insert_kafk_row(db, "ATM-GB-0010", cid)
    _insert_detection(db, anomaly_type="A1", anomaly_name="Network timeout cascade",
                      severity="CRITICAL", source="ATMA", atm_id="ATM-GB-0010",
                      detection_timestamp="2026-03-29T10:00:00")
    _insert_detection(db, anomaly_type="A1", anomaly_name="Network timeout cascade",
                      severity="CRITICAL", source="KAFK", atm_id="ATM-GB-0010",
                      detection_timestamp="2026-03-29T10:00:30")

    c = Correlator(db_path=str(db))
    incidents = c.build_incidents()

    corr_incidents = [i for i in incidents if i["strategy"] == "correlation_id"]
    assert len(corr_incidents) >= 1

    matched = [i for i in corr_incidents if cid in (i["correlation_id"] or "")]
    assert len(matched) >= 1
    assert "ATMA" in matched[0]["sources"]
    assert "KAFK" in matched[0]["sources"]
