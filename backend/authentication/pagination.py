from clinic.pagination import ClinicPagination


class StaffPagination(ClinicPagination):
    """Staff account directories always default to ten, with a hard cap of ten."""
    page_size = 10
    max_page_size = 10

    def get_paginated_response_schema(self, schema):
        result = super().get_paginated_response_schema(schema)
        result["properties"]["page_size"].update(maximum=10, example=10)
        return result

    def get_schema_operation_parameters(self, view):
        parameters = super().get_schema_operation_parameters(view)
        for parameter in parameters:
            if parameter["name"] == "page_size":
                parameter["schema"].update(maximum=10, default=10)
                parameter["description"] = "Default 10; requests above 10 are clamped to 10."
        return parameters
