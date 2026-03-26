import os
import csv
import json
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# File paths - change these to point to where your source files are
# ──────────────────────────────────────────────────────────────────────────────

BASE_PATH = "data/synthetic"

FILE_ATM_APP_LOG        = f"{BASE_PATH}/atm_application_log.json"
FILE_ATM_HW_LOG         = f"{BASE_PATH}/atm_hardware_sensor_log.json"
FILE_TERMINAL_LOG       = f"{BASE_PATH}/terminal_handler_app_log.json"
FILE_KAFKA_STREAM       = f"{BASE_PATH}/kafka_atm_metrics_stream.json"
FILE_PROMETHEUS_METRICS = f"{BASE_PATH}/prometheus_metrics.csv"
FILE_WINDOWS_METRICS    = f"{BASE_PATH}/windows_os_metrics.csv"
FILE_GCP_METRICS        = f"{BASE_PATH}/gcp_cloud_metrics.csv"


# ──────────────────────────────────────────────────────────────────────────────
# Output folder - all text files will be written here
# ──────────────────────────────────────────────────────────────────────────────

OutputFolder = "data/raw"
error_path   = "data/clean/broken_logs.json"

try:
    os.mkdir(OutputFolder)
except OSError:
    print("Output folder already exists, continuing...")


# ──────────────────────────────────────────────────────────────────────────────
# Malformed input handling
# ──────────────────────────────────────────────────────────────────────────────

def isFileEmpty(filepath):
    # returns True if the file has no content or only whitespace
    InFile  = open(filepath, 'r', encoding='utf-8')
    content = InFile.read().strip()
    InFile.close()

    if len(content) == 0:
        print("  WARNING: " + filepath + " is empty - skipping.")
        return True
    return False


def isValidTimestamp(value, rowNumber, filename):
    # checks the timestamp looks like a valid ISO 8601 date e.g. 2026-03-05T00:00:00
    # returns True if valid, False if not
    if value == "" or value == "None" or value is None:
        print("  WARNING: row " + str(rowNumber) + " in " + filename + " has a missing timestamp.")
        return False

    try:
        # strip the trailing Z if present and try to parse it
        clean = str(value).replace("Z", "").replace(".000", "")
        datetime.strptime(clean[:19], "%Y-%m-%dT%H:%M:%S")
        return True
    except ValueError:
        print("  WARNING: row " + str(rowNumber) + " in " + filename + " has a bad timestamp: " + str(value))
        return False


def checkRequiredFields(rec, requiredFields, rowNumber, filename):
    # checks that all required fields exist and are not empty in a record
    # returns True if all required fields are present, False if any are missing
    allPresent = True

    for field in requiredFields:
        value = rec.get(field, "")
        if value == "" or value is None or str(value).strip() == "None":
            print("  WARNING: row " + str(rowNumber) + " in " + filename + " is missing required field: " + field)
            allPresent = False

    return allPresent



def loadATMAppLog():
    print("Loading ATM Application Log...")

    if isFileEmpty(FILE_ATM_APP_LOG):
        return

    with open(FILE_ATM_APP_LOG, 'r', encoding='utf-8') as InFile:
        records = json.load(InFile)

    with open(OutputFolder + "/atm_application_logs.txt", 'w', newline='', encoding='utf-8') as Outfile:
        writer = csv.writer(Outfile)

        # write header row
        writer.writerow(["timestamp","log_level","atm_id","location_code","session_id",
                    "correlation_id","transaction_id","event_type","message","component",
                    "thread_id","response_time_ms","error_code","error_detail","atm_status",
                    "os_version","app_version"
        ])

        # required fields per schema (non-nullable fields only)
        requiredFields = ["timestamp", "log_level", "atm_id", "location_code",
                        "event_type", "message", "component", "atm_status", "app_version"]

        count        = 0
        skippedCount = 0

        for rec in records:
            rowNumber = count + skippedCount + 1

            if not checkRequiredFields(rec, requiredFields, rowNumber, FILE_ATM_APP_LOG):
                skippedCount += 1
                continue

            if not isValidTimestamp(rec.get("timestamp", ""), rowNumber, FILE_ATM_APP_LOG):
                skippedCount += 1
                continue

            writer.writerow([
                rec.get("timestamp",""),
                rec.get("log_level",""),
                rec.get("atm_id",""),
                rec.get("location_code",""),
                rec.get("session_id",""),
                rec.get("correlation_id",""),
                rec.get("transaction_id",""),
                rec.get("event_type",""),
                rec.get("message",""),
                rec.get("component",""),
                rec.get("thread_id",""),
                rec.get("response_time_ms",""),
                rec.get("error_code",""),
                rec.get("error_detail",""),
                rec.get("atm_status",""),
                rec.get("os_version",""),
                rec.get("app_version","")
            ])
            count += 1

    print("  Rows written: " + str(count))
    if skippedCount > 0:
        print("  Rows skipped (malformed): " + str(skippedCount))
    print("  Saved to: " + OutputFolder + "/atm_application_logs.txt")


