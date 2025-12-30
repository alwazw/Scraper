import streamlit as st
import json
import os
import subprocess
import time
import sys

# Define Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config/search_manifest.json')
LOG_PATH = os.path.join(PROJECT_ROOT, 'modules/harvester/logs/harvester.log')
SCRAPER_SCRIPT = os.path.join(PROJECT_ROOT, 'modules/harvester/gmaps_scraper.py')

# Ensure directories exist
os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Page Config
st.set_page_config(page_title="Harvester Mission Control", layout="wide")
st.title("🕵️ Harvester Mission Control")

# --- Sidebar: Configuration ---
st.sidebar.header("Configuration")

# Load existing config if available
default_niches = ""
default_locations = ""
default_headless = True
default_max_results = 20

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            default_niches = "\n".join(config.get('niches', []))
            default_locations = "\n".join(config.get('locations', []))
            settings = config.get('settings', {})
            default_headless = settings.get('headless', True)
            default_max_results = settings.get('max_results', 20)
    except Exception as e:
        st.sidebar.error(f"Error loading config: {e}")

# Inputs
niches_input = st.sidebar.text_area("Target Niches (one per line)", value=default_niches, help="e.g. Plumbers\nRoofers")
locations_input = st.sidebar.text_area("Target Locations (one per line)", value=default_locations, help="e.g. Toronto\nNew York")
headless_mode = st.sidebar.checkbox("Headless Mode", value=default_headless)
max_results = st.sidebar.slider("Max Results Per Query", 10, 200, value=default_max_results)

# Actions
col1, col2 = st.sidebar.columns(2)
if col1.button("Reset Form"):
    # Streamlit doesn't support direct reset easily without session state hacks,
    # but reloading the page or clearing session state works.
    # For now, we'll just advise user.
    st.sidebar.info("Refresh page to reset.")

if col2.button("Save Configuration"):
    niches = [n.strip() for n in niches_input.split('\n') if n.strip()]
    locations = [l.strip() for l in locations_input.split('\n') if l.strip()]

    if not niches:
        st.error("You must define at least one niche.")
    elif not locations:
        st.error("You must define at least one location.")
    else:
        config_data = {
            "niches": niches,
            "locations": locations,
            "settings": {
                "headless": headless_mode,
                "max_results": max_results
            }
        }
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config_data, f, indent=4)
            st.sidebar.success("Configuration Saved!")
        except Exception as e:
            st.sidebar.error(f"Failed to save config: {e}")

# --- Main Panel: Execution ---
st.header("Execution Panel")

# Check if running
lock_file = os.path.join(PROJECT_ROOT, '.harvester.lock') # Simple lock mechanism

# Session state for process tracking is tricky with Streamlit re-runs.
# We'll use a simple approach: if user clicks start, we spawn process.
# We can't easily track the exact PID across reloads without persistent storage or global state.
# But for "Start/Stop", we can check if a python process running our script exists.

def is_running():
    # Only checks if OUR specific script is running
    try:
        # Grep for the script name in process list
        # This is Linux specific.
        result = subprocess.run(['pgrep', '-f', SCRAPER_SCRIPT], stdout=subprocess.PIPE)
        return result.returncode == 0
    except:
        return False

running = is_running()

if running:
    st.warning("⚠️ Scraper is currently RUNNING")
    if st.button("STOP SCRAPING"):
        # Kill the process
        try:
            subprocess.run(['pkill', '-f', SCRAPER_SCRIPT])
            st.success("Scraper Stopped.")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Failed to stop: {e}")
else:
    st.info("🟢 System Ready")
    if st.button("START HARVESTER", type="primary"):
        try:
            # Run in background
            # We use subprocess.Popen
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen([sys.executable, SCRAPER_SCRIPT], stdout=devnull, stderr=devnull)
            st.success("Harvester Started!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Failed to start harvester: {e}")

# --- Live Log Console ---
st.subheader("Live Logs")
log_container = st.empty()

# We can't do a true infinite loop here or Streamlit blocks.
# But we can read the file once.
# To make it "live", users usually rely on st.empty() and a loop,
# but that blocks interaction.
# A better way for Streamlit is `st.fragment` (new) or just showing the last lines.
# The prompt asks for "auto-refreshes".
# We can use `st.empty` with a short loop, but that might prevent clicking "Stop".
# Standard pattern: Show logs, add a "Refresh" button, or use `st_autorefresh` component if allowed.
# Since I can't install arbitrary custom components easily without checking,
# I will implement a text area that shows current logs.
# Streamlit has `st.rerun()` but we don't want to rerun the whole page constantly.
# I'll just show the logs. The user can interact to refresh (e.g. click "Update Logs" or just interactions trigger re-run).
# Wait, prompt says "auto-refreshes".
# I'll simulate it with a loop that breaks if session state changes or after some time, or just let the user refresh.
# Actually, standard simple streamlit:
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, 'r') as f:
        lines = f.readlines()
        last_lines = lines[-50:]
        log_content = "".join(last_lines)
else:
    log_content = "No logs found yet."

st.text_area("Log Output", log_content, height=300)

if running:
    # Auto-refresh mechanism
    time.sleep(2)
    st.rerun()
