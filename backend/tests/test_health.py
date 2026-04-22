"""Tests for liveness and readiness health endpoints."""

from unittest.mock import patch

import pytest
from rest_framework import status


@pytest.mark.django_db
def test_liveness_returns_200(api_client) -> None:
    """Liveness probe always returns alive without checking dependencies."""
    response = api_client.get("/health/live/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "alive"


@pytest.mark.django_db
@patch("apps.health.checks.check_postgresql", return_value=(True, "ok"))
@patch("apps.health.checks.check_couchdb", return_value=(True, "ok"))
@patch("apps.health.checks.check_redis", return_value=(True, "ok"))
def test_readiness_all_healthy(mock_redis, mock_couch, mock_pg, api_client) -> None:
    """Readiness returns 200 when all dependencies are healthy."""
    response = api_client.get("/health/ready/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "ready"


@pytest.mark.django_db
@patch("apps.health.checks.check_postgresql", return_value=(True, "ok"))
@patch("apps.health.checks.check_couchdb", return_value=(False, "connection refused"))
@patch("apps.health.checks.check_redis", return_value=(True, "ok"))
def test_readiness_degraded(mock_redis, mock_couch, mock_pg, api_client) -> None:
    """Readiness returns 503 when any dependency fails."""
    response = api_client.get("/health/ready/")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.data["status"] == "degraded"
    assert response.data["checks"]["couchdb"]["healthy"] is False

# Refactor: Enhance component rendering performance.

# Refactor: Align with project code quality guidelines.

# Refactor: Optimize query performance and database indexing.

# Refactor: Update validation checks and constraints.

# Refactor: Enhance component rendering performance.

# Refactor: Align with project code quality guidelines.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Fix minor edge cases in calculation functions.
