# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, GENDER_CHOICES, ROLE_CHOICES
from django.contrib.auth.password_validation import validate_password
from .utils import SendMail
import logging

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Keep only this
    profile_pix = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['user', 'fullname', 'phone', 'gender', 'profile_pix', 'role']  # Remove 'username' and 'email'

    def get_profile_pix(self, obj):
        if obj.profile_pix:
            return obj.profile_pix.url
        return None

class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    fullname = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=GENDER_CHOICES,
        required=False
    )
    role = serializers.ChoiceField(
        choices=ROLE_CHOICES,
        default='PATIENT'
    )
    profile_pix = serializers.ImageField(required=False, allow_null=True)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        
        validate_password(data['password1'])
        
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already taken.")
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already registered.")
        
        return data

    # In users/serializers.py - Update the create method
    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password1')
        validated_data.pop('password2', None)
        profile_pix = validated_data.pop('profile_pix', None)

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Get or create profile
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Update profile fields
        profile.fullname = validated_data.get('fullname', '')
        profile.phone = validated_data.get('phone', '')
        profile.gender = validated_data.get('gender', None)
        profile.role = validated_data.get('role', 'PATIENT')

        if profile_pix:
            profile.profile_pix = profile_pix
        profile.save()

        # Send welcome email (non-blocking)
        try:
            # Use threading or celery for async email in production
            # For now, we'll run it in a way that won't block
            import threading
            def send_email_async():
                try:
                    from .utils import SendMail
                    SendMail(email)
                except Exception:
                    pass  # Silently fail in async thread
            
            email_thread = threading.Thread(target=send_email_async)
            email_thread.daemon = True
            email_thread.start()
            
            logger.info(f"User {username} registered, email sent async")
            
        except Exception as e:
            logger.warning(f"Failed to schedule email for {email}: {str(e)}")
            # Don't fail registration because of email

        return profile


class UpdateProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = Profile
        fields = ['username', 'email', 'fullname', 'phone', 'gender', 'profile_pix', 'role']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        if 'username' in user_data:
            user.username = user_data['username']
        if 'email' in user_data:
            user.email = user_data['email']
        user.save()

        for attr in ('fullname', 'phone', 'gender', 'profile_pix', 'role'):
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])
        instance.save()
        return instance