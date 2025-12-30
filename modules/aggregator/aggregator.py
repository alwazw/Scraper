import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.db_factory import DBFactory
from common.db_utils import init_db
from common.logging_config import setup_logger

logger = setup_logger('aggregator', 'modules/aggregator/aggregator.log')

RAW_DB_PATH = 'modules/harvester/raw_leads.db'
ENRICHED_DB_PATH = 'modules/enrichment/enriched_data.db'
MASTER_DB_PATH = 'final_delivery/master_leads.db'
MASTER_SCHEMA = 'master_leads'

def normalize_phone(phone):
    if not phone:
        return None
    # Basic normalization: Keep digits and +, remove spaces, parenthesis, dashes
    # If using E.164, we'd need phonenumbers lib, but keeping it simple as per "Zero Touch" constraint
    # to avoid complex dependency issues unless necessary.
    import re
    cleaned = re.sub(r'[^\d+]', '', phone)
    return cleaned

def aggregate_data():
    logger.info("Starting Aggregation Phase...")

    if not os.path.exists(RAW_DB_PATH) or not os.path.exists(ENRICHED_DB_PATH):
        logger.error("Source databases missing.")
        return

    # Connect to DBs
    raw_conn = sqlite3.connect(RAW_DB_PATH)
    raw_conn.row_factory = sqlite3.Row
    raw_cursor = raw_conn.cursor()

    enriched_conn = sqlite3.connect(ENRICHED_DB_PATH)
    enriched_conn.row_factory = sqlite3.Row
    enriched_cursor = enriched_conn.cursor()

    master_factory = DBFactory(MASTER_DB_PATH)
    master_conn = master_factory.get_connection()
    init_db(master_conn, MASTER_SCHEMA)
    master_cursor = master_conn.cursor()

    try:
        # Get all raw leads
        raw_cursor.execute("SELECT * FROM lead_harvest")
        raw_leads = raw_cursor.fetchall()

        count_processed = 0

        for lead in raw_leads:
            lead_id = lead['id']

            # Get enrichment data
            # We take the LATEST enrichment data if multiple exist (ORDER BY id DESC)
            enriched_cursor.execute("SELECT * FROM enrichment WHERE lead_id = ? ORDER BY id DESC LIMIT 1", (lead_id,))
            enrichment = enriched_cursor.fetchone()

            # Prepare Master Record
            business_name = lead['name']
            phone_number = normalize_phone(lead['phone'])
            website = lead['website']
            address = lead['address']
            source_url = lead['google_maps_url']

            email = enrichment['email'] if enrichment else None
            facebook_url = enrichment['facebook'] if enrichment else None
            instagram_url = enrichment['instagram'] if enrichment else None
            linkedin_url = enrichment['linkedin'] if enrichment else None

            # Deduplication Check
            # We check if a record with the same business name and (phone OR website) already exists
            # Actually, the requirement says "Deduplicate (Priority: Keep entries with Email)"
            # Since we are iterating and inserting, we can check if it exists.

            # Simple deduplication: Check by Business Name for now (safest unique identifier usually, though imperfect)
            # Or Google Maps URL if we want strictly unique locations.

            master_cursor.execute("SELECT id, email FROM master_leads WHERE business_name = ?", (business_name,))
            existing = master_cursor.fetchone()

            if existing:
                # If existing has no email but new one does, update it
                if not existing[1] and email:
                    logger.info(f"Updating existing record {business_name} with email.")
                    master_cursor.execute('''
                        UPDATE master_leads SET
                            phone_number = ?, website = ?, email = ?, facebook_url = ?, instagram_url = ?, linkedin_url = ?, address = ?, source_url = ?
                        WHERE id = ?
                    ''', (phone_number, website, email, facebook_url, instagram_url, linkedin_url, address, source_url, existing[0]))
                else:
                    logger.info(f"Skipping duplicate: {business_name}")
            else:
                master_cursor.execute('''
                    INSERT INTO master_leads (business_name, phone_number, website, email, facebook_url, instagram_url, linkedin_url, address, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (business_name, phone_number, website, email, facebook_url, instagram_url, linkedin_url, address, source_url))
                count_processed += 1

        master_conn.commit()
        logger.info(f"Aggregation complete. Processed {len(raw_leads)} raw leads. Added {count_processed} new records.")

    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
    finally:
        raw_conn.close()
        enriched_conn.close()
        master_conn.close()

if __name__ == "__main__":
    aggregate_data()
