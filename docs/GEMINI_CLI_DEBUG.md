# Gemini CLI Debugging Guide

## Log Locations
-   **General Logs:** `logs/app.log` (or specific module logs).
-   **DB Factory Log:** `.jules_state/db_factory.log`.
-   **Error Ledger:** `.jules_state/error_ledger.md`.

## Known Fragile Points
-   **Google Maps Scraper:** DOM selectors in `modules/harvester/scraper.py` (TBD) are subject to change by Google.
-   **Network Timeouts:** Website scraping in Phase 2 may timeout.

## Test Commands
-   **Harvester Validation:** `python modules/harvester/validate.py` (TBD).
-   **Enrichment Validation:** `python modules/enrichment/validate.py` (TBD).
-   **Aggregator Validation:** `python modules/aggregator/validate.py` (TBD).
