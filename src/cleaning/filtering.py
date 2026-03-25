import logging 
from datetime import datetime

from src.cleaning.schemas import LOG_SCHEMAS

logger = logging.getLogger(__name__)

# required fields
UNIVERSAL_FIELDS = {
    "correlation_id": (str, type(None)),
    "source": str, 
    "timestamp": str,
    "host_id": (str, type(None)),
    "anomaly_flag": bool,
    "anomaly_type": (str, type(None)),
}

class LogFilter:

    def __init__(self):
        self.seen.records = set()
    
    # duplication detection 
    def is_duplicate(self, record):

        key = (
            record.get("correlation_id"),
            record.get("timestamp"),
            record.get("source"),
        )

        if key in self.seen_records:
            logger.warning(f"duplicate record detected: {key}")
            return True
        
        self.seen_records.add(key)
        return False
    
    # field validation
    def field_validation(self, record):

        for field, expected_type in UNIVERSAL_FIELDS.items():

            if field not in record:
                logger.error(f"missing field: {field}")
                return False
            
            if not isinstance(record[field], expected_type):
                logger.error(f"invalid type for field: {field}")
                return False
            
        return True
    
    # schema validation
    def schema_validation(self, record, source):
        
        if source not in LOG_SCHEMAS:
            logger.error(f"unknown source type: {source}")
            return False
        
        schema = LOG_SCHEMAS[source]

        for field, expected_type in schema.items():

            if field not in record:
                logger.error(f"missing field '{field}' in {source} record")
                return False
            
            if not isinstance(record[field], expected_type):
                logger.error(f"invalid field type '{field}' in {source} record")
                return False
            
        return True
    
    # time validation 
    def time_validation(self, timestamp): 
        
        try:
            ts = datetime.fromisoformat(timestamp)

            if ts.year < 2000 or ts.year > 2100:
                logger.error(f"out of range timestamp: {timestamp}")
                return False
            
            return True

        except Exception:
            logger.error(f"malformed time stamp: {timestamp}")
            return False
        
    # validate record pipeline
    def record_validation(self, record, source):

        if not record:
            logger.error("empty record found")
            return False
        
        if not self.field_validation(record):
            return False
        
        if not self.schema_validation(record, source):
            return False
        
        if not self.time_validation(record.get("timestamp")):
            return False
        
        if self.is_duplicate(record):
            return False
        
        return True
    
    # filtering
    def filter_logs(records, atm_id=None, date=None, error_type=None):

        results = []

        for record in records:

            if atm_id and record.get("atm_id") != atm_id:
                continue

            if date and not record.get("timestamp", "").startswith(date):
                continue

            if error_type and error_type.lower() not in str(record).lower():
                continue

            results.append(record)

        return results
