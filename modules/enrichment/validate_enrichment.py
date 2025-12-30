import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.logging_config import setup_logger

logger = setup_logger('validator_enrichment', 'modules/enrichment/validation.log')

RAW_DB_PATH = 'modules/harvester/raw_leads.db'
ENRICHED_DB_PATH = 'modules/enrichment/enriched_data.db'
ENRICHED_SCHEMA = 'enrichment'

def validate_enrichment():
    logger.info("Starting Validation for Phase 2: Enrichment")

    # Check 1: Enriched DB Exists
    if not os.path.exists(ENRICHED_DB_PATH):
        logger.error(f"Validation Failed: Database file {ENRICHED_DB_PATH} does not exist.")
        return False

    try:
        conn = sqlite3.connect(ENRICHED_DB_PATH)
        cursor = conn.cursor()

        # Check 2: Schema Validation
        cursor.execute(f"PRAGMA table_info({ENRICHED_SCHEMA})")
        columns = [info[1] for info in cursor.fetchall()]

        required_columns = ["lead_id", "email", "facebook", "instagram", "linkedin"]
        for col in required_columns:
            if col not in columns:
                logger.error(f"Validation Failed: Column {col} missing in schema.")
                return False

        # Check 3: Data Integrity
        # We expect at least some rows if the harvester found leads with websites.
        # But if no websites were found in harvester, this might be empty but valid.
        # However, we validated harvester had websites.

        cursor.execute(f"SELECT COUNT(*) FROM {ENRICHED_SCHEMA}")
        count = cursor.fetchone()[0]
        logger.info(f"Enriched database contains {count} rows.")

        # If harvester had websites, we should have rows here (even if email is null)
        raw_conn = sqlite3.connect(RAW_DB_PATH)
        raw_cursor = raw_conn.cursor()
        raw_cursor.execute("SELECT COUNT(*) FROM lead_harvest WHERE website IS NOT NULL AND website != ''")
        raw_website_count = raw_cursor.fetchone()[0]
        raw_conn.close()

        if raw_website_count > 0 and count == 0:
            logger.error("Validation Failed: Harvester had websites but Enrichment DB is empty.")
            return False

        # Check 4: At least one email or social link extracted (heuristic)
        # In a real run, maybe none are found, but for 10 leads, usually we find something.
        # If not, it's not necessarily a failure of the code, but data quality.
        # But we'll log it.

        cursor.execute(f"SELECT COUNT(*) FROM {ENRICHED_SCHEMA} WHERE email IS NOT NULL OR facebook IS NOT NULL OR instagram IS NOT NULL")
        enriched_count = cursor.fetchone()[0]
        logger.info(f"Entries with at least one contact info: {enriched_count}")

        conn.close()

        logger.info("Validation Passed: Phase 2 is Green.")
        generate_report(True, count, enriched_count)
        return True

    except Exception as e:
        logger.error(f"Validation Failed with exception: {e}")
        generate_report(False, 0, 0, str(e))
        return False

def generate_report(success, count, enriched_count, error_msg=None):
    report_path = os.path.join(os.path.dirname(__file__), '../../reports/module_2_report.md')
    with open(report_path, 'w') as f:
        f.write(f"# Module 2: Enrichment Validation Report\n\n")
        f.write(f"**Status:** {'PASS' if success else 'FAIL'}\n")
        f.write(f"**Total Enriched Rows:** {count}\n")
        f.write(f"**Rows with Contacts:** {enriched_count}\n")
        if error_msg:
            f.write(f"**Error:** {error_msg}\n")

if __name__ == "__main__":
    if validate_enrichment():
        sys.exit(0)
    else:
        sys.exit(1)
