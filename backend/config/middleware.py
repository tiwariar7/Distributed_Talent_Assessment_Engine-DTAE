"""
Centralized exception handling middleware for non-DRF views and general Django cycle errors.
"""

import logging
import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CentralizedExceptionMiddleware(MiddlewareMixin):
    """
    Catches exceptions occurring in Django views/middlewares
    and returns a standardized JSON response.
    """

    def process_exception(self, request, exception):
        logger.error(
            "Unhandled server exception on %s %s: %s",
            request.method,
            request.path,
            exception,
            exc_info=True,
        )

        response_data = {
            "success": False,
            "data": None,
            "error": {
                "code": "internal_error",
                "details": str(exception),
            },
            "message": "An unexpected server error occurred.",
        }

        return JsonResponse(response_data, status=500)
