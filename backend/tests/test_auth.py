"""Tests for JWT registration and login."""

import pytest
from rest_framework import status

from apps.accounts.models import Membership, User


@pytest.mark.django_db
def test_register_creates_user_and_membership(api_client, organization, candidate_role) -> None:
    """Registration returns JWT tokens and persists membership."""
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "newbie@test.com",
            "password": "SecurePass123!",
            "organization_slug": organization.slug,
            "role": "candidate",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert "message" in response.data
    assert "email" in response.data
    assert User.objects.filter(email="newbie@test.com").exists()
    assert Membership.objects.filter(
        user__email="newbie@test.com",
        organization=organization,
        role=candidate_role,
    ).exists()


@pytest.mark.django_db
def test_login_with_email_returns_jwt(api_client, candidate_user) -> None:
    """Candidates can obtain tokens using email + password."""
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": "candidate@test.com", "password": "testpass123"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


@pytest.mark.django_db
def test_profile_requires_authentication(api_client) -> None:
    """Profile endpoint rejects unauthenticated callers."""
    response = api_client.get("/api/v1/auth/me/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_profile_returns_memberships(api_client, candidate_user) -> None:
    """Authenticated users see organization roles on /me/."""
    api_client.force_authenticate(user=candidate_user)
    response = api_client.get("/api/v1/auth/me/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == "candidate@test.com"
    assert len(response.data["memberships"]) == 1
    assert response.data["memberships"][0]["role"] == "candidate"

# Refactor: Optimize imports and clean up code structure.

# Refactor: Improve error handling and exception logging.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Improve responsive styles and layouts.

# Refactor: Refactor variable names for better readability.

# Refactor: Improve error handling and exception logging.
