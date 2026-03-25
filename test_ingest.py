import os
import csv
import json
import unittest
import tempfile
import shutil
import sys

# ──────────────────────────────────────────────────────────────────────────────
# Point Python to where ingest.py lives so we can import from it.
# Adjust this path if your folder structure is different.
# e.g. if ingest.py is at src/parsers/ingest.py, use:
#   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'parsers'))
# ──────────────────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ingest


# ──────────────────────────────────────────────────────────────────────────────
# Sample synthetic records — one clean record per source, taken from the schema
# ──────────────────────────────────────────────────────────────────────────────

SAMPLE_ATM_APP_LOG = [
    {
        "timestamp":        "2026-03-05T00:00:00.000Z",
        "log_level":        "INFO",
        "atm_id":           "ATM-GB-0001",
        "location_code":    "LOC-0101",
        "session_id":       None,
        "correlation_id":   None,
        "transaction_id":   None,
        "event_type":       "STARTUP",
        "message":          "ATM client application started successfully. Self-test passed.",
        "component":        "BootManager",
        "thread_id":        1,
        "response_time_ms": None,
        "error_code":       None,
        "error_detail":     None,
        "atm_status":       "Online",
        "os_version":       "Windows 10 LTSB 2016 Build 14393",
        "app_version":      "3.4.1-build.209",
        "_anomaly":         None
    }
]

SAMPLE_ATM_HW_LOG = [
    {
        "timestamp":        "2026-03-05T00:00:00.000Z",
        "atm_id":           "ATM-GB-0001",
        "correlation_id":   None,
        "component":        "TEMPERATURE_SENSOR",
        "event_type":       "TEMPERATURE_NORMAL",
        "severity":         "INFO",
        "message":          "Internal temperature within normal range: 34.3°C.",
        "metric_name":      "internal_temp_celsius",
        "metric_value":     34.3,
        "metric_unit":      "celsius",
        "threshold_value":  55.0,
        "firmware_version": "FW-1.0.1",
        "_anomaly":         None
    }
]

SAMPLE_TERMINAL_LOG = [
    {
        "timestamp":         "2026-03-05T00:00:00.000Z",
        "log_level":         "INFO",
        "service_name":      "terminal-handler",
        "service_version":   "2.7.0-SNAPSHOT",
        "container_id":      "a3f2b19c04d1",
        "pod_name":          "terminal-handler-pod-7d9f-xk2lp",
        "correlation_id":    None,
        "transaction_id":    None,
        "atm_id":            None,
        "event_type":        "STARTUP",
        "message":           "Terminal Handler service started.",
        "logger_name":       "com.synthbank.terminalhandler.App",
        "thread_name":       "main",
        "response_time_ms":  None,
        "http_status_code":  None,
        "exception_class":   None,
        "exception_message": None,
        "db_query_time_ms":  None,
        "environment":       "prod-sim",
        "_anomaly":          None
    }
]

SAMPLE_KAFKA_STREAM = [
    {
        "timestamp":                  "2026-03-05T00:00:00.000Z",
        "event_id":                   "evt-0001-001001",
        "correlation_id":             None,
        "atm_id":                     "ATM-GB-0001",
        "atm_status":                 "Online",
        "transaction_rate_tps":       1.35,
        "response_time_ms":           278,
        "transaction_volume":         4,
        "transaction_success_rate":   99.3,
        "transaction_failure_reason": "NONE",
        "failure_count":              0,
        "window_duration_seconds":    60,
        "kafka_partition":            0,
        "kafka_offset":               1001,
        "_anomaly":                   None
    }
]

SAMPLE_PROMETHEUS_METRICS = (
    "timestamp,metric_name,metric_type,metric_value,service_name,"
    "pod_name,container_id,label_area,label_env,help_text,_anomaly\n"
    "2026-03-05T00:00:00.000Z,jvm_memory_used_bytes,gauge,320240054,"
    "terminal-handler,terminal-handler-pod-7d9f-xk2lp,a3f2b19c04d1,"
    "heap,prod-sim,Used bytes of JVM heap memory,\n"
)

