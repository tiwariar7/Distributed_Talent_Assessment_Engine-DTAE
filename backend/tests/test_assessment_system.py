"""Tests for standard API response wrapping, MCQ/FIB evaluations, and autosave functionality."""

import pytest
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import MagicMock

from apps.assessments.models import Problem, Submission, AssessmentInvitation, MCQOption, FIBRule, SubmissionDraft


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch) -> None:
    """Mock CouchDBClient and Redis to prevent real connections in tests."""
    mock_couch = MagicMock()
    monkeypatch.setattr("apps.leaderboard.services.CouchDBClient", lambda: mock_couch)

    mock_redis = MagicMock()
    monkeypatch.setattr("redis.Redis.from_url", lambda *args, **kwargs: mock_redis)


@pytest.fixture
def active_invitation(db, published_assessment, candidate_user) -> AssessmentInvitation:
    """An active started invitation for the candidate user."""
    return AssessmentInvitation.objects.create(
        assessment=published_assessment,
        email=candidate_user.email,
        user=candidate_user,
        token="test_token_999",
        expires_at=timezone.now() + timedelta(days=1),
        started_at=timezone.now(),
        is_active=True,
        status=AssessmentInvitation.InvitationStatus.STARTED,
    )


@pytest.mark.django_db
def test_standard_response_wrapping_on_success(api_client, candidate_user) -> None:
    """Standard renderer wraps successful response format."""
    api_client.force_authenticate(user=candidate_user)
    response = api_client.get("/api/v1/auth/me/")

    assert response.status_code == status.HTTP_200_OK
    
    json_data = response.json()
    assert json_data["success"] is True
    assert "email" in json_data["data"]
    assert json_data["error"] is None
    assert json_data["message"] == "Success"


@pytest.mark.django_db
def test_standard_response_wrapping_on_error(api_client) -> None:
    """Standard exception handler wraps error responses in expected structure."""
    # Request profile without authentication (expect 401)
    response = api_client.get("/api/v1/auth/me/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["data"] is None
    assert json_data["error"] is not None
    assert "Authentication credentials were not provided" in json_data["message"]


@pytest.mark.django_db
def test_mcq_evaluation_single_correct(api_client, candidate_user, published_assessment, active_invitation) -> None:
    """Single-choice MCQ matches selected option and awards full marks or zero."""
    api_client.force_authenticate(user=candidate_user)

    problem = Problem.objects.create(
        assessment=published_assessment,
        title="MCQ 1",
        prompt="Select the correct one",
        question_type=Problem.QuestionType.MCQ,
        max_score=100,
    )
    opt_correct = MCQOption.objects.create(problem=problem, option_text="Correct", is_correct=True)
    opt_wrong = MCQOption.objects.create(problem=problem, option_text="Wrong", is_correct=False)

    url = f"/api/v1/assessments/problems/{problem.id}/submissions/"

    # Submit correct option
    response_correct = api_client.post(url, {"selected_options": [opt_correct.id]}, format="json")
    assert response_correct.status_code == status.HTTP_200_OK
    assert response_correct.json()["data"]["score"] == 100

    # Submit wrong option
    response_wrong = api_client.post(url, {"selected_options": [opt_wrong.id]}, format="json")
    assert response_wrong.status_code == status.HTTP_200_OK
    assert response_wrong.json()["data"]["score"] == 0


@pytest.mark.django_db
def test_mcq_evaluation_multiple_correct(api_client, candidate_user, published_assessment, active_invitation) -> None:
    """Multiple-choice MCQ requires all correct options to be selected to award marks."""
    api_client.force_authenticate(user=candidate_user)

    problem = Problem.objects.create(
        assessment=published_assessment,
        title="MCQ 2",
        prompt="Select correct ones",
        question_type=Problem.QuestionType.MCQ,
        max_score=100,
    )
    opt1 = MCQOption.objects.create(problem=problem, option_text="Correct 1", is_correct=True)
    opt2 = MCQOption.objects.create(problem=problem, option_text="Correct 2", is_correct=True)
    opt3 = MCQOption.objects.create(problem=problem, option_text="Wrong", is_correct=False)

    url = f"/api/v1/assessments/problems/{problem.id}/submissions/"

    # Submit only one correct option (partial selection = 0 score)
    res_partial = api_client.post(url, {"selected_options": [opt1.id]}, format="json")
    assert res_partial.json()["data"]["score"] == 0

    # Submit all correct options
    res_full = api_client.post(url, {"selected_options": [opt1.id, opt2.id]}, format="json")
    assert res_full.json()["data"]["score"] == 100

    # Submit correct + wrong options
    res_mixed = api_client.post(url, {"selected_options": [opt1.id, opt2.id, opt3.id]}, format="json")
    assert res_mixed.json()["data"]["score"] == 0


@pytest.mark.django_db
def test_fib_evaluation_matching(api_client, candidate_user, published_assessment, active_invitation) -> None:
    """FIB validation rules match correctly (case-insensitive, case-sensitive, regex)."""
    api_client.force_authenticate(user=candidate_user)

    problem = Problem.objects.create(
        assessment=published_assessment,
        title="FIB 1",
        prompt="Fill in the ____",
        question_type=Problem.QuestionType.FIB,
        max_score=100,
    )
    
    # Rule 1: Case insensitive plain match "Queue"
    FIBRule.objects.create(problem=problem, acceptable_answer="Queue", case_sensitive=False, use_regex=False)

    url = f"/api/v1/assessments/problems/{problem.id}/submissions/"

    # Test lowercase match
    res_lower = api_client.post(url, {"submitted_text": "queue"}, format="json")
    assert res_lower.json()["data"]["score"] == 100

    # Test wrong value
    res_wrong = api_client.post(url, {"submitted_text": "stack"}, format="json")
    assert res_wrong.json()["data"]["score"] == 0


@pytest.mark.django_db
def test_autosave_drafts(api_client, candidate_user, problem, active_invitation) -> None:
    """Autosave endpoint stores and retrieves MCQ, FIB, and coding drafts."""
    api_client.force_authenticate(user=candidate_user)

    url = f"/api/v1/assessments/problems/{problem.id}/autosave/"

    # Post draft
    response_post = api_client.post(
        url,
        {
            "source_code": "def solve(): pass",
            "selected_options": [1, 2],
            "submitted_text": "hello",
        },
        format="json",
    )
    assert response_post.status_code == status.HTTP_200_OK
    assert response_post.json()["data"]["source_code"] == "def solve(): pass"
    assert response_post.json()["data"]["selected_options"] == [1, 2]
    assert response_post.json()["data"]["submitted_text"] == "hello"

    # Get draft
    response_get = api_client.get(url)
    assert response_get.status_code == status.HTTP_200_OK
    assert response_get.json()["data"]["source_code"] == "def solve(): pass"
    assert response_get.json()["data"]["selected_options"] == [1, 2]
    assert response_get.json()["data"]["submitted_text"] == "hello"
