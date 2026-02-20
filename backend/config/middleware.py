"""Custom middleware for MindArena."""
import logging
import time

logger = logging.getLogger('apps')


class RequestTimingMiddleware:
    """Log request method, path, status code, and duration for API requests."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/'):
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        log_method = logger.info if duration_ms < 500 else logger.warning
        log_method(
            '%s %s %d (%.0fms) user=%s',
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            getattr(request, 'user', None) or '-',
        )
        return response
