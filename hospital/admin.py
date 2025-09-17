from django.contrib import admin
from .models import Appointment, Vitals, LabResult, MedicalReport, BlogPost


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'age', 'sex', 'patient', 'doctor', 'status', 'booked_at')
    list_filter = ('status', 'sex', 'booked_at')
    search_fields = ('name', 'patient__user__username', 'doctor__user__username')
    ordering = ('-booked_at',)


@admin.register(Vitals)
class VitalsAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'nurse', 'blood_pressure', 'height_cm', 'weight_kg', 'blood_sugar', 'recorded_at')
    search_fields = ('appointment__name', 'nurse__user__username')
    list_filter = ('recorded_at',)


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'lab_scientist', 'test_name', 'blood_group', 'recorded_at')
    search_fields = ('test_name', 'appointment__name', 'lab_scientist__user__username')
    list_filter = ('blood_group', 'recorded_at')


@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'doctor', 'medical_condition', 'next_appointment', 'created_at')
    search_fields = ('appointment__name', 'doctor__user__username', 'medical_condition')
    list_filter = ('created_at', 'next_appointment')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'published', 'published_date', 'created_at', 'updated_at')
    list_filter = ('published', 'published_date', 'created_at')
    search_fields = ('title', 'description', 'content', 'author__user__username')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-published_date', '-created_at')
