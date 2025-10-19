from django.contrib import admin
from .models import Appointment, Vitals, LabResult, MedicalReport, BlogPost


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'status', 'booked_at')
    list_filter = ('status', 'booked_at')
    search_fields = ('patient__user__username', 'doctor__user__username')
    ordering = ('-booked_at',)

@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'doctor', 'medical_condition', 'next_appointment', 'created_at')
    search_fields = ('appointment__patient__user__username', 'doctor__user__username', 'medical_condition')
    list_filter = ('created_at', 'next_appointment')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
# ---------------- LabResultAdmin ----------------
@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'test_request', 'lab_scientist', 'test_name', 'result', 'units', 'reference_range', 'recorded_at')
    list_filter = ('test_request', 'lab_scientist', 'test_name', 'recorded_at')
    search_fields = ('test_name', 'result', 'lab_scientist__fullname')


# ---------------- VitalsAdmin ----------------
@admin.register(Vitals)
class VitalsAdmin(admin.ModelAdmin):
    list_display = ('id', 'vital_request', 'nurse', 'blood_pressure', 'respiration_rate', 'pulse_rate', 'body_temperature', 'height_cm', 'weight_kg', 'recorded_at')
    list_filter = ('nurse', 'recorded_at')
    search_fields = ('nurse__fullname',)


# ---------------- BlogPostAdmin ----------------
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published', 'published_date', 'created_at')
    list_filter = ('published', 'author')
    search_fields = ('title', 'content', 'author__fullname')