def loadATMHardwareLog():
    print("Loading ATM Hardware Sensor Log...")

    if isFileEmpty(FILE_ATM_HW_LOG):
        return

    with open(FILE_ATM_HW_LOG, 'r', encoding='utf-8') as InFile:
        records = json.load(InFile)

    with open(OutputFolder + "/atm_hardware_sensor_logs.txt", 'w', newline='', encoding='utf-8') as Outfile:
        writer = csv.writer(Outfile)

        # write header row
        writer.writerow(["timestamp","atm_id","correlation_id","component","event_type",
                    "severity","message","metric_name","metric_value","metric_unit",
                    "threshold_value","firmware_version"
        ])

        # required fields per schema
        requiredFields = ["timestamp", "atm_id", "component", "event_type", "severity", "message"]

        count        = 0
        skippedCount = 0

        for rec in records:
            rowNumber = count + skippedCount + 1

            if not checkRequiredFields(rec, requiredFields, rowNumber, FILE_ATM_HW_LOG):
                skippedCount += 1
                continue

            if not isValidTimestamp(rec.get("timestamp", ""), rowNumber, FILE_ATM_HW_LOG):
                skippedCount += 1
                continue

            writer.writerow([
                rec.get("timestamp",""),
                rec.get("atm_id",""),
                rec.get("correlation_id",""),
                rec.get("component",""),
                rec.get("event_type",""),
                rec.get("severity",""),
                rec.get("message",""),
                rec.get("metric_name",""),
                rec.get("metric_value",""),
                rec.get("metric_unit",""),
                rec.get("threshold_value",""),
                rec.get("firmware_version","")
            ])
            count += 1

    print("  Rows written: " + str(count))
    if skippedCount > 0:
        print("  Rows skipped (malformed): " + str(skippedCount))
    print("  Saved to: " + OutputFolder + "/atm_hardware_sensor_logs.txt")


def loadTerminalHandlerLog():
    print("Loading Terminal Handler App Log...")

    if isFileEmpty(FILE_TERMINAL_LOG):
        return

    with open(FILE_TERMINAL_LOG, 'r', encoding='utf-8') as InFile:
        records = json.load(InFile)

    with open(OutputFolder + "/terminal_handler_app_log.txt", 'w', newline='', encoding='utf-8') as Outfile:
        writer = csv.writer(Outfile)

        # write header row
        writer.writerow(["timestamp","log_level","service_name","service_version","container_id",
                    "pod_name","correlation_id","transaction_id","atm_id","event_type",
                    "message","logger_name","thread_name","response_time_ms","http_status_code",
                    "exception_class","exception_message","db_query_time_ms","environment"
        ])

        # required fields per schema
        requiredFields = ["timestamp", "log_level", "service_name", "service_version",
                        "event_type", "message", "environment"]

        count        = 0
        skippedCount = 0

        for rec in records:
            rowNumber = count + skippedCount + 1

            if not checkRequiredFields(rec, requiredFields, rowNumber, FILE_TERMINAL_LOG):
                skippedCount += 1
                continue

            if not isValidTimestamp(rec.get("timestamp", ""), rowNumber, FILE_TERMINAL_LOG):
                skippedCount += 1
                continue

            writer.writerow([
                rec.get("timestamp",""),
                rec.get("log_level",""),
                rec.get("service_name",""),
                rec.get("service_version",""),
                rec.get("container_id",""),
                rec.get("pod_name",""),
                rec.get("correlation_id",""),
                rec.get("transaction_id",""),
                rec.get("atm_id",""),
                rec.get("event_type",""),
                rec.get("message",""),
                rec.get("logger_name",""),
                rec.get("thread_name",""),
                rec.get("response_time_ms",""),
                rec.get("http_status_code",""),
                rec.get("exception_class",""),
                rec.get("exception_message",""),
                rec.get("db_query_time_ms",""),
                rec.get("environment","")
            ])
            count += 1

    print("  Rows written: " + str(count))
    if skippedCount > 0:
        print("  Rows skipped (malformed): " + str(skippedCount))
    print("  Saved to: " + OutputFolder + "/terminal_handler_app_log.txt")



