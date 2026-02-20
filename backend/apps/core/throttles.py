from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """Stricter rate limit for authentication endpoints (login, register)."""
    scope = 'auth'
