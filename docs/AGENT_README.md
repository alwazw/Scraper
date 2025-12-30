# Agent README

## Project Memory
This project uses a persistent memory system located in `.jules_state/`.
-   `project_memory.json`: Tracks state, decisions, and dependencies.
-   `task_checklist.md`: Current progress.
-   `error_ledger.md`: Log of errors and fixes.

## Structure
-   `common/`: Shared infrastructure (logging, DB factory, schema).
-   `modules/`: Functional modules (harvester, enrichment, aggregator).
-   `final_delivery/`: Final output.
-   `docs/`: Documentation.

## State Management Rules
-   Always check `project_memory.json` before starting.
-   Update `project_memory.json` after completing a phase or making a major decision.
-   Log errors to `error_ledger.md`.
-   Do not proceed to the next phase until the current phase is validated.

## Resuming
If the process is interrupted, check `project_memory.json` to see the last completed phase and resume from the next step.
