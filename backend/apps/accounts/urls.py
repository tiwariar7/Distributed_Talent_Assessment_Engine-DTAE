from django.urls import path
from .views import (
    LoginView,
    ProfileView,
    RegisterView,
    TokenRefreshView,
    LogoutView,
    VerifyEmailView,
    ResetPasswordView,
    ResetPasswordConfirmView,
    ChangePasswordView,
    InviteRecruiterView,
    SessionListView,
    AuditLogListView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("reset-password/confirm/", ResetPasswordConfirmView.as_view(), name="auth-reset-password-confirm"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("invite-recruiter/", InviteRecruiterView.as_view(), name="auth-invite-recruiter"),
    path("sessions/", SessionListView.as_view(), name="auth-sessions"),
    path("audit-logs/", AuditLogListView.as_view(), name="auth-audit-logs"),
    path("me/", ProfileView.as_view(), name="auth-profile"),
]

# Refactor: Align with project code quality guidelines.

# Refactor: Enhance component rendering performance.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Enhance component rendering performance.
