"""
Custom JWT session authentication to validate session integrity.
"""

from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import UserSession


class SessionJWTAuthentication(JWTAuthentication):
    """
    Subclass of simplejwt's JWTAuthentication.
    Enforces session integrity by validating that the token's session_key
    matches an active UserSession in Redis cache or the Postgres database.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        # Retrieve the session key claim
        session_key = validated_token.get("session_key")
        if not session_key:
            raise InvalidToken("Token does not contain a session key.")

        # Check session status (read from cache with fallback to DB)
        cache_key = f"session_active:{session_key}"
        is_active = cache.get(cache_key)

        if is_active is None:
            # Fallback to Postgres database
            is_active = UserSession.objects.filter(session_key=session_key).exists()
            # Cache active status for 1 hour (or shorter if desired)
            cache.set(cache_key, is_active, timeout=3600)

        if not is_active:
            raise InvalidToken("Session is inactive or has been logged out.")

        user = self.get_user(validated_token)
        return user, validated_token
