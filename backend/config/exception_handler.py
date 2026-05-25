"""
Centralized exception handling for Django REST Framework.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Catch API exceptions and format as standardized JSON errors.
    """
    # Call DRF's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # The exception has been handled by DRF
        err_data = response.data
        message = "An error occurred."

        if isinstance(err_data, dict):
            err_copy = err_data.copy()
            if "detail" in err_copy:
                message = str(err_copy.pop("detail"))
            elif "message" in err_copy:
                message = str(err_copy.pop("message"))
            elif err_copy:
                # Validation errors or other dicts of errors
                first_key = next(iter(err_copy))
                first_val = err_copy[first_key]
                if isinstance(first_val, list) and first_val:
                    message = f"{first_key}: {first_val[0]}"
                else:
                    message = f"{first_key}: {first_val}"
        elif isinstance(err_data, list):
            if err_data:
                message = str(err_data[0])

        response.data = {
            "success": False,
            "data": None,
            "error": err_data if err_data else None,
            "message": message,
        }
    else:
        # Unhandled exceptions (e.g., database integrity errors, division by zero, etc.)
        logger.error(
            "Unhandled API exception on endpoint %s: %s",
            context["request"].path if "request" in context else "unknown",
            exc,
            exc_info=True,
        )
        response = Response(
            {
                "success": False,
                "data": None,
                "error": {"code": "server_error", "details": str(exc)},
                "message": "Internal Server Error",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
