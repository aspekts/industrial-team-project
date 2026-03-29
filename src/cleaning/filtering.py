import logging
import sqlite3

logger = logging.getLogger(__name__)


class LogFilter:

    def filter_logs(self, db_path, atm_id=None, date=None, error_type=None):

        conn = sqlite3.connect(db_path)

        # build the query dynamically based on which filters were provided
        query  = "SELECT * FROM logs WHERE 1=1"
        params = []

        if atm_id:
            query += " AND atm_id = ?"
            params.append(atm_id)

        if date:
            query += " AND timestamp LIKE ?"
            params.append(date + "%")

        if error_type:
            query += " AND error_type = ?"
            params.append(error_type)

        cursor = conn.execute(query, params)
        results = cursor.fetchall()

        conn.close()
        return results
