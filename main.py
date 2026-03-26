# main.py
from src.parsers.ingest import run_ingestion
from src.cleaning.schemas import LOG_SCHEMAS
from src.cleaning.data_cleaning import LogCleaner
from src.cleaning.database import DatabaseHandler
from src.dashboard.server import create_app

def run_pipeline():
    run_ingestion()

    RAW_DATA_DIR = "data/raw"
    CLEANED_DB_PATH = "data/clean/atm_logs.db"

    db_handler = DatabaseHandler(db_path=CLEANED_DB_PATH)

    db_handler.setup_database(LOG_SCHEMAS)

    cleaner = LogCleaner(db_handler=db_handler, input_dir=RAW_DATA_DIR)

    cleaner.process_all_files()

if __name__ == "__main__":
    run_pipeline()
    app = create_app()
    print("[INFO] Pipeline complete. Starting dashboard at http://127.0.0.1:5000")
    app.run(debug=True)