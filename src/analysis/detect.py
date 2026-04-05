from __future__ import annotations

import sqlite3
from collections import defaultdict

from src.analysis.analyse_data import AnalyseData


class Detection:
    """
    Detection class responsible for:
    1. Running anomaly detection checks via AnalyseData
    2. Aggregating and summarising results
    3. Storing detections into a SQLite database
    4. Providing simple processors for printing/logging detections
    """

    def __init__(self, db_path: str = "data/clean/atm_logs.db"):
        # Path to SQLite database
        self.db_path = db_path

        # Instance of analysis engine that performs raw anomaly detection
        self.analyse_data = AnalyseData(db_path=db_path)

    def store_detections(self) -> None:
        """
        Runs all detection checks, summarises results, and stores them
        into the `analysis_detections` table.
        """

        def _summarise(detections, anomaly_type, anomaly_name, severity, desc_fn):
            """
            Groups detections by (source, atm_id) and aggregates:
            - count of events
            - first timestamp
            - latest description

            Returns list of rows ready for DB insertion.
            """
            groups = defaultdict(lambda: {"count": 0, "timestamp": None, "desc": ""})

            for d in detections:
                # Group by source and ATM ID
                key = (d.get("source", "UNKNOWN"), d.get("atm_id") or "N/A")

                groups[key]["count"] += 1

                # Store first timestamp seen
                if groups[key]["timestamp"] is None:
                    groups[key]["timestamp"] = d.get("timestamp")

                # Generate description using provided function
                groups[key]["desc"] = desc_fn(d)

            # Convert grouped data into DB row format
            return [
                (
                    anomaly_type,
                    anomaly_name,
                    severity,
                    src,
                    atm_id,
                    info["timestamp"],
                    info["desc"],
                    info["count"],
                )
                for (src, atm_id), info in groups.items()
            ]

        rows = []

        # ---------------------------
        # A1: Network timeout cascade
        # ---------------------------
        rows += _summarise(
            self.analyse_data.check_network_errors(),
            "A1",
            "Network timeout cascade",
            "CRITICAL",
            lambda d: (
                f"Host unavailable: {d.get('transaction_failure_reason')}"
                if d.get("source") == "KAFK"
                else f"Disconnect/timeout: {d.get('error_code')} — {(d.get('error_detail') or '')[:80]}"
                if d.get("source") == "ATMA"
                else f"Network timeout: {(d.get('message') or '')[:80]}"
            ),
        )

        # ---------------------------
        # A2: Cash cassette depletion
        # ---------------------------
        rows += _summarise(
            self.analyse_data.check_cash_cassette_depletion(),
            "A2",
            "Cash cassette depletion",
            "CRITICAL",
            lambda d: (
                f"Cassette {d.get('event_type')} ({d.get('severity')})"
                if d.get("source") == "ATMH"
                else f"Transaction failure: {d.get('transaction_failure_reason')}"
            ),
        )

        # ---------------------------
        # A4: Container restart loop
        # ---------------------------
        rows += _summarise(
            self.analyse_data.check_container_restarts(),
            "A4",
            "Container restart loop",
            "WARNING",
            lambda d: (
                f"Container restarted {d.get('restart_count')}x"
                if d.get("source") == "GCP"
                else f"Service {d.get('event_type') or 'OOM'}: {(d.get('exception_class') or d.get('message') or '')[:80]}"
            ),
        )

        # ---------------------------
        # A5: Performance degradation
        # ---------------------------
        rows += _summarise(
            self.analyse_data.check_performance_degradation(),
            "A5",
            "Performance degradation",
            "WARNING",
            lambda d: (
                f"Resp {d.get('response_time_ms')}ms, "
                f"success {d.get('transaction_success_rate')}%, "
                f"failures {d.get('failure_count')}"
            ),
        )

        # ---------------------------
        # A6: OS memory pressure
        # ---------------------------
        rows += _summarise(
            self.analyse_data.check_windows_os_metrics(),
            "A6",
            "OS memory pressure",
            "WARNING",
            lambda d: (
                f"Mem {d.get('memory_usage_percent')}%, "
                f"CPU {d.get('cpu_usage_percent')}%, "
                f"net errors {d.get('network_errors')}"
            ),
        )

        # ---------------------------
        # A7: Kafka anomalies
        # ---------------------------
        rows += _summarise(
            self.analyse_data.check_kafka_events(),
            "A7",
            "Out-of-order / malformed Kafka event",
            "WARNING",
            lambda d: f"Offset {d.get('kafka_offset')} ordering or integrity issue",
        )

        # ---------------------------
        # Database operations
        # ---------------------------
        with sqlite3.connect(self.db_path) as conn:

            # Create table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    anomaly_type TEXT NOT NULL,
                    anomaly_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    atm_id TEXT,
                    detection_timestamp TEXT,
                    description TEXT,
                    event_count INTEGER DEFAULT 1,
                    discovery_method TEXT NOT NULL DEFAULT 'static',
                    detected_at TEXT DEFAULT (datetime('now'))
                )
            """)

            # Handle schema migration (older tables without discovery_method)
            existing_cols = [
                row[1] for row in conn.execute("PRAGMA table_info(analysis_detections)").fetchall()
            ]
            if "discovery_method" not in existing_cols:
                conn.execute(
                    "ALTER TABLE analysis_detections ADD COLUMN discovery_method TEXT NOT NULL DEFAULT 'static'"
                )

            # Clear previous detections (full refresh)
            conn.execute("DELETE FROM analysis_detections")

            # Insert new detection rows
            conn.executemany("""
                INSERT INTO analysis_detections
                    (anomaly_type, anomaly_name, severity, source, atm_id,
                     detection_timestamp, description, event_count, discovery_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'static')
            """, rows)

            conn.commit()

        print(f"[INFO] Analysis complete: {len(rows)} detection groups written to analysis_detections.")

    # ------------------------------------------------------------------
    # Below: Processing functions (mainly for logging / debugging output)
    # ------------------------------------------------------------------

    def process_network_detections(self, detections):
        """Prints network-related anomalies (A1)."""
        for detection in detections:
            source = detection.get('source')
            atm_id = detection.get('atm_id')

            if source == 'KAFK':
                print(f"A1 Network anomaly detected from {source} at {detection.get('timestamp')}. "
                      f"Details: {atm_id} - {detection.get('transaction_failure_reason')}")

            elif source == 'ATMA':
                print(f"Network anomaly detected from {source} at {detection.get('timestamp')}. "
                      f"Details: {atm_id} - {detection.get('error_code')} - {detection.get('error_detail')}")

            elif source == 'TERM':
                print(f"A1 Network anomaly detected from {source} at {detection.get('timestamp')}. "
                      f"Details: {atm_id} - {detection.get('message')}")

        return True

    def process_cassette_detections(self, detections):
        """Prints cash cassette depletion anomalies (A2)."""
        for detection in detections:
            source = detection.get('source')
            atm_id = detection.get('atm_id')

            if source == 'KAFK':
                print(f"A2 Cash cassette depletion anomaly detected from {source} at {detection.get('timestamp')}. "
                      f"Details: {atm_id} - {detection.get('transaction_failure_reason')}")

            elif source == 'ATMH':
                print(f"A2 Cash cassette depletion anomaly detected from {source} at {detection.get('timestamp')}. "
                      f"Details: {atm_id} - {detection.get('severity')} - {detection.get('message')}")

        return True

    def process_memory_leak_detections(self, detections):
        """
        Placeholder for A3 (Memory leak detection).
        Currently not implemented.
        """
        pass

    def process_container_restart_detections(self, detections):
        """Prints container restart anomalies (A4)."""
        for detection in detections:
            if detection.get('source') == 'TERM':
                print(f"A4 Container restart anomaly detected from TERM at {detection.get('timestamp')}. "
                      f"Details: {detection.get('atm_id')} - {detection.get('message')}")
        return True

    def process_performance_degradation_detections(self, detections):
        """Prints performance degradation anomalies (A5)."""
        for detection in detections:
            if detection.get('source') == 'KAFK':
                print(f"A5 Performance degradation anomaly detected from KAFK at {detection.get('timestamp')}. "
                      f"Details: {detection.get('atm_id')} - {detection.get('transaction_failure_reason')}")
        return True

    def process_windows_os_metrics_detections(self, detections):
        """Prints OS-level anomalies (A6)."""
        for detection in detections:
            if detection.get('source') == 'WINOS':
                print(f"A6 Windows OS metrics anomaly detected from WINOS at {detection.get('timestamp')}. "
                      f"Details: {detection.get('atm_id')} - "
                      f"CPU: {detection.get('cpu_usage_percent')}%, "
                      f"Memory: {detection.get('memory_usage_percent')}%, "
                      f"Network: {detection.get('network_errors')}")
        return True

    def process_kafka_events_detections(self, detections):
        """Prints Kafka-related anomalies (A7)."""
        for detection in detections:
            if detection.get('source') == 'KAFK':
                print(f"A7 Kafka event anomaly detected from KAFK at {detection.get('timestamp')}. "
                      f"Details: {detection.get('atm_id')} - {detection.get('event_details')}")
        return True