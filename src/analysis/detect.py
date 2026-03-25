from src.analysis.analyse_data import AnalyseData

class Detection:
    def __init__(self):
        self.analyse_data = AnalyseData()

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