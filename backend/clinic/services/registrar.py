"""
Registrar integration boundary.

For the midterm implementation this service uses deterministic mock data.
The public service interface is intentionally isolated so the mock
implementation can later be replaced by the real Registrar REST API without
changing Clinic views or domain models.
"""


class StudentNotFoundError(Exception):
    """Raised when Registrar does not contain the requested student."""


class StudentUnavailableError(Exception):
    """Raised when a student cannot participate in a new Clinic operation."""


class MockRegistrarService:
    """Midterm mock implementation of the Registrar integration."""

    _students = [
        {
            "student_id": "2026-0001",
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "course": "BSIT",
            "section": "3A",
            "status": "ACTIVE",
        },
        {
            "student_id": "2026-0002",
            "first_name": "Maria",
            "last_name": "Santos",
            "course": "BSCS",
            "section": "2B",
            "status": "ACTIVE",
        },
        {
            "student_id": "2026-0003",
            "first_name": "Pedro",
            "last_name": "Reyes",
            "course": "BSIT",
            "section": "4A",
            "status": "GRADUATED",
        },
    ]

    def list_students(self, search=None):
        students = [student.copy() for student in self._students]

        if not search:
            return students

        term = str(search).strip().lower()

        return [
            student
            for student in students
            if term in student["student_id"].lower()
            or term in student["first_name"].lower()
            or term in student["last_name"].lower()
            or term in student["course"].lower()
            or term in student["section"].lower()
        ]

    def get_student(self, student_id):
        student_id = str(student_id).strip()

        for student in self._students:
            if student["student_id"] == student_id:
                return student.copy()

        raise StudentNotFoundError(
            f"Student '{student_id}' was not found in Registrar."
        )

    def student_exists(self, student_id):
        try:
            self.get_student(student_id)
            return True
        except StudentNotFoundError:
            return False

    def validate_student_for_clinic(self, student_id):
        student = self.get_student(student_id)

        if student["status"] != "ACTIVE":
            raise StudentUnavailableError(
                f"Student '{student_id}' is not active."
            )

        return student


registrar_service = MockRegistrarService()