"""
OpenAPI metadata normalization for drf-spectacular.

The operation summaries are derived from the repository's canonical
openapi.yaml and embedded here so runtime schema generation remains
self-contained.

This module changes documentation metadata only. It does not modify
runtime routes, authentication behavior, permissions, or domain logic.
"""

from __future__ import annotations


HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
}


OPERATION_SUMMARIES = {('DELETE', '/api/v1/consultations/{consultation_id}/'): 'Delete consultation',
 ('DELETE', '/api/v1/health-records/{health_record_id}/'): 'Delete health record',
 ('DELETE', '/api/v1/health-statuses/{status_id}/'): 'Delete health status',
 ('GET', '/api/auth/csrf/'): 'Get CSRF token',
 ('GET', '/api/auth/me/'): 'Get current Clinic user',
 ('GET', '/api/v1/consultations/'): 'List consultations',
 ('GET', '/api/v1/consultations/{consultation_id}/'): 'Get consultation',
 ('GET', '/api/v1/dashboard/'): 'Get Clinic dashboard',
 ('GET', '/api/v1/health'): 'Check Clinic API health',
 ('GET', '/api/v1/health-records/'): 'List health records',
 ('GET', '/api/v1/health-records/{health_record_id}/'): 'Get health record',
 ('GET', '/api/v1/health-statuses/'): 'List health statuses',
 ('GET', '/api/v1/health-statuses/{status_id}/'): 'Get health status',
 ('GET', '/api/v1/integrations/faculty/health-status/{student_id}/'): 'Get student health status '
                                                                      'for Faculty',
 ('GET', '/api/v1/integrations/student-portal/health-status/{student_id}/'): 'Get student health '
                                                                             'status for Student '
                                                                             'Portal',
 ('GET', '/api/v1/medicine-dispensations/'): 'List medicine dispensations',
 ('GET', '/api/v1/medicine-dispensations/{dispensation_id}/'): 'Get medicine dispensation',
 ('GET', '/api/v1/medicines/'): 'List medicines',
 ('GET', '/api/v1/medicines/{medicine_id}/'): 'Get medicine',
 ('GET', '/api/v1/reports/clinic-visits/'): 'Get clinic visits report',
 ('GET', '/api/v1/reports/health-records/'): 'Get health records report',
 ('GET', '/api/v1/reports/medicine-dispensations/'): 'Get medicine dispensations report',
 ('GET', '/api/v1/reports/medicine-inventory/'): 'Get medicine inventory report',
 ('GET', '/api/v1/students/'): 'List students',
 ('GET', '/api/v1/students/{student_id}/'): 'Get student',
 ('GET', '/api/v1/users/'): 'List Clinic staff accounts',
 ('GET', '/api/v1/users/{user_id}/'): 'Get Clinic staff account',
 ('PATCH', '/api/v1/consultations/{consultation_id}/'): 'Partially update consultation',
 ('PATCH', '/api/v1/health-records/{health_record_id}/'): 'Partially update health record',
 ('PATCH', '/api/v1/health-statuses/{status_id}/'): 'Partially update health status',
 ('PATCH', '/api/v1/users/{user_id}/'): 'Partially update Clinic staff account',
 ('POST', '/api/auth/login/'): 'Log in to the Clinic system',
 ('POST', '/api/auth/logout/'): 'Log out of the Clinic system',
 ('POST', '/api/v1/consultations/'): 'Create consultation',
 ('POST', '/api/v1/health-records/'): 'Create health record',
 ('POST', '/api/v1/health-statuses/'): 'Create health status',
 ('POST', '/api/v1/medicine-dispensations/'): 'Dispense medicine',
 ('POST', '/api/v1/medicine-dispensations/{dispensation_id}/rollback/'): 'Roll back medicine '
                                                                         'dispensation',
 ('POST', '/api/v1/users/'): 'Create Clinic staff account',
 ('POST', '/api/v1/users/{user_id}/activate/'): 'Activate Clinic staff account',
 ('POST', '/api/v1/users/{user_id}/deactivate/'): 'Deactivate Clinic staff account',
 ('PUT', '/api/v1/consultations/{consultation_id}/'): 'Replace consultation',
 ('PUT', '/api/v1/health-records/{health_record_id}/'): 'Replace health record',
 ('PUT', '/api/v1/health-statuses/{status_id}/'): 'Replace health status',
 ('PUT', '/api/v1/users/{user_id}/'): 'Update Clinic staff account'}


PUBLIC_OPERATIONS = {
    ("GET", "/api/v1/health"),
    ("GET", "/api/auth/csrf/"),
    ("POST", "/api/auth/login/"),
}


def postprocess_openapi_metadata(
    result,
    generator,
    request,
    public,
):
    """
    Complete metadata required by the project's Redocly rules.

    - Add canonical summaries to every operation.
    - Explicitly mark public operations with security: [] when needed.
    - Fail schema generation if an unknown/protected operation lacks
      a security declaration.
    """

    seen = set()

    for path, path_item in result.get(
        "paths",
        {},
    ).items():

        for method, operation in path_item.items():

            if method not in HTTP_METHODS:
                continue

            key = (
                method.upper(),
                path,
            )

            summary = OPERATION_SUMMARIES.get(
                key
            )

            if summary is None:
                raise RuntimeError(
                    "No canonical summary registered for "
                    f"{method.upper()} {path}."
                )

            operation[
                "summary"
            ] = summary

            if key in PUBLIC_OPERATIONS:
                operation[
                    "security"
                ] = []

            elif "security" not in operation:
                raise RuntimeError(
                    "Non-public operation has no "
                    "OpenAPI security declaration: "
                    f"{method.upper()} {path}."
                )

            seen.add(
                key
            )

    missing = (
        set(OPERATION_SUMMARIES)
        - seen
    )

    if missing:

        formatted = ", ".join(
            f"{method} {path}"
            for method, path
            in sorted(missing)
        )

        raise RuntimeError(
            "Canonical summary entries missing "
            "from generated schema: "
            + formatted
        )

    return result