def loadKafkaStream():
    print("Loading Kafka ATM Metrics Stream...")

    if isFileEmpty(FILE_KAFKA_STREAM):
        return

    with open(FILE_KAFKA_STREAM, 'r', encoding='utf-8') as InFile:
        records = json.load(InFile)

    with open(OutputFolder + "/kafka_atm_metrics_stream.txt", 'w', newline='', encoding='utf-8') as Outfile:
        writer = csv.writer(Outfile)

        # write header row
        writer.writerow(["timestamp","event_id","correlation_id","atm_id","atm_status",
                        "transaction_rate_tps","response_time_ms","transaction_volume",
                        "transaction_success_rate","transaction_failure_reason",
                        "failure_count","window_duration_seconds","kafka_partition",
                        "kafka_offset"
        ])

        # required fields per schema
        requiredFields = ["timestamp", "event_id", "atm_id", "atm_status",
                        "transaction_rate_tps", "response_time_ms", "transaction_volume",
                        "transaction_success_rate", "transaction_failure_reason",
                        "failure_count", "window_duration_seconds"]

        count        = 0
        skippedCount = 0

        for rec in records:
            rowNumber = count + skippedCount + 1

            if not checkRequiredFields(rec, requiredFields, rowNumber, FILE_KAFKA_STREAM):
                skippedCount += 1
                continue

            if not isValidTimestamp(rec.get("timestamp", ""), rowNumber, FILE_KAFKA_STREAM):
                skippedCount += 1
                continue

            writer.writerow([
                    rec.get("timestamp",""),
                    rec.get("event_id",""),
                    rec.get("correlation_id",""),
                    rec.get("atm_id",""),
                    rec.get("atm_status",""),
                    rec.get("transaction_rate_tps",""),
                    rec.get("response_time_ms",""),
                    rec.get("transaction_volume",""),
                    rec.get("transaction_success_rate",""),
                    rec.get("transaction_failure_reason",""),
                    rec.get("failure_count",""),
                    rec.get("window_duration_seconds",""),
                    rec.get("kafka_partition",""),
                    rec.get("kafka_offset","")
            ])
            count += 1

    print("  Rows written: " + str(count))
    if skippedCount > 0:
        print("  Rows skipped (malformed): " + str(skippedCount))
    print("  Saved to: " + OutputFolder + "/kafka_atm_metrics_stream.txt")



