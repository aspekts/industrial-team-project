"""
Live Agent — streaming log generation for the ATM Operations Hub.

Runs as a background thread, inserting synthetic ATM log entries directly
into atm_logs.db at a configurable interval.  After each batch it re-runs
rules-based detection and cross-source correlation so the dashboard
reflects new data without a full pipeline restart.

Anomaly injection: call inject_anomaly(anomaly_type) to schedule
anomaly-indicative records for the next few ticks.

Supported injection types: A1, A2, A4, A5, A6, A7
"""

from __future__ import annotations

import random
import sqlite3
import threading
import time
from datetime import datetime, timezone
from uuid import uuid4


ATMS = [
    {"id": "ATM-GB-0001", "location": "LOC-0101", "host": "ATM-HOST-0001"},
    {"id": "ATM-GB-0002", "location": "LOC-0202", "host": "ATM-HOST-0002"},
    {"id": "ATM-GB-0003", "location": "LOC-0303", "host": "ATM-HOST-0003"},
    {"id": "ATM-GB-0004", "location": "LOC-0404", "host": "ATM-HOST-0004"},
    {"id": "ATM-GB-0005", "location": "LOC-0505", "host": "ATM-HOST-0005"},
    {"id": "ATM-GB-0006", "location": "LOC-0606", "host": "ATM-HOST-0006"},
]

APP_VERSION = "3.4.1-build.209"
SVC_VERSION = "2.7.0-SNAPSHOT"


