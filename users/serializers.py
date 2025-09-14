from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.password_validation import validate_password
from .utils import SendMail  # <-- import your email sender

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'fullname', 'phone', 'gender', 'profile_pix', 'role']

class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    fullname = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=Profile._meta.get_field('gender').choices,
        required=False
    )
    role = serializers.ChoiceField(
        choices=Profile._meta.get_field('role').choices,
        default='PATIENT'
    )

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(data['password1'])  # enforce Django password validators
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already taken.")
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already registered.")
        return data

    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password1')
        validated_data.pop('password2', None)

        # ✅ Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # ✅ Update the auto-created profile (from the signal)
        profile = user.profile
        profile.fullname = validated_data.get('fullname')
        profile.phone = validated_data.get('phone', '')
        profile.gender = validated_data.get('gender', None)
        profile.role = validated_data.get('role', 'PATIENT')
        profile.save()

        # Send welcome email
        SendMail(email)

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
