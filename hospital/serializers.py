from rest_framework import serializers
from .models import Appointment, Vitals, LabResult, MedicalReport
from users.serializers import ProfileSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    patient = ProfileSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id','patient','patient_id','name','age','sex','address','booked_at','doctor','status']
        read_only_fields = ['booked_at','status','doctor']
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # optionally include last vitals and lab summary:
        rep['vitals'] = VitalsSerializer(instance=instance.vitals.last()).data if instance.vitals.exists() else None
        rep['lab_results'] = [LabResultSerializer(r).data for r in instance.lab_results.all()]
        rep['medical_report'] = MedicalReportSerializer(instance=instance.medical_report).data if hasattr(instance,'medical_report') else None
        return rep

class VitalsSerializer(serializers.ModelSerializer):
    nurse = ProfileSerializer(read_only=True)
    class Meta:
        model = Vitals
        fields = ['id','appointment','nurse','blood_pressure','height_cm','weight_kg','blood_sugar','recorded_at']
        read_only_fields = ['nurse','recorded_at']

class LabResultSerializer(serializers.ModelSerializer):
    lab_scientist = ProfileSerializer(read_only=True)
    class Meta:
        model = LabResult
        fields = ['id','appointment','lab_scientist','blood_group','test_name','result','recorded_at']
        read_only_fields = ['lab_scientist','recorded_at']

class MedicalReportSerializer(serializers.ModelSerializer):
    doctor = ProfileSerializer(read_only=True)
    class Meta:
        model = MedicalReport
        fields = ['id','appointment','doctor','medical_condition','drug_prescription','next_appointment','created_at']
        read_only_fields = ['doctor','created_at']
