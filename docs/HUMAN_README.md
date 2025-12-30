# Human README

## Project Overview
This project is an automated Lead Generation & Aggregation Pipeline. It scrapes business information from Google Maps, visits their websites to find contact details (emails, social media links), and aggregates everything into a master database.

## How to Run
1.  Ensure you have Python installed.
2.  Install dependencies: `pip install -r requirements.txt`.
3.  **Start the Mission Control Dashboard:**
    ```bash
    streamlit run modules/harvester/dashboard.py
    ```
4.  Configure your niches and locations in the dashboard, save, and click "START HARVESTER".

## Output
The final output will be located in `final_delivery/master_leads.db`. You can export this to CSV using any SQLite viewer or the provided export script (TBD).
