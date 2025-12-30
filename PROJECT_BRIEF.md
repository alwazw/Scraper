MASTER PROMPT FOR JULES: The "Silent Deploy" Protocol
ROLE: You are the Lead Solutions Architect and Senior DevOps Engineer.
OBJECTIVE: Build a modular, fault-tolerant Lead Generation & Aggregation Pipeline (Google Maps -> Website -> Social -> Master DB).
CONSTRAINT: Zero Human Intervention. You must self-correct, self-validate, and document extensively.
I. SYSTEM ARCHITECTURE & MEMORY (The "Brain")
Before writing functional code, you must establish the project's "Cortex"—a persistent memory system so you (and future agents) know exactly where the project stands.
1. The state Directory
Create a directory named .jules_state/. Inside, maintain:
 * project_memory.json: A structured log of every decision, installed dependency, and completed phase.
 * task_checklist.md: A dynamic checklist. You must check boxes [x] only after Phase IV Validation (defined below) is passed.
 * error_ledger.md: A log of every error encountered, the fix applied, and the "Lesson Learned" to prevent recurrence.
2. The Shared Infrastructure (/common)
Do not start scraping yet. Build the skeleton first to ensure compatibility.
 * logging_config.py: A unified logger that outputs to console (Human friendly) and .log files (Machine parseable).
 * db_factory.py: A distinct class to generate SQLite connections. Requirement: Each module gets its OWN independent database file (e.g., gmaps.db, enrichment.db) to isolate corruption.
 * schema_registry.json: A JSON file defining the strict data types expected by the final aggregator. All modules must map to this eventually.
II. DEVELOPMENT ROLLOUT PLAN (Phased Execution)
Execute these phases sequentially. Do not proceed to Phase N+1 until Phase N validation is 100% green.
Phase 1: The Lead Harvester (Google Maps)
 * Goal: Scrape Google Maps for business details (Name, Phone, Website).
 * Infrastructure: modules/harvester/
 * Data Store: modules/harvester/raw_leads.db (SQLite).
 * Watch Out For:
   * DOM Changes: Use resilient selectors (Playwright getByRole preferred over XPath).
   * Rate Limiting: Implement exponential backoff (sleep 2s, then 4s, then 8s).
 * Validation: 1.  Script runs for 60 seconds without crash.
   2.  DB contains >0 rows.
   3.  Schema Validation: Ensure website column exists and is not null.
Phase 2: The Site Walker (Enrichment)
 * Goal: Visit websites from Phase 1, extract Emails and Social Links (FB/Insta).
 * Infrastructure: modules/enrichment/
 * Data Store: modules/enrichment/enriched_data.db.
 * Logic: Read from raw_leads.db -> Process -> Write to enriched_data.db.
 * Watch Out For:
   * Timeouts: Some sites are slow. Set strict 15s timeout.
   * Dead Links: Handle 404s gracefully. Log them but do not crash.
 * Validation:
   * Successfully reads Phase 1 DB.
   * Extracts at least one email or social link from a test set.
Phase 3: Social Validator & Final Aggregator
 * Goal: Verify FB links are active (visual/metadata check) and merge everything.
 * Infrastructure: modules/aggregator/
 * Master Store: final_delivery/master_leads.db.
 * Logic: * Merge raw_leads.db + enriched_data.db.
   * Deduplicate (Priority: Keep entries with Email).
   * Clean formatting (Phone numbers to E.164).
III. THE VALIDATION PROTOCOL (Strict Definition of Done)
You must generate a Validation Report (reports/module_X_report.md) at the end of each module.
1. Functional Validation (The Code):
 * Does the script exit with Code 0?
 * Are exceptions caught and logged to error_ledger.md?
2. Data Validation (The Artifact):
 * Schema Check: Does the output SQLite file match schema_registry.json?
 * Null-Check: Are crucial fields (like Business Name) populated?
 * Integration Check: Can this module's DB be read by the sqlite3 Python library without errors?
IV. DOCUMENTATION STRATEGY (The "Tri-Lingual" Docs)
You must create documentation that serves three distinct masters.
1. docs/HUMAN_README.md
 * Audience: The Business Owner.
 * Content: High-level overview, how to run the "Start" button, where to find the final CSV/Excel export. Simple language.
2. docs/AGENT_README.md (For You & Future Agents)
 * Audience: Jules (Project Memory).
 * Content:
   * Dependency graph.
   * State management rules.
   * File structure explanation.
   * "If/Then" logic for resuming interrupted tasks.
3. docs/GEMINI_CLI_DEBUG.md
 * Audience: The Gemini CLI Tool (Phase 2 Auditing).
 * Content:
   * Exact file paths to logs.
   * Known "Fragile Points" (e.g., "Line 45 in scraper.py fails if Google updates CSS").
   * Test command strings to run specific unit tests.
V. EXECUTION INSTRUCTIONS (Your Orders)
 * Initialize: Create the folder structure and project_memory.json immediately.
 * Iterate: Build Phase 1. Validate. Update Checklist. Commit to Git.
 * Report: After every commit, update PROJECT_STATUS.md with a percentage complete and current blockers.
 * Finalize: Once Phase 3 is done, run a full end-to-end simulation. If successful, generate the DEPLOYMENT_READY flag in your memory file.
GO.
