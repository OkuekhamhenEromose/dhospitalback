# hospital/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'assignments', views.AssignmentViewSet, basename='assignment')

urlpatterns = [
    # Appointments
    path('appointments/', views.AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/create/', views.AppointmentCreateView.as_view(), name='appointment-create'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),
    
    # Patients
    path('patients/', views.PatientListView.as_view(), name='patients-list'),

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
    path('staff/', views.StaffListView.as_view(), name='staff-list'),

    # Staff Availability
    path('staff/available/', views.AvailableStaffView.as_view(), name='available-staff'),
    
    # Assignments
    path('', include(router.urls)),
    path('appointments/<int:appointment_id>/assignments/', 
         views.AppointmentAssignmentsView.as_view(),
         name='appointment-assignments'),
    path('assign-staff/', views.AssignStaffView.as_view(), name='assign-staff'),

    # ---------------- Enhanced Blog URLs ----------------
    # Public blog endpoints
    path('blog/', views.BlogPostListCreateView.as_view(), name='blog-list-create'),
    path('blog/search/', views.BlogPostSearchView.as_view(), name='blog-search'),
    path('blog/latest/', views.BlogPostLatestView.as_view(), name='blog-latest'),
    path('blog/author/<int:author_id>/', views.BlogPostByAuthorView.as_view(), name='blog-by-author'),
    path('blog/<slug:slug>/', views.BlogPostDetailView.as_view(), name='blog-detail'),
    
    # Admin-only blog endpoints
    path('blog/admin/all/', views.AdminBlogPostListView.as_view(), name='blog-admin-all'),
    path('blog/admin/stats/', views.BlogStatsView.as_view(), name='blog-stats'),
]