def loadPrometheusMetrics():
    print("Loading Prometheus Metrics...")

    if isFileEmpty(FILE_PROMETHEUS_METRICS):
        return

    with open(FILE_PROMETHEUS_METRICS, 'r', encoding='utf-8', newline='') as InFile:
        reader = csv.DictReader(InFile)

        with open(OutputFolder + "/prometheus_metrics.txt", 'w', newline='', encoding='utf-8') as OutFile:
            writer = csv.writer(OutFile)

            # write header row
            writer.writerow([
                "timestamp","metric_name","metric_type","metric_value",
                "service_name","pod_name","container_id","label_area",
                "label_env","help_text"
            ])

            # required fields per schema
            requiredFields = ["timestamp", "metric_name", "metric_type", "metric_value", "service_name"]

            count        = 0
            skippedCount = 0

            for row in reader:
                rowNumber = count + skippedCount + 1

                if not checkRequiredFields(row, requiredFields, rowNumber, FILE_PROMETHEUS_METRICS):
                    skippedCount += 1
                    continue

                if not isValidTimestamp(row.get("timestamp", ""), rowNumber, FILE_PROMETHEUS_METRICS):
                    skippedCount += 1
                    continue

                writer.writerow([
                    row.get("timestamp",""),
                    row.get("metric_name",""),
                    row.get("metric_type",""),
                    row.get("metric_value",""),
                    row.get("service_name",""),
                    row.get("pod_name",""),
                    row.get("container_id",""),
                    row.get("label_area",""),
                    row.get("label_env",""),
                    row.get("help_text","")
                ])
                count += 1

    print("  Rows written: " + str(count))
    if skippedCount > 0:
        print("  Rows skipped (malformed): " + str(skippedCount))
    print("  Saved to: " + OutputFolder + "/prometheus_metrics.txt")


def loadWindowsMetrics():
    print("Loading Windows OS Metrics...")

    if isFileEmpty(FILE_WINDOWS_METRICS):
        return

    with open(FILE_WINDOWS_METRICS, 'r', encoding='utf-8', newline='') as InFile:
        reader = csv.DictReader(InFile)

        with open(OutputFolder + "/windows_os_metrics.txt", 'w', newline='', encoding='utf-8') as OutFile:
            writer = csv.writer(OutFile)

            # write header row
            writer.writerow([
                "timestamp","atm_id","hostname","os_version","cpu_usage_percent",
                "memory_used_mb","memory_total_mb","memory_usage_percent",
                "disk_read_bytes_per_sec","disk_write_bytes_per_sec","disk_free_gb",
                "network_bytes_sent_per_sec","network_bytes_recv_per_sec",
                "network_errors","process_count","system_uptime_seconds",
                "event_log_errors_last_min"
            ])

            # required fields per schema
            requiredFields = ["timestamp", "atm_id", "hostname", "cpu_usage_percent",
                            "memory_used_mb", "memory_total_mb", "disk_free_gb"]

            count        = 0
            skippedCount = 0

            for row in reader:
                rowNumber = count + skippedCount + 1

                if not checkRequiredFields(row, requiredFields, rowNumber, FILE_WINDOWS_METRICS):
                    skippedCount += 1
                    continue

                if not isValidTimestamp(row.get("timestamp", ""), rowNumber, FILE_WINDOWS_METRICS):
                    skippedCount += 1
                    continue

                writer.writerow([
                    row.get("timestamp",""),
                    row.get("atm_id",""),
                    row.get("hostname",""),
                    row.get("os_version",""),
                    row.get("cpu_usage_percent",""),
                    row.get("memory_used_mb",""),
                    row.get("memory_total_mb",""),
                    row.get("memory_usage_percent",""),
                    row.get("disk_read_bytes_per_sec",""),
                    row.get("disk_write_bytes_per_sec",""),
                    row.get("disk_free_gb",""),
                    row.get("network_bytes_sent_per_sec",""),
                    row.get("network_bytes_recv_per_sec",""),
                    row.get("network_errors",""),
                    row.get("process_count",""),
                    row.get("system_uptime_seconds",""),
                    row.get("event_log_errors_last_min",""),
                ])
                count += 1

    print("  Rows written: " + str(count))
    if skippedCount > 0:
        print("  Rows skipped (malformed): " + str(skippedCount))
    print("  Saved to: " + OutputFolder + "/windows_os_metrics.txt")


