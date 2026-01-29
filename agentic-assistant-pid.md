# Project Initiation Document (PID)

## Project Title

**Agentic Assistant for Application Data Access and Workflow Automation**
**Audience:** Technical Review

## 1. Background

The application is a production-style system used to manage core domain data and user workflows through a web interface. It exposes functionality through structured data models, forms, and APIs (CRUD), while also storing information across multiple related records and unstructured fields. Current access patterns rely on manual UI interaction or narrowly scoped endpoints.

## 2. Objective

To design and implement an agentic layer that translates natural language requests into **read (query/RAG)** and **write (CRUD)** operations against the existing application stack, without altering core business logic.

## 3. Technical Scope & Approach

The assistant will:

* Perform **intent classification** to distinguish between:

  * Information retrieval (read-only)
  * Data mutation (create, update, delete)
* Execute **CRUD operations** via existing Flask APIs or form handlers
* Use **RAG-style retrieval** for questions requiring aggregation or synthesis across:

  * Multiple tables
  * Historical records
  * Unstructured notes
* Support **multi-intent prompts** via task decomposition and ordered execution

## 4. Agentic Architecture

* **Planner:** Breaks prompts into discrete steps
* **Tool Layer:**

  * API calls for mutations
  * SQL / retrieval layer for reads
* **RAG Pipeline (Read-only):** Retrieve relevant records and generate synthesized responses
* **Guardrails:** Validation and confirmation before write operations

## 5. Non-Goals (Explicit)

* No autonomous clinical or business decision-making
* No replacement of validation logic or data ownership
* No model-driven writes without confirmation

## 6. Success Criteria (Technical)

* Correct intent classification
* Reliable API invocation for CRUD operations
* Accurate, explainable retrieval across records
* Clear separation of read vs. write paths
