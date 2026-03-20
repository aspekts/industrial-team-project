import os
import csv
import json

# ──────────────────────────────────────────────────────────────────────────────
# File paths - change these to point to where your source files are
# ──────────────────────────────────────────────────────────────────────────────
BASE_PATH = "data/synthetic"

FILE_ATM_APP_LOG        = f"{BASE_PATH}/atm_application_log.json"
FILE_ATM_HW_LOG         = f"{BASE_PATH}/atm_hardware_sensor_log.json"
FILE_GCP_METRICS        = f"{BASE_PATH}/gcp_cloud_metrics.csv"
FILE_PROMETHEUS_METRICS = f"{BASE_PATH}/prometheus_metrics.csv"
FILE_WINDOWS_METRICS    = f"{BASE_PATH}/windows_os_metrics.csv"
FILE_KAFKA_STREAM       = f"{BASE_PATH}/kafka_atm_metrics_stream.json"
FILE_TERMINAL_LOG       = f"{BASE_PATH}/terminal_handler_app_log.json"

# ──────────────────────────────────────────────────────────────────────────────
# Output folder - all text files will be written here
# ──────────────────────────────────────────────────────────────────────────────

OutputFolder = "data/raw"

try:
    os.mkdir(OutputFolder)
except:
    print("Output folder already exists, continuing...")


# ──────────────────────────────────────────────────────────────────────────────
# Load each source file and write it out as a CSV-style text file
# ──────────────────────────────────────────────────────────────────────────────

def loadATMAppLog():
    print("Loading ATM Application Log...")

    InFile  = open(FILE_ATM_APP_LOG, 'r', encoding='utf-8')
    records = json.load(InFile)
    InFile.close()

    OutFile = open(OutputFolder + "/atm_application_logs.txt", 'w')

    # write header row
    OutFile.write("timestamp,log_level,atm_id,location_code,session_id," +
                  "correlation_id,transaction_id,event_type,message,component," +
                  "thread_id,response_time_ms,error_code,error_detail,atm_status," +
                  "os_version,app_version\n")

    count = 0
    for rec in records:
        OutFile.write(
            str(rec.get("timestamp",        "")) + "," +
            str(rec.get("log_level",        "")) + "," +
            str(rec.get("atm_id",           "")) + "," +
            str(rec.get("location_code",    "")) + "," +
            str(rec.get("session_id",       "")) + "," +
            str(rec.get("correlation_id",   "")) + "," +
            str(rec.get("transaction_id",   "")) + "," +
            str(rec.get("event_type",       "")) + "," +
            str(rec.get("message",          "")) + "," +
            str(rec.get("component",        "")) + "," +
            str(rec.get("thread_id",        "")) + "," +
            str(rec.get("response_time_ms", "")) + "," +
            str(rec.get("error_code",       "")) + "," +
            str(rec.get("error_detail",     "")) + "," +
            str(rec.get("atm_status",       "")) + "," +
            str(rec.get("os_version",       "")) + "," +
            str(rec.get("app_version",      "")) + "\n"
        )
        count += 1

    OutFile.close()
    print("  Rows written: " + str(count))
    print("  Saved to: " + OutputFolder + "/atm_application_logs.txt")


def loadATMHardwareLog():
    print("Loading ATM Hardware Sensor Log...")

    InFile  = open(FILE_ATM_HW_LOG, 'r', encoding='utf-8')
    records = json.load(InFile)
    InFile.close()

    OutFile = open(OutputFolder + "/atm_hardware_sensor_logs.txt", 'w')

    # write header row
    OutFile.write("timestamp,atm_id,correlation_id,component,event_type," +
                  "severity,message,metric_name,metric_value,metric_unit," +
                  "threshold_value,firmware_version\n")

    count = 0
    for rec in records:
        OutFile.write(
            str(rec.get("timestamp",        "")) + "," +
            str(rec.get("atm_id",           "")) + "," +
            str(rec.get("correlation_id",   "")) + "," +
            str(rec.get("component",        "")) + "," +
            str(rec.get("event_type",       "")) + "," +
            str(rec.get("severity",         "")) + "," +
            str(rec.get("message",          "")) + "," +
            str(rec.get("metric_name",      "")) + "," +
            str(rec.get("metric_value",     "")) + "," +
            str(rec.get("metric_unit",      "")) + "," +
            str(rec.get("threshold_value",  "")) + "," +
            str(rec.get("firmware_version", "")) + "\n"
        )
        count += 1

    OutFile.close()
    print("  Rows written: " + str(count))
    print("  Saved to: " + OutputFolder + "/atm_hardware_sensor_logs.txt")


