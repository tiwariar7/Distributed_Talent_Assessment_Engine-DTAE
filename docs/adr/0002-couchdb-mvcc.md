# ADR 0002: CouchDB MVCC for Concurrent Execution Logging

## Status
Approved

## Context
When a submission is evaluated against multiple test cases, logs are appended concurrently from executing runners. Storing execution logs directly inside relational models causes slow transactional locking on PostgreSQL. Using traditional database locks blocks worker threads, degrades performance, and hurts system scalability.

## Decision
We decouple raw execution outputs from relational tables and store logs as structured append-only documents in CouchDB.
To handle concurrent edits without distributed application-level locks, we leverage CouchDB's Multi-Version Concurrency Control (MVCC):
1. Each document update is signed with an opaque revision token (`_rev`).
2. When appending a log entry, the client fetches the document, retrieves its current `_rev`, appends the entry, and attempts to save the updated body.
3. If another worker thread updated the document concurrently, CouchDB rejects the update with an HTTP `409 Conflict`.
4. The client catches the conflict, implements exponential backoff retries, pulls the updated document, merges the logs, and retries the save.

## Consequences
- Highly scalable log logging without blocking PostgreSQL database connections.
- Complete isolation of candidate outputs from critical core transaction tables.
- Resilience under load, with conflict rates naturally dropping as backoff delays stagger execution completion times.


- Note: Refactor variable names for better readability.


- Note: Fix minor edge cases in calculation functions.


- Note: Optimize imports and clean up code structure.


- Note: Add typing hints and documentation docstrings.
