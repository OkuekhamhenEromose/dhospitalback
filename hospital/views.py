from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Appointment, Vitals, LabResult, MedicalReport
from .serializers import AppointmentSerializer, VitalsSerializer, LabResultSerializer, MedicalReportSerializer
from .permissions import IsRole
from users.models import Profile
from django.shortcuts import get_object_or_404

# Patient books an appointment (patient user can create their own appointment)
class AppointmentCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['PATIENT']  # only patient creates their appointment
    serializer_class = AppointmentSerializer

    def get_serializer(self, *args, **kwargs):
        # set patient queryset
        kwargs.setdefault('context', self.get_serializer_context())
        ser = super().get_serializer(*args, **kwargs)
        return ser

    def perform_create(self, serializer):
        # force the appointment.patient to be the authenticated user's profile
        profile = self.request.user.profile
        serializer.save(patient=profile)

# Nurse posts vitals for an appointment
class VitalsCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['NURSE']
    serializer_class = VitalsSerializer

    def perform_create(self, serializer):
        profile = self.request.user.profile
        # appointment id should be provided in payload
        serializer.save(nurse=profile)

# Lab scientist posts lab results
class LabResultCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['LAB']
    serializer_class = LabResultSerializer

    def perform_create(self, serializer):
        serializer.save(lab_scientist=self.request.user.profile)

# Doctor creates final medical report (reads appointment, vitals, lab)
class MedicalReportCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['DOCTOR']
    serializer_class = MedicalReportSerializer

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.profile)
        # optionally update appointment status
        appt = serializer.validated_data['appointment']
        appt.status = 'COMPLETED'
        appt.save()

# Doctor/authorized users can list appointments and retrieve a single appointment
class AppointmentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        if profile.role == 'PATIENT':
            return Appointment.objects.filter(patient=profile).order_by('-booked_at')
        elif profile.role == 'DOCTOR':
            # show all pending and assigned appointments; tweak as needed
            return Appointment.objects.all().order_by('-booked_at')
        else:
            # nurses and lab can see appointment details to post data
            return Appointment.objects.all().order_by('-booked_at')

class AppointmentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
