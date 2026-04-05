import sqlite3
import configparser


class AnalyseData:
    """
    AnalyseData is responsible for querying raw ATM-related logs
    and identifying anomaly signals based on predefined rules.

    It uses:
    - SQLite database as the data source
    - config.ini for dynamic threshold configuration
    """

    def __init__(self, db_path="data/clean/atm_logs.db"):
        # Load configuration file (thresholds, limits, etc.)
        self.config = configparser.ConfigParser()
        self.config.read("src/analysis/config.ini")

        # Path to SQLite database
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Helper methods for reading config values
    # ------------------------------------------------------------------

    def _get_int(self, section, option):
        """Retrieve integer value from config file"""
        return self.config.getint(section, option)

    def _get_float(self, section, option):
        """Retrieve float value from config file"""
        return self.config.getfloat(section, option)

    # ------------------------------------------------------------------
    # A1: Network Errors Detection
    # ------------------------------------------------------------------

    def check_network_errors(self):
        """
        Detect network-related anomalies across multiple data sources:
        - ATMA (ATM application logs)
        - KAFK (Kafka metrics/events)
        - TERM (Terminal handler logs)
        """

        errors = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Enables dict-like access
            cursor = conn.cursor()

            # ---------------------------
            # ATMA signals
            # ---------------------------
            # 1. NETWORK_DISCONNECT with specific error code
            # 2. TIMEOUT events with response_time matching configured threshold
            timeout_value = self._get_int('NETWORK', 'timeout')

            cursor.execute(
                """
                SELECT 'ATMA' AS source, *
                FROM ATMA
                WHERE (event_type = 'NETWORK_DISCONNECT' AND error_code = 'ERR-0040')
                   OR (event_type = 'TIMEOUT' AND response_time_ms = ?)
                """,
                (timeout_value,)
            )
            errors.extend(dict(row) for row in cursor.fetchall())

            # ---------------------------
            # KAFK signals
            # ---------------------------
            # ATM offline due to host unavailability
            cursor.execute(
                """
                SELECT 'KAFK' AS source, *
                FROM KAFK
                WHERE atm_status = 'Offline'
                  AND transaction_failure_reason = 'HOST_UNAVAILABLE'
                """
            )
            errors.extend(dict(row) for row in cursor.fetchall())

            # ---------------------------
            # TERM signals
            # ---------------------------
            # Specific ATM experiencing network timeout
            cursor.execute(
                """
                SELECT 'TERM' AS source, *
                FROM TERM
                WHERE event_type = 'NETWORK_TIMEOUT'
                  AND atm_id = 'ATM-GB-0003'
                """
            )
            errors.extend(dict(row) for row in cursor.fetchall())

        return errors

    # ------------------------------------------------------------------
    # A2: Cash Cassette Depletion Detection
    # ------------------------------------------------------------------

    def check_cash_cassette_depletion(self):
        """
        Detect ATM cash depletion conditions using:
        - Hardware logs (ATMH)
        - Kafka transaction metrics
        """

        findings = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # ---------------------------
            # ATMH (hardware) signals
            # ---------------------------
            # Detect cassette low or empty states
            cursor.execute(
                """
                SELECT 'ATMH' AS source, *
                FROM ATMH
                WHERE component = 'CASH_DISPENSER'
                  AND ((event_type = 'CASSETTE_LOW' AND severity = 'WARNING')
                       OR (event_type = 'CASSETTE_EMPTY' AND severity = 'CRITICAL'))
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

            # ---------------------------
            # KAFK signals
            # ---------------------------
            # ATM out of service due to dispense error OR no transactions occurring
            cursor.execute(
                """
                SELECT 'KAFK' AS source, *
                FROM KAFK
                WHERE (atm_status = 'Out of Service' AND transaction_failure_reason = 'CASH_DISPENSE_ERROR')
                   OR (transaction_rate_tps = 0.0 AND transaction_success_rate = 0.0)
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings

    # ------------------------------------------------------------------
    # A3: Memory Leak Detection
    # ------------------------------------------------------------------

    def check_memory_leaks(self):
        """
        Detect potential memory leaks using:
        - Prometheus metrics (PROM)
        - GCP infrastructure metrics
        - Terminal logs (TERM)
        """

        findings = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # ---------------------------
            # PROM (Prometheus) signals
            # ---------------------------
            threshold_bytes = self._get_int('MEMORY', 'threshold_bytes')
            gc_pause_threshold = self._get_float('GC', 'gc_pause_threshold_seconds')
            cpu_threshold = self._get_float('CPU', 'threshold_usage')

            cursor.execute(
                """
                SELECT 'PROM' AS source, *
                FROM PROM
                WHERE (metric_name = 'jvm_memory_used_bytes' AND metric_value > ?)
                   OR (metric_name = 'jvm_gc_pause_seconds_sum' AND metric_value > ?)
                   OR (metric_name = 'process_cpu_usage' AND metric_value > ?)
                """,
                (threshold_bytes, gc_pause_threshold, cpu_threshold),
            )
            findings.extend(dict(row) for row in cursor.fetchall())

            # ---------------------------
            # GCP signals
            # ---------------------------
            # High CPU usage may indicate memory pressure or GC thrashing
            cpu_usage_threshold = cpu_threshold * 100

            cursor.execute(
                """
                SELECT 'GCP' AS source, *
                FROM GCP
                WHERE cpu_usage_percent > ?
                """,
                (cpu_usage_threshold,),
            )
            findings.extend(dict(row) for row in cursor.fetchall())

            # ---------------------------
            # TERM signals
            # ---------------------------
            # Fatal JVM memory errors
            cursor.execute(
                """
                SELECT 'TERM' AS source, *
                FROM TERM
                WHERE log_level = 'FATAL' AND exception_class = 'OutOfMemoryError'
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings

    # ------------------------------------------------------------------
    # A4: Container Restart Detection
    # ------------------------------------------------------------------

    def check_container_restarts(self):
        """
        Detect container restart loops using:
        - GCP restart counts
        - Terminal startup / fatal logs
        """

        findings = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # GCP: container restart count > 0
            cursor.execute(
                """
                SELECT 'GCP' AS source, *
                FROM GCP
                WHERE restart_count > 0
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

            # TERM: startup events or fatal crashes (often linked to restarts)
            cursor.execute(
                """
                SELECT 'TERM' AS source, *
                FROM TERM
                WHERE event_type = 'STARTUP'
                   OR (log_level = 'FATAL' AND exception_class = 'OutOfMemoryError')
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings

    # ------------------------------------------------------------------
    # A5: Performance Degradation Detection
    # ------------------------------------------------------------------

    def check_performance_degradation(self):
        """
        Detect degraded performance using Kafka metrics:
        - High response time
        - Low success rate
        - High failure count
        """

        findings = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Load thresholds from config
            response_time_min = self._get_int('PERFORMANCE', 'response_time_min_ms')
            success_rate_max = self._get_float('TRANSACTION', 'success_rate_max')
            failure_count_min = self._get_int('TRANSACTION', 'failure_count_min')

            cursor.execute(
                """
                SELECT 'KAFK' AS source, *
                FROM KAFK
                WHERE response_time_ms >= ?
                   OR transaction_success_rate <= ?
                   OR failure_count >= ?
                """,
                (response_time_min, success_rate_max, failure_count_min),
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings

    # ------------------------------------------------------------------
    # A6: Windows OS Metrics Detection
    # ------------------------------------------------------------------

    def check_windows_os_metrics(self):
        """
        Detect OS-level stress conditions from Windows metrics:
        - High memory usage
        - High CPU usage
        - Excessive network errors
        """

        findings = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Load thresholds
            memory_threshold = self._get_float('MEMORY', 'threshold_percent')
            network_threshold = self._get_int('NETWORK', 'error_threshold')
            cpu_threshold_pct = self._get_float('CPU', 'threshold_usage') * 100

            cursor.execute(
                """
                SELECT 'WINOS' AS source, *
                FROM WINOS
                WHERE memory_usage_percent > ?
                   OR network_errors > ?
                   OR cpu_usage_percent > ?
                """,
                (memory_threshold, network_threshold, cpu_threshold_pct),
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings

    # ------------------------------------------------------------------
    # A7: Kafka Event Integrity Checks
    # ------------------------------------------------------------------

    def check_kafka_events(self):
        """
        Detect Kafka data issues:
        1. Out-of-order events (timestamp regression)
        2. Missing required fields (malformed records)
        """

        findings = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # ---------------------------
            # Out-of-order detection
            # ---------------------------
            # Compare each row with its previous offset
            cursor.execute(
                """
                SELECT 'KAFK' AS source, k1.*
                FROM KAFK k1
                JOIN KAFK k2 ON k2.kafka_offset = k1.kafka_offset - 1
                WHERE k1.timestamp < k2.timestamp
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

            # ---------------------------
            # Malformed records
            # ---------------------------
            # Required fields missing (NULL values)
            cursor.execute(
                """
                SELECT 'KAFK' AS source, *
                FROM KAFK
                WHERE atm_status IS NULL OR transaction_rate_tps IS NULL
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings