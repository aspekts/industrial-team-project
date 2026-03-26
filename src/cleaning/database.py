import sqlite3

class DatabaseHandler:
    def __init__(self, db_path="data/clean/atm_logs.db"):
        self.db_path = db_path

    def _get_sql_type(self, py_type):
        if isinstance(py_type, tuple):
            py_type = py_type[0]
            
        if py_type == int:
            return "INTEGER"
        elif py_type == float:
            return "REAL"
        elif py_type == str:
            return "TEXT"
        else:
            return "TEXT"

    def setup_database(self, schemas):        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for table_name, schema in schemas.items():
                columns = []
                for field, expected_type in schema.items():
                    sql_type = self._get_sql_type(expected_type)
                    columns.append(f"{field} {sql_type}")

                columns_sql = ", ".join(columns)
                query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql});"
                
                cursor.execute(query)
                
        print("Database tables are ready!")

    def load_to_sql(self, buffer):
        if not buffer:
            return

        batches = {}
        for table_name, clean_line in buffer:
            if table_name not in batches:
                batches[table_name] = []
            
            batches[table_name].append(tuple(clean_line.values()))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for table_name, rows in batches.items():
                if not rows:
                    continue
                    
                num_columns = len(rows[0])
                placeholders = ", ".join(["?"] * num_columns)
                
                query = f"INSERT INTO {table_name} VALUES ({placeholders})"
                
                cursor.executemany(query, rows)

    def setup_atm_view_generic(self):
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
            
            cursor.execute("SELECT DISTINCT atm_id FROM ATMA WHERE atm_id IS NOT NULL")
            atm_ids = [row[0] for row in cursor.fetchall()]
            
            for atm in atm_ids:
                safe_name = atm.replace("-", "_") 
                
                query = f"""
                    CREATE VIEW IF NOT EXISTS view_{safe_name} AS
                    SELECT timestamp, source, event_type, message 
                    FROM view_atm_master_timeline 
                    WHERE atm_id = '{atm}'
                    ORDER BY timestamp;
                """
                cursor.execute(query)

    def test_views(self):
        self.setup_atm_view_generic()
        self.setup_atm_view_individual()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Test if the master view works
            try:
                cursor.execute("SELECT * FROM view_atm_master_timeline LIMIT 5;")
                rows = cursor.fetchall()
                
                if not rows:
                    print("Master view is empty")
                else:
                    for row in rows:
                        print(f"   {row}")
            except Exception as e:
                print("Master view failed")

            # Test if the individual ATM views were created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'view_%';")
            views = cursor.fetchall()
