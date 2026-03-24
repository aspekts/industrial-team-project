"""
Isolation Forest ML Anomaly Detection Tests
Covers acceptance criteria from issue #11.
"""
import sqlite3

import numpy as np
import pandas as pd
import pytest

from src.ml.features import FeatureExtractor
from src.ml.model import AnomalyDetector
from src.ml.scorer import AnomalyScorer


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_features():
    """100-row numeric DataFrame simulating KAFK-style features, no nulls."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "transaction_rate_tps": rng.uniform(0, 100, 100),
        "response_time_ms": rng.integers(10, 5000, 100).astype(float),
        "transaction_success_rate": rng.uniform(50, 100, 100),
        "failure_count": rng.integers(0, 50, 100).astype(float),
    })


@pytest.fixture
def db_with_data(tmp_path):
    """Temp SQLite DB with all four metric tables populated, including nulls."""
    db_path = str(tmp_path / "test_atm_logs.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    rng = np.random.default_rng(42)

    # KAFK
    cursor.execute("""
        CREATE TABLE KAFK (
            timestamp TEXT, atm_id TEXT,
            transaction_rate_tps REAL, response_time_ms INTEGER,
            transaction_success_rate REAL, failure_count INTEGER
        )
    """)
    kafk_rows = [
        (
            f"2026-03-05T{h:02d}:00:00Z", "ATM-GB-0001",
            float(rng.uniform(0, 100)), int(rng.integers(10, 2000)),
            float(rng.uniform(50, 100)), int(rng.integers(0, 20)),
        )
        for h in range(50)
    ]
    # Inject a null to verify fillna logic
    kafk_rows[5] = (kafk_rows[5][0], kafk_rows[5][1], None, kafk_rows[5][3], kafk_rows[5][4], kafk_rows[5][5])
    cursor.executemany("INSERT INTO KAFK VALUES (?,?,?,?,?,?)", kafk_rows)

    # WINOS
    cursor.execute("""
        CREATE TABLE WINOS (
            timestamp TEXT, atm_id TEXT, hostname TEXT,
            cpu_usage_percent REAL, memory_usage_percent REAL,
            network_errors INTEGER, event_log_errors_last_min INTEGER
        )
    """)
    winos_rows = [
        (
            f"2026-03-05T{h:02d}:00:00Z", "ATM-GB-0001", "ATM-HOST-0001",
            float(rng.uniform(5, 90)), float(rng.uniform(20, 95)),
            int(rng.integers(0, 5)), int(rng.integers(0, 3)),
        )
        for h in range(50)
    ]
    cursor.executemany("INSERT INTO WINOS VALUES (?,?,?,?,?,?,?)", winos_rows)

    # GCP
    cursor.execute("""
        CREATE TABLE GCP (
            timestamp TEXT, cpu_usage_percent REAL,
            memory_usage_bytes INTEGER, restart_count INTEGER,
            network_ingress_bytes INTEGER
        )
    """)
    gcp_rows = [
        (
            f"2026-03-05T{h:02d}:00:00Z",
            float(rng.uniform(5, 80)), int(rng.integers(int(1e8), int(2e9))),
            int(rng.integers(0, 3)), int(rng.integers(int(1e6), int(1e8))),
        )
        for h in range(50)
    ]
    cursor.executemany("INSERT INTO GCP VALUES (?,?,?,?,?)", gcp_rows)

    # PROM — multiple rows per metric_name (realistic)
    cursor.execute("""
        CREATE TABLE PROM (
            timestamp TEXT, metric_name TEXT, metric_value REAL,
            pod_name TEXT, container_id TEXT
        )
    """)
    metric_names = ["jvm_memory_used_bytes", "jvm_gc_pause_seconds_sum", "process_cpu_usage"]
    prom_rows = [
        (
            f"2026-03-05T{h:02d}:00:00Z",
            metric_names[h % 3],
            float(rng.uniform(1e7, 1e9)),
            "pod-1", "abc123",
        )
        for h in range(51)  # 51 rows: 17 of each metric
    ]
    cursor.executemany("INSERT INTO PROM VALUES (?,?,?,?,?)", prom_rows)

    conn.commit()
    conn.close()
    return db_path


# ── Feature Extraction Tests ───────────────────────────────────────────────────

def test_feature_extraction_no_nulls(db_with_data):
    """get_all_features() must return a null-free DataFrame for each source."""
    extractor = FeatureExtractor(db_with_data)
    for source in ("KAFK", "WINOS", "GCP", "PROM"):
        df = extractor.get_all_features(source)
        null_count = df.isnull().sum().sum()
        assert null_count == 0, (
            f"Source {source} has {null_count} null(s) after fillna — check null handling in get_all_features"
        )


# ── Model Tests ────────────────────────────────────────────────────────────────

def test_model_trains_without_error(sample_features):
    """AnomalyDetector.train() must fit without raising and produce 100 estimators."""
    detector = AnomalyDetector()
    detector.train(sample_features)
    assert hasattr(detector.model, "estimators_"), \
        "Model missing estimators_ — train() did not fit the IsolationForest"
    assert len(detector.model.estimators_) == 100


def test_scores_are_floats(sample_features):
    """score() must return a float64 array with one value per input row."""
    detector = AnomalyDetector()
    detector.train(sample_features)
    scores = detector.score(sample_features)
    assert scores.dtype == np.float64, \
        f"Expected float64 anomaly scores, got {scores.dtype}"
    assert len(scores) == len(sample_features)


def test_anomaly_rate_in_range(sample_features):
    """predict() anomaly rate must sit between 2% and 15% on mixed normal/outlier data."""
    rng = np.random.default_rng(0)
    outliers = pd.DataFrame({
        "transaction_rate_tps": rng.uniform(1000, 5000, 10),
        "response_time_ms": rng.integers(50000, 100000, 10).astype(float),
        "transaction_success_rate": rng.uniform(0, 5, 10),
        "failure_count": rng.integers(500, 1000, 10).astype(float),
    })
    X = pd.concat([sample_features, outliers], ignore_index=True)

    detector = AnomalyDetector(contamination=0.05, random_state=42)
    detector.train(X)
    predictions = detector.predict(X)

    anomaly_rate = (predictions == -1).mean()
    assert 0.02 <= anomaly_rate <= 0.15, (
        f"Anomaly rate {anomaly_rate:.2%} is outside expected 2–15% range"
    )


# ── Scorer / Integration Tests ─────────────────────────────────────────────────

@pytest.fixture
def _clean_features():
    """Minimal clean feature DataFrame used by scorer integration tests."""
    rng = np.random.default_rng(1)
    return pd.DataFrame({
        "transaction_rate_tps": rng.uniform(0, 100, 50),
        "response_time_ms": rng.integers(10, 2000, 50).astype(float),
        "transaction_success_rate": rng.uniform(50, 100, 50),
        "failure_count": rng.integers(0, 20, 50).astype(float),
    })


def test_output_table_exists(db_with_data, monkeypatch, _clean_features):
    """ml_anomaly_scores table must exist in the DB after score_and_store_anomalies()."""
    monkeypatch.setattr(
        FeatureExtractor, "get_all_features",
        lambda self, source: _clean_features,
    )

    scorer = AnomalyScorer(db_with_data)
    scorer.score_and_store_anomalies()

    conn = sqlite3.connect(db_with_data)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ml_anomaly_scores'"
    )
    result = cursor.fetchone()
    conn.close()
    assert result is not None, "ml_anomaly_scores table was not created in the database"


def test_output_schema(db_with_data, monkeypatch, _clean_features):
    """ml_anomaly_scores must contain every column required by the output schema."""
    required_columns = {
        "source", "row_index", "timestamp", "atm_id",
        "anomaly_score", "is_anomaly", "model_version",
    }
    monkeypatch.setattr(
        FeatureExtractor, "get_all_features",
        lambda self, source: _clean_features,
    )

    scorer = AnomalyScorer(db_with_data)
    scorer.score_and_store_anomalies()

    conn = sqlite3.connect(db_with_data)
    df = pd.read_sql_query("SELECT * FROM ml_anomaly_scores LIMIT 1", conn)
    conn.close()

    missing = required_columns - set(df.columns)
    assert not missing, (
        f"ml_anomaly_scores is missing required columns: {missing}"
    )
