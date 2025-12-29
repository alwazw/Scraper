import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.logging_config import setup_logger

logger = setup_logger('validator_aggregator', 'modules/aggregator/validation.log')

MASTER_DB_PATH = 'final_delivery/master_leads.db'
MASTER_SCHEMA = 'master_leads'

def validate_aggregator():
    logger.info("Starting Validation for Phase 3: Aggregator")

    # Check 1: Master DB Exists
    if not os.path.exists(MASTER_DB_PATH):
        logger.error(f"Validation Failed: Master DB {MASTER_DB_PATH} does not exist.")
        return False

    try:
        conn = sqlite3.connect(MASTER_DB_PATH)
        cursor = conn.cursor()

        # Check 2: Schema Validation
        cursor.execute(f"PRAGMA table_info({MASTER_SCHEMA})")
        columns = [info[1] for info in cursor.fetchall()]

        required_columns = ["business_name", "phone_number", "website", "email", "facebook_url", "instagram_url", "linkedin_url", "address", "source_url"]
        for col in required_columns:
            if col not in columns:
                logger.error(f"Validation Failed: Column {col} missing in schema.")
                return False

        # Check 3: Data Integrity
        cursor.execute(f"SELECT COUNT(*) FROM {MASTER_SCHEMA}")
        count = cursor.fetchone()[0]
        logger.info(f"Master database contains {count} rows.")

        if count == 0:
            logger.error("Validation Failed: Master DB is empty.")
            return False

        # Check 4: Check if email fields are populated (at least some)
        cursor.execute(f"SELECT COUNT(*) FROM {MASTER_SCHEMA} WHERE email IS NOT NULL")
        email_count = cursor.fetchone()[0]
        logger.info(f"Records with email: {email_count}")

        # Check 5: Check if data looks clean (e.g. phone numbers are digits/normalized)
        cursor.execute(f"SELECT phone_number FROM {MASTER_SCHEMA} WHERE phone_number IS NOT NULL LIMIT 5")
        phones = cursor.fetchall()
        for p in phones:
            logger.info(f"Sample Phone: {p[0]}")
            # Simple check: no letters
            if any(c.isalpha() for c in p[0]):
                 logger.warning(f"Phone number {p[0]} contains letters. Normalization might be weak.")

        conn.close()

        logger.info("Validation Passed: Phase 3 is Green.")
        return True

    except Exception as e:
        logger.error(f"Validation Failed with exception: {e}")
        return False

if __name__ == "__main__":
    if validate_aggregator():
        sys.exit(0)
    else:
        sys.exit(1)
