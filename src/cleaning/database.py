import sqlite3

class DatabaseHandler:
    def __init__(self, db_path="data/clean/atm_logs.db"):
        self.db_path = db_path

    def _get_sql_type(self, py_type):
        """Helper to map Python types to SQLite types."""
        # If the type is a tuple like (int, type(None)), grab the first type
        if isinstance(py_type, tuple):
            py_type = py_type[0]
            
        if py_type is int:
            return "INTEGER"
        elif py_type is float:
            return "REAL"
        elif py_type is str:
            return "TEXT"
        else:
            return "TEXT" # Default fallback

    def setup_database(self, schemas):
        """Creates the tables based on your LOG_SCHEMAS if they don't exist."""
        print(f"Setting up database at {self.db_path}...")
        
        # Using 'with' automatically commits and cleanly closes the connection
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for table_name, schema in schemas.items():
                columns = []
                for field, expected_type in schema.items():
                    sql_type = self._get_sql_type(expected_type)
                    columns.append(f"{field} {sql_type}")

                # Build the SQL string: "CREATE TABLE IF NOT EXISTS ATMA (timestamp TEXT, ...)"
                columns_sql = ", ".join(columns)
                query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql});"
                
                cursor.execute(query)
                
        print("Database tables are ready!")

    def load_to_sql(self, buffer):
        """Sorts the mixed buffer by table and performs a batch insert."""
        if not buffer:
            return

        # 1. Group the mixed buffer into separate buckets for each table
        batches = {}
        for table_name, clean_line in buffer:
            if table_name not in batches:
                batches[table_name] = []
            
            # Convert the dictionary values into a tuple for SQLite
            batches[table_name].append(tuple(clean_line.values()))

        # 2. Open DB and insert everything
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for table_name, rows in batches.items():
                if not rows:
                    continue
                    
                # Dynamically generate the right amount of "?" placeholders
                # e.g., for 3 columns: "?, ?, ?"
                num_columns = len(rows[0])
                placeholders = ", ".join(["?"] * num_columns)
                
                query = f"INSERT INTO {table_name} VALUES ({placeholders})"
                
                # executemany is the secret to high-performance database loading
                cursor.executemany(query, rows)

    def setup_atm_view_generic(self):
        """Creates a master chronological timeline for any ATM."""
        print("Building ATM Master Timeline View...")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS view_atm_master_timeline AS
                
                SELECT timestamp, atm_id, 'APP' AS source, event_type, message, correlation_id
                FROM ATMA
                
                UNION ALL
                
                SELECT timestamp, atm_id, 'HARDWARE' AS source, event_type, message, correlation_id
                FROM ATMH
                
                UNION ALL
                
                SELECT timestamp, atm_id, 'TERMINAL' AS source, event_type, message, correlation_id
                FROM TERM
                WHERE atm_id IS NOT NULL;
            """)
    
    def setup_atm_view_individual(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Find all the unique ATMs in the simulation
            cursor.execute("SELECT DISTINCT atm_id FROM ATMA WHERE atm_id IS NOT NULL")
            atm_ids = [row[0] for row in cursor.fetchall()]
            
            # 2. Create a specific view for each one
            for atm in atm_ids:
                # Clean up the name for SQL (e.g., ATM-GB-0042 -> ATM_GB_0042)
                safe_name = atm.replace("-", "_") 
                
                query = f"""
                    CREATE VIEW IF NOT EXISTS view_{safe_name} AS
                    SELECT timestamp, source, event_type, message 
                    FROM view_atm_master_timeline 
                    WHERE atm_id = '{atm}'
                    ORDER BY timestamp;
                """
                cursor.execute(query)