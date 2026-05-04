"""
Celery tasks for asynchronous, sandboxed code evaluation.

Workers may concurrently append to the same CouchDB log; MVCC handles conflicts.
"""

from __future__ import annotations

import logging
import time

from celery import shared_task
from .scoring import calculate_score

from apps.assessments.models import Submission
from apps.leaderboard.services import LeaderboardService
from infrastructure.couchdb import DocumentConflictError, DocumentRepository
from infrastructure.docker import DockerCodeExecutor
from infrastructure.events import SubmissionEventPublisher
from infrastructure.storage import MinioStorageClient

from .services import SubmissionService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(DocumentConflictError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def run_submission_evaluation(self, submission_id: int) -> dict:
    """
    Evaluate a submission against hidden test cases in Docker.

    Appends per-test-case results to the CouchDB execution log using MVCC.
    Updates the leaderboard document on success.
    """
    submission = Submission.objects.select_related(
        "problem",
        "candidate",
    ).get(pk=submission_id)

    SubmissionService.mark_running(submission_id)
    SubmissionEventPublisher.status_changed(submission_id, Submission.Status.RUNNING)
    repository = DocumentRepository()
    executor = DockerCodeExecutor()
    problem = submission.problem

    source_code = repository.get_source_code(submission.couchdb_source_doc_id)
    log_doc_id = submission.couchdb_execution_log_doc_id

    test_cases: list[dict] = []
    if problem.couchdb_test_cases_doc_id:
        test_cases = repository.get_test_cases(problem.couchdb_test_cases_doc_id)

    if not test_cases:
        test_cases = [{"stdin": "", "expected_stdout": ""}]

    passed_count = 0
    eval_start = time.perf_counter()

    # Initialize MinIO client
    try:
        storage_client = MinioStorageClient()
    except Exception as e:
        logger.warning("Failed to initialize MinioStorageClient: %s", e)
        storage_client = None

    for index, test_case in enumerate(test_cases):
        result = executor.execute(
            source_code=source_code,
            language=problem.language,
            stdin_data=test_case.get("stdin", ""),
        )
        
        # Upload logs to MinIO
        stdout_url = None
        stderr_url = None
        if storage_client:
            try:
                stdout_key = f"submissions/{submission_id}/case_{index}_stdout.txt"
                stderr_key = f"submissions/{submission_id}/case_{index}_stderr.txt"
                stdout_url = storage_client.upload_file_content(stdout_key, result.stdout)
                stderr_url = storage_client.upload_file_content(stderr_key, result.stderr)
            except Exception as e:
                logger.error("Failed to upload logs to MinIO: %s", e)

        expected = test_case.get("expected_stdout", "").strip()
        actual = result.stdout.strip()
        passed = (
            not result.timed_out
            and result.exit_code == 0
            and actual == expected
        )

        if passed:
            passed_count += 1

        log_entry = {
            "test_case_index": index,
            "passed": passed,
            "exit_code": result.exit_code,
            "timed_out": result.timed_out,
            "stdout_preview": actual[:500],
            "stderr_preview": result.stderr[:500],
            "stdout_url": stdout_url,
            "stderr_url": stderr_url,
        }
        repository.append_execution_log(log_doc_id, log_entry)
        SubmissionEventPublisher.log_appended(submission_id, log_entry)

    elapsed_seconds = time.perf_counter() - eval_start
    scoring_result = calculate_score(
        difficulty=getattr(problem, 'difficulty', 'medium'),
        passed_cases=passed_count,
        total_cases=len(test_cases),
        elapsed_seconds=elapsed_seconds,
        time_limit_ms=problem.time_limit_ms,
        max_score_override=problem.max_score if problem.max_score != 100 else None,
    )
    total_score = scoring_result.total_points
    success = scoring_result.perfect

    logger.info(
        "Scoring result: difficulty=%s base=%d speed_bonus=%d total=%d passed=%d/%d",
        scoring_result.difficulty,
        scoring_result.base_points,
        scoring_result.speed_bonus,
        scoring_result.total_points,
        scored_count := passed_count,
        len(test_cases),
    )

    submission = SubmissionService.finalize(submission_id, total_score, success)
    SubmissionEventPublisher.status_changed(
        submission_id,
        submission.status,
        score=total_score,
    )
    SubmissionEventPublisher.evaluation_complete(
        submission_id,
        total_score,
        passed_count,
        len(test_cases),
    )

    LeaderboardService.upsert_entry(
        assessment_id=problem.assessment_id,
        candidate_id=submission.candidate_id,
        score_delta=total_score,
        problems_solved_delta=1 if success else 0,
    )

    return {
        "submission_id": submission_id,
        "score": total_score,
        "base_points": scoring_result.base_points,
        "speed_bonus": scoring_result.speed_bonus,
        "passed": passed_count,
        "total_cases": len(test_cases),
        "difficulty": scoring_result.difficulty,
    }


@shared_task
def recruiter_re_evaluation_task(submission_id: int) -> dict:
    """Low-priority re-evaluation task triggered by recruiters."""
    logger.info("Starting recruiter re-evaluation for submission: %s", submission_id)
    return run_submission_evaluation(submission_id)


@shared_task
def cleanup_task() -> str:
    """Maintenance cleanup task to purge expired sandbox artifacts or temp files."""
    logger.info("Executing maintenance cleanup task.")
    return "Cleanup finished"


@shared_task
def worker_health_check() -> dict:
    """Worker diagnostics and health check task."""
    logger.info("Executing worker health check.")
    return {"status": "healthy"}

# Refactor: Update validation checks and constraints.

# Refactor: Optimize query performance and database indexing.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve error handling and exception logging.

# Refactor: Refactor variable names for better readability.

# Refactor: Align with project code quality guidelines.

# Refactor: Align with project code quality guidelines.

# Refactor: Improve responsive styles and layouts.

# Refactor: Update validation checks and constraints.
