# ADR 0003: Celery & RabbitMQ Priority Queue Topology and Resiliency

## Status
Approved

## Context
A Distributed Talent Assessment Engine needs to process tasks with highly varying urgency and latency constraints:
1. **Interactive Submissions:** Candidates executing code need near-instantaneous feedback (seconds).
2. **Leaderboard & Scoring Updates:** Scoring calculations can run slightly decoupled from the execution loop (tens of seconds).
3. **Bulk Re-evaluations:** Recruiters updating test cases may trigger retro-active runs on hundreds of submissions concurrently, which must not block interactive candidates.
4. **Maintenance & Cleanup:** Container pruning, CouchDB indexing, and file system cleanups are background jobs with no real-time urgency.

Directly pushing all tasks to a single queue leads to queue starvation, where long low-priority recruiter runs block critical candidate execution tasks. We need a routing layer capable of handling task priorities, queue isolation, dead-letter routing, and task cancellation.

## Decision
We implement a multi-tiered direct-exchange priority queue topology using RabbitMQ as our Celery broker:

1. **Queue Isolation and Priorities:**
   - **`high_priority`** (Routing key: `high`, max priority: 10): Reserved for candidate code evaluations (`apps.executions.tasks.run_submission_evaluation`).
   - **`medium_priority`** (Routing key: `medium`, max priority: 5): Reserved for leaderboard updates (`apps.leaderboard.tasks.update_leaderboard_task`).
   - **`low_priority`** (Routing key: `low`, max priority: 3): Reserved for bulk or retroactive recruiter re-evaluations (`apps.executions.tasks.recruiter_re_evaluation_task`).
   - **`maintenance`** (Routing key: `maintenance`): System housekeeping tasks (`apps.executions.tasks.cleanup_task`).

2. **Dead-Letter Queue (DLQ) Integration:**
   - All standard queues (`high_priority`, `medium_priority`, `low_priority`) are configured with dead-letter exchange arguments (`x-dead-letter-exchange: "dead_letter"` and `x-dead-letter-routing-key: "dead_letter"`).
   - If a task runs out of retries or experiences an unrecoverable worker exception, RabbitMQ automatically routes the failed task to the **`dead_letter`** queue for manual/automated triage, preventing silent task drops.

3. **Task Revocation and Cancellation:**
   - If a candidate updates their code before a previous execution completes, or if an assessment is terminated, the engine issues a Celery revoke command (`app.control.revoke(task_id, terminate=True, signal="SIGKILL")`).
   - This instantly kills any running docker container associated with that worker task, conserving system resources.

## Consequences
- **Zero Interference:** Candidates will always experience low execution latencies regardless of heavy recruiter re-evaluation load.
- **Improved Observability:** Bad code submissions or container-related failures that crash worker tasks are isolated in the `dead_letter` queue, exposing failures immediately.
- **Resource Recovery:** Revocation cleanly stops orphan Docker sandboxes, preventing memory leaks and CPU exhaustion under frequent submission cycles.


- Note: Fix minor edge cases in calculation functions.


- Note: Enhance component rendering performance.
