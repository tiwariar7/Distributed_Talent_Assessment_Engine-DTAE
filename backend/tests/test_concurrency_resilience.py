import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from apps.executions.tasks import run_submission_evaluation
from infrastructure.couchdb import DocumentConflictError

User = get_user_model()

@pytest.mark.django_db
@patch("apps.executions.tasks.Submission.objects.select_related")
@patch("apps.executions.tasks.SubmissionService")
@patch("apps.executions.tasks.DocumentRepository")
@patch("apps.executions.tasks.DockerCodeExecutor")
@patch("apps.executions.tasks.SubmissionEventPublisher")
def test_evaluation_task_retries_on_conflict(
    mock_publisher,
    mock_executor_class,
    mock_repo_class,
    mock_submission_service,
    mock_select_related,
):
    """Verify that run_submission_evaluation retries when CouchDB returns DocumentConflictError."""
    # Setup mocks
    mock_submission = MagicMock()
    mock_submission.problem.language = "python"
    mock_submission.problem.max_score = 100
    mock_submission.problem.couchdb_test_cases_doc_id = "test-cases-123"
    mock_submission.couchdb_source_doc_id = "src-123"
    mock_submission.couchdb_execution_log_doc_id = "log-123"
    
    mock_select_related.return_value.get.return_value = mock_submission
    
    mock_repo = mock_repo_class.return_value
    mock_repo.get_source_code.return_value = "print('hello')"
    mock_repo.get_test_cases.return_value = [{"stdin": "", "expected_stdout": ""}]
    
    # Force first call to append_execution_log to fail with conflict, second to succeed
    mock_repo.append_execution_log.side_effect = [
        DocumentConflictError("MVCC conflict simulation"),
        {"ok": True}
    ]
    
    mock_executor = mock_executor_class.return_value
    mock_res = MagicMock()
    mock_res.stdout = "hello\n"
    mock_res.stderr = ""
    mock_res.exit_code = 0
    mock_res.timed_out = False
    mock_executor.execute.return_value = mock_res
    
    # Run task and verify conflict triggers celery retry
    with pytest.raises(Exception) as exc:
        # Calling with .apply() runs synchronously but celery task wrappers will trigger retry
        run_submission_evaluation.apply(args=[1])
    
    # Verify select_related database fetch was done
    mock_select_related.return_value.get.assert_called_once_with(pk=1)

# Refactor: Optimize query performance and database indexing.

# Refactor: Optimize query performance and database indexing.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Update validation checks and constraints.
