"""
Custom user model and role assignments (PostgreSQL, 3NF).

Roles are normalized into a separate table to avoid repeating role strings
on every user row (removes transitive dependency on role name).
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.organizations.models import Organization


class Role(models.Model):
    """
    Canonical role identifier (e.g. recruiter, candidate, admin).

    Stored once; users reference this row via Membership.
    """

    code = models.CharField(max_length=32, unique=True)
    description = models.CharField(max_length=255)

    class Meta:
        db_table = "roles"

    def __str__(self) -> str:
        return self.code


class User(AbstractUser):
    """
    Platform user. Organization linkage is via Membership (3NF).

    Email is the natural login identifier; username mirrors email for Django admin.
    """

    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    profile_image = models.FileField(upload_to="profiles/", null=True, blank=True)

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return self.email


class VerificationToken(models.Model):
    """
    Temporary token for email verification or password reset.
    """
    class TokenType(models.TextChoices):
        VERIFICATION = "VERIFICATION", "Verification"
        PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tokens")
    token = models.CharField(max_length=64, unique=True)
    token_type = models.CharField(max_length=20, choices=TokenType.choices)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verification_tokens"


class RecruiterInvitation(models.Model):
    """
    Invitation to join an organization as a recruiter.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invitations")
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recruiter_invitations"


class AuditLog(models.Model):
    """
    Activity and security auditing log.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]


class UserSession(models.Model):
    """
    Tracks active user sessions and devices.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_sessions"
        ordering = ["-last_activity"]



class Membership(models.Model):
    """
    Associates a user with an organization under a specific role.

    Composite uniqueness prevents duplicate role assignments (race-safe at DB level).
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organization", "role"],
                name="unique_membership_per_role",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.organization.slug} ({self.role.code})"
class CandidateProfile(models.Model):
    """
    Dedicated profile for candidate users.
    Stores professional credentials and portfolio information.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="candidate_profile")
    github_username = models.CharField(max_length=39, blank=True)
    resume_file = models.FileField(upload_to="resumes/", null=True, blank=True)
    skill_tags = models.JSONField(default=list, blank=True, help_text="e.g., ['Python', 'DSA', 'Algorithms']")
    cumulative_score = models.IntegerField(default=0)

    class Meta:
        db_table = "candidate_profiles"

    def __str__(self) -> str:
        return f"CandidateProfile for {self.user.email}"

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Optimize imports and clean up code structure.

# Refactor: Improve error handling and exception logging.

# Refactor: Align with project code quality guidelines.
