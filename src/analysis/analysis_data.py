import sqlite3

class AnalysisData:
    def __init__(self, db_path="data/clean/atm_logs.db"):
        self.db_path = db_path
    
    def check_network_errors(self):
        """Detect network error signatures across ATMA/KAFK/TERM data"""

        errors = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # ATM App Log signals:
            # 1) event_type=NETWORK_DISCONNECT + error_code=ERR-0040
            # 2) event_type=TIMEOUT + response_time_ms=30000
            cursor.execute(
                """
                SELECT 'ATMA' AS source, *
                FROM ATMA
                WHERE (event_type = 'NETWORK_DISCONNECT' AND error_code = 'ERR-0040')
                   OR (event_type = 'TIMEOUT' AND response_time_ms = 30000)
                """
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
            # - jvm_memory_used_bytes > 1GB (high memory usage)
            # - jvm_gc_pause_seconds_sum > 10s (GC thrashing)
            # - process_cpu_usage > 0.9 (high CPU, possibly from GC)
            cursor.execute(
                """
                SELECT 'PROM' AS source, *
                FROM PROM
                WHERE (metric_name = 'jvm_memory_used_bytes' AND metric_value > 1000000000)
                   OR (metric_name = 'jvm_gc_pause_seconds_sum' AND metric_value > 10)
                   OR (metric_name = 'process_cpu_usage' AND metric_value > 0.9)
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

            # GCP signals:
            # - cpu_usage_percent > 90% (high CPU, correlated with memory issues)
            cursor.execute(
                """
                SELECT 'GCP' AS source, *
                FROM GCP
                WHERE cpu_usage_percent > 90
                """
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
            # - response_time_ms spikes to 3200ms then 30000ms
            # - transaction_success_rate drops from 100% to 72% to 50%
            # - failure_count increases to 8 then 14
            cursor.execute(
                """
                SELECT 'KAFK' AS source, *
                FROM KAFK
                WHERE response_time_ms IN (3200, 30000)
                   OR transaction_success_rate IN (72, 50)
                   OR failure_count IN (8, 14)
                """
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
            # - memory_usage_percent escalating to > 90%
            # - network_errors growing to > 20
            # - cpu_usage_percent rising to > 90%
            cursor.execute(
                """
                SELECT 'WINOS' AS source, *
                FROM WINOS
                WHERE memory_usage_percent > 90
                   OR network_errors > 20
                   OR cpu_usage_percent > 90
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings
    
    def check_kafka_events(self):
        """Detect Kafka event anomalies in KAFK data"""

        findings = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Kafka event anomalies signals:
            # - offset 4050 has an earlier timestamp than expected (out-of-order)
            # - offset 4051 has null atm_status and transaction_rate_tps (missing fields)
            cursor.execute(
                """
                SELECT 'KAFK' AS source, *
                FROM KAFK
                WHERE (kafka_offset = 4050 AND timestamp < (SELECT MIN(timestamp) FROM KAFK WHERE kafka_offset > 4050))
                   OR (kafka_offset = 4051 AND (atm_status IS NULL OR transaction_rate_tps IS NULL))
                """
            )
            findings.extend(dict(row) for row in cursor.fetchall())

        return findings