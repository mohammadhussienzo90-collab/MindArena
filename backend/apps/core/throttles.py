from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """Stricter rate limit for authentication endpoints (login, register)."""
    scope = 'auth'


class CompanionRateThrottle(UserRateThrottle):
    """Rate limit for AI companion chat to control API costs."""
    scope = 'companion'
