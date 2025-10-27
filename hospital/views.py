from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import (
    Appointment, TestRequest, VitalRequest, Vitals, LabResult, MedicalReport, BlogPost
)
import random
from users.models import Profile
from django.db import models
from .serializers import (
    AppointmentSerializer, TestRequestSerializer, VitalRequestSerializer,
    VitalsSerializer, LabResultSerializer, MedicalReportSerializer, BlogPostSerializer
)
from rest_framework.exceptions import PermissionDenied
from .permissions import IsRole
from django.shortcuts import get_object_or_404

# --------------- Appointment ---------------
# hospital/views.py
class AppointmentCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsRole]
    allowed_roles = ['PATIENT']
    serializer_class = AppointmentSerializer

    def perform_create(self, serializer):
        profile = self.request.user.profile
        
        # Get available doctors and assign one randomly
        available_doctors = Profile.objects.filter(role='DOCTOR', user__is_active=True)
        assigned_doctor = None
        
        if available_doctors.exists():
            assigned_doctor = random.choice(list(available_doctors))
        
        appointment = serializer.save(patient=profile, doctor=assigned_doctor)
        
        print(f"Appointment created for patient: {profile.user.username}")
        print(f"Assigned doctor: {assigned_doctor}")
        print(f"Appointment data: {serializer.data}")

# hospital/views.py
class AppointmentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        if profile.role == 'PATIENT':
            return Appointment.objects.filter(patient=profile).order_by('-booked_at')
        if profile.role == 'DOCTOR':
            # Doctor sees appointments assigned to them OR pending appointments that need assignment
            return Appointment.objects.filter(
                models.Q(doctor=profile) | 
                models.Q(doctor__isnull=True, status='PENDING')
            ).order_by('-booked_at')
        # staff/admin/lab/nurse see all for now
        return Appointment.objects.all().order_by('-booked_at')

class AppointmentDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()


# --------------- TestRequest (doctor -> lab) ---------------

class TestRequestCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsRole]
    allowed_roles = ['DOCTOR']
    serializer_class = TestRequestSerializer

    def perform_create(self, serializer):
        # doctor creates request
        serializer.save(requested_by=self.request.user.profile)
        # Optionally, mark appointment as awaiting results
        appt = serializer.validated_data['appointment']
        appt.status = 'AWAITING_RESULTS'
        appt.save()


class TestRequestListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TestRequestSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        if profile.role == 'LAB':
            # lab scientists see requests assigned to them or all pending
            return TestRequest.objects.filter(models.Q(assigned_to=profile) | models.Q(status='PENDING')).order_by('-created_at')
        if profile.role == 'DOCTOR':
            return TestRequest.objects.filter(requested_by=profile).order_by('-created_at')
        return TestRequest.objects.all().order_by('-created_at')


# --------------- VitalRequest (doctor -> nurse) ---------------

class VitalRequestCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsRole]
    allowed_roles = ['DOCTOR']
    serializer_class = VitalRequestSerializer

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user.profile)
        appt = serializer.validated_data['appointment']
        appt.status = 'IN_REVIEW'
        appt.save()


class VitalRequestListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VitalRequestSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        if profile.role == 'NURSE':
            return VitalRequest.objects.filter(models.Q(assigned_to=profile) | models.Q(status='PENDING')).order_by('-created_at')
        if profile.role == 'DOCTOR':
            return VitalRequest.objects.filter(requested_by=profile).order_by('-created_at')
        return VitalRequest.objects.all().order_by('-created_at')


# --------------- Nurse fills Vitals ---------------

class VitalsCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsRole]
    allowed_roles = ['NURSE']
    serializer_class = VitalsSerializer

    def perform_create(self, serializer):
        serializer.save(nurse=self.request.user.profile)
        # mark associated VitalRequest as done
        vital_request = serializer.validated_data['vital_request']
        vital_request.status = 'DONE'
        vital_request.save()


# --------------- Lab scientist fills LabResult ---------------

class LabResultCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsRole]
    allowed_roles = ['LAB']
    serializer_class = LabResultSerializer

    def perform_create(self, serializer):
        serializer.save(lab_scientist=self.request.user.profile)
        test_request = serializer.validated_data['test_request']
        # optionally set test_request to IN_PROGRESS or DONE if all tests submitted
        # For simplicity, set it to DONE when a labresult is posted (consider multi-test flows later)
        test_request.status = 'DONE'
        test_request.save()


# --------------- Doctor creates Medical Report ---------------

class MedicalReportCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsRole]
    allowed_roles = ['DOCTOR']
    serializer_class = MedicalReportSerializer

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.profile)
        # Appointment status updated in MedicalReport.save()

# ---------------- Blog: Only Admin can Create / Update / Delete ---------------- #
class BlogPostListCreateView(generics.ListCreateAPIView):
    """
    - Anyone (authenticated or not) can view blog posts.
    - Only authenticated users with ADMIN role can create blog posts.
    """
    queryset = BlogPost.objects.all().order_by('-created_at')
    serializer_class = BlogPostSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsRole()]
        return [permissions.AllowAny()]

    allowed_roles = ['ADMIN']

    def perform_create(self, serializer):
        profile = self.request.user.profile
        if profile.role != 'ADMIN':
            raise PermissionDenied("Only admins can create blog posts.")
        serializer.save(author=profile)


class BlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    - Anyone can view a blog post.
    - Only admins can update or delete.
    """
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsRole()]
        return [permissions.AllowAny()]

    allowed_roles = ['ADMIN']

    def perform_update(self, serializer):
        profile = self.request.user.profile
        if profile.role != 'ADMIN':
            raise PermissionDenied("Only admins can update blog posts.")
        serializer.save()

    def perform_destroy(self, instance):
        profile = self.request.user.profile
        if profile.role != 'ADMIN':
            raise PermissionDenied("Only admins can delete blog posts.")
        instance.delete()
