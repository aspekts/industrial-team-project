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