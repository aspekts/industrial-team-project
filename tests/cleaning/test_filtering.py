import sqlite3
from src.cleaning.filtering import LogFilter

# test that filtering by atm id returns correct rows
def test_atm_filter():

    # create temporary test database
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()

    # add some super simple table for testing
    cursor.execute("CREATE TABLE logs (atm_id TEXT, timestamp TEXT, error_type TEXT)")

    # insert test data
    cursor.execute("INSERT INTO logs VALUES ('ATM1', '2026-01-01', 'ERROR')")
    cursor.execute("INSERT INTO logs VALUES ('ATM2', '2026-01-01', 'OK')")
    cursor.execute("INSERT INTO logs VALUES ('ATM1', '2026-01-02', 'OK')")
    cursor.execute("INSERT INTO logs VALUES ('ATM3', '2026-01-04', 'ERROR')")
    cursor.execute("INSERT INTO logs VALUES ('ATM1', '2026-01-03', 'ERROR')")

    # save and close connection
    conn.commit()
    conn.close()

    f = LogFilter()

    # filter for ATM1
    results = f.filter_logs("test.db", atm_id="ATM1")

    # check theres the expected 3 logs
    assert len(results) == 3

# test that filtering by date returns correct rows
def test_date_filter():

    f = LogFilter()

    # filter by date
    results = f.filter_logs("test.db", date="2026-01-01")

    # check for 2 expected logs
    assert len(results) == 2

# test that filtering by errors returns correct rows
def test_error_filter():

    f = LogFilter()

    # filter for error entry
    results = f.filter_logs("test.db", error_type="ERROR")

    assert len(results) == 3

# test that filtering by combination returns correct rows
def test_combined_filter():

    f = LogFilter()

    results = f.filter_logs("test.db", atm_id="ATM1", error_type="ERROR")

    # should return 2 logs for atm1
    assert len(results) == 2