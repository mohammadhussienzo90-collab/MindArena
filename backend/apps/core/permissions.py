from rest_framework.permissions import BasePermission


class IsOnboarded(BasePermission):
    """Only allow access if player has completed onboarding assessment."""
    message = 'Please complete your personality assessment first.'

    def has_permission(self, request, view):
        if not hasattr(request.user, 'player'):
            return False
        return request.user.player.onboarding_done


class IsPremium(BasePermission):
    """Only allow access for premium tier players."""
    message = 'This feature requires a premium subscription.'

    def has_permission(self, request, view):
        if not hasattr(request.user, 'player'):
            return False
        return request.user.player.premium_tier in ('premium', 'premium_plus')
