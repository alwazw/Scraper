import os
import json
import sqlite3

# --- EXPECTED STANDARD ---
REQUIRED_DIRS = [
    ".jules_state",
    "modules/harvester",
    "modules/enrichment",
    "modules/aggregator",
    "common",
    "docs",
    "reports"
]

REQUIRED_FILES = [
    ".jules_state/project_memory.json",
    ".jules_state/task_checklist.md",
    ".jules_state/error_ledger.md",
    "common/logging_config.py",
    "common/db_factory.py",
    "docs/HUMAN_README.md",
    "docs/AGENT_README.md",
    "docs/GEMINI_CLI_DEBUG.md"
]

def check_structure():
    print("--- 1. ARCHITECTURE CHECK ---")
    missing_items = []

    for d in REQUIRED_DIRS:
        if os.path.isdir(d):
            print(f"[OK] Dir: {d}")
        else:
            print(f"[FAIL] Missing Dir: {d}")
            missing_items.append(d)

    for f in REQUIRED_FILES:
        if os.path.isfile(f):
            print(f"[OK] File: {f}")
        else:
            print(f"[FAIL] Missing File: {f}")
            missing_items.append(f)

    return len(missing_items) == 0

def check_decoupling():
    print("\n--- 2. DB DECOUPLING CHECK ---")
    # Check if separate DBs exist or if logic implies them
    dbs_found = [f for f in os.listdir('.') if f.endswith('.db')]
    module_dbs = []

    # scan modules for .db files (Preferred architecture)
    for root, dirs, files in os.walk("modules"):
        for file in files:
            if file.endswith(".db"):
                module_dbs.append(os.path.join(root, file))

    if len(module_dbs) > 1:
        print(f"[OK] Found independent DBs: {module_dbs}")
    elif len(dbs_found) == 1:
        print(f"[WARNING] Found only 1 root DB: {dbs_found}. Risk of monolithic failure.")
    else:
        print("[INFO] No DB files generated yet. Check if Phase 1 has run.")

def check_memory():
    print("\n--- 3. MEMORY CHECK ---")
    mem_file = ".jules_state/project_memory.json"
    if os.path.exists(mem_file):
        try:
            with open(mem_file, 'r') as f:
                data = json.load(f)
            print("[OK] project_memory.json is valid JSON.")
            # Loose check for content
            if "current_phase" in data or "completed_phases" in data:
                 print("[OK] Memory contains phase/task tracking.")
            else:
                 print("[FAIL] Memory file is empty or missing structure.")
        except:
            print("[FAIL] project_memory.json is corrupted.")
    else:
        print("[FAIL] No memory file found.")

if __name__ == "__main__":
    print("AUDITING JULES WORK...\n")
    struct_ok = check_structure()
    check_decoupling()
    check_memory()

    print("\n--- AUDIT CONCLUSION ---")
    if struct_ok:
        print("✅ PASS: Structure follows the 'Silent Deploy' protocol.")
    else:
        print("❌ FAIL: Structural violations found.")
