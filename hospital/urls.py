from django.urls import path
from .views import (
    AppointmentCreateView, AppointmentListView, AppointmentDetailView,
    VitalsCreateView, LabResultCreateView, MedicalReportCreateView
)

urlpatterns = [
    path('appointments/', AppointmentListView.as_view(), name='appointments_list'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment_detail'),
    path('appointments/create/', AppointmentCreateView.as_view(), name='appointment_create'),
    path('vitals/create/', VitalsCreateView.as_view(), name='vitals_create'),
    path('lab/create/', LabResultCreateView.as_view(), name='lab_create'),
    path('report/create/', MedicalReportCreateView.as_view(), name='report_create'),
]