def loadGCPMetrics():
    print("Loading GCP Cloud Metrics...")

    InFile = open(FILE_GCP_METRICS, 'r', encoding='utf-8', newline='')
    reader = csv.DictReader(InFile)

    OutFile = open(OutputFolder + "/gcp_cloud_metrics.txt", 'w')

    # write header row
    OutFile.write("timestamp,project_id,resource_type,resource_id,zone," +
                  "metric_name,metric_value,metric_unit,cpu_usage_percent," +
                  "memory_usage_bytes,memory_limit_bytes,network_ingress_bytes," +
                  "network_egress_bytes,restart_count,label_app,label_env," +
                  "label_version\n")

    count = 0
    for row in reader:
        OutFile.write(
            str(row.get("timestamp",             "")) + "," +
            str(row.get("project_id",            "")) + "," +
            str(row.get("resource_type",         "")) + "," +
            str(row.get("resource_id",           "")) + "," +
            str(row.get("zone",                  "")) + "," +
            str(row.get("metric_name",           "")) + "," +
            str(row.get("metric_value",          "")) + "," +
            str(row.get("metric_unit",           "")) + "," +
            str(row.get("cpu_usage_percent",     "")) + "," +
            str(row.get("memory_usage_bytes",    "")) + "," +
            str(row.get("memory_limit_bytes",    "")) + "," +
            str(row.get("network_ingress_bytes", "")) + "," +
            str(row.get("network_egress_bytes",  "")) + "," +
            str(row.get("restart_count",         "")) + "," +
            str(row.get("label_app",             "")) + "," +
            str(row.get("label_env",             "")) + "," +
            str(row.get("label_version",         "")) + "\n"
        )
        count += 1

    InFile.close()
    OutFile.close()
    print("  Rows written: " + str(count))
    print("  Saved to: " + OutputFolder + "/gcp_cloud_metrics.txt")


def loadPrometheusMetrics():
    print("Loading Prometheus Metrics...")

    InFile = open(FILE_PROMETHEUS_METRICS, 'r', encoding='utf-8', newline='')
    reader = csv.DictReader(InFile)

    OutFile = open(OutputFolder + "/prometheus_metrics.txt", 'w')

    # write header row
    OutFile.write("timestamp,metric_name,metric_type,metric_value," +
                  "service_name,pod_name,container_id,label_area," +
                  "label_env,help_text\n")

    count = 0
    for row in reader:
        OutFile.write(
            str(row.get("timestamp",    "")) + "," +
            str(row.get("metric_name",  "")) + "," +
            str(row.get("metric_type",  "")) + "," +
            str(row.get("metric_value", "")) + "," +
            str(row.get("service_name", "")) + "," +
            str(row.get("pod_name",     "")) + "," +
            str(row.get("container_id", "")) + "," +
            str(row.get("label_area",   "")) + "," +
            str(row.get("label_env",    "")) + "," +
            str(row.get("help_text",    "")) + "\n"
        )
        count += 1

    InFile.close()
    OutFile.close()
    print("  Rows written: " + str(count))
    print("  Saved to: " + OutputFolder + "/prometheus_metrics.txt")


def loadWindowsMetrics():
    print("Loading Windows OS Metrics...")

    InFile = open(FILE_WINDOWS_METRICS, 'r', encoding='utf-8', newline='')
    reader = csv.DictReader(InFile)

    OutFile = open(OutputFolder + "/windows_os_metrics.txt", 'w')

    # write header row
    OutFile.write("timestamp,atm_id,hostname,os_version,cpu_usage_percent," +
                  "memory_used_mb,memory_total_mb,memory_usage_percent," +
                  "disk_read_bytes_per_sec,disk_write_bytes_per_sec,disk_free_gb," +
                  "network_bytes_sent_per_sec,network_bytes_recv_per_sec," +
                  "network_errors,process_count,system_uptime_seconds," +
                  "event_log_errors_last_min\n")

    count = 0
    for row in reader:
        OutFile.write(
            str(row.get("timestamp",                  "")) + "," +
            str(row.get("atm_id",                     "")) + "," +
            str(row.get("hostname",                   "")) + "," +
            str(row.get("os_version",                 "")) + "," +
            str(row.get("cpu_usage_percent",          "")) + "," +
            str(row.get("memory_used_mb",             "")) + "," +
            str(row.get("memory_total_mb",            "")) + "," +
            str(row.get("memory_usage_percent",       "")) + "," +
            str(row.get("disk_read_bytes_per_sec",    "")) + "," +
            str(row.get("disk_write_bytes_per_sec",   "")) + "," +
            str(row.get("disk_free_gb",               "")) + "," +
            str(row.get("network_bytes_sent_per_sec", "")) + "," +
            str(row.get("network_bytes_recv_per_sec", "")) + "," +
            str(row.get("network_errors",             "")) + "," +
            str(row.get("process_count",              "")) + "," +
            str(row.get("system_uptime_seconds",      "")) + "," +
            str(row.get("event_log_errors_last_min",  "")) + "\n"
        )
        count += 1

    InFile.close()
    OutFile.close()
    print("  Rows written: " + str(count))
    print("  Saved to: " + OutputFolder + "/windows_os_metrics.txt")


