# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
from decouple import config
from .serializers import (
    RegistrationSerializer,
    ProfileSerializer,
    UpdateProfileSerializer
)
from .models import Profile
import logging
from django.shortcuts import redirect
from urllib.parse import urlencode
import requests
from django.urls import reverse

logger = logging.getLogger(__name__)

class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        try:
            if request.user.is_authenticated:
                return Response({"Message": "You are logged in already"})
            
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

# users/views.py - Update LoginView
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'detail': 'Username and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is None:
            # Try with email
            try:
                user = User.objects.get(email=username)
                user = authenticate(username=user.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is None:
            return Response(
                {'detail': 'Invalid credentials'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.is_active:
            return Response(
                {'detail': 'Account is disabled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        
        try:
            refresh = RefreshToken.for_user(user)
        except Exception as e:
            logger.error(f"Token generation failed: {str(e)}")
            return Response(
                {'detail': 'Authentication failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Get profile data
        try:
            profile = Profile.objects.select_related('user').get(user=user)
            # Use ProfileSerializer with request context
            profile_serializer = ProfileSerializer(
                profile, 
                context={'request': request}
            )
            profile_data = {
                'role': profile.role,
                'fullname': profile.fullname,
                'profile_pix': profile_serializer.data.get('profile_pix'),
                'phone': profile.phone,
                'gender': profile.gender,
            }
        except Profile.DoesNotExist:
            logger.warning(f"Profile not found for user {user.id}")
            profile_data = {
                'role': 'PATIENT',
                'fullname': user.get_full_name() or user.username,
                'profile_pix': None,
                'phone': None,
                'gender': None,
            }
        
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
        
        logger.info(f"User {user.username} logged in successfully")
        return Response(response_data, status=status.HTTP_200_OK)

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
        try:
            profile = Profile.objects.select_related('user').get(user=request.user)
            serializer = ProfileSerializer(
                profile, 
                context={'request': request}
            )
            profile_data = {
                'role': profile.role,
                'fullname': profile.fullname,
                'profile_pix': serializer.data.get('profile_pix'),
                'phone': profile.phone,
                'gender': profile.gender,
            }
            response_data = {
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'profile': profile_data
                }
            }
                        
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

class SocialAuthUrlsView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        base_url = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
        
        return Response({
            'google': f"{base_url}/api/users/login/google-oauth2/",
            'facebook': f"{base_url}/api/users/login/facebook/",
            'linkedin': f"{base_url}/api/users/login/linkedin-oauth2/"
        })

class SocialAuthSuccessView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Generate JWT tokens for the authenticated user
        from rest_framework_simplejwt.tokens import RefreshToken
        
        if request.user.is_authenticated:
            refresh = RefreshToken.for_user(request.user)
            
            # Redirect to frontend with tokens
            frontend_url = "https://ettahospitalclone.vercel.app"  # Update with your frontend URL
            redirect_url = f"{frontend_url}/auth/callback?access={str(refresh.access_token)}&refresh={str(refresh)}"
            
            from django.shortcuts import redirect
            return redirect(redirect_url)
        
        return Response({'error': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)
    
class SocialAuthErrorView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        error = request.GET.get('error', 'Unknown error occurred')
        frontend_url = "https://ettahospitalclone.vercel.app"
        
        from django.shortcuts import redirect
        return redirect(f"{frontend_url}/auth/error?message={error}")


class SocialAuthLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Alternative social auth login that returns JWT directly"""
        provider = request.data.get('provider')
        access_token = request.data.get('access_token')
        
        if not provider or not access_token:
            return Response(
                {'error': 'Provider and access token required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify the social token and get user data
            user_data = self.verify_social_token(provider, access_token)
            if not user_data:
                return Response(
                    {'error': 'Invalid social token'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find or create user
            user, created = self.get_or_create_social_user(provider, user_data)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Get profile data
            try:
                profile = Profile.objects.get(user=user)
                profile_data = {
                    'role': profile.role,
                    'fullname': profile.fullname,
                    'profile_pix': profile.profile_pix.url if profile.profile_pix else None,
                    'phone': profile.phone,
                    'gender': profile.gender,
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
                },
                'is_new_user': created
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Social auth login error: {str(e)}")
            return Response(
                {'error': 'Social authentication failed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def verify_social_token(self, provider, access_token):
        """Verify social token with provider"""
        try:
            if provider == 'google':
                response = requests.get(
                    'https://www.googleapis.com/oauth2/v3/userinfo',
                    params={'access_token': access_token}
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'email': data.get('email'),
                        'name': data.get('name'),
                        'first_name': data.get('given_name'),
                        'last_name': data.get('family_name'),
                        'picture': data.get('picture'),
                    }
            
            elif provider == 'facebook':
                response = requests.get(
                    'https://graph.facebook.com/me',
                    params={
                        'access_token': access_token,
                        'fields': 'id,name,email,first_name,last_name,picture'
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'email': data.get('email'),
                        'name': data.get('name'),
                        'first_name': data.get('first_name'),
                        'last_name': data.get('last_name'),
                        'picture': data.get('picture', {}).get('data', {}).get('url'),
                    }
            
            elif provider == 'linkedin':
                response = requests.get(
                    'https://api.linkedin.com/v2/me',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                if response.status_code == 200:
                    data = response.json()
                    # Get email separately
                    email_response = requests.get(
                        'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
                        headers={'Authorization': f'Bearer {access_token}'}
                    )
                    email_data = email_response.json() if email_response.status_code == 200 else {}
                    email = email_data.get('elements', [{}])[0].get('handle~', {}).get('emailAddress', '')
                    
                    return {
                        'email': email,
                        'name': f"{data.get('localizedFirstName', '')} {data.get('localizedLastName', '')}".strip(),
                        'first_name': data.get('localizedFirstName', ''),
                        'last_name': data.get('localizedLastName', ''),
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Token verification error for {provider}: {str(e)}")
            return None
    
    def get_or_create_social_user(self, provider, user_data):
        """Find or create user from social data"""
        email = user_data.get('email')
        if not email:
            raise ValueError("Email is required for social authentication")
        
        try:
            # Try to find existing user by email
            user = User.objects.get(email=email)
            created = False
        except User.DoesNotExist:
            # Create new user
            username = self.generate_username(user_data.get('name', ''), email)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=None  # No password for social auth users
            )
            user.first_name = user_data.get('first_name', '')
            user.last_name = user_data.get('last_name', '')
            user.save()
            created = True
            
            # Create profile
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.fullname = user_data.get('name', f"{user.first_name} {user.last_name}".strip())
            profile.save()
        
        return user, created
    
    def generate_username(self, name, email):
        """Generate unique username from name and email"""
        base_username = name.replace(' ', '_').lower() if name else email.split('@')[0]
        username = base_username
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        return username