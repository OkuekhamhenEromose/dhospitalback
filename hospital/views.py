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
from django.db.models import Q
from users.serializers import ProfileSerializer

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
# hospital/views.py - Update AppointmentListView for doctors
class AppointmentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        if profile.role == 'PATIENT':
            return Appointment.objects.filter(patient=profile).order_by('-booked_at')
        if profile.role == 'DOCTOR':
            # Doctor sees appointments assigned to them
            return Appointment.objects.filter(doctor=profile).order_by('-booked_at')
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
        # Create the test request
        test_request = serializer.save(requested_by=self.request.user.profile)
        
        # Mark appointment as awaiting results
        appt = test_request.appointment
        appt.status = 'AWAITING_RESULTS'
        appt.save()
        
        print(f"Test request created by doctor {self.request.user.profile.fullname}")
        print(f"Assigned to lab scientist: {test_request.assigned_to}")


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
        # Create the vital request
        vital_request = serializer.save(requested_by=self.request.user.profile)
        
        # Mark appointment as in review
        appt = vital_request.appointment
        appt.status = 'IN_REVIEW'
        appt.save()
        
        print(f"Vital request created by doctor {self.request.user.profile.fullname}")
        print(f"Assigned to nurse: {vital_request.assigned_to}")


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
        vitals = serializer.save(nurse=self.request.user.profile)
        vital_request = vitals.vital_request
        
        # Mark vital request as done
        vital_request.status = 'DONE'
        vital_request.save()
        
        appointment = vital_request.appointment
        print(f"Vitals recorded for {appointment.name}")
        print(f"BP: {vitals.blood_pressure}, Pulse: {vitals.pulse_rate}")


# --------------- Lab scientist fills LabResult ---------------

class LabResultCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsRole]
    allowed_roles = ['LAB']
    serializer_class = LabResultSerializer

    def perform_create(self, serializer):
        lab_result = serializer.save(lab_scientist=self.request.user.profile)
        test_request = lab_result.test_request
        
        # Update appointment status when results are submitted
        appointment = test_request.appointment
        
        print(f"Lab result submitted for {appointment.name}")
        print(f"Test: {lab_result.test_name}, Result: {lab_result.result}")
        
        # Check if all requested tests have results
        requested_tests = [test.strip() for test in test_request.tests.split(',')]
        completed_tests = test_request.lab_results.values_list('test_name', flat=True)
        
        # If all tests have results, mark test request as done
        if set(requested_tests).issubset(set(completed_tests)):
            test_request.status = 'DONE'
            test_request.save()
            print(f"All tests completed for {appointment.name}")

# --------------- Doctor creates Medical Report ---------------

class MedicalReportCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsRole]
    allowed_roles = ['DOCTOR']
    serializer_class = MedicalReportSerializer

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.profile)
        # Appointment status updated in MedicalReport.save()


class StaffListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer  # You'll need to create this or use existing one

    def get_queryset(self):
        # Return all staff members (doctors, nurses, lab scientists)
        return Profile.objects.filter(
            Q(role='DOCTOR') | Q(role='NURSE') | Q(role='LAB')
        ).filter(user__is_active=True)

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