def loadKafkaStream():
    print("Loading Kafka ATM Metrics Stream...")

    InFile  = open(FILE_KAFKA_STREAM, 'r', encoding='utf-8')
    records = json.load(InFile)
    InFile.close()

    OutFile = open(OutputFolder + "/kafka_atm_metrics_stream.txt", 'w')

    # write header row
    OutFile.write("timestamp,event_id,correlation_id,atm_id,atm_status," +
                  "transaction_rate_tps,response_time_ms,transaction_volume," +
                  "transaction_success_rate,transaction_failure_reason," +
                  "failure_count,window_duration_seconds,kafka_partition," +
                  "kafka_offset\n")

    count = 0
    for rec in records:
        OutFile.write(
            str(rec.get("timestamp",                  "")) + "," +
            str(rec.get("event_id",                   "")) + "," +
            str(rec.get("correlation_id",             "")) + "," +
            str(rec.get("atm_id",                     "")) + "," +
            str(rec.get("atm_status",                 "")) + "," +
            str(rec.get("transaction_rate_tps",       "")) + "," +
            str(rec.get("response_time_ms",           "")) + "," +
            str(rec.get("transaction_volume",         "")) + "," +
            str(rec.get("transaction_success_rate",   "")) + "," +
            str(rec.get("transaction_failure_reason", "")) + "," +
            str(rec.get("failure_count",              "")) + "," +
            str(rec.get("window_duration_seconds",    "")) + "," +
            str(rec.get("kafka_partition",            "")) + "," +
            str(rec.get("kafka_offset",               "")) + "\n"
        )
        count += 1

    OutFile.close()
    print("  Rows written: " + str(count))
    print("  Saved to: " + OutputFolder + "/kafka_atm_metrics_stream.txt")


def loadTerminalHandlerLog():
    print("Loading Terminal Handler App Log...")

    InFile  = open(FILE_TERMINAL_LOG, 'r', encoding='utf-8')
    records = json.load(InFile)
    InFile.close()

    OutFile = open(OutputFolder + "/terminal_handler_app_log.txt", 'w')

    # write header row
    OutFile.write("timestamp,log_level,service_name,service_version,container_id," +
                  "pod_name,correlation_id,transaction_id,atm_id,event_type," +
                  "message,logger_name,thread_name,response_time_ms,http_status_code," +
                  "exception_class,exception_message,db_query_time_ms,environment\n")

    count = 0
    for rec in records:
        OutFile.write(
            str(rec.get("timestamp",         "")) + "," +
            str(rec.get("log_level",         "")) + "," +
            str(rec.get("service_name",      "")) + "," +
            str(rec.get("service_version",   "")) + "," +
            str(rec.get("container_id",      "")) + "," +
            str(rec.get("pod_name",          "")) + "," +
            str(rec.get("correlation_id",    "")) + "," +
            str(rec.get("transaction_id",    "")) + "," +
            str(rec.get("atm_id",            "")) + "," +
            str(rec.get("event_type",        "")) + "," +
            str(rec.get("message",           "")) + "," +
            str(rec.get("logger_name",       "")) + "," +
            str(rec.get("thread_name",       "")) + "," +
            str(rec.get("response_time_ms",  "")) + "," +
            str(rec.get("http_status_code",  "")) + "," +
            str(rec.get("exception_class",   "")) + "," +
            str(rec.get("exception_message", "")) + "," +
            str(rec.get("db_query_time_ms",  "")) + "," +
            str(rec.get("environment",       "")) + "\n"
        )
        count += 1

    OutFile.close()
    print("  Rows written: " + str(count))
    print("  Saved to: " + OutputFolder + "/terminal_handler_app_log.txt")


def checkRowCounts():
    print("\nRow counts in output files:")

    files = [
        "atm_application_logs.txt",
        "atm_hardware_sensor_logs.txt",
        "gcp_cloud_metrics.txt",
        "prometheus_metrics.txt",
        "windows_os_metrics.txt",
        "kafka_atm_metrics_stream.txt",
        "terminal_handler_app_log.txt"
    ]

    for fname in files:
        path   = OutputFolder + "/" + fname
        InFile = open(path, 'r', encoding='utf-8')
        Lines  = InFile.readlines()
        InFile.close()
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

    elif not os.path.exists(FILE_GCP_METRICS):
        print("ERROR: cannot find " + FILE_GCP_METRICS)

    elif not os.path.exists(FILE_PROMETHEUS_METRICS):
        print("ERROR: cannot find " + FILE_PROMETHEUS_METRICS)

    elif not os.path.exists(FILE_WINDOWS_METRICS):
        print("ERROR: cannot find " + FILE_WINDOWS_METRICS)

    elif not os.path.exists(FILE_KAFKA_STREAM):
        print("ERROR: cannot find " + FILE_KAFKA_STREAM)

    elif not os.path.exists(FILE_TERMINAL_LOG):
        print("ERROR: cannot find " + FILE_TERMINAL_LOG)


    else:
        # step 1 - load each source file and write it to a text file
        loadATMAppLog()
        loadATMHardwareLog()
        loadGCPMetrics()
        loadPrometheusMetrics()
        loadWindowsMetrics()
        loadKafkaStream()
        loadTerminalHandlerLog()

        # step 2 - confirm everything loaded correctly
        checkRowCounts()

        print("\nDone. All logs saved to the '" + OutputFolder + "' folder.")
