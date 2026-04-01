from __future__ import annotations

import sqlite3
from collections import defaultdict

from src.analysis.analyse_data import AnalyseData


class Detection:
    def __init__(self, db_path: str = "data/clean/atm_logs.db"):
        self.db_path = db_path
        self.analyse_data = AnalyseData(db_path=db_path)

    def store_detections(self) -> None:
        def _summarise(detections, anomaly_type, anomaly_name, severity, desc_fn):
            groups = defaultdict(lambda: {"count": 0, "timestamp": None, "desc": ""})
            for d in detections:
                key = (d.get("source", "UNKNOWN"), d.get("atm_id") or "N/A")
                groups[key]["count"] += 1
                if groups[key]["timestamp"] is None:
                    groups[key]["timestamp"] = d.get("timestamp")
                groups[key]["desc"] = desc_fn(d)
            return [
                (anomaly_type, anomaly_name, severity, src, atm_id,
                 info["timestamp"], info["desc"], info["count"])
                for (src, atm_id), info in groups.items()
            ]

        rows = []
        rows += _summarise(
            self.analyse_data.check_network_errors(), "A1", "Network timeout cascade", "CRITICAL",
            lambda d: f"Host unavailable: {d.get('transaction_failure_reason')}" if d.get("source") == "KAFK"
            else f"Disconnect/timeout: {d.get('error_code')} — {(d.get('error_detail') or '')[:80]}" if d.get("source") == "ATMA"
            else f"Network timeout: {(d.get('message') or '')[:80]}",
        )
        rows += _summarise(
            self.analyse_data.check_cash_cassette_depletion(), "A2", "Cash cassette depletion", "CRITICAL",
            lambda d: f"Cassette {d.get('event_type')} ({d.get('severity')})" if d.get("source") == "ATMH"
            else f"Transaction failure: {d.get('transaction_failure_reason')}",
        )
        rows += _summarise(
            self.analyse_data.check_container_restarts(), "A4", "Container restart loop", "WARNING",
            lambda d: f"Container restarted {d.get('restart_count')}x" if d.get("source") == "GCP"
            else f"Service {d.get('event_type') or 'OOM'}: {(d.get('exception_class') or d.get('message') or '')[:80]}",
        )
        rows += _summarise(
            self.analyse_data.check_performance_degradation(), "A5", "Performance degradation", "WARNING",
            lambda d: f"Resp {d.get('response_time_ms')}ms, success {d.get('transaction_success_rate')}%, failures {d.get('failure_count')}",
        )
        rows += _summarise(
            self.analyse_data.check_windows_os_metrics(), "A6", "OS memory pressure", "WARNING",
            lambda d: f"Mem {d.get('memory_usage_percent')}%, CPU {d.get('cpu_usage_percent')}%, net errors {d.get('network_errors')}",
        )
        rows += _summarise(
            self.analyse_data.check_kafka_events(), "A7", "Out-of-order / malformed Kafka event", "WARNING",
            lambda d: f"Offset {d.get('kafka_offset')} ordering or integrity issue",
        )

        with sqlite3.connect(self.db_path) as conn:
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
            # Migrate: add discovery_method to tables created before the column existed
            existing_cols = [
                row[1] for row in conn.execute("PRAGMA table_info(analysis_detections)").fetchall()
            ]
            if "discovery_method" not in existing_cols:
                conn.execute(
                    "ALTER TABLE analysis_detections ADD COLUMN discovery_method TEXT NOT NULL DEFAULT 'static'"
                )
            conn.execute("DELETE FROM analysis_detections")
            conn.executemany("""
                INSERT INTO analysis_detections
                    (anomaly_type, anomaly_name, severity, source, atm_id,
                     detection_timestamp, description, event_count, discovery_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'static')
            """, rows)
            conn.commit()

        print(f"[INFO] Analysis complete: {len(rows)} detection groups written to analysis_detections.")

    def detect(self):
        """
            This function will execute the analysis functions and then process the results to a readable format.
            Currently the processing is printing into the console but this will be uploaded to the db and then cached for the dashboard to display
        """

        network_detections = self.analyse_data.check_network_errors()
        
        if network_detections:
            print("------ Network Error(s) Detected ------")
            self.process_network_detections(network_detections)
            print("--------------------------------------")

        cassette_detections = self.analyse_data.check_cash_cassette_depletion()

        if cassette_detections:
            print("------ Cash Cassette Depletion Detected ------")
            self.process_cassette_detections(cassette_detections)
            print("---------------------------------------------")


        """
        For memory leaks, there is over 5000 detections in the data, will need to find an optimal solution to display all the data.
        """
        # memory_leak_detections = self.analyse_data.check_memory_leaks()

        # print(len(memory_leak_detections))

        # if memory_leak_detections:
        #     print("------ Memory Leak Anomalies Detected ------")
        #     self.process_memory_leak_detections(memory_leak_detections)
        #     print("-------------------------------------------")

        container_restart_detections = self.analyse_data.check_container_restarts()

        if container_restart_detections:
            print("------ Container Restart Anomalies Detected ------")
            self.process_container_restart_detections(container_restart_detections)
            print("-----------------------------------------------")


        performance_degradation_detections = self.analyse_data.check_performance_degradation()

        if performance_degradation_detections:
            print("------ Performance Degradation Anomalies Detected ------")
            self.process_performance_degradation_detections(performance_degradation_detections)
            print("-----------------------------------------------")

        windows_os_metrics_detections = self.analyse_data.check_windows_os_metrics()

        if windows_os_metrics_detections:
            print("------ Windows OS Metrics Anomalies Detected ------")
            self.process_windows_os_metrics_detections(windows_os_metrics_detections)
            print("-----------------------------------------------")

        kafka_events_detections = self.analyse_data.check_kafka_events()

        if kafka_events_detections:
            print("------ Kafka Event Anomalies Detected ------")
            self.process_kafka_events_detections(kafka_events_detections)
            print("-------------------------------------------")

    def process_network_detections(self, detections):
        for detection in detections:
            source = detection.get('source')
            atm_id = detection.get('atm_id')
            
            if source == 'KAFK':
                timestamp = detection.get('timestamp')
                transaction_failure_reason = detection.get('transaction_failure_reason')
                
                print(f"A1 Network anomaly detected from {source} at {timestamp}. Details: {atm_id} - {transaction_failure_reason}")
            elif source == 'ATMA':
                timestamp = detection.get('timestamp')
                error_detail = detection.get('error_detail')
                error_code = detection.get('error_code')
                
                print(f"Network anomaly detected from {source} at {timestamp}. Details: {atm_id} - {error_code} - {error_detail}")
            elif source == 'TERM':
                timestamp = detection.get('timestamp')
                message = detection.get('message')
                
                print(f"A1 Network anomaly detected from {source} at {timestamp}. Details: {atm_id} - {message}")

        return True

    def process_cassette_detections(self, detections):
        for detection in detections:
            source = detection.get('source')
            atm_id = detection.get('atm_id')
            
            if source == 'KAFK':
                timestamp = detection.get('timestamp')
                transaction_failure_reason = detection.get('transaction_failure_reason')
                
                print(f"A2 Cash cassette depletion anomaly detected from {source} at {timestamp}. Details: {atm_id} - {transaction_failure_reason}")
            elif source == 'ATMH':
                timestamp = detection.get('timestamp')
                message = detection.get('message')
                severity = detection.get('severity')
                
                print(f"A2 Cash cassette depletion anomaly detected from {source} at {timestamp}. Details: {atm_id} - {severity} - {message}")

        return True

    def process_memory_leak_detections(self, detections):
        # for detection in detections:
        #     source = detection.get('source')
        #   atm_id = detection.get('atm_id')
            
        #     if source == 'PROM':
        #         timestamp = detection.get('timestamp')
        #         metric_name = detection.get('metric_name')
        #         metric_value = detection.get('metric_value')
                
        #         print(f"A3 Memory leak anomaly detected from {source} at {timestamp}. Details: {atm_id} - {metric_name} - {metric_value}")
        #     elif source == 'GCP':
        #         timestamp = detection.get('timestamp')
        #         message = detection.get('message')
        #         severity = detection.get('severity')
                
        #         print(f"A3 Memory leak anomaly detected from {source} at {timestamp}. Details: {atm_id} - {severity} - {message}")
        #     elif source == 'TERM':
        #         timestamp = detection.get('timestamp')
        #         message = detection.get('message')
                
        #         print(f"A3 Memory leak anomaly detected from {source} at {timestamp}. Details: {atm_id} - {message}")
        pass

    def process_container_restart_detections(self, detections):
        for detection in detections:
            source = detection.get('source')
            
            # if source == 'GCP':
            #     timestamp = detection.get('timestamp')
            #     message = detection.get('message')
            #     severity = detection.get('severity')
                
            #     print(f"A4 Container restart anomaly detected from {source} at {timestamp}. Details: {severity} - {message}")
            if source == 'TERM':
                timestamp = detection.get('timestamp')
                message = detection.get('message')
                atm_id = detection.get('atm_id')
                
                print(f"A4 Container restart anomaly detected from {source} at {timestamp}. Details: {atm_id} - {message}")
        return True

    def process_performance_degradation_detections(self, detections):
        for detection in detections:
            source = detection.get('source')
            
            if source == 'KAFK':
                timestamp = detection.get('timestamp')
                transaction_failure_reason = detection.get('transaction_failure_reason')
                atm_id = detection.get('atm_id')
                
                print(f"A5 Performance degradation anomaly detected from {source} at {timestamp}. Details: {atm_id} - {transaction_failure_reason}")
        return True

    def process_windows_os_metrics_detections(self, detections):
        for detection in detections:
            source = detection.get('source')
            
            if source == 'WINOS':
                timestamp = detection.get('timestamp')
                atm_id = detection.get('atm_id')
                cpu = detection.get('cpu_usage_percent')
                memory = detection.get('memory_usage_percent')
                network = detection.get('network_errors')
                metric_value = f"CPU: {cpu}%, Memory: {memory}%, Network: {network}"
                
                print(f"A6 Windows OS metrics anomaly detected from {source} at {timestamp}. Details: {atm_id} - {metric_value}")
        return True

    def process_kafka_events_detections(self, detections):
        for detection in detections:
            source = detection.get('source')
            
            if source == 'KAFK':
                timestamp = detection.get('timestamp')
                atm_id = detection.get('atm_id')
                event_details = detection.get('event_details')

                print(f"A7 Kafka event anomaly detected from {source} at {timestamp}. Details: {atm_id} - {event_details}")
        return True