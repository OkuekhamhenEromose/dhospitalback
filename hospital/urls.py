from django.urls import path
from . import views

urlpatterns = [
    # ---------------- Appointments ----------------
    path('appointments/', views.AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/create/', views.AppointmentCreateView.as_view(), name='appointment-create'),
    path('appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),

    # ---------------- Vitals ----------------
    path('vitals/create/', views.VitalsCreateView.as_view(), name='vitals-create'),

    # ---------------- Lab Results ----------------
    path('lab-results/create/', views.LabResultCreateView.as_view(), name='labresult-create'),

    # ---------------- Medical Reports ----------------
    path('medical-reports/create/', views.MedicalReportCreateView.as_view(), name='medicalreport-create'),

    # ---------------- Blog ----------------
    path('blog/', views.BlogPostListCreateView.as_view(), name='blog-list-create'),
    path('blog/<slug:slug>/', views.BlogPostDetailView.as_view(), name='blog-detail'),
]
