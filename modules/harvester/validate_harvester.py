import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.logging_config import setup_logger

logger = setup_logger('validator', 'modules/harvester/validation.log')

DB_PATH = 'modules/harvester/raw_leads.db'
SCHEMA_NAME = 'lead_harvest'

def validate_harvester():
    logger.info("Starting Validation for Phase 1: Harvester")

    # Check 1: DB Exists
    if not os.path.exists(DB_PATH):
        logger.error(f"Validation Failed: Database file {DB_PATH} does not exist.")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check 2: Row Count > 0
        cursor.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}")
        count = cursor.fetchone()[0]
        logger.info(f"Database contains {count} rows.")

        if count == 0:
            logger.error("Validation Failed: Database is empty.")
            return False

        # Check 3: Schema Validation (Website Exists)
        # Note: Not all businesses have websites, but the column must exist.
        # We can check if we grabbed at least one website in the dataset.

        cursor.execute(f"PRAGMA table_info({SCHEMA_NAME})")
        columns = [info[1] for info in cursor.fetchall()]

        required_columns = ["name", "phone", "website", "address", "google_maps_url"]
        for col in required_columns:
            if col not in columns:
                logger.error(f"Validation Failed: Column {col} missing in schema.")
                return False

        # Optional: Check if at least one entry has a website or phone
        cursor.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME} WHERE website IS NOT NULL AND website != ''")
        website_count = cursor.fetchone()[0]
        logger.info(f"Entries with website: {website_count}")

        conn.close()

        logger.info("Validation Passed: Phase 1 is Green.")
        generate_report(True, count, website_count)
        return True

    except Exception as e:
        logger.error(f"Validation Failed with exception: {e}")
        generate_report(False, 0, 0, str(e))
        return False

def generate_report(success, count, website_count, error_msg=None):
    report_path = os.path.join(os.path.dirname(__file__), '../../reports/module_1_report.md')
    with open(report_path, 'w') as f:
        f.write(f"# Module 1: Harvester Validation Report\n\n")
        f.write(f"**Status:** {'PASS' if success else 'FAIL'}\n")
        f.write(f"**Rows Extracted:** {count}\n")
        f.write(f"**Rows with Website:** {website_count}\n")
        if error_msg:
            f.write(f"**Error:** {error_msg}\n")

if __name__ == "__main__":
    if validate_harvester():
        sys.exit(0)
    else:
        sys.exit(1)