SAMPLE_WINDOWS_METRICS = (
    "timestamp,atm_id,hostname,os_version,cpu_usage_percent,memory_used_mb,"
    "memory_total_mb,memory_usage_percent,disk_read_bytes_per_sec,"
    "disk_write_bytes_per_sec,disk_free_gb,network_bytes_sent_per_sec,"
    "network_bytes_recv_per_sec,network_errors,process_count,"
    "system_uptime_seconds,event_log_errors_last_min,_anomaly\n"
    "2026-03-05T00:00:00.000Z,ATM-GB-0001,ATM-HOST-0001,"
    "Windows 10 LTSB 2016 Build 14393,11.1,1835.2,4096.0,44.8,"
    "190223,51619,18.6,10513,8206,0,71,861908,0,\n"
)

SAMPLE_GCP_METRICS = (
    "timestamp,project_id,resource_type,resource_id,zone,metric_name,"
    "metric_value,metric_unit,cpu_usage_percent,memory_usage_bytes,"
    "memory_limit_bytes,network_ingress_bytes,network_egress_bytes,"
    "restart_count,label_app,label_env,label_version,_anomaly\n"
    "2026-03-05T00:00:00.000Z,synth-banking-sim-001,gke_container,"
    "terminal-handler-pod-7d9f-xk2lp,europe-west2-b,"
    "container/cpu/usage_time,0.0838,s{CPU},8.38,312923413,"
    "1073741824,178504,107449,0,terminal-handler,prod-sim,2.7.0,\n"
)


# ──────────────────────────────────────────────────────────────────────────────
# Base class — sets up a temporary folder for each test so files don't clash
# ──────────────────────────────────────────────────────────────────────────────

