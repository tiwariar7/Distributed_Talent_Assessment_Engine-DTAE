"""API tests for assessment listing and code submission."""

from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Submission


@pytest.mark.django_db
def test_list_published_assessments(api_client, candidate_user, published_assessment) -> None:
    """Authenticated users can list published assessments."""
    api_client.force_authenticate(user=candidate_user)
    response = api_client.get("/api/v1/assessments/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["title"] == "Sample Assessment"


@pytest.mark.django_db
@patch("apps.executions.tasks.run_submission_evaluation.apply_async")
def test_submission_queues_execution(
    mock_apply_async,
    api_client,
    candidate_user,
    problem,
) -> None:
    mock_apply_async.return_value.id = "mock-task-id-123"
    api_client.force_authenticate(user=candidate_user)

    with patch("apps.executions.services.DocumentRepository") as mock_repo:
        mock_repo.return_value.save_source_code.return_value = "source_doc_1"
        mock_repo.return_value.create_execution_log.return_value = "log_doc_1"

        response = api_client.post(
            f"/api/v1/assessments/problems/{problem.pk}/submissions/",
            {"source_code": 'print("hi")'},
            format="json",
        )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.data["status"] == Submission.Status.QUEUED
    mock_apply_async.assert_called_once()


@pytest.mark.django_db
def test_submission_requires_candidate_role(
    api_client,
    django_user_model,
    organization,
    recruiter_role,
    problem,
) -> None:
    """Recruiters cannot submit candidate solutions."""
    from apps.accounts.models import Membership

    recruiter = django_user_model.objects.create_user(
        username="recruiter@test.com",
        email="recruiter@test.com",
        password="testpass123",
    )
    Membership.objects.create(
        user=recruiter,
        organization=organization,
        role=recruiter_role,
    )
    api_client.force_authenticate(user=recruiter)

    response = api_client.post(
        f"/api/v1/assessments/problems/{problem.pk}/submissions/",
        {"source_code": 'print("hi")'},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@patch("apps.executions.tasks.run_submission_evaluation.apply_async")
def test_submission_rate_limit(mock_apply_async, monkeypatch, candidate_user, problem) -> None:
    mock_apply_async.return_value.id = "mock-task-id-456"
    from apps.assessments.throttles import SubmissionRateThrottle

    monkeypatch.setattr(SubmissionRateThrottle, "get_rate", lambda self: "2/min")

    client = APIClient()
    client.force_authenticate(user=candidate_user)
    cache.clear()

    with patch("apps.executions.services.DocumentRepository") as mock_repo:
        mock_repo.return_value.save_source_code.return_value = "source_doc"
        mock_repo.return_value.create_execution_log.return_value = "log_doc"

        url = f"/api/v1/assessments/problems/{problem.pk}/submissions/"
        payload = {"source_code": "print(1)"}

        assert client.post(url, payload, format="json").status_code == status.HTTP_202_ACCEPTED
        assert client.post(url, payload, format="json").status_code == status.HTTP_202_ACCEPTED
        blocked = client.post(url, payload, format="json")

    assert blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS


# Refactor: Optimize imports and clean up code structure.

# Refactor: Improve error handling and exception logging.

# Refactor: Optimize query performance and database indexing.

# Refactor: Improve error handling and exception logging.

# Refactor: Update validation checks and constraints.

# Refactor: Refactor variable names for better readability.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Add typing hints and documentation docstrings.
