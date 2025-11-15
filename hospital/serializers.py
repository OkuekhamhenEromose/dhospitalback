# hospital/serializers.py
from rest_framework import serializers
from .models import (
    Appointment, Vitals, LabResult, MedicalReport, BlogPost,
    TestRequest, VitalRequest
)
from users.models import Profile
from users.serializers import ProfileSerializer

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

class AppointmentSerializer(serializers.ModelSerializer):
    patient = ProfileSerializer(read_only=True)
    doctor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'patient_id', 'name', 'age', 'sex', 'message', 'address', 'booked_at', 'doctor', 'status']
        read_only_fields = ['booked_at', 'status', 'doctor']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        
        # Always include basic related data for better UX
        # Include test requests
        if instance.test_requests.exists():
            rep['test_requests'] = TestRequestSerializer(
                instance.test_requests.all(), 
                many=True
            ).data
        
        # Include vital requests
        if instance.vital_requests.exists():
            rep['vital_requests'] = VitalRequestSerializer(
                instance.vital_requests.all(), 
                many=True
            ).data
        
        # Include vitals if available
        vital_request = instance.vital_requests.last()
        if vital_request and vital_request.vitals_entries.exists():
            rep['vitals'] = VitalsSerializer(
                vital_request.vitals_entries.last()
            ).data
        
        # Include lab results if available
        lab_results_data = []
        for test_request in instance.test_requests.all():
            if test_request.lab_results.exists():
                lab_results_data.extend(
                    LabResultSerializer(
                        test_request.lab_results.all(), 
                        many=True
                    ).data
                )
        if lab_results_data:
            rep['lab_results'] = lab_results_data
        
        # Include medical report if available
        if hasattr(instance, 'medical_report'):
            rep['medical_report'] = MedicalReportSerializer(
                instance.medical_report
            ).data
        
        return rep

# ---------------- Enhanced Blog Serializers ---------------- #

class BlogPostListSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)
    has_toc = serializers.SerializerMethodField()
    toc_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'description', 'author', 'featured_image',
            'published', 'published_date', 'created_at', 'slug', 
            'enable_toc', 'has_toc', 'toc_items_count'
        ]
        read_only_fields = ['author', 'published_date', 'created_at', 'updated_at', 'slug']

    def get_has_toc(self, obj):
        return obj.enable_toc and bool(obj.table_of_contents)

    def get_toc_items_count(self, obj):
        return len(obj.table_of_contents) if obj.table_of_contents else 0


class BlogPostSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)
    table_of_contents = serializers.SerializerMethodField()
    toc_display = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'description', 'content', 'author',
            'featured_image', 'published', 'published_date',
            'created_at', 'updated_at', 'slug', 'enable_toc',
            'table_of_contents', 'toc_display'
        ]
        read_only_fields = ['author', 'published_date', 'created_at', 'updated_at', 'slug', 'table_of_contents']

    def get_table_of_contents(self, obj):
        return obj.table_of_contents

    def get_toc_display(self, obj):
        return obj.get_toc_display()


class BlogPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'description', 'content', 'featured_image',
            'published', 'enable_toc'
        ]

    def create(self, validated_data):
        # TOC will be auto-generated in the model's save method
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # TOC will be auto-generated in the model's save method
        return super().update(instance, validated_data)