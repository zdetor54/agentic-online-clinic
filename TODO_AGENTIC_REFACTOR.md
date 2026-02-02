# Refactor Agentic and Manual Workflows for DRY, Modular Design

## Task 1: Move Filtering Logic to CRUD Layer
- Filtering logic is duplicated in:
  - [src/api/patients/routes.py] → function: list_patients_endpoint
  - [src/llm/agent.py] → function: search_patients (uses HTTP API)
- Create or update [src/api/patients/crud.py]:
  - New function: list_patients_filtered(name: str | None, phone: str | None) -> list[PatientResponse]
- Both endpoint and agent tool will use this.

## Task 1a: Do NOT Use Endpoint Functions as Agent Tools
- [src/api/patients/routes.py]: list_patients_endpoint contains filtering logic and is tied to FastAPI.
- Do not use endpoint functions directly as agent tools.
- Instead, refactor filtering logic into CRUD and call from both endpoint and agent tool.

## Task 2: Refactor Agent Tools to Use CRUD Directly
- [src/llm/agent.py]:
  - search_patients (uses httpx to call API)
  - get_patient_by_id (uses httpx to call API)
  - create_patient (uses httpx to call API)
- Refactor to call CRUD functions directly.
- Remove all httpx usage from these functions.

## Task 3: Refactor FastAPI Endpoints to Use Shared CRUD
- [src/api/patients/routes.py]:
  - list_patients_endpoint (calls list_patients, does its own filtering)
  - get_patient_by_id_endpoint, create_patient_endpoint, etc.
- Refactor endpoints to call shared CRUD functions for all business logic.

## Task 4: Update/Write Tests for CRUD and Agent Tools
- [tests/]:
  - Add/modify tests for list_patients_filtered, get_patient_by_id, create_patient in CRUD.
  - Add/modify tests for agent tool functions (now using CRUD directly).

## Task 5: Update Documentation
- [README.md], [AGENT_IMPLEMENTATION.md], and docstrings may reference old architecture.
- Update documentation to describe the new shared CRUD approach and agent specialization.

## Task 6: (Optional) Modularize Agent Creation
- [src/llm/agent.py]: get_agent (single agent for all logic)
- Refactor to [src/llm/patient_agent.py]: get_patient_agent (for patient logic)
- [src/llm/booking_agent.py]: get_booking_agent (for booking logic, if/when needed)

## Task 7: (Optional) Add Orchestrator for Complex Workflows
- No orchestrator; all logic in a single agent.
- [src/llm/orchestrator.py] (or similar): orchestrate multi-step workflows by calling specialized agents.

## Task 8: Code Cleanup
- [src/llm/agent.py]: httpx usage, duplicated logic, unused imports.
- Remove httpx and any now-unused code from [src/llm/agent.py] and related files.
- Ensure all modules follow project style and type hinting standards.
