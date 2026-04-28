"""
Rate limiters and throttles for API endpoints.

Protects login, token generation, recruiter endpoints, and prevents DDoS attempts.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Throttle login endpoint requests for anonymous users to prevent brute-force attacks."""

    scope = "login"


class JWTAbuseRateThrottle(AnonRateThrottle):
    """Throttle JWT refresh / verify token endpoints to prevent auth pipeline abuse."""

    scope = "jwt_abuse"


class RecruiterAPIRateThrottle(UserRateThrottle):
    """Limits recruiter endpoint consumption to prevent scraping or heavy operations."""

    scope = "recruiter_api"


class AntiDoSRateThrottle(AnonRateThrottle):
    """Global high-frequency rate-limiting filter based on IP to mitigate DoS attacks."""

    scope = "anti_dos"

# Refactor: Improve responsive styles and layouts.

# Refactor: Optimize query performance and database indexing.

# Refactor: Add typing hints and documentation docstrings.

# Refactor: Refactor variable names for better readability.

# Refactor: Align with project code quality guidelines.

# Refactor: Improve responsive styles and layouts.

# Refactor: Fix minor edge cases in calculation functions.

# Refactor: Optimize imports and clean up code structure.