class LiveAgent:
    """Background agent that generates synthetic ATM log entries on a timer."""

    SUPPORTED_INJECTIONS = {"A1", "A2", "A4", "A5", "A6", "A7"}

    def __init__(self, db_path: str, interval_seconds: int = 10) -> None:
        self.db_path = db_path
        self.interval_seconds = max(1, int(interval_seconds))
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        self.events_generated: int = 0
        self.last_event_ts: str | None = None
        self.current_injection: str | None = None
        self._injection_ticks_remaining: int = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> bool:
        """Start the agent. Returns False if already running."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            return True

    def stop(self) -> None:
        """Signal the agent to stop after the current tick completes."""
        self._stop_event.set()

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def inject_anomaly(self, anomaly_type: str, ticks: int = 3) -> bool:
        """Schedule anomaly injection for the next N ticks.
        Returns False for unsupported types."""
        if anomaly_type not in self.SUPPORTED_INJECTIONS:
            return False
        with self._lock:
            self.current_injection = anomaly_type
            self._injection_ticks_remaining = ticks
        return True

    def status(self) -> dict:
        return {
            "running": self.running,
            "events_generated": self.events_generated,
            "last_event_ts": self.last_event_ts,
            "current_injection": self.current_injection,
            "interval_seconds": self.interval_seconds,
        }

    # ── Private loop ──────────────────────────────────────────────────────────

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as exc:
                print(f"[LiveAgent] tick error: {exc}")
            self._stop_event.wait(self.interval_seconds)

    def _tick(self) -> None:
        ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

        with self._lock:
            injection = self.current_injection
            if self._injection_ticks_remaining > 0:
                self._injection_ticks_remaining -= 1
                if self._injection_ticks_remaining == 0:
                    self.current_injection = None

        atm = random.choice(ATMS)
        corr_id = str(uuid4())

        with sqlite3.connect(self.db_path) as conn:
            count = 0
            count += self._write_atma(conn, ts, atm, corr_id, injection)
            count += self._write_kafk(conn, ts, atm, corr_id, injection)
            count += self._write_atmh(conn, ts, atm, corr_id, injection)

            if injection in ("A4",):
                count += self._write_gcp(conn, ts, atm, corr_id, injection)
                count += self._write_term(conn, ts, atm, corr_id, injection)
            elif injection in ("A1",):
                count += self._write_term(conn, ts, atm, corr_id, injection)

            if injection == "A6":
                count += self._write_winos(conn, ts, atm, anomalous=True)
            else:
                count += self._write_winos(conn, ts, atm, anomalous=False)

        self.events_generated += count
        self.last_event_ts = ts

        # Re-run rules detection and incident correlation on the updated data
        try:
            from src.analysis.detect import Detection
            from src.analysis.correlate import Correlator
            Detection(db_path=self.db_path).store_detections()
            Correlator(db_path=self.db_path).store_incidents()
        except Exception as exc:
            print(f"[LiveAgent] detection re-run failed: {exc}")

    # ── Record builders ───────────────────────────────────────────────────────

    def _write_atma(self, conn, ts: str, atm: dict, corr_id: str, injection: str | None) -> int:
        if injection == "A1":
            event_type = random.choice(["NETWORK_DISCONNECT", "TIMEOUT"])
            error_code = "ERR-0040"
            response_time_ms = 30000
            message = "Network timeout cascade — host unreachable"
            atm_status = "Offline"
        else:
            event_type = random.choice(["TRANSACTION", "STATUS", "INFO"])
            error_code = None
            response_time_ms = random.randint(100, 800)
            message = "ATM operational event"
            atm_status = "In Service"

        conn.execute(
            """
            INSERT INTO ATMA (
                timestamp, log_level, atm_id, location_code,
                session_id, correlation_id, transaction_id, event_type,
                message, component, thread_id, response_time_ms, error_code,
                error_detail, atm_status, os_version, app_version, _anomaly
            ) VALUES (?, 'INFO', ?, ?, ?, ?, ?, ?, ?, 'NETWORK', ?, ?, ?, NULL, ?, NULL, ?, ?)
            """,
            (
                ts, atm["id"], atm["location"],
                str(uuid4()), corr_id, str(uuid4()),
                event_type, message,
                random.randint(1, 100), response_time_ms, error_code,
                atm_status, APP_VERSION,
                injection,
            ),
        )
        return 1

    def _write_kafk(self, conn, ts: str, atm: dict, corr_id: str, injection: str | None) -> int:
        if injection == "A1":
            atm_status = "Offline"
            failure_reason = "HOST_UNAVAILABLE"
            failure_count = random.randint(1, 5)
            response_time_ms = 30000
            tps = 0.0
            success_rate = 0.0
        elif injection == "A2":
            atm_status = "Out of Service"
            failure_reason = "CASH_DISPENSE_ERROR"
            failure_count = random.randint(1, 3)
            response_time_ms = random.randint(200, 400)
            tps = 0.0
            success_rate = 0.0
        elif injection == "A5":
            atm_status = "In Service"
            failure_reason = "TIMEOUT"
            failure_count = random.randint(3, 10)
            response_time_ms = random.randint(5000, 12000)
            tps = round(random.uniform(0.1, 0.5), 2)
            success_rate = round(random.uniform(0.1, 0.4), 2)
        elif injection == "A7":
            # Malformed: null required fields trigger the Kafka event check
            atm_status = None
            failure_reason = None
            failure_count = 0
            response_time_ms = random.randint(100, 600)
            tps = None
            success_rate = round(random.uniform(0.95, 1.0), 2)
        else:
            atm_status = "In Service"
            failure_reason = None
            failure_count = 0
            response_time_ms = random.randint(100, 600)
            tps = round(random.uniform(1.5, 4.0), 2)
            success_rate = round(random.uniform(0.95, 1.0), 2)

        row = conn.execute("SELECT MAX(kafka_offset) FROM KAFK").fetchone()
        max_offset = row[0] if row and row[0] is not None else 0

        conn.execute(
            """
            INSERT INTO KAFK (
                timestamp, event_id, correlation_id, atm_id,
                atm_status, transaction_rate_tps, response_time_ms,
                transaction_volume, transaction_success_rate,
                transaction_failure_reason, failure_count,
                window_duration_seconds, kafka_partition, kafka_offset, _anomaly
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 60, ?, ?, ?)
            """,
            (
                ts, str(uuid4()), corr_id, atm["id"],
                atm_status, tps, response_time_ms,
                random.randint(5, 50), success_rate,
                failure_reason, failure_count,
                random.randint(0, 3), max_offset + 1,
                injection,
            ),
        )
        return 1

    def _write_atmh(self, conn, ts: str, atm: dict, corr_id: str, injection: str | None) -> int:
        if injection == "A2":
            component = "CASH_DISPENSER"
            event_type = random.choice(["CASSETTE_LOW", "CASSETTE_EMPTY"])
            severity = "CRITICAL" if event_type == "CASSETTE_EMPTY" else "WARNING"
            message = f"Cash cassette {event_type.replace('_', ' ').lower()}"
            metric_value = 0
        else:
            component = random.choice(["CARD_READER", "RECEIPT_PRINTER", "KEYPAD", "DISPLAY"])
            event_type = "STATUS_OK"
            severity = "INFO"
            message = "Hardware sensor nominal"
            metric_value = random.randint(20, 80)

        conn.execute(
            """
            INSERT INTO ATMH (
                timestamp, atm_id, correlation_id, component,
                event_type, severity, message, metric_name, metric_value,
                metric_unit, threshold_value, firmware_version, _anomaly
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'cassette_level', ?, 'percent', 20, NULL, ?)
            """,
            (ts, atm["id"], corr_id, component, event_type, severity, message, metric_value, injection),
        )
        return 1

    def _write_term(self, conn, ts: str, atm: dict, corr_id: str, injection: str | None) -> int:
        if injection == "A1":
            event_type = "NETWORK_TIMEOUT"
            log_level = "ERROR"
            message = "Network timeout cascade on terminal handler"
            exception_class = None
            atm_id = atm["id"]
        elif injection == "A4":
            event_type = "STARTUP"
            log_level = "WARN"
            message = "Container restart detected — unexpected STARTUP event"
            exception_class = "OutOfMemoryError"
            atm_id = None
        else:
            event_type = "REQUEST"
            log_level = "INFO"
            message = "Terminal handler request processed"
            exception_class = None
            atm_id = atm["id"]

        conn.execute(
            """
            INSERT INTO TERM (
                timestamp, log_level, service_name, service_version,
                container_id, pod_name, correlation_id, transaction_id, atm_id,
                event_type, message, logger_name, thread_name, response_time_ms,
                http_status_code, exception_class, exception_message,
                db_query_time_ms, environment, _anomaly
            ) VALUES (?, ?, 'terminal-handler', ?, ?, NULL, ?, ?, ?, ?, ?, NULL, NULL,
                      NULL, 200, ?, NULL, NULL, 'production', ?)
            """,
            (
                ts, log_level, SVC_VERSION,
                str(uuid4())[:12], corr_id, str(uuid4()),
                atm_id, event_type, message,
                exception_class, injection,
            ),
        )
        return 1

    def _write_winos(self, conn, ts: str, atm: dict, anomalous: bool) -> int:
        if anomalous:
            cpu = round(random.uniform(91.0, 99.0), 1)
            mem_used = random.randint(14000, 15800)
            net_errors = random.randint(22, 60)
        else:
            cpu = round(random.uniform(20.0, 60.0), 1)
            mem_used = random.randint(4000, 8000)
            net_errors = 0

        mem_total = 16000
        mem_pct = round(mem_used / mem_total * 100, 1)

        conn.execute(
            """
            INSERT INTO WINOS (
                timestamp, atm_id, hostname, os_version,
                cpu_usage_percent, memory_used_mb, memory_total_mb,
                memory_usage_percent, disk_read_bytes_per_sec,
                disk_write_bytes_per_sec, disk_free_gb,
                network_bytes_sent_per_sec, network_bytes_recv_per_sec,
                network_errors, process_count, system_uptime_seconds,
                event_log_errors_last_min, _anomaly
            ) VALUES (?, ?, ?, 'Windows 10 LTSB 2016',
                      ?, ?, ?, ?, NULL, NULL, ?,
                      NULL, NULL, ?, ?, ?, 0, ?)
            """,
            (
                ts, atm["id"], atm["host"],
                cpu, mem_used, mem_total, mem_pct,
                round(random.uniform(10.0, 50.0), 1),
                net_errors,
                random.randint(50, 200),
                random.randint(100_000, 300_000),
                "A6" if anomalous else None,
            ),
        )
        return 1

    def _write_gcp(self, conn, ts: str, atm: dict, corr_id: str, injection: str | None) -> int:
        restart_count = random.randint(1, 5) if injection == "A4" else 0
        cpu_pct = round(random.uniform(70.0, 90.0), 1) if injection == "A4" else round(random.uniform(20.0, 50.0), 1)

        conn.execute(
            """
            INSERT INTO GCP (
                timestamp, project_id, resource_type, resource_id,
                zone, metric_name, metric_value, metric_unit,
                cpu_usage_percent, memory_usage_bytes, memory_limit_bytes,
                network_ingress_bytes, network_egress_bytes, restart_count,
                label_app, label_env, label_version, _anomaly
            ) VALUES (
                ?, 'synth-banking-sim-001', 'k8s_container', ?,
                'europe-west2-b', 'container/cpu/usage_time', ?, 'seconds',
                ?, NULL, NULL, NULL, NULL, ?,
                'terminal-handler', 'production', ?, ?
            )
            """,
            (ts, str(uuid4())[:20], cpu_pct, cpu_pct, restart_count, SVC_VERSION, injection),
        )
        return 1
