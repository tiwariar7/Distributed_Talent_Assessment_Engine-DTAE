"""Tests for CouchDB-backed leaderboard service."""

from unittest.mock import MagicMock, patch

import pytest

from apps.leaderboard.services import LeaderboardService


@pytest.mark.django_db
@patch("redis.Redis.from_url")
@patch("apps.leaderboard.services.CouchDBClient")
def test_get_rankings_queries_mapreduce_view(mock_client_cls, mock_redis_cls) -> None:
    """Rankings are fetched from the Redis cache if hit."""
    mock_redis = MagicMock()
    mock_redis_cls.return_value = mock_redis
    mock_redis.zrevrange.return_value = [(b"42", 200), (b"7", 100)]
    mock_redis.hget.side_effect = [b"2", b"1"]

    from apps.accounts.models import User
    User.objects.create_user(id=42, username="user42@test.com", email="user42@test.com")
    User.objects.create_user(id=7, username="user7@test.com", email="user7@test.com")

    rankings = LeaderboardService.get_rankings(assessment_id=1, limit=10)

    assert rankings[0]["rank"] == 1
    assert rankings[0]["candidate_id"] == 42
    assert rankings[0]["total_score"] == 200
    assert rankings[0]["problems_solved"] == 2


@pytest.mark.django_db
@patch("redis.Redis.from_url")
@patch("apps.leaderboard.services.CouchDBClient")
def test_upsert_entry_creates_document_when_missing(mock_client_cls, mock_redis_cls) -> None:
    """First score for a candidate creates a new leaderboard document."""
    mock_redis = MagicMock()
    mock_redis_cls.return_value = mock_redis
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    import requests

    not_found = requests.HTTPError("not found")
    not_found.response = MagicMock(status_code=404)
    mock_client.get_document.side_effect = not_found

    # Setup database entities
    from apps.organizations.models import Organization
    from apps.assessments.models import Assessment, Problem, Submission
    from apps.accounts.models import User
    org = Organization.objects.create(name="Test Org", slug="test-org")
    assessment = Assessment.objects.create(id=5, organization=org, title="Ass1")
    prob = Problem.objects.create(assessment=assessment, title="P1", max_score=100)
    user = User.objects.create_user(id=9, username="candidate9@test.com", email="candidate9@test.com")
    Submission.objects.create(problem=prob, candidate=user, score=50)

    LeaderboardService.upsert_entry(
        assessment_id=5,
        candidate_id=9,
        score_delta=50,
        problems_solved_delta=1,
    )

    mock_client.create_document.assert_called_once()
    args, _ = mock_client.create_document.call_args
    assert args[0] == "leaderboard_5_9"
    assert args[1]["total_score"] == 50


@pytest.mark.django_db
@pytest.mark.integration
def test_bootstrap_and_leaderboard_integration(couchdb_available) -> None:
    """Integration: install views and upsert a leaderboard entry in real CouchDB."""
    if not couchdb_available:
        pytest.skip("CouchDB is not available")

    from django.core.management import call_command
    from infrastructure.couchdb import CouchDBClient
    from apps.organizations.models import Organization
    from apps.assessments.models import Assessment, Problem, Submission
    from apps.accounts.models import User

    # Set up database records
    org = Organization.objects.create(name="Integration Org", slug="integration-org")
    assessment = Assessment.objects.create(id=999, organization=org, title="Int Ass")
    prob = Problem.objects.create(assessment=assessment, title="P1", max_score=100)
    user = User.objects.create_user(id=1, username="integration_user@test.com", email="integration_user@test.com")
    Submission.objects.create(problem=prob, candidate=user, score=75)

    client = CouchDBClient()
    try:
        doc = client.get_document("leaderboard_999_1")
        client.session.delete(f"{client.db_url}/leaderboard_999_1", params={"rev": doc["_rev"]})
    except Exception:
        pass

    call_command("bootstrap_couchdb")
    LeaderboardService.upsert_entry(
        assessment_id=999,
        candidate_id=1,
        score_delta=75,
        problems_solved_delta=1,
    )

    document = client.get_document("leaderboard_999_1")
    assert document["total_score"] == 75


# Refactor: Improve error handling and exception logging.
