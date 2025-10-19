from django.urls import path
from . import views

urlpatterns = [
    # Appointments
    path('appointments/', views.AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/create/', views.AppointmentCreateView.as_view(), name='appointment-create'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),

    # Test Requests (doctor -> lab)
    path('test-requests/', views.TestRequestListView.as_view(), name='testrequest-list'),
    path('test-requests/create/', views.TestRequestCreateView.as_view(), name='testrequest-create'),

    # Vital Requests (doctor -> nurse)
    path('vital-requests/', views.VitalRequestListView.as_view(), name='vitalrequest-list'),
    path('vital-requests/create/', views.VitalRequestCreateView.as_view(), name='vitalrequest-create'),

    # Nurse posts vitals
    path('vitals/create/', views.VitalsCreateView.as_view(), name='vitals-create'),

    # Lab posts results
    path('lab-results/create/', views.LabResultCreateView.as_view(), name='labresult-create'),

    # Doctor posts final report
    path('medical-reports/create/', views.MedicalReportCreateView.as_view(), name='medicalreport-create'),

    # ---------------- Blog ----------------
    path('blog/', views.BlogPostListCreateView.as_view(), name='blog-list-create'),
    path('blog/<slug:slug>/', views.BlogPostDetailView.as_view(), name='blog-detail'),
]
