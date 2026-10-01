"""
Canonical API exception handling for the IDSC Clinic System.

Errors handled through Django REST Framework are returned using the
Clinic API Problem Details contract.
"""

import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404

from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)


PROBLEM_TYPES = {
    400: "https://clinic.example/problems/bad-request",
    401: "https://clinic.example/problems/unauthorized",
    403: "https://clinic.example/problems/forbidden",
    404: "https://clinic.example/problems/not-found",
    409: "https://clinic.example/problems/conflict",
    422: "https://clinic.example/problems/unprocessable-entity",
    500: "https://clinic.example/problems/internal-server-error",
    502: "https://clinic.example/problems/bad-gateway",
}


PROBLEM_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
    502: "Bad Gateway",
}


PROBLEM_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "unprocessable_entity",
    500: "internal_server_error",
    502: "bad_gateway",
}


def _problem_response(
    request,
    status_code,
    detail,
    *,
    errors=None,
    code=None,
):
    """
    Build the canonical Clinic Problem Details response.
    """
    data = {
        "type": PROBLEM_TYPES.get(
            status_code,
            "https://clinic.example/problems/error",
        ),
        "title": PROBLEM_TITLES.get(status_code, "Error"),
        "status": status_code,
        "detail": str(detail),
        "instance": request.path if request is not None else "",
        "code": code or PROBLEM_CODES.get(status_code, "error"),
    }

    if errors is not None:
        data["errors"] = errors

    return Response(
        data,
        status=status_code,
        content_type="application/problem+json",
    )


def _extract_detail(data, fallback):
    """
    Extract a human-readable detail string from a DRF error response.
    """
    if isinstance(data, dict):
        detail = data.get("detail")

        if detail is not None:
            return str(detail)

    if isinstance(data, list) and data:
        return str(data[0])

    return fallback


def custom_exception_handler(exc, context):
    """
    Convert handled API exceptions into the canonical Clinic
    Problem Details representation.
    """
    request = context.get("request")

    # Let DRF determine the appropriate status code first.
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code

        if isinstance(exc, DRFValidationError):
            return _problem_response(
                request,
                status_code,
                "The request contains invalid data.",
                errors=response.data,
            )

        detail = _extract_detail(
            response.data,
            PROBLEM_TITLES.get(status_code, "The request failed."),
        )

        code = None

        if hasattr(exc, "get_codes"):
            codes = exc.get_codes()

            if isinstance(codes, str):
                code = codes

        return _problem_response(
            request,
            status_code,
            detail,
            code=code,
        )

    # Django validation errors.
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            errors = exc.message_dict
        elif hasattr(exc, "messages"):
            errors = {"non_field_errors": exc.messages}
        else:
            errors = {"detail": str(exc)}

        return _problem_response(
            request,
            status.HTTP_400_BAD_REQUEST,
            "The request contains invalid data.",
            errors=errors,
        )

    # Django/model lookup failures.
    if isinstance(exc, (ObjectDoesNotExist, Http404)):
        return _problem_response(
            request,
            status.HTTP_404_NOT_FOUND,
            "The requested resource was not found.",
        )

    # Database constraint violations.
    if isinstance(exc, IntegrityError):
        logger.warning("Database IntegrityError encountered: %s", exc)

        return _problem_response(
            request,
            status.HTTP_400_BAD_REQUEST,
            "A database integrity constraint was violated.",
        )

    # Anything else is treated as an unexpected server error.
    logger.exception("Unhandled server error: %s", exc)

    return _problem_response(
        request,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "An unexpected server error occurred.",
    )