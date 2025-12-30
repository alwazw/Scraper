import asyncio
import random
from playwright.async_api import async_playwright
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from common.db_factory import DBFactory
from common.db_utils import init_db
from common.logging_config import setup_logger

logger = setup_logger('harvester', 'modules/harvester/harvester.log')

DB_PATH = 'modules/harvester/raw_leads.db'
SCHEMA_NAME = 'lead_harvest'

async def exponential_backoff(attempt):
    delay = 2 ** attempt
    logger.info(f"Backoff: Sleeping for {delay} seconds...")
    await asyncio.sleep(delay)

async def scrape_google_maps(query, max_leads=10):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()

        try:
            logger.info(f"Navigating to Google Maps for query: {query}")
            await page.goto("https://www.google.com/maps", timeout=60000)

            # Wait for search box
            await page.wait_for_selector("input#searchboxinput", timeout=10000)
            await page.fill("input#searchboxinput", query)
            await page.press("input#searchboxinput", "Enter")

            logger.info("Search submitted. Waiting for results...")

            # Wait for the feed
            try:
                await page.wait_for_selector("div[role='feed']", timeout=15000)
            except:
                logger.warning("Feed selector not found directly, trying to find result links.")

            # Scroll the feed
            feed = page.locator("div[role='feed']")
            if await feed.count() > 0:
                for _ in range(3):
                    await feed.evaluate("node => node.scrollTop = node.scrollHeight")
                    await asyncio.sleep(2)

            # Get result elements
            results = page.locator("a[href*='/maps/place/']")
            count = await results.count()
            logger.info(f"Found {count} potential results initially.")

            leads = []

            for i in range(min(count, max_leads)):
                try:
                    # Re-query results
                    results = page.locator("a[href*='/maps/place/']")
                    if i >= await results.count():
                        break

                    result = results.nth(i)

                    # Extract Name from list item first (safer)
                    aria_label = await result.get_attribute("aria-label")
                    name = aria_label.split(" · ")[0] if aria_label else "Unknown"
                    # If aria-label is missing or weird, try inner_text of the first child div which often has the title
                    if name == "Unknown" or not name:
                         # Try fallback
                         try:
                             name = await result.locator(".fontHeadlineSmall").first.inner_text()
                         except:
                             pass

                    # Click
                    await result.click()

                    # Wait for URL change
                    try:
                        await page.wait_for_url("**/maps/place/**", timeout=5000)
                    except:
                        logger.warning("URL didn't change, might be already there or failed.")

                    # Wait for details to settle (generic wait)
                    await asyncio.sleep(2)

                    # Try to refine name from details if possible, but don't crash
                    try:
                         # Try finding the specific H1 again, but don't fail if not found
                         # We skip strict checks here and just try to find something plausible if we have "Unknown"
                         if name == "Unknown":
                             details_name = await page.locator("h1.DUwDvf").first.inner_text(timeout=1000)
                             if details_name:
                                 name = details_name
                    except:
                        pass

                    # Phone
                    phone = None
                    phone_loc = page.locator("button[data-item-id^='phone:']")
                    if await phone_loc.count() > 0:
                         phone = await phone_loc.get_attribute("aria-label")
                         if phone:
                             phone = phone.replace("Phone: ", "").strip()

                    # Website
                    website = None
                    website_loc = page.locator("a[data-item-id='authority']")
                    if await website_loc.count() > 0:
                        website = await website_loc.get_attribute("href")

                    # Address
                    address = None
                    address_loc = page.locator("button[data-item-id='address']")
                    if await address_loc.count() > 0:
                        address = await address_loc.get_attribute("aria-label")
                        if address:
                            address = address.replace("Address: ", "").strip()

                    # Google Maps URL
                    google_maps_url = page.url

                    lead = {
                        "name": name,
                        "phone": phone,
                        "website": website,
                        "address": address,
                        "google_maps_url": google_maps_url
                    }

                    logger.info(f"Extracted: {name}")
                    leads.append(lead)

                    # Random delay
                    await asyncio.sleep(random.uniform(1, 2))

                except Exception as e:
                    logger.error(f"Error extracting lead {i}: {e}")
                    continue

            return leads

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return []
        finally:
            await browser.close()

def save_leads(leads):
    db_factory = DBFactory(DB_PATH)
    conn = db_factory.get_connection()

    try:
        init_db(conn, SCHEMA_NAME)
        cursor = conn.cursor()

        for lead in leads:
            try:
                cursor.execute(f'''
                    INSERT OR IGNORE INTO {SCHEMA_NAME} (name, phone, website, address, google_maps_url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (lead['name'], lead['phone'], lead['website'], lead['address'], lead['google_maps_url']))
            except sqlite3.Error as e:
                logger.error(f"Failed to insert lead {lead.get('name')}: {e}")

        conn.commit()
        logger.info(f"Saved {len(leads)} leads to database.")

    except Exception as e:
        logger.error(f"Database operation failed: {e}")
    finally:
        conn.close()

async def main():
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "software companies in San Francisco"

    logger.info(f"Starting harvest for: {query}")

    for attempt in range(3):
        leads = await scrape_google_maps(query)
        if leads:
            save_leads(leads)
            break
        else:
            logger.warning("No leads found or scraping failed. Retrying...")
            await exponential_backoff(attempt)

if __name__ == "__main__":
    asyncio.run(main())
