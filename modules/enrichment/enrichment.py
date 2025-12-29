import asyncio
import re
import sqlite3
import sys
import os
from playwright.async_api import async_playwright

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.db_factory import DBFactory
from common.db_utils import init_db
from common.logging_config import setup_logger
from urllib.parse import unquote, parse_qs, urlparse

logger = setup_logger('enrichment', 'modules/enrichment/enrichment.log')

RAW_DB_PATH = 'modules/harvester/raw_leads.db'
ENRICHED_DB_PATH = 'modules/enrichment/enriched_data.db'
RAW_SCHEMA = 'lead_harvest'
ENRICHED_SCHEMA = 'enrichment'

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
FACEBOOK_REGEX = r'facebook\.com\/[a-zA-Z0-9\._-]+'
INSTAGRAM_REGEX = r'instagram\.com\/[a-zA-Z0-9\._-]+'
LINKEDIN_REGEX = r'linkedin\.com\/in\/[a-zA-Z0-9\._-]+'

def clean_url(url):
    """Cleans Google Maps redirection URLs to get the actual target URL."""
    if not url:
        return None
    if "/url?q=" in url:
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            if 'q' in qs:
                return qs['q'][0]
        except Exception as e:
            logger.warning(f"Failed to parse URL {url}: {e}")
            return url
    return url

async def extract_contacts(page, url):
    contacts = {
        "email": None,
        "facebook": None,
        "instagram": None,
        "linkedin": None
    }

    clean_target_url = clean_url(url)
    if not clean_target_url:
        return contacts

    try:
        logger.info(f"Visiting {clean_target_url}")
        # 15s timeout as per requirements
        await page.goto(clean_target_url, timeout=15000, wait_until="domcontentloaded")

        # Get all text and hrefs
        content = await page.content()
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => a.href);
        }''')

        # Extract Email (simple regex on content)
        emails = re.findall(EMAIL_REGEX, content)
        # Filter out common false positives (like png@, js@ if regex is loose, but this regex is decent)
        # Also filter out example.com etc.
        valid_emails = [e for e in emails if not e.endswith('.png') and not e.endswith('.jpg') and 'example.com' not in e]
        if valid_emails:
            contacts["email"] = valid_emails[0] # Take first one

        # Extract Socials from links
        for link in links:
            if not contacts["facebook"] and "facebook.com" in link:
                contacts["facebook"] = link
            if not contacts["instagram"] and "instagram.com" in link:
                contacts["instagram"] = link
            if not contacts["linkedin"] and "linkedin.com" in link:
                contacts["linkedin"] = link

        # If email not found in main page, try "Contact" page?
        # Keeping it simple for now as per "Zero Touch" constraint (less complexity = less bugs).
        # We can scan links for "contact" and visit if needed, but strict 15s timeout might be tight.

    except Exception as e:
        logger.warning(f"Failed to process {url}: {e}")
        # Dead links should be logged but not crash

    return contacts

async def process_leads():
    # Read raw leads
    if not os.path.exists(RAW_DB_PATH):
        logger.error("Raw leads DB not found.")
        return

    raw_conn = sqlite3.connect(RAW_DB_PATH)
    raw_cursor = raw_conn.cursor()

    try:
        raw_cursor.execute(f"SELECT id, website FROM {RAW_SCHEMA} WHERE website IS NOT NULL AND website != ''")
        leads = raw_cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Failed to read raw leads: {e}")
        return
    finally:
        raw_conn.close()

    logger.info(f"Found {len(leads)} leads with websites to process.")

    # Setup Enriched DB
    enriched_factory = DBFactory(ENRICHED_DB_PATH)
    enriched_conn = enriched_factory.get_connection()
    init_db(enriched_conn, ENRICHED_SCHEMA)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()

        for lead_id, website in leads:
            contacts = await extract_contacts(page, website)

            # Save to Enriched DB
            try:
                cursor = enriched_conn.cursor()
                cursor.execute(f'''
                    INSERT INTO {ENRICHED_SCHEMA} (lead_id, email, facebook, instagram, linkedin)
                    VALUES (?, ?, ?, ?, ?)
                ''', (lead_id, contacts['email'], contacts['facebook'], contacts['instagram'], contacts['linkedin']))
                enriched_conn.commit()
                logger.info(f"Enriched lead {lead_id} -> Email: {contacts['email']}")
            except sqlite3.Error as e:
                logger.error(f"Failed to save enriched data for lead {lead_id}: {e}")

        await browser.close()

    enriched_conn.close()

if __name__ == "__main__":
    asyncio.run(process_leads())
