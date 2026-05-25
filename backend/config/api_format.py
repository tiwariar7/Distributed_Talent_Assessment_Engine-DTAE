"""
Custom DRF JSON renderer to standardize response formats.
"""

from rest_framework.renderers import JSONRenderer


class StandardResponseRenderer(JSONRenderer):
    """
    Standardized response renderer.
    Wraps response payloads in the format:
    {
        "success": true/false,
        "data": {},
        "error": null or err_details,
        "message": ""
    }
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        # Check if response is already formatted (e.g., from custom_exception_handler)
        is_formatted = (
            isinstance(data, dict)
            and "success" in data
            and "data" in data
            and "error" in data
        )

        if not is_formatted:
            # Determine success status based on HTTP status code.
            success = True
            if response and not (200 <= response.status_code < 300):
                success = False

            message = ""
            if isinstance(data, dict):
                if "message" in data:
                    data = data.copy()
                    message = data.pop("message")

            # Fallback for empty message based on status code
            if not message:
                if response and response.status_code == 201:
                    message = "Created successfully"
                elif response and response.status_code == 200:
                    message = "Success"

            data = {
                "success": success,
                "data": data,
                "error": None if success else data,
                "message": message,
            }

        return super().render(data, accepted_media_type, renderer_context)
