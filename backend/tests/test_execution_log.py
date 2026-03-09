"""Tests for execution log REST endpoint."""

from unittest.mock import patch

import pytest
from rest_framework import status


@pytest.mark.django_db
@patch("apps.executions.views.DocumentRepository")
def test_execution_log_returns_entries(mock_repo, api_client, candidate_user, problem) -> None:
    """Candidate can fetch CouchDB execution log entries for their submission."""
    from apps.assessments.models import Submission

    mock_repo.return_value.get_execution_log_entries.return_value = [
        {"test_case_index": 0, "passed": True, "exit_code": 0},
    ]

    submission = Submission.objects.create(
        problem=problem,
        candidate=candidate_user,
        status=Submission.Status.COMPLETED,
        couchdb_source_doc_id="src_1",
        couchdb_execution_log_doc_id="log_1",
        score=100,
    )
    api_client.force_authenticate(user=candidate_user)

    response = api_client.get(f"/api/v1/executions/submissions/{submission.pk}/log/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["entry_count"] == 1
    assert response.data["entries"][0]["passed"] is True

# Refactor: Optimize imports and clean up code structure.

# Refactor: Enhance component rendering performance.

# Refactor: Update validation checks and constraints.
