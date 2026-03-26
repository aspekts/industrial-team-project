# main.py
from src.parsers.ingest import run_ingestion
from src.cleaning.schemas import LOG_SCHEMAS
from src.cleaning.data_cleaning import LogCleaner
from src.cleaning.database import DatabaseHandler

import time

def run_pipeline():
    run_ingestion() 
    
    RAW_DATA_DIR = "data/raw"
    CLEANED_DB_PATH = "data/clean/atm_logs.db"
    ERROR_PATH = "data/clean"

    db_handler = DatabaseHandler(db_path=CLEANED_DB_PATH)
    
    db_handler.setup_database(LOG_SCHEMAS)
    
    cleaner = LogCleaner(db_handler=db_handler, input_dir=RAW_DATA_DIR, error_dir=ERROR_PATH)

    cleaner.process_all_files()

    # db_handler.test_views()

def run_simulation(interval_min=5):
    try:
        while True:
            try:
                run_pipeline()

            except:
                continue
            time.sleep(interval_min * 60)
    except:
        print("Keyboard interrupt.")

    
if __name__ == "__main__":
    run_simulation(1)