class BaseTestCase(unittest.TestCase):

    def setUp(self):
        # create a fresh temporary directory for each test
        self.testDir = tempfile.mkdtemp()

        # point ingest.py's globals at the temp directory
        self.originalOutputFolder = ingest.OutputFolder
        ingest.OutputFolder = self.testDir

    def tearDown(self):
        # delete the temporary directory and restore the original output folder
        shutil.rmtree(self.testDir)
        ingest.OutputFolder = self.originalOutputFolder

    def writeJSON(self, filename, data):
        # helper: write a list of dicts as a JSON file in the temp directory
        path = os.path.join(self.testDir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return path

    def writeCSV(self, filename, content):
        # helper: write a raw CSV string as a file in the temp directory
        path = os.path.join(self.testDir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def writeEmpty(self, filename):
        # helper: write a completely empty file in the temp directory
        path = os.path.join(self.testDir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write("")
        return path

    def readOutput(self, filename):
        # helper: read back an output file and return all rows as a list of lists
        path = os.path.join(self.testDir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            return list(reader)


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — Test each of the 7 parsers against a sample synthetic record
# ══════════════════════════════════════════════════════════════════════════════

class TestATMAppLogParser(BaseTestCase):

    def test_sample_record_is_written(self):
        # write a sample JSON file and point ingest at it
        path = self.writeJSON("atm_application_log.json", SAMPLE_ATM_APP_LOG)
        ingest.FILE_ATM_APP_LOG = path

        ingest.loadATMAppLog()

        rows = self.readOutput("atm_application_logs.txt")
        # header + 1 data row
        self.assertEqual(len(rows), 2)

    def test_correct_values_are_written(self):
        path = self.writeJSON("atm_application_log.json", SAMPLE_ATM_APP_LOG)
        ingest.FILE_ATM_APP_LOG = path

        ingest.loadATMAppLog()

        rows = self.readOutput("atm_application_logs.txt")
        dataRow = rows[1]

        self.assertEqual(dataRow[0], "2026-03-05T00:00:00.000Z")  # timestamp
        self.assertEqual(dataRow[1], "INFO")                       # log_level
        self.assertEqual(dataRow[2], "ATM-GB-0001")                # atm_id
        self.assertEqual(dataRow[3], "LOC-0101")                   # location_code
        self.assertEqual(dataRow[7], "STARTUP")                    # event_type
        self.assertEqual(dataRow[14], "Online")                    # atm_status
        self.assertEqual(dataRow[16], "3.4.1-build.209")           # app_version

    def test_header_row_is_correct(self):
        path = self.writeJSON("atm_application_log.json", SAMPLE_ATM_APP_LOG)
        ingest.FILE_ATM_APP_LOG = path

        ingest.loadATMAppLog()

        rows = self.readOutput("atm_application_logs.txt")
        self.assertEqual(rows[0][0], "timestamp")
        self.assertEqual(rows[0][2], "atm_id")


class TestATMHardwareLogParser(BaseTestCase):

    def test_sample_record_is_written(self):
        path = self.writeJSON("atm_hardware_sensor_log.json", SAMPLE_ATM_HW_LOG)
        ingest.FILE_ATM_HW_LOG = path

        ingest.loadATMHardwareLog()

        rows = self.readOutput("atm_hardware_sensor_logs.txt")
        self.assertEqual(len(rows), 2)

    def test_correct_values_are_written(self):
        path = self.writeJSON("atm_hardware_sensor_log.json", SAMPLE_ATM_HW_LOG)
        ingest.FILE_ATM_HW_LOG = path

        ingest.loadATMHardwareLog()

        rows = self.readOutput("atm_hardware_sensor_logs.txt")
        dataRow = rows[1]

        self.assertEqual(dataRow[0], "2026-03-05T00:00:00.000Z")  # timestamp
        self.assertEqual(dataRow[1], "ATM-GB-0001")                # atm_id
        self.assertEqual(dataRow[3], "TEMPERATURE_SENSOR")         # component
        self.assertEqual(dataRow[4], "TEMPERATURE_NORMAL")         # event_type
        self.assertEqual(dataRow[5], "INFO")                       # severity


class TestTerminalHandlerLogParser(BaseTestCase):

    def test_sample_record_is_written(self):
        path = self.writeJSON("terminal_handler_app_log.json", SAMPLE_TERMINAL_LOG)
        ingest.FILE_TERMINAL_LOG = path

        ingest.loadTerminalHandlerLog()

        rows = self.readOutput("terminal_handler_app_log.txt")
        self.assertEqual(len(rows), 2)

    def test_correct_values_are_written(self):
        path = self.writeJSON("terminal_handler_app_log.json", SAMPLE_TERMINAL_LOG)
        ingest.FILE_TERMINAL_LOG = path

        ingest.loadTerminalHandlerLog()

        rows = self.readOutput("terminal_handler_app_log.txt")
        dataRow = rows[1]

        self.assertEqual(dataRow[0], "2026-03-05T00:00:00.000Z")  # timestamp
        self.assertEqual(dataRow[1], "INFO")                       # log_level
        self.assertEqual(dataRow[2], "terminal-handler")           # service_name
        self.assertEqual(dataRow[9], "STARTUP")                    # event_type
        self.assertEqual(dataRow[18], "prod-sim")                  # environment


class TestKafkaStreamParser(BaseTestCase):

    def test_sample_record_is_written(self):
        path = self.writeJSON("kafka_atm_metrics_stream.json", SAMPLE_KAFKA_STREAM)
        ingest.FILE_KAFKA_STREAM = path

        ingest.loadKafkaStream()

        rows = self.readOutput("kafka_atm_metrics_stream.txt")
        self.assertEqual(len(rows), 2)

    def test_correct_values_are_written(self):
        path = self.writeJSON("kafka_atm_metrics_stream.json", SAMPLE_KAFKA_STREAM)
        ingest.FILE_KAFKA_STREAM = path

        ingest.loadKafkaStream()

        rows = self.readOutput("kafka_atm_metrics_stream.txt")
        dataRow = rows[1]

        self.assertEqual(dataRow[0], "2026-03-05T00:00:00.000Z")  # timestamp
        self.assertEqual(dataRow[1], "evt-0001-001001")            # event_id
        self.assertEqual(dataRow[3], "ATM-GB-0001")                # atm_id
        self.assertEqual(dataRow[4], "Online")                     # atm_status


class TestPrometheusMetricsParser(BaseTestCase):

    def test_sample_record_is_written(self):
        path = self.writeCSV("prometheus_metrics.csv", SAMPLE_PROMETHEUS_METRICS)
        ingest.FILE_PROMETHEUS_METRICS = path

        ingest.loadPrometheusMetrics()

        rows = self.readOutput("prometheus_metrics.txt")
        self.assertEqual(len(rows), 2)

    def test_correct_values_are_written(self):
        path = self.writeCSV("prometheus_metrics.csv", SAMPLE_PROMETHEUS_METRICS)
        ingest.FILE_PROMETHEUS_METRICS = path

        ingest.loadPrometheusMetrics()

        rows = self.readOutput("prometheus_metrics.txt")
        dataRow = rows[1]

        self.assertEqual(dataRow[0], "2026-03-05T00:00:00.000Z")  # timestamp
        self.assertEqual(dataRow[1], "jvm_memory_used_bytes")      # metric_name
        self.assertEqual(dataRow[2], "gauge")                      # metric_type
        self.assertEqual(dataRow[4], "terminal-handler")           # service_name


class TestWindowsMetricsParser(BaseTestCase):

    def test_sample_record_is_written(self):
        path = self.writeCSV("windows_os_metrics.csv", SAMPLE_WINDOWS_METRICS)
        ingest.FILE_WINDOWS_METRICS = path

        ingest.loadWindowsMetrics()

        rows = self.readOutput("windows_os_metrics.txt")
        self.assertEqual(len(rows), 2)

    def test_correct_values_are_written(self):
        path = self.writeCSV("windows_os_metrics.csv", SAMPLE_WINDOWS_METRICS)
        ingest.FILE_WINDOWS_METRICS = path

        ingest.loadWindowsMetrics()

        rows = self.readOutput("windows_os_metrics.txt")
        dataRow = rows[1]

        self.assertEqual(dataRow[0], "2026-03-05T00:00:00.000Z")  # timestamp
        self.assertEqual(dataRow[1], "ATM-GB-0001")                # atm_id
        self.assertEqual(dataRow[2], "ATM-HOST-0001")              # hostname
        self.assertEqual(dataRow[4], "11.1")                       # cpu_usage_percent


class TestGCPMetricsParser(BaseTestCase):

    def test_sample_record_is_written(self):
        path = self.writeCSV("gcp_cloud_metrics.csv", SAMPLE_GCP_METRICS)
        ingest.FILE_GCP_METRICS = path

        ingest.loadGCPMetrics()

        rows = self.readOutput("gcp_cloud_metrics.txt")
        self.assertEqual(len(rows), 2)

    def test_correct_values_are_written(self):
        path = self.writeCSV("gcp_cloud_metrics.csv", SAMPLE_GCP_METRICS)
        ingest.FILE_GCP_METRICS = path

        ingest.loadGCPMetrics()

        rows = self.readOutput("gcp_cloud_metrics.txt")
        dataRow = rows[1]

        self.assertEqual(dataRow[0], "2026-03-05T00:00:00.000Z")        # timestamp
        self.assertEqual(dataRow[1], "synth-banking-sim-001")            # project_id
        self.assertEqual(dataRow[2], "gke_container")                    # resource_type
        self.assertEqual(dataRow[5], "container/cpu/usage_time")         # metric_name


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — Test the three malformed input handler functions directly
# ══════════════════════════════════════════════════════════════════════════════

class TestIsFileEmpty(BaseTestCase):

    def test_empty_file_returns_true(self):
        path = self.writeEmpty("empty.json")
        result = ingest.isFileEmpty(path)
        self.assertTrue(result)

    def test_whitespace_only_file_returns_true(self):
        path = os.path.join(self.testDir, "whitespace.json")
        with open(path, 'w') as f:
            f.write("   \n  ")
        result = ingest.isFileEmpty(path)
        self.assertTrue(result)

    def test_file_with_content_returns_false(self):
        path = self.writeJSON("notempty.json", [{"key": "value"}])
        result = ingest.isFileEmpty(path)
        self.assertFalse(result)


class TestIsValidTimestamp(BaseTestCase):

    def test_valid_timestamp_returns_true(self):
        result = ingest.isValidTimestamp("2026-03-05T00:00:00.000Z", 1, "test.json")
        self.assertTrue(result)

    def test_valid_timestamp_without_milliseconds_returns_true(self):
        result = ingest.isValidTimestamp("2026-03-05T00:00:00Z", 1, "test.json")
        self.assertTrue(result)

    def test_missing_timestamp_returns_false(self):
        result = ingest.isValidTimestamp("", 1, "test.json")
        self.assertFalse(result)

    def test_none_timestamp_returns_false(self):
        result = ingest.isValidTimestamp(None, 1, "test.json")
        self.assertFalse(result)

    def test_bad_timestamp_format_returns_false(self):
        result = ingest.isValidTimestamp("05/03/2026 00:00:00", 1, "test.json")
        self.assertFalse(result)

    def test_random_string_returns_false(self):
        result = ingest.isValidTimestamp("not-a-date", 1, "test.json")
        self.assertFalse(result)


class TestCheckRequiredFields(BaseTestCase):

    def test_all_fields_present_returns_true(self):
        rec = {
            "timestamp":   "2026-03-05T00:00:00.000Z",
            "log_level":   "INFO",
            "atm_id":      "ATM-GB-0001",
            "event_type":  "STARTUP",
            "message":     "Started.",
            "component":   "BootManager",
            "atm_status":  "Online",
            "app_version": "3.4.1-build.209",
            "location_code": "LOC-0101"
        }
        requiredFields = ["timestamp", "log_level", "atm_id", "event_type",
                          "message", "component", "atm_status", "app_version", "location_code"]
        result = ingest.checkRequiredFields(rec, requiredFields, 1, "test.json")
        self.assertTrue(result)

    def test_missing_field_returns_false(self):
        rec = {
            "timestamp":  "2026-03-05T00:00:00.000Z",
            "log_level":  "INFO",
            # atm_id is missing
            "event_type": "STARTUP",
            "message":    "Started.",
            "component":  "BootManager",
            "atm_status": "Online",
            "app_version": "3.4.1-build.209",
            "location_code": "LOC-0101"
        }
        requiredFields = ["timestamp", "log_level", "atm_id", "event_type",
                          "message", "component", "atm_status", "app_version", "location_code"]
        result = ingest.checkRequiredFields(rec, requiredFields, 1, "test.json")
        self.assertFalse(result)

    def test_none_value_returns_false(self):
        rec = {
            "timestamp":     "2026-03-05T00:00:00.000Z",
            "log_level":     None,   # None value on a required field
            "atm_id":        "ATM-GB-0001",
            "event_type":    "STARTUP",
            "message":       "Started.",
            "component":     "BootManager",
            "atm_status":    "Online",
            "app_version":   "3.4.1-build.209",
            "location_code": "LOC-0101"
        }
        requiredFields = ["timestamp", "log_level", "atm_id", "event_type",
                          "message", "component", "atm_status", "app_version", "location_code"]
        result = ingest.checkRequiredFields(rec, requiredFields, 1, "test.json")
        self.assertFalse(result)

    def test_empty_string_value_returns_false(self):
        rec = {
            "timestamp":     "2026-03-05T00:00:00.000Z",
            "log_level":     "INFO",
            "atm_id":        "",     # empty string on a required field
            "event_type":    "STARTUP",
            "message":       "Started.",
            "component":     "BootManager",
            "atm_status":    "Online",
            "app_version":   "3.4.1-build.209",
            "location_code": "LOC-0101"
        }
        requiredFields = ["timestamp", "log_level", "atm_id", "event_type",
                          "message", "component", "atm_status", "app_version", "location_code"]
        result = ingest.checkRequiredFields(rec, requiredFields, 1, "test.json")
        self.assertFalse(result)


# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — Test that malformed records are skipped inside the full loaders
# ══════════════════════════════════════════════════════════════════════════════

class TestMalformedInputInLoaders(BaseTestCase):

    def test_atm_app_log_skips_record_with_missing_field(self):
        # record is missing atm_id which is required
        badRecord = [
            {
                "timestamp":     "2026-03-05T00:00:00.000Z",
                "log_level":     "INFO",
                # atm_id missing
                "location_code": "LOC-0101",
                "event_type":    "STARTUP",
                "message":       "Started.",
                "component":     "BootManager",
                "atm_status":    "Online",
                "app_version":   "3.4.1-build.209"
            }
        ]
        path = self.writeJSON("atm_application_log.json", badRecord)
        ingest.FILE_ATM_APP_LOG = path

        ingest.loadATMAppLog()

        rows = self.readOutput("atm_application_logs.txt")
        # only the header row, no data rows written
        self.assertEqual(len(rows), 1)

    def test_atm_app_log_skips_record_with_bad_timestamp(self):
        badRecord = [
            {
                "timestamp":     "not-a-date",
                "log_level":     "INFO",
                "atm_id":        "ATM-GB-0001",
                "location_code": "LOC-0101",
                "event_type":    "STARTUP",
                "message":       "Started.",
                "component":     "BootManager",
                "atm_status":    "Online",
                "app_version":   "3.4.1-build.209"
            }
        ]
        path = self.writeJSON("atm_application_log.json", badRecord)
        ingest.FILE_ATM_APP_LOG = path

        ingest.loadATMAppLog()

        rows = self.readOutput("atm_application_logs.txt")
        self.assertEqual(len(rows), 1)

    def test_atm_app_log_skips_empty_file(self):
        path = self.writeEmpty("atm_application_log.json")
        ingest.FILE_ATM_APP_LOG = path

        # should return early without creating an output file
        ingest.loadATMAppLog()

        outputPath = os.path.join(self.testDir, "atm_application_logs.txt")
        self.assertFalse(os.path.exists(outputPath))

    def test_atm_app_log_writes_good_skips_bad(self):
        # mix of one good and one bad record — only the good one should be written
        mixedRecords = [
            {
                "timestamp":     "2026-03-05T00:00:00.000Z",
                "log_level":     "INFO",
                "atm_id":        "ATM-GB-0001",
                "location_code": "LOC-0101",
                "event_type":    "STARTUP",
                "message":       "Started.",
                "component":     "BootManager",
                "atm_status":    "Online",
                "app_version":   "3.4.1-build.209"
            },
            {
                "timestamp":     "bad-timestamp",
                "log_level":     "INFO",
                "atm_id":        "ATM-GB-0002",
                "location_code": "LOC-0102",
                "event_type":    "STARTUP",
                "message":       "Started.",
                "component":     "BootManager",
                "atm_status":    "Online",
                "app_version":   "3.4.1-build.209"
            }
        ]
        path = self.writeJSON("atm_application_log.json", mixedRecords)
        ingest.FILE_ATM_APP_LOG = path

        ingest.loadATMAppLog()

        rows = self.readOutput("atm_application_logs.txt")
        # header + 1 good row only
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][2], "ATM-GB-0001")

    def test_kafka_stream_skips_record_with_missing_atm_status(self):
        # atm_status is required per schema - A7 anomaly signal
        badRecord = [
            {
                "timestamp":                  "2026-03-05T00:00:00.000Z",
                "event_id":                   "evt-0001-001001",
                "correlation_id":             None,
                "atm_id":                     "ATM-GB-0001",
                # atm_status missing
                "transaction_rate_tps":       1.35,
                "response_time_ms":           278,
                "transaction_volume":         4,
                "transaction_success_rate":   99.3,
                "transaction_failure_reason": "NONE",
                "failure_count":              0,
                "window_duration_seconds":    60
            }
        ]
        path = self.writeJSON("kafka_atm_metrics_stream.json", badRecord)
        ingest.FILE_KAFKA_STREAM = path

        ingest.loadKafkaStream()

        rows = self.readOutput("kafka_atm_metrics_stream.txt")
        self.assertEqual(len(rows), 1)

    def test_atm_app_log_skips_record_where_all_fields_are_null(self):
    # a record where every field is null / empty
    allNullRecord = [
        {
            "timestamp":        None,
            "log_level":        None,
            "atm_id":           None,
            "location_code":    None,
            "session_id":       None,
            "correlation_id":   None,
            "transaction_id":   None,
            "event_type":       None,
            "message":          None,
            "component":        None,
            "thread_id":        None,
            "response_time_ms": None,
            "error_code":       None,
            "error_detail":     None,
            "atm_status":       None,
            "os_version":       None,
            "app_version":      None,
            "_anomaly":         None
        }
    ]
    path = self.writeJSON("atm_application_log.json", allNullRecord)
    ingest.FILE_ATM_APP_LOG = path

    ingest.loadATMAppLog()

    rows = self.readOutput("atm_application_logs.txt")
    # only the header row — the null record should be skipped entirely
    self.assertEqual(len(rows), 1)


# ──────────────────────────────────────────────────────────────────────────────
# Run all tests
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
