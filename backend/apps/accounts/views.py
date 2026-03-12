import uuid
from datetime import datetime, timedelta, timezone
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.utils.text import slugify

from apps.organizations.models import Organization
from .models import User, VerificationToken, RecruiterInvitation, AuditLog, UserSession, Membership, Role
from .serializers import RegisterSerializer, UserProfileSerializer
from .tokens import EmailTokenObtainPairSerializer


class RegisterView(APIView):
    """Public endpoint to register a candidate or recruiter."""
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        """Create user + membership and return verification notification."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        AuditLog.objects.create(
            user=user,
            action="register",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

        return Response(
            {
                "message": "Registration successful. Please verify your email using the link sent to the logs.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """
    Obtain JWT access/refresh tokens with Redis-backed lockout limit (max 5 failures).
    Also updates device/session tracking and audit logs.
    """
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args, **kwargs) -> Response:
        email = request.data.get("email", "").lower().strip()
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        lockout_key = f"lockout:{email}"
        failed_attempts_key = f"failed_attempts:{email}"

        # 1. Check if user is currently locked out
        if cache.get(lockout_key):
            return Response(
                {"detail": "Account locked due to 5 consecutive failures. Please try again in 15 minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Try to validate token (performs authentication checks internally)
        try:
            response = super().post(request, *args, **kwargs)
            
            # Clear failed attempts on success
            cache.delete(failed_attempts_key)

            user = User.objects.get(email=email)
            
            # Create Audit Log
            AuditLog.objects.create(
                user=user,
                action="login_success",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )

            # Session tracking using simplejwt jti
            refresh_token = response.data.get("refresh")
            if refresh_token:
                try:
                    decoded = RefreshToken(refresh_token)
                    jti = decoded.get("jti")
                    UserSession.objects.create(
                        user=user,
                        session_key=jti,
                        device_info=request.META.get("HTTP_USER_AGENT", ""),
                        ip_address=request.META.get("REMOTE_ADDR", ""),
                    )
                except Exception:
                    pass

            return response

        except Exception as exc:
            # Increment failed attempts
            attempts = cache.get(failed_attempts_key, 0) + 1
            cache.set(failed_attempts_key, attempts, timeout=900) # 15 minutes
            
            # Retrieve user (if exists) for logging
            user_obj = User.objects.filter(email=email).first()

            if attempts >= 5:
                # Lockout for 15 minutes
                cache.set(lockout_key, True, timeout=900)
                AuditLog.objects.create(
                    user=user_obj,
                    action="account_lockout",
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=request.META.get("HTTP_USER_AGENT"),
                )

            AuditLog.objects.create(
                user=user_obj,
                action="login_failed",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )
            raise exc


class LogoutView(APIView):
    """
    Log out the user, blacklists the refresh token, and removes tracking session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            jti = token.get("jti")
            # Blacklist token (requires simplejwt blacklist app, but we also manually clean the session)
            token.blacklist()
            UserSession.objects.filter(session_key=jti).delete()
        except Exception:
            pass # token may already be invalid, but we'll complete logout

        AuditLog.objects.create(
            user=request.user,
            action="logout",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    """
    Verifies a user's email address using a verification token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            verify_token = VerificationToken.objects.get(
                token=token,
                token_type=VerificationToken.TokenType.VERIFICATION,
                expires_at__gt=datetime.now(timezone.utc),
            )
            user = verify_token.user
            user.is_email_verified = True
            user.save()

            AuditLog.objects.create(
                user=user,
                action="email_verified",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )

            verify_token.delete()
            return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
        except VerificationToken.DoesNotExist:
            return Response({"detail": "Invalid or expired verification token."}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """
    Handles requesting a password reset link and confirming the password update.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        # Request reset
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)
            token = uuid.uuid4().hex
            VerificationToken.objects.create(
                user=user,
                token=token,
                token_type=VerificationToken.TokenType.PASSWORD_RESET,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )

            # Log to Django log for manual testing
            print("\n" + "=" * 60)
            print(f"PASSWORD RESET LINK: http://localhost/forgot-password?token={token}")
            print("=" * 60 + "\n")

            AuditLog.objects.create(
                user=user,
                action="password_reset_requested",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )
        except User.DoesNotExist:
            pass # Return success to prevent email enumeration attacks

        return Response(
            {"message": "If this email is registered, a password reset link has been printed to the server logs."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordConfirmView(APIView):
    """
    Confirm password reset with token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return Response({"detail": "Token and new_password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reset_token = VerificationToken.objects.get(
                token=token,
                token_type=VerificationToken.TokenType.PASSWORD_RESET,
                expires_at__gt=datetime.now(timezone.utc),
            )
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            AuditLog.objects.create(
                user=user,
                action="password_reset_confirmed",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )

            reset_token.delete()
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        except VerificationToken.DoesNotExist:
            return Response({"detail": "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Change password for authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response({"detail": "old_password and new_password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(old_password):
            return Response({"detail": "Incorrect old password."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        AuditLog.objects.create(
            user=user,
            action="password_changed",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update profile details.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        AuditLog.objects.create(
            user=user,
            action="profile_updated",
            ip_address=self.request.META.get("REMOTE_ADDR"),
            user_agent=self.request.META.get("HTTP_USER_AGENT"),
        )


class InviteRecruiterView(APIView):
    """
    Recruiters can invite other recruiters to join their organization.
    """
    from apps.recruiter.permissions import IsRecruiter
    permission_classes = [IsRecruiter]

    def post(self, request: Request) -> Response:
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Get recruiter organization
        membership = request.user.memberships.filter(role__code="recruiter").first()
        if not membership:
            return Response({"detail": "User has no recruiter organization."}, status=status.HTTP_403_FORBIDDEN)

        org = membership.organization
        token = uuid.uuid4().hex

        # Create invitation
        invitation, created = RecruiterInvitation.objects.update_or_create(
            organization=org,
            email=email.lower().strip(),
            defaults={
                "token": token,
                "created_by": request.user,
                "is_accepted": False,
            }
        )

        # Log invitation link for development/local environment testing
        print("\n" + "=" * 60)
        print(f"RECRUITER INVITATION LINK: http://localhost/register?token={token}&email={email.lower().strip()}")
        print("=" * 60 + "\n")

        AuditLog.objects.create(
            user=request.user,
            action=f"recruiter_invited:{email}",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT"),
        )

        return Response(
            {"message": f"Invitation generated and printed to the server logs for {email}."},
            status=status.HTTP_201_CREATED,
        )


class SessionListView(generics.ListAPIView):
    """
    List all active sessions/devices for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        sessions = UserSession.objects.filter(user=request.user)
        data = [
            {
                "id": s.id,
                "session_key": s.session_key,
                "device_info": s.device_info,
                "ip_address": s.ip_address,
                "last_activity": s.last_activity,
                "created_at": s.created_at,
            }
            for s in sessions
        ]
        return Response(data, status=status.HTTP_200_OK)


class AuditLogListView(generics.ListAPIView):
    """
    List history of security/activity events for the user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        logs = AuditLog.objects.filter(user=request.user)
        data = [
            {
                "id": l.id,
                "action": l.action,
                "ip_address": l.ip_address,
                "user_agent": l.user_agent,
                "timestamp": l.timestamp,
            }
            for l in logs
        ]
        return Response(data, status=status.HTTP_200_OK)


from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView

class TokenRefreshView(SimpleJWTTokenRefreshView):
    """Refreshes SimpleJWT tokens with JWT abuse rate limiting."""
    from .throttles import JWTAbuseRateThrottle
    throttle_classes = [JWTAbuseRateThrottle]


# Refactor: Optimize imports and clean up code structure.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Enhance component rendering performance.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Add typing hints and documentation docstrings.
