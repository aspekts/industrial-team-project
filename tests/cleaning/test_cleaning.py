import sqlite3

import pytest

from src.cleaning.data_cleaning import LogCleaner
from src.cleaning.database import DatabaseHandler
from src.cleaning.schemas import LOG_SCHEMAS


@pytest.fixture
def cleaner(tmp_path):
    raw_dir = tmp_path / "raw"
    clean_dir = tmp_path / "clean"
    db_path = clean_dir / "test_atm.db"

    raw_dir.mkdir()
    clean_dir.mkdir()

    db = DatabaseHandler(db_path=str(db_path))
    db.setup_database(LOG_SCHEMAS)
    return LogCleaner(db, str(raw_dir), str(clean_dir)), raw_dir, clean_dir, db_path


def test_find_schema(cleaner):
    log_cleaner, _, _, _ = cleaner

    fake_atma_log = {
        "timestamp": "2023-10-01",
        "log_level": "INFO",
        "atm_id": "ATM1",
        "location_code": "NY",
        "session_id": "123",
        "correlation_id": "456",
        "transaction_id": "789",
        "event_type": "TEST",
        "message": "hello",
        "component": "app",
        "thread_id": "1",
        "response_time_ms": "100",
        "error_code": "None",
        "error_detail": "None",
        "atm_status": "OK",
        "os_version": "1.0",
        "app_version": "2.0",
        "_anomaly": "None",
    }

    result = log_cleaner.find_schema(fake_atma_log)

    assert result == "ATMA"


def test_convert_types(cleaner):
    log_cleaner, _, _, _ = cleaner

    fake_prom_log = {
        "timestamp": "2023-10-01",
        "metric_name": "cpu_usage",
        "metric_type": "gauge",
        "metric_value": "99.5",
        "service_name": "atm-service",
        "pod_name": "pod-1",
        "container_id": "cont-1",
        "label_area": "None",
        "label_env": "dev",
        "help_text": "None",
        "_anomaly": "None",
    }

    clean_log = log_cleaner.convert_types(fake_prom_log, "PROM")

    assert clean_log["metric_value"] == 99.5
    assert clean_log["label_area"] is None


def test_broken_logs_are_saved(cleaner):
    log_cleaner, raw_dir, clean_dir, _ = cleaner
    error_file = clean_dir / "broken_logs.json"
    bad_file_path = raw_dir / "bad_log.txt"

    bad_file_path.write_text("AT1,time_offset\napple,2311-gb\n", encoding="utf-8")

    log_cleaner.process_all_files()

    assert error_file.exists()


def test_valid_log_loads_to_database(cleaner):
    log_cleaner, raw_dir, _, db_path = cleaner
    good_file_path = raw_dir / "good_log.txt"

    headers = (
        "timestamp,log_level,atm_id,location_code,session_id,correlation_id,"
        "transaction_id,event_type,message,component,thread_id,response_time_ms,"
        "error_code,error_detail,atm_status,os_version,app_version,_anomaly"
    )
    values = (
        "2026-03-05T08:00:00.000Z,INFO,ATM-GB-0001,LOC-0101,None,None,None,"
        "STARTUP,ATM client application started successfully.,BootManager,1,None,"
        "None,None,Online,Windows 10 LTSB 2016,3.4.1-build.209,None"
    )

    good_file_path.write_text(f"{headers}\n{values}\n", encoding="utf-8")

    log_cleaner.process_all_files()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ATMA WHERE atm_id = 'ATM-GB-0001'")
        rows = cursor.fetchall()

    expected_row = (
        "2026-03-05T08:00:00.000Z",
        "INFO",
        "ATM-GB-0001",
        "LOC-0101",
        None,
        None,
        None,
        "STARTUP",
        "ATM client application started successfully.",
        "BootManager",
        1,
        None,
        None,
        None,
        "Online",
        "Windows 10 LTSB 2016",
        "3.4.1-build.209",
        None,
    )

    assert len(rows) == 1
    assert rows[0] == expected_row
