# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
from .serializers import (
    RegistrationSerializer,
    ProfileSerializer,
    UpdateProfileSerializer
)
from .models import Profile
import logging

logger = logging.getLogger(__name__)

class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        try:
            if request.user.is_authenticated:
                return Response({"Message":"You are logged in already"})
            
            serializer = RegistrationSerializer(data=request.data)
            
            if serializer.is_valid():
                profile = serializer.save()
                # Return minimal data for faster response
                data = {
                    'id': profile.user.id,
                    'username': profile.user.username,
                    'email': profile.user.email,
                    'role': profile.role
                }
                logger.info(f"User {profile.user.username} registered successfully")
                return Response(data, status=status.HTTP_201_CREATED)
            else:
                logger.warning(f"Registration validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Registration exception: {str(e)}")
            return Response(
                {'error': 'Registration failed. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            
            # Optimized: Only fetch necessary profile data
            try:
                profile = Profile.objects.only('role', 'fullname').get(user=user)
                profile_data = {
                    'role': profile.role,
                    'fullname': profile.fullname
                }
            except Profile.DoesNotExist:
                profile_data = {}
            
            response_data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'profile': profile_data
                }
            }
            
            # Cache user data for faster subsequent access
            cache_key = f"user_{user.id}_basic"
            cache.set(cache_key, profile_data, 300)  # Cache for 5 minutes
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        logger.warning(f"Failed login attempt for username: {username}")
        return Response(
            {'detail': 'Invalid credentials'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            user_id = request.user.id
            
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception as e:
                    logger.warning(f"Token blacklist failed: {str(e)}")
            
            # Clear user cache on logout
            cache.delete(f"user_{user_id}_basic")
            cache.delete(f"user_dashboard_{user_id}")
            
            return Response({'detail': 'Logged out successfully'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {'detail': 'Logged out'}, 
                status=status.HTTP_200_OK
            )

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cache_key = f"user_dashboard_{request.user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.debug(f"Serving cached dashboard for user {request.user.id}")
            return Response(cached_data)
        
        try:
            # Optimized database query with select_related
            profile = Profile.objects.select_related('user').get(user=request.user)
            serializer = ProfileSerializer(profile)
            
            response_data = {
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'profile': serializer.data
                }
            }
            
            # Cache dashboard data for 2 minutes
            cache.set(cache_key, response_data, 120)
            
            return Response(response_data)
            
        except Profile.DoesNotExist:
            logger.error(f"Profile not found for user {request.user.id}")
            return Response(
                {'detail': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class UpdateProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = UpdateProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile = request.user.profile
        serializer = UpdateProfileSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            # Clear cached data after profile update
            user_id = request.user.id
            cache.delete(f"user_{user_id}_basic")
            cache.delete(f"user_dashboard_{user_id}")
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)