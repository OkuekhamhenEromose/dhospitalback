from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from .models import Appointment, Vitals, LabResult, MedicalReport, BlogPost
from .serializers import AppointmentSerializer, VitalsSerializer, LabResultSerializer, MedicalReportSerializer, BlogPostSerializer
from .permissions import IsRole
from django.db.models import Q

# ---------------- Appointment Logic ---------------- #

class AppointmentCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['PATIENT']
    serializer_class = AppointmentSerializer

    def perform_create(self, serializer):
        profile = self.request.user.profile
        serializer.save(patient=profile)


class VitalsCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['NURSE']
    serializer_class = VitalsSerializer

    def perform_create(self, serializer):
        serializer.save(nurse=self.request.user.profile)


class LabResultCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['LAB']
    serializer_class = LabResultSerializer

    def perform_create(self, serializer):
        serializer.save(lab_scientist=self.request.user.profile)


class MedicalReportCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['DOCTOR']
    serializer_class = MedicalReportSerializer

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.profile)
        appt = serializer.validated_data['appointment']
        appt.status = 'COMPLETED'
        appt.save()


class AppointmentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        if profile.role == 'PATIENT':
            return Appointment.objects.filter(patient=profile).order_by('-booked_at')
        return Appointment.objects.all().order_by('-booked_at')


class AppointmentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()


# ---------------- Blog Logic ---------------- #

class BlogPostListCreateView(generics.ListCreateAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = BlogPost.objects.filter(published=True)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(content__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        profile = self.request.user.profile
        if profile.role not in ['ADMIN', 'DOCTOR']:
            raise permissions.PermissionDenied("Only admins or doctors can create blog posts.")
        serializer.save(author=profile)


class BlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        profile = self.request.user.profile
        obj = self.get_object()
        if obj.author != profile and profile.role != 'ADMIN':
            raise permissions.PermissionDenied("You can only edit your own posts or be an admin.")
        serializer.save()
