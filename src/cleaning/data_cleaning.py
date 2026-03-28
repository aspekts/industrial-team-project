import csv
import os

from src.cleaning.schemas import LOG_SCHEMAS

class LogCleaner:
    def __init__(self, db_handler, input_dir, error_dir):
        self.input_dir = input_dir
        self.db_handler = db_handler
        self.error_dir = error_dir

    def find_schema(self, raw_line):
        """Returns the schema name if keys match exactly."""
        line_keys = set(raw_line.keys())
        
        for schema_name, schema_keys in LOG_SCHEMAS.items():
            if line_keys == set(schema_keys.keys()):
                return schema_name
        return None
    
    def validate_fields(self, raw_line, schema_type):
        schema = LOG_SCHEMAS.get(schema_type)

        raw_keys = set(raw_line.keys())
        # Maybe I'll need a set here too, need to check later how it works on broken JSON shapes
        expected_keys = set(schema.keys())

        missing = expected_keys - raw_keys
        if missing:
            print(f"Missing keys: {missing}.")

        extra_keys = raw_keys - expected_keys
        if extra_keys:
            print(f"Extra keys: {extra_keys}.")

        if raw_keys != expected_keys:
            return False
        
        return True
    

    def validate_types(self, raw_line, schema_type):
        schema = LOG_SCHEMAS.get(schema_type)

        # print(f"Checking value types for the following log:\n{raw_line}")

        for field, expected_type in schema.items():
            raw_value = raw_line.get(field)

            if not isinstance(raw_value, expected_type):
                print(f"Log has a wrong type in field {field}, expected type - {expected_type}.")
                return False
            
        return True

    def convert_types(self, raw_log, schema_type):
        schema = LOG_SCHEMAS.get(schema_type)

        clean_log = {}

        for field, exp_type in schema.items():
            target = raw_log.get(field)

            #if not target:
            #    clean_log[field] = None
            #    continue

            type_list = exp_type if isinstance(exp_type, tuple) else (exp_type,)

            null_fields = ["None", "Null", "", "NONE", "NULL"]

            if target is None or str(target).strip() in null_fields:
                clean_log[field] = None
                continue

            for t in type_list:
                try:
                    if t is type(None):
                        clean_log[field] = None
                        break
                    
                    clean_log[field] = t(target)
                    break
                except Exception:
                    continue

        return clean_log

    def process_all_files(self):
        buffer = []
        batch_size = 100
        broken_logs = []

        for filename in os.listdir(self.input_dir):
            if not filename.endswith(".txt"):
                continue

            file_path = os.path.join(self.input_dir, filename)
            print(f"Reading {filename}...")

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for line in reader:
                    schema = self.find_schema(line)
                    if not schema:
                        broken_logs.append(line)
                        continue

                    try:
                        clean_line = self.convert_types(line, schema)
                        if not self.validate_types(clean_line, schema):
                            broken_logs.append(line)
                            continue
                        
                        buffer.append((schema, clean_line))
                    except Exception:
                        broken_logs.append(line)
                        continue

                    if len(buffer) >= batch_size:
                        self.db_handler.load_to_sql(buffer)
                        buffer = []

        if buffer:
            self.db_handler.load_to_sql(buffer)

        if broken_logs:
            error_path = self.error_dir + "/broken_logs.json"
            with open(error_path, "w", encoding='utf-8') as err:
                json.dump(broken_logs, err, indent=4)
                print(f"Saved broken log to {error_path}")

            
        print("[INFO] Data loaded to SQL.")