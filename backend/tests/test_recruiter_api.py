"""Tests for recruiter dashboard API."""

from unittest.mock import patch

import pytest
from rest_framework import status

from apps.assessments.models import Assessment, Problem


@pytest.fixture
def recruiter_client(api_client, django_user_model, organization, recruiter_role):
    """Authenticated recruiter API client."""
    from apps.accounts.models import Membership

    user = django_user_model.objects.create_user(
        username="recruiter@test.com",
        email="recruiter@test.com",
        password="testpass123",
    )
    Membership.objects.create(user=user, organization=organization, role=recruiter_role)
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
def test_recruiter_creates_draft_assessment(recruiter_client, organization) -> None:
    """Recruiter can create a draft assessment for their organization."""
    response = recruiter_client.post(
        "/api/v1/recruiter/assessments/",
        {
            "title": "New Hire Screen",
            "description": "Backend skills",
            "duration_minutes": 45,
            "organization_slug": organization.slug,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == Assessment.Status.DRAFT
    assert Assessment.objects.filter(title="New Hire Screen").exists()


@pytest.mark.django_db
@patch("apps.recruiter.services.DocumentRepository")
def test_recruiter_uploads_test_cases(
    mock_repository,
    recruiter_client,
    organization,
) -> None:
    """Recruiter can upload hidden test cases to CouchDB."""
    mock_repository.return_value.save_test_cases.return_value = "test_cases_problem_99"

    assessment = Assessment.objects.create(
        organization=organization,
        title="Draft",
        status=Assessment.Status.DRAFT,
    )
    problem = Problem.objects.create(
        assessment=assessment,
        title="Add Numbers",
        prompt="sum stdin",
        language=Problem.Language.PYTHON,
    )

    response = recruiter_client.put(
        f"/api/v1/recruiter/assessments/{assessment.pk}/problems/{problem.pk}/test-cases/",
        {
            "test_cases": [
                {"stdin": "1\n2\n", "expected_stdout": "3"},
            ],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["test_case_count"] == 1
    problem.refresh_from_db()
    assert problem.couchdb_test_cases_doc_id == "test_cases_problem_99"


@pytest.mark.django_db
def test_publish_requires_test_cases(recruiter_client, organization) -> None:
    """Publishing fails when problems lack CouchDB test cases."""
    assessment = Assessment.objects.create(
        organization=organization,
        title="Incomplete",
        status=Assessment.Status.DRAFT,
    )
    Problem.objects.create(
        assessment=assessment,
        title="No Tests",
        prompt="...",
    )

    response = recruiter_client.post(
        f"/api/v1/recruiter/assessments/{assessment.pk}/publish/",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@patch("apps.recruiter.services.DocumentRepository")
def test_publish_assessment_success(mock_repository, recruiter_client, organization) -> None:
    """Assessment publishes when all problems have test cases."""
    mock_repository.return_value.save_test_cases.return_value = "test_cases_problem_1"

    assessment = Assessment.objects.create(
        organization=organization,
        title="Ready",
        status=Assessment.Status.DRAFT,
    )
    Problem.objects.create(
        assessment=assessment,
        title="Hello",
        prompt="print hello",
        couchdb_test_cases_doc_id="test_cases_problem_1",
    )

    response = recruiter_client.post(
        f"/api/v1/recruiter/assessments/{assessment.pk}/publish/",
    )

    assert response.status_code == status.HTTP_200_OK
    assessment.refresh_from_db()
    assert assessment.status == Assessment.Status.PUBLISHED

# Refactor: Optimize query performance and database indexing.

# Refactor: Update validation checks and constraints.

# Refactor: Enhance component rendering performance.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Add typing hints and documentation docstrings.
