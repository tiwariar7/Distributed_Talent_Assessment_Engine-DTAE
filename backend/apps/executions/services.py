"""
Submission orchestration — coordinates PostgreSQL, CouchDB, and Celery.

Open/Closed Principle: execution strategy is delegated to tasks/executor.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from apps.assessments.models import Problem, Submission
from infrastructure.couchdb import DocumentRepository
from infrastructure.events import SubmissionEventPublisher

logger = logging.getLogger(__name__)


class SubmissionService:
    """
    Application service for the submission lifecycle.

    Single Responsibility: coordinate persistence and async dispatch.
    """

    @staticmethod
    def create_and_queue(
        problem: Problem,
        candidate,
        source_code: str,
    ) -> Submission:
        """
        Atomically create a PostgreSQL submission row and CouchDB artifacts.

        Returns immediately; evaluation runs in a Celery worker.
        """
        repository = DocumentRepository()

        with transaction.atomic():
            submission = Submission.objects.create(
                problem=problem,
                candidate=candidate,
                status=Submission.Status.QUEUED,
                couchdb_source_doc_id="",
                couchdb_execution_log_doc_id="",
            )
            source_doc_id = repository.save_source_code(source_code, submission.pk)
            log_doc_id = repository.create_execution_log(submission.pk)

            submission.couchdb_source_doc_id = source_doc_id
            submission.couchdb_execution_log_doc_id = log_doc_id
            submission.save(
                update_fields=[
                    "couchdb_source_doc_id",
                    "couchdb_execution_log_doc_id",
                ],
            )

        from .tasks import run_submission_evaluation

        # Dynamically route tasks to language-specific queues to support distributed scaling clusters
        queue_name = f"lang_{problem.language.lower()}"
        task_result = run_submission_evaluation.apply_async(
            args=[submission.pk],
            queue=queue_name,
            routing_key=problem.language.lower(),
            priority=10,
        )
        submission.celery_task_id = task_result.id
        submission.save(update_fields=["celery_task_id"])
        SubmissionEventPublisher.status_changed(
            submission.pk,
            Submission.Status.QUEUED,
        )
        logger.info(
            "Queued submission",
            extra={"submission_id": submission.pk, "problem_id": problem.pk},
        )
        return submission

    @staticmethod
    def mark_running(submission_id: int) -> None:
        """Transition submission to running (idempotent for retries)."""
        Submission.objects.filter(pk=submission_id).update(
            status=Submission.Status.RUNNING,
        )

    @staticmethod
    def finalize(
        submission_id: int,
        score: int,
        success: bool,
    ) -> Submission:
        """Persist final score and timestamp in PostgreSQL."""
        status = Submission.Status.COMPLETED if success else Submission.Status.FAILED
        Submission.objects.filter(pk=submission_id).update(
            status=status,
            score=score,
            completed_at=timezone.now(),
        )
        return Submission.objects.select_related("problem", "candidate").get(
            pk=submission_id,
        )


class ExecutionCancellationService:
    """Handles revocation of celery tasks for active evaluations."""

    @staticmethod
    def cancel_submission(submission_id: int) -> bool:
        """Revoke the celery task for a given submission and mark it failed."""
        try:
            submission = Submission.objects.get(pk=submission_id)
            if submission.status in (Submission.Status.QUEUED, Submission.Status.RUNNING):
                if submission.celery_task_id:
                    from config.celery import app
                    app.control.revoke(submission.celery_task_id, terminate=True, signal="SIGKILL")
                submission.status = Submission.Status.FAILED
                submission.save(update_fields=["status"])
                SubmissionEventPublisher.status_changed(submission_id, Submission.Status.FAILED)
                return True
        except Submission.DoesNotExist:
            pass
        return False

# Refactor: Fix minor edge cases in calculation functions.
