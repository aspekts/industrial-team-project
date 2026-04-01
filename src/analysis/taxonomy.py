from __future__ import annotations

import sqlite3

# A1-A7 known static anomaly taxonomy entries (A3 is excluded — memory-leak
# detection is disabled pending a volume management solution).
STATIC_TAXONOMY: list[dict] = [
    {
        "anomaly_type": "A1",
        "anomaly_name": "Network timeout cascade",
        "severity": "CRITICAL",
        "source": "KAFK,ATMA,TERM",
        "discovery_method": "static",
        "description": (
            "ATM goes offline or times out across multiple sources: "
            "HOST_UNAVAILABLE in Kafka, NETWORK_DISCONNECT/TIMEOUT in ATM app log, "
            "NETWORK_TIMEOUT in terminal handler."
        ),
    },
    {
        "anomaly_type": "A2",
        "anomaly_name": "Cash cassette depletion",
        "severity": "CRITICAL",
        "source": "ATMH,KAFK",
        "discovery_method": "static",
        "description": (
            "Cash dispenser reports CASSETTE_LOW or CASSETTE_EMPTY in hardware log; "
            "corroborated by CASH_DISPENSE_ERROR or zero transaction rate in Kafka."
        ),
    },
    {
        "anomaly_type": "A4",
        "anomaly_name": "Container restart loop",
        "severity": "WARNING",
        "source": "GCP,TERM",
        "discovery_method": "static",
        "description": (
            "Container restart_count > 0 in GCP metrics; "
            "STARTUP events or OutOfMemoryError in terminal handler log."
        ),
    },
    {
        "anomaly_type": "A5",
        "anomaly_name": "Performance degradation",
        "severity": "WARNING",
        "source": "KAFK",
        "discovery_method": "static",
        "description": (
            "Kafka metrics show elevated response_time_ms, "
            "depressed transaction_success_rate, or rising failure_count."
        ),
    },
    {
        "anomaly_type": "A6",
        "anomaly_name": "OS memory pressure",
        "severity": "WARNING",
        "source": "WINOS",
        "discovery_method": "static",
        "description": (
            "Windows OS metrics show memory_usage_percent > 90%, "
            "cpu_usage_percent > 90%, or network_errors > 20."
        ),
    },
    {
        "anomaly_type": "A7",
        "anomaly_name": "Out-of-order / malformed Kafka event",
        "severity": "WARNING",
        "source": "KAFK",
        "discovery_method": "static",
        "description": (
            "Kafka stream contains out-of-order timestamps (offset N arrives "
            "before N-1) or rows with null required fields."
        ),
    },
]


class AnomalyTaxonomy:
    """Manages the anomaly_taxonomy table — static A1-A7 entries and
    dynamically registered entries discovered at runtime (e.g. by ML)."""

    TABLE_DDL = """
        CREATE TABLE IF NOT EXISTS anomaly_taxonomy (
            anomaly_type     TEXT PRIMARY KEY,
            anomaly_name     TEXT NOT NULL,
            severity         TEXT NOT NULL,
            source           TEXT NOT NULL,
            discovery_method TEXT NOT NULL CHECK(discovery_method IN ('static', 'dynamic')),
            description      TEXT,
            registered_at    TEXT DEFAULT (datetime('now'))
        )
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def setup(self) -> None:
        """Create the taxonomy table if it does not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(self.TABLE_DDL)

    def seed_static(self) -> None:
        """Insert or replace all static A1-A7 taxonomy entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(self.TABLE_DDL)
            conn.executemany(
                """
                INSERT OR REPLACE INTO anomaly_taxonomy
                    (anomaly_type, anomaly_name, severity, source,
                     discovery_method, description)
                VALUES (:anomaly_type, :anomaly_name, :severity, :source,
                        :discovery_method, :description)
                """,
                STATIC_TAXONOMY,
            )
        print(f"[INFO] Taxonomy: {len(STATIC_TAXONOMY)} static entries seeded.")

    def register_dynamic(
        self,
        anomaly_type: str,
        anomaly_name: str,
        severity: str,
        source: str,
        description: str = "",
    ) -> None:
        """Register a newly discovered anomaly class (discovery_method='dynamic').
        Uses INSERT OR IGNORE so re-runs do not overwrite an existing entry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(self.TABLE_DDL)
            conn.execute(
                """
                INSERT OR IGNORE INTO anomaly_taxonomy
                    (anomaly_type, anomaly_name, severity, source,
                     discovery_method, description)
                VALUES (?, ?, ?, ?, 'dynamic', ?)
                """,
                (anomaly_type, anomaly_name, severity, source, description),
            )

    def get_all(self) -> list[dict]:
        """Return all taxonomy entries as a list of dicts."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM anomaly_taxonomy ORDER BY discovery_method, anomaly_type"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_by_method(self, discovery_method: str) -> list[dict]:
        """Return taxonomy entries filtered by discovery_method."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM anomaly_taxonomy WHERE discovery_method = ? "
                "ORDER BY anomaly_type",
                (discovery_method,),
            ).fetchall()
        return [dict(r) for r in rows]
