import sqlite3
import configparser

class AnalyseData:
    def __init__(self, db_path="data/clean/atm_logs.db"):
        self.config = configparser.ConfigParser()
        self.config.read("src/analysis/config.ini")
        self.db_path = db_path

    def _get_int(self, section, option):
        return self.config.getint(section, option)

    def _get_float(self, section, option):
        return self.config.getfloat(section, option)

    def check_network_errors(self):
        """Detect network error signatures across ATMA/KAFK/TERM data"""

        errors = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # ATM App Log signals:
            # 1) event_type=NETWORK_DISCONNECT + error_code=ERR-0040
            # 2) event_type=TIMEOUT + response_time_ms= 30000 (configurable via config.ini)
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

            # Kafka ATM metrics signal:
            # atm_status=Offline, transaction_failure_reason=HOST_UNAVAILABLE
            cursor.execute(
                """
                SELECT 'KAFK' AS source, *
                FROM KAFK
                WHERE atm_status = 'Offline'
                  AND transaction_failure_reason = 'HOST_UNAVAILABLE'
                """
            )
            errors.extend(dict(row) for row in cursor.fetchall())

            # Terminal Handler signal:
            # event_type=NETWORK_TIMEOUT for ATM-GB-0003
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

    def check_cash_cassette_depletion(self):
        """Detect cassette depletion signals across ATMH/KAFK data"""

        findings = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Hardware logs (ATMH) signals:
            # - CASSETTE_LOW on CASH_DISPENSER with WARNING severity
            # - CASSETTE_EMPTY on CASH_DISPENSER with CRITICAL severity
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

            # Kafka metrics signals:
            # - Out of Service + CASH_DISPENSE_ERROR
            # - transaction_rate_tps = 0.0, transaction_success_rate = 0.0
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

    def check_memory_leaks(self):
        """Detect memory leak signals across PROM/GCP/TERM data"""

        findings = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Prometheus signals:
            # - jvm_memory_used_bytes > 1GB (high memory usage) (configurable via config.ini)
            # - jvm_gc_pause_seconds_sum > 10s (GC thrashing) (configurable via config.ini)
            # - process_cpu_usage > 0.9 (high CPU, possibly from GC) (configurable via config.ini)
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

            # GCP signals:
            # - cpu_usage_percent > 90% (high CPU, correlated with memory issues) (configurable via config.ini)
            cpu_usage_threshold = self._get_float('CPU', 'threshold_usage') * 100
            cursor.execute(
                """
                SELECT 'GCP' AS source, *
                FROM GCP
                WHERE cpu_usage_percent > ?
                """,
                (cpu_usage_threshold,),
            )
            findings.extend(dict(row) for row in cursor.fetchall())

            # Terminal Handler signals:
            # - FATAL events with OutOfMemoryError
            cursor.execute(
                """
                SELECT 'TERM' AS source, *
                FROM TERM
                WHERE log_level = 'FATAL' AND exception_class = 'OutOfMemoryError'
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings

    def check_container_restarts(self):
        """Detect container restart loop signals across GCP/TERM data"""

        findings = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # GCP signals:
            # - restart_count > 0 (container has restarted)
            cursor.execute(
                """
                SELECT 'GCP' AS source, *
                FROM GCP
                WHERE restart_count > 0
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

            # Terminal Handler signals:
            # - event_type=STARTUP (container startup events)
            # - FATAL events with OutOfMemoryError (often precedes restarts)
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

    def check_performance_degradation(self):
        """Detect performance degradation signals across KAFK data"""

        findings = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Kafka signals:
            # - response_time_ms spikes above min threshold (configurable via config.ini)
            # - transaction_success_rate drops below max threshold (configurable via config.ini)
            # - failure_count rises above min threshold (configurable via config.ini)
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

    def check_windows_os_metrics(self):
        """Detect Windows OS metric escalation signals in WINOS data"""

        findings = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Windows OS Metrics signals:
            # - memory_usage_percent escalating to > 90% (configurable via config.ini)
            # - network_errors growing to > 20 (configurable via config.ini)
            # - cpu_usage_percent rising to > 90% (configurable via config.ini)
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

    def check_kafka_events(self):
        """Detect Kafka event anomalies: out-of-order timestamps and missing required fields"""

        findings = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Out-of-order: rows where timestamp is earlier than the maximum timestamp
            # of any row with a smaller kafka_offset (generic, not tied to specific offsets)
            cursor.execute(
                """
                SELECT 'KAFK' AS source, *
                FROM KAFK k1
                WHERE k1.timestamp < (
                    SELECT MAX(k2.timestamp)
                    FROM KAFK k2
                    WHERE k2.kafka_offset < k1.kafka_offset
                )
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

            # Malformed: rows with null values in required fields
            cursor.execute(
                """
                SELECT 'KAFK' AS source, *
                FROM KAFK
                WHERE atm_status IS NULL OR transaction_rate_tps IS NULL
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings
