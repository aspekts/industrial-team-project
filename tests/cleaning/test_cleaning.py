import os
import sqlite3

from src.cleaning.data_cleaning import LogCleaner
from src.cleaning.database import DatabaseHandler
from src.cleaning.schemas import LOG_SCHEMAS

TEST_RAW = "test_data/raw"
TEST_CLEAN = "test_data/clean"
TEST_DB = TEST_CLEAN + "/test_atm.db"

def setup():
    """
    Sets up DatabaseHandler and LogCleaner classes;
    Returns LogCleaner object instance
    """
    # Make sure directories exist
    if not os.path.exists(TEST_RAW):
        os.makedirs(TEST_RAW)
    if not os.path.exists(TEST_CLEAN):
        os.makedirs(TEST_CLEAN)
        
    db = DatabaseHandler(db_path=TEST_DB)
    db.setup_database(LOG_SCHEMAS)
    cleaner = LogCleaner(db, TEST_RAW, TEST_CLEAN)
    
    return cleaner

def test_find_schema(cleaner):
    """
    Tests the find_shema function of LogCleaner class.    
    """
    print("Testing if it can find the right schema.")
    
    # A fake ATMA log row
    fake_atma_log = {
        "timestamp": "2023-10-01", "log_level": "INFO", "atm_id": "ATM1", 
        "location_code": "NY", "session_id": "123", "correlation_id": "456", 
        "transaction_id": "789", "event_type": "TEST", "message": "hello", 
        "component": "app", "thread_id": "1", "response_time_ms": "100", 
        "error_code": "None", "error_detail": "None", "atm_status": "OK", 
        "os_version": "1.0", "app_version": "2.0", "_anomaly": "None"
    }
    
    result = cleaner.find_schema(fake_atma_log)
    
    # Check if the found shcema is the correct one
    assert result == "ATMA", f"Expected ATMA schema type, but got {result}"
    print("Schema finder passed the test.")

def test_convert_types(cleaner):
    """
    Tests convert_types() function of LogCleaner class.
    """
    print("Testing type conversion.")
    
    fake_prom_log = {
        "timestamp": "2023-10-01",
        "metric_name": "cpu_usage",
        "metric_type": "gauge",
        # The following entry needs to be covnerted to float
        "metric_value": "99.5",
        "service_name": "atm-service",
        "pod_name": "pod-1",
        "container_id": "cont-1",
        # The following entry needs to be covnerted to None
        "label_area": "None",
        "label_env": "dev",
        "help_text": "None",
        "_anomaly": "None"
    }
    
    clean_log = cleaner.convert_types(fake_prom_log, "PROM")
    
    # metric_value should become a float
    assert clean_log["metric_value"] == 99.5, "metric_value did not convert to float"
    
    # The string "None" should become a None type
    assert clean_log["label_area"] is None, "label_area did not convert to None"
    print("Type conversion test passed.")

def test_broken_logs(cleaner):
    """
    Test if malformed logs are saved to appropriate file during cleaning pipeline.
    """
    print("Testing if malformed log gets sent to broken_logs.json.")
    error_file = TEST_CLEAN + "/broken_logs.json"

    # Create a fake text file with malformed data
    bad_file_path = TEST_RAW + "/bad_log.txt"
    with open(bad_file_path, "w") as f:
        # write malformed data
        f.write("AT1,time_offset\n")
        f.write("apple,2311-gb\n")
        
    # Run the cleaner
    cleaner.process_all_files()
    
    # Check if broken_logs.json was created in the clean folder
    assert os.path.exists(error_file), "broken_logs.json was not created"
    
    # Remove the fake files
    if os.path.exists(bad_file_path):
        os.remove(bad_file_path)
    if os.path.exists(error_file):
        os.remove(error_file)
    print("Broken log test passed.")

    
def test_database_load(cleaner):
    """
    Tests if the data loads to the database correctly.
    """
    print("Testing if a valid log gets saved to the database.")
    
    good_file_path = TEST_RAW + "/good_log.txt"
    
    # Write this as comma-separated for csv.DictReader used by cleaner
    headers = "timestamp,log_level,atm_id,location_code,session_id,correlation_id,transaction_id,event_type,message,component,thread_id,response_time_ms,error_code,error_detail,atm_status,os_version,app_version,_anomaly"
    values = "2026-03-05T08:00:00.000Z,INFO,ATM-GB-0001,LOC-0101,None,None,None,STARTUP,ATM client application started successfully.,BootManager,1,None,None,None,Online,Windows 10 LTSB 2016,3.4.1-build.209,None"
    
    with open(good_file_path, "w", encoding="utf-8") as f:
        f.write(headers + "\n")
        f.write(values + "\n")
        
    # Process the file and load it to SQL
    cleaner.process_all_files()
    
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    
    # Query the log back from the database
    cursor.execute("SELECT * FROM ATMA WHERE atm_id = 'ATM-GB-0001'")
    rows = cursor.fetchall()
    
    # We expect exactly 1 row to be returned
    assert len(rows) == 1, "The valid log was not found in the database!"

    expected_row = (
        "2026-03-05T08:00:00.000Z",
        "INFO",
        "ATM-GB-0001",
        "LOC-0101",
        None,
        None,
        None,
        "STARTUP",
        "ATM client application started successfully.",
        "BootManager",
        1,
        None,
        None,
        None,
        "Online",
        "Windows 10 LTSB 2016",
        "3.4.1-build.209",
        None
    )
    
    # Check that rows[0] is exactly as we expect it to be
    assert rows[0] == expected_row, f"Query data did not match; \nExpected: {expected_row}\nGot: {rows[0]}"
    
    # Clean up the test file and close the connection
    if os.path.exists(good_file_path):
        os.remove(good_file_path)
    conn.close()
    
    print("Database load test passed.")

def run_cleaning_test():
    """
    Runs all the LogCleaner related tests and cleans up the directory after.
    """
    cleaning_test = setup()
    
    test_find_schema(cleaning_test)
    test_convert_types(cleaning_test)
    test_broken_logs(cleaning_test)
    test_database_load(cleaning_test)

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    if os.path.exists(TEST_RAW):
        os.rmdir(TEST_RAW)
    if os.path.exists(TEST_CLEAN):
        os.rmdir(TEST_CLEAN)
    if os.path.exists("test_data"):
        os.rmdir("test_data")