def loadGCPMetrics():
    print("Loading GCP Cloud Metrics...")

    if isFileEmpty(FILE_GCP_METRICS):
        return

    with open(FILE_GCP_METRICS, 'r', encoding='utf-8', newline='') as InFile:
        reader = csv.DictReader(InFile)

        with open(OutputFolder + "/gcp_cloud_metrics.txt", 'w', newline='', encoding='utf-8') as OutFile:
            writer = csv.writer(OutFile)

            # write header row
            writer.writerow([
                "timestamp","project_id","resource_type","resource_id","zone",
                "metric_name","metric_value","metric_unit","cpu_usage_percent",
                "memory_usage_bytes","memory_limit_bytes","network_ingress_bytes",
                "network_egress_bytes","restart_count","label_app","label_env",
                "label_version"
            ])

            # required fields per schema
            requiredFields = ["timestamp", "project_id", "resource_type", "resource_id",
                            "metric_name", "metric_value"]

            count        = 0
            skippedCount = 0

            for row in reader:
                rowNumber = count + skippedCount + 1

                if not checkRequiredFields(row, requiredFields, rowNumber, FILE_GCP_METRICS):
                    skippedCount += 1
                    continue

                if not isValidTimestamp(row.get("timestamp", ""), rowNumber, FILE_GCP_METRICS):
                    skippedCount += 1
                    continue

                writer.writerow([
                    row.get("timestamp",""),
                    row.get("project_id",""),
                    row.get("resource_type",""),
                    row.get("resource_id",""),
                    row.get("zone",""),
                    row.get("metric_name",""),
                    row.get("metric_value",""),
                    row.get("metric_unit",""),
                    row.get("cpu_usage_percent",""),
                    row.get("memory_usage_bytes",""),
                    row.get("memory_limit_bytes",""),
                    row.get("network_ingress_bytes",""),
                    row.get("network_egress_bytes",""),
                    row.get("restart_count",""),
                    row.get("label_app",""),
                    row.get("label_env",""),
                    row.get("label_version",""),
                ])
                count += 1

    print("  Rows written: " + str(count))
    if skippedCount > 0:
        print("  Rows skipped (malformed): " + str(skippedCount))
    print("  Saved to: " + OutputFolder + "/gcp_cloud_metrics.txt")

    print("  Saved to: " + OutputFolder + "/gcp_cloud_metrics.txt")


def checkRowCounts():
    print("\nRow counts in output files:")

    files = [
        "atm_application_logs.txt",
        "atm_hardware_sensor_logs.txt",
        "terminal_handler_app_log.txt",
        "kafka_atm_metrics_stream.txt",
        "prometheus_metrics.txt",
        "windows_os_metrics.txt",
        "gcp_cloud_metrics.txt"
    ]

    for fname in files:
        path   = OutputFolder + "/" + fname
        with open(path, 'r', encoding='utf-8') as InFile:
            Lines = InFile.readlines()
        # subtract 1 to exclude the header row from the count
        count = len(Lines) - 1
        print("  " + fname + ": " + str(count) + " rows")


# ──────────────────────────────────────────────────────────────────────────────
# Main - runs all the steps in order
# ──────────────────────────────────────────────────────────────────────────────


def run_ingestion():
    # check all source files exist before doing anything
    if not os.path.exists(FILE_ATM_APP_LOG):
        print("ERROR: cannot find " + FILE_ATM_APP_LOG)

    elif not os.path.exists(FILE_ATM_HW_LOG):
        print("ERROR: cannot find " + FILE_ATM_HW_LOG)

    elif not os.path.exists(FILE_TERMINAL_LOG):
        print("ERROR: cannot find " + FILE_TERMINAL_LOG)

    elif not os.path.exists(FILE_KAFKA_STREAM):
        print("ERROR: cannot find " + FILE_KAFKA_STREAM)

    elif not os.path.exists(FILE_PROMETHEUS_METRICS):
        print("ERROR: cannot find " + FILE_PROMETHEUS_METRICS)

    elif not os.path.exists(FILE_WINDOWS_METRICS):
        print("ERROR: cannot find " + FILE_WINDOWS_METRICS)

    elif not os.path.exists(FILE_GCP_METRICS):
        print("ERROR: cannot find " + FILE_GCP_METRICS)


    else:
        # step 1 - load each source file and write it to a text file
        loadATMAppLog()
        loadATMHardwareLog()
        loadTerminalHandlerLog()
        loadKafkaStream()
        loadPrometheusMetrics()
        loadWindowsMetrics()
        loadGCPMetrics()

        # step 2 - confirm everything loaded correctly
        checkRowCounts()

        print("\nDone. All logs saved to the '" + OutputFolder + "' folder.")