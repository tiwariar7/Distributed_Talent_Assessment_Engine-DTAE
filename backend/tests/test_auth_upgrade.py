import pytest
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from apps.accounts.models import VerificationToken, RecruiterInvitation, UserSession, AuditLog

User = get_user_model()


@pytest.mark.django_db
def test_recruiter_register_onboarding_organization(api_client, recruiter_role):
    url = reverse("auth-register")
    data = {
        "email": "hiring@newcorp.test",
        "password": "NewSecurePassword123!",
        "first_name": "Alice",
        "last_name": "Hiring",
        "organization_name": "New Corp",
        "role": "recruiter",
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "verify your email" in response.data["message"]

    # Verify user and organization are created
    user = User.objects.get(email="hiring@newcorp.test")
    assert user.first_name == "Alice"
    assert user.is_email_verified is False

    # Check organization slugification
    membership = user.memberships.first()
    assert membership.organization.name == "New Corp"
    assert membership.organization.slug == "new-corp"
    assert membership.role.code == "recruiter"


@pytest.mark.django_db
def test_login_brute_force_lockout(api_client, candidate_user, monkeypatch):
    # Disable the login endpoint rate throttle to only test brute-force lockout
    monkeypatch.setattr(
        "apps.accounts.throttles.LoginRateThrottle.allow_request",
        lambda self, request, view: True
    )

    # Reset cache keys
    email = candidate_user.email
    cache.delete(f"lockout:{email}")
    cache.delete(f"failed_attempts:{email}")

    url = reverse("auth-login")
    
    # Perform 4 failed login attempts (expect 401)
    for _ in range(4):
        response = api_client.post(url, {"email": email, "password": "WrongPassword"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # The 5th failed attempt should lock it out and also return 401 (first lockout trigger)
    response = api_client.post(url, {"email": email, "password": "WrongPassword"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # The 6th attempt should be locked out (returns 429)
    response = api_client.post(url, {"email": email, "password": "WrongPassword"})
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "locked" in response.json()["error"]["detail"]

    # Lockout audit log should be present
    assert AuditLog.objects.filter(user=candidate_user, action="account_lockout").exists()

    # Clear cache to reset test state
    cache.delete(f"lockout:{email}")
    cache.delete(f"failed_attempts:{email}")


@pytest.mark.django_db
def test_email_verification_flow(api_client, candidate_role):
    register_url = reverse("auth-register")
    reg_data = {
        "email": "verify@test.com",
        "password": "SecurePassWord123!",
        "role": "candidate",
    }
    api_client.post(register_url, reg_data)

    user = User.objects.get(email="verify@test.com")
    assert user.is_email_verified is False

    token_obj = VerificationToken.objects.get(user=user, token_type=VerificationToken.TokenType.VERIFICATION)
    
    # Call verify-email endpoint
    verify_url = reverse("auth-verify-email")
    response = api_client.post(verify_url, {"token": token_obj.token})
    assert response.status_code == status.HTTP_200_OK
    
    user.refresh_from_db()
    assert user.is_email_verified is True
    assert not VerificationToken.objects.filter(pk=token_obj.pk).exists()


@pytest.mark.django_db
def test_password_reset_flow(api_client, candidate_user):
    # Request password reset
    url = reverse("auth-reset-password")
    response = api_client.post(url, {"email": candidate_user.email})
    assert response.status_code == status.HTTP_200_OK

    token_obj = VerificationToken.objects.get(user=candidate_user, token_type=VerificationToken.TokenType.PASSWORD_RESET)

    # Confirm password reset
    confirm_url = reverse("auth-reset-password-confirm")
    response = api_client.post(confirm_url, {
        "token": token_obj.token,
        "new_password": "NewCrazyPassword123!!",
    })
    assert response.status_code == status.HTTP_200_OK

    # Attempt to log in with new password
    login_url = reverse("auth-login")
    response = api_client.post(login_url, {
        "email": candidate_user.email,
        "password": "NewCrazyPassword123!!",
    })
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


@pytest.mark.django_db
def test_recruiter_invitation_flow(api_client, recruiter_user, recruiter_role):
    # Authenticate recruiter
    api_client.force_authenticate(user=recruiter_user)

    invite_url = reverse("auth-invite-recruiter")
    response = api_client.post(invite_url, {"email": "new_recruiter@demo.test"})
    assert response.status_code == status.HTTP_201_CREATED

    invitation = RecruiterInvitation.objects.get(email="new_recruiter@demo.test")
    assert invitation.is_accepted is False

    api_client.force_authenticate(user=None)

    # Register using invitation
    register_url = reverse("auth-register")
    data = {
        "email": "new_recruiter@demo.test",
        "password": "AnotherNewPassword123!",
        "role": "recruiter",
        "invitation_token": invitation.token,
    }
    response = api_client.post(register_url, data)
    assert response.status_code == status.HTTP_201_CREATED

    invitation.refresh_from_db()
    assert invitation.is_accepted is True

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Optimize query performance and database indexing.

# Refactor: Optimize query performance and database indexing.
