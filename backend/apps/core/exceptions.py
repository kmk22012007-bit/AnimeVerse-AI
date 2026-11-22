import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError, NotFound, PermissionDenied
from django.http import Http404
from django.conf import settings

logger = logging.getLogger(__name__)

class AnimeverseAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_error = "bad_request"
    default_message = "A bad request occurred."

    def __init__(self, message=None, details=None, error=None, status_code=None):
        self.message = message or self.default_message
        self.details = details or {}
        self.error = error or self.default_error
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)

class ValidationError(AnimeverseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_error = "validation_error"
    default_message = "Validation failed."

class NotFoundError(AnimeverseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_error = "not_found"
    default_message = "The requested resource was not found."

class ForbiddenError(AnimeverseAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_error = "permission_denied"
    default_message = "You do not have permission to perform this action."

class DuplicateError(AnimeverseAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_error = "duplicate_resource"
    default_message = "The specified resource already exists."

class ServiceUnavailableError(AnimeverseAPIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_error = "service_unavailable"
    default_message = "An external service is currently unavailable."

class RateLimitError(AnimeverseAPIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_error = "rate_limit_exceeded"
    default_message = "Rate limit reached. Please retry after a delay."

def custom_exception_handler(exc, context):
    """
    Standardizes all API error responses to match SRS specification:
    {
        "error": "validation_error",
        "message": "Human readable message",
        "details": { "field": "Reason" }
    }
    """
    # Let DRF handle standard exceptions first
    response = exception_handler(exc, context)

    if isinstance(exc, AnimeverseAPIException):
        return Response({
            "error": exc.error,
            "message": exc.message,
            "details": exc.details
        }, status=exc.status_code)

    if response is not None:
        data = response.data
        status_code = response.status_code
        error_code = "error"
        message = "An error occurred."
        details = {}

        if status_code == 400:
            error_code = "validation_error"
            message = "Validation failed."
            if isinstance(data, dict):
                details = {}
                first_msgs = []
                for k, v in data.items():
                    msg_str = " ".join([str(item) for item in v]) if isinstance(v, list) else str(v)
                    details[k] = msg_str
                    first_msgs.append(f"{k}: {msg_str}")
                if first_msgs:
                    message = first_msgs[0]
            elif isinstance(data, list):
                details = {"non_field_errors": [str(x) for x in data]}
                message = str(data[0]) if data else "Validation failed."
        elif status_code == 403:
            error_code = "permission_denied"
            message = data.get("detail", "You do not have permission to perform this action.") if isinstance(data, dict) else str(data)
            details = {}
        elif status_code == 404:
            error_code = "not_found"
            message = data.get("detail", "The requested resource was not found.") if isinstance(data, dict) else str(data)
            details = {}
        elif status_code == 409:
            error_code = "duplicate"
            message = data.get("detail", "Resource already exists.") if isinstance(data, dict) else str(data)
            details = {}
        elif status_code == 429:
            error_code = "rate_limited"
            message = data.get("detail", "Too many requests. Please wait.") if isinstance(data, dict) else str(data)
            details = {}
        elif status_code == 503:
            error_code = "service_unavailable"
            message = data.get("detail", "Service is unavailable.") if isinstance(data, dict) else str(data)
            details = {}
        else:
            if isinstance(data, dict):
                message = str(data.get("detail", message))
                details = data
            else:
                message = str(data)

        response.data = {
            "error": error_code,
            "message": str(message),
            "details": details
        }
        return response

    # Fallback for unexpected unhandled exceptions (secure sanitization)
    logger.exception("Unhandled server exception: %s", exc)
    msg = str(exc) if (getattr(settings, 'DEBUG', False) and exc) else "An unexpected internal server error occurred."
    return Response({
        "error": "server_error",
        "message": msg,
        "details": {}
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
