"""Shared pytest fixtures."""

import os
os.environ["OTEL_ENABLED"] = "False"

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Role
from apps.assessments.models import Assessment, Problem
from apps.organizations.models import Organization
from infrastructure.couchdb import CouchDBClient


@pytest.fixture(autouse=True)
def clear_cache_before_test() -> None:
    """Reset throttle counters between tests."""
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def organization(db) -> Organization:
    """Active demo organization."""
    return Organization.objects.create(name="Test Org", slug="test-org")


@pytest.fixture
def candidate_role(db) -> Role:
    """Candidate role row."""
    return Role.objects.create(code="candidate", description="Candidate")


@pytest.fixture
def recruiter_role(db) -> Role:
    """Recruiter role row."""
    return Role.objects.create(code="recruiter", description="Recruiter")


@pytest.fixture
def candidate_user(db, organization, candidate_role, django_user_model):
    """Authenticated candidate with membership."""
    user = django_user_model.objects.create_user(
        username="candidate@test.com",
        email="candidate@test.com",
        password="testpass123",
    )
    Membership.objects.create(
        user=user,
        organization=organization,
        role=candidate_role,
    )
    return user


@pytest.fixture
def recruiter_user(db, organization, recruiter_role, django_user_model):
    """Authenticated recruiter with membership."""
    user = django_user_model.objects.create_user(
        username="recruiter@test.com",
        email="recruiter@test.com",
        password="testpass123",
    )
    Membership.objects.create(
        user=user,
        organization=organization,
        role=recruiter_role,
    )
    return user


@pytest.fixture
def published_assessment(db, organization) -> Assessment:
    """Published assessment with one Python problem."""
    assessment = Assessment.objects.create(
        organization=organization,
        title="Sample Assessment",
        description="Test assessment",
        status=Assessment.Status.PUBLISHED,
        duration_minutes=60,
    )
    return assessment


@pytest.fixture
def problem(db, published_assessment) -> Problem:
    """Problem linked to the published assessment."""
    return Problem.objects.create(
        assessment=published_assessment,
        title="Echo Input",
        prompt="Read a line from stdin and print it.",
        language=Problem.Language.PYTHON,
        max_score=100,
        couchdb_test_cases_doc_id="test_cases_problem_1",
    )


@pytest.fixture
def couchdb_available() -> bool:
    """Return True when CouchDB accepts connections (for integration tests)."""
    try:
        client = CouchDBClient()
        response = client.session.get(f"{client.base_url}/_up", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(autouse=True)
def mock_redis_connection(monkeypatch):
    """Mock Redis client for the WebSocket consumer to avoid connection hang."""
    class MockRedisClient:
        def __init__(self):
            self.storage = {}

        async def incr(self, key, amount=1):
            val = self.storage.get(key, 0) + amount
            self.storage[key] = val
            return val

        async def decr(self, key, amount=1):
            val = self.storage.get(key, 0) - amount
            self.storage[key] = val
            return val

        async def expire(self, key, time):
            return True

        async def close(self):
            pass

    client = MockRedisClient()
    import redis.asyncio as aioredis
    monkeypatch.setattr(aioredis, "from_url", lambda *args, **kwargs: client)
    return client

