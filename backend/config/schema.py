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


OPERATION_SUMMARIES = {
    ("GET", "/api/auth/setup/"): "Check first Owner registration availability",
    ("POST", "/api/auth/owner/register/"): "Register the first and only Owner",
    ('POST', '/api/v1/students/import/'): 'Get student by Registrar ID',
    ('GET', '/api/v1/mock/registrar/students/'): 'List mock Registrar students (owner only)',
    ('POST', '/api/v1/mock/registrar/students/'): 'Add mock Registrar student (owner only)',
    ('PATCH', '/api/v1/mock/registrar/students/{student_id}/'): 'Edit mock Registrar student (owner only)',
    ('GET', '/api/v1/mock/inventory/medicines/'): 'List mock Inventory medicines (owner only)',
    ('POST', '/api/v1/mock/inventory/medicines/'): 'Add mock Inventory medicine (owner only)',
    ('PATCH', '/api/v1/mock/inventory/medicines/{medicine_id}/'): 'Edit mock Inventory medicine (owner only)',
    ('DELETE', '/api/v1/mock/inventory/medicines/{medicine_id}/'): 'Delete mock Inventory medicine (owner only)',
    ('GET', '/api/v1/restock-requests/'): 'List Clinic restock requests',
    ('POST', '/api/v1/restock-requests/'): 'Request all or selected medicine restock',
    ('POST', '/api/v1/mock/inventory/restock-requests/{request_id}/fulfill/'): 'Fulfill mock restock request (owner only)',
    ('GET', '/api/v1/inventory-notifications/'): 'Read unread Inventory notifications',
    ('POST', '/api/v1/inventory-notifications/'): 'Mark Inventory notifications read',
    ('DELETE', '/api/v1/medicine-dispensations/{dispensation_id}/'): 'Delete dispensing history (owner or admin)',

    ("GET", "/api/v1/admins/{user_id}/"): "Retrieve administrator account (owner only)",
    ("PUT", "/api/v1/admins/{user_id}/"): "Update administrator account (owner only)",
    ("PATCH", "/api/v1/admins/{user_id}/"): "Partially update administrator account (owner only)",
 ('DELETE', '/api/v1/consultations/{consultation_id}/'): 'Delete consultation',
 ('DELETE', '/api/v1/admins/{user_id}/'): 'Delete Clinic administrator',
 ('DELETE', '/api/v1/users/{user_id}/'): 'Delete Clinic staff account',
 ('POST', '/api/v1/admins/{user_id}/deactivate/'): 'Deactivate Clinic administrator',
 ('POST', '/api/v1/admins/{user_id}/activate/'): 'Activate Clinic administrator',
 ('GET', '/api/v1/admins/'): 'List Clinic administrators',
 ('POST', '/api/v1/admins/'): 'Create Clinic administrator',
 ('POST', '/api/auth/username/change/'): 'Change your username',
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
 ('POST', '/api/auth/password/change/'): 'Change your password',
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
    ("GET", "/api/auth/setup/"),
    ("POST", "/api/auth/owner/register/"),
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

    for path, item in result.get('paths',{}).items():
        for method, operation in item.items():
            if method in ('post','put','patch','delete') and path.startswith('/api/v1/') and '/users/' not in path and '/admins/' not in path:
                operation.setdefault('parameters',[]).append({'name':'Idempotency-Key','in':'header','required':False,'description':'Optional actor/path scoped replay key. Reuse identical key/body after a network failure; changed body returns 409.','schema':{'type':'string','maxLength':128}})
            if method in ('put','patch','delete') and any(resource in path for resource in ('health-records/','consultations/','health-statuses/')):
                operation.setdefault('parameters',[]).append({'name':'If-Match','in':'header','required':False,'description':'ETag from latest detail response. Database mode rejects stale writes with 409.','schema':{'type':'string'}})
                operation['parameters'].append({'name':'X-Record-Version','in':'header','required':False,'description':'Original updated_at ISO datetime; database mode rejects stale edits with 409.','schema':{'type':'string','format':'date-time'}})
    return result
