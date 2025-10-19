from rest_framework import serializers
from .models import (
    Appointment, Vitals, LabResult, MedicalReport, BlogPost,
    TestRequest, VitalRequest
)
from users.models import Profile
from users.serializers import ProfileSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    patient = ProfileSerializer(read_only=True)
    doctor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'patient_id', 'name', 'age', 'sex', 'message', 'address', 'booked_at', 'doctor', 'status']
        read_only_fields = ['booked_at', 'status', 'doctor']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        
        # Only include basic data to prevent performance issues
        # Add related data only when explicitly needed
        include_details = self.context.get('request') and self.context['request'].query_params.get('include_details')
        
        if include_details:
            # Only fetch related data when explicitly requested
            vital_request = instance.vital_requests.last()
            if vital_request and vital_request.vitals_entries.exists():
                rep['vitals'] = VitalsSerializer(instance=vital_request.vitals_entries.last()).data
            
            lab_results_data = []
            for test_request in instance.test_requests.all():
                lab_results_data.extend(LabResultSerializer(test_request.lab_results.all(), many=True).data)
            rep['lab_results'] = lab_results_data
            
            rep['test_requests'] = TestRequestSerializer(instance=instance.test_requests.last()).data if instance.test_requests.exists() else None
            rep['vital_requests'] = VitalRequestSerializer(instance=instance.vital_requests.last()).data if instance.vital_requests.exists() else None
            rep['medical_report'] = MedicalReportSerializer(instance=instance.medical_report).data if hasattr(instance, 'medical_report') else None
        
        return rep

class TestRequestSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = TestRequest
        fields = '__all__'
        read_only_fields = ['requested_by', 'created_at', 'updated_at']


class VitalRequestSerializer(serializers.ModelSerializer):
    requested_by = ProfileSerializer(read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all(), required=False, allow_null=True)


    class Meta:
        model = VitalRequest
        fields = ['id', 'appointment', 'requested_by', 'assigned_to', 'note', 'status', 'created_at', 'updated_at']
        read_only_fields = ['requested_by', 'created_at', 'updated_at']


class VitalsSerializer(serializers.ModelSerializer):
    nurse = ProfileSerializer(read_only=True)
    vital_request = serializers.PrimaryKeyRelatedField(queryset=VitalRequest.objects.all())

    class Meta:
        model = Vitals
        fields = ['id', 'vital_request', 'nurse', 'blood_pressure', 'respiration_rate', 'pulse_rate', 'body_temperature', 'height_cm', 'weight_kg', 'recorded_at']
        read_only_fields = ['nurse', 'recorded_at']


class LabResultSerializer(serializers.ModelSerializer):
    lab_scientist = ProfileSerializer(read_only=True)
    test_request = serializers.PrimaryKeyRelatedField(queryset=TestRequest.objects.all())

    class Meta:
        model = LabResult
        fields = ['id', 'test_request', 'lab_scientist', 'test_name', 'result', 'units', 'reference_range', 'recorded_at']
        read_only_fields = ['lab_scientist', 'recorded_at']


class MedicalReportSerializer(serializers.ModelSerializer):
    doctor = ProfileSerializer(read_only=True)

    class Meta:
        model = MedicalReport
        fields = ['id', 'appointment', 'doctor', 'medical_condition', 'drug_prescription', 'advice', 'next_appointment', 'created_at']
        read_only_fields = ['doctor', 'created_at']

# ---------------- Blog Serializers ---------------- #

class BlogPostSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'description', 'content', 'author',
            'featured_image', 'published', 'published_date',
            'created_at', 'updated_at', 'slug'
        ]
        read_only_fields = ['author', 'published_date', 'created_at', 'updated_at', 'slug']
