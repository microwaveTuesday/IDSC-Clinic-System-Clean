"""Compatibility exports for existing URL imports; controllers live in focused modules."""
from .view_support import clinic_service, parse_optional_report_date, Conflict, UnprocessableEntity
from .report_views import HealthView
from .report_views import DashboardView
from .report_views import ClinicVisitsReportView
from .report_views import HealthRecordsReportView
from .report_views import MedicineInventoryReportView
from .report_views import MedicineDispensationReportView
from .report_views import StudentListView
from .report_views import StudentDetailView
from .clinical_views import HealthRecordViewSet
from .clinical_views import ConsultationViewSet
from .clinical_views import HealthStatusViewSet
from .inventory_views import MedicineListView
from .inventory_views import MedicineDetailView
from .inventory_views import MedicineDispensationViewSet
from .projection_views import HealthStatusIntegrationView
from .projection_views import FacultyHealthStatusIntegrationView
from .projection_views import StudentPortalHealthStatusIntegrationView
