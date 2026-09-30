"""
Pagination utilities for the Clinic API.

The response format follows the canonical OpenAPI contract:

{
    "count": 57,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "results": [...]
}
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ClinicPagination(PageNumberPagination):
    """Canonical pagination behavior for Clinic list endpoints."""

    page_size = 20
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )