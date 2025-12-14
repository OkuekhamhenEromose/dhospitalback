# users/views.py - COMPLETE FIXED VERSION WITH ALL IMPORTS
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
from django.shortcuts import redirect  # CRITICAL: Add this import at the top
import urllib.parse
import requests
import logging
from django.contrib.auth import login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .serializers import (
    RegistrationSerializer,
    ProfileSerializer,
    UpdateProfileSerializer
)
from .models import Profile
from social_django.models import UserSocialAuth  # Add this import

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

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = request.data.get('username')  # Can be username OR email
        password = request.data.get('password')
        
        if not identifier or not password:
            return Response(
                {'detail': 'Username/Email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to authenticate with username first
        user = authenticate(username=identifier, password=password)
        
        if user is None:
            # Try with email
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
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

# In users/views.py - REPLACE the SocialAuthSuccessView with this FIXED version
@method_decorator(csrf_exempt, name='dispatch')
class SocialAuthSuccessView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        logger.info(f"=== SOCIAL AUTH SUCCESS VIEW ===")
        logger.info(f"User: {request.user}")
        logger.info(f"Authenticated: {request.user.is_authenticated}")
        logger.info(f"Session key: {request.session.session_key}")
        logger.info(f"Session data: {dict(request.session)}")
        
        # Check if there's a social auth user in the session
        social_user_id = request.session.get('social_auth_last_login_backend')
        logger.info(f"Social auth in session: {social_user_id}")
        
        # Try to find the authenticated user
        user = None
        
        if not request.user.is_authenticated:
            # Check for recently authenticated user in session
            user_id = request.session.get('_auth_user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    logger.info(f"Found user in session: {user.email}")
                except User.DoesNotExist:
                    logger.error(f"User with id {user_id} not found")
        
        # If still no user, check if this is a social auth callback
        if not user:
            # Check for social auth user
            try:
                # Social auth stores user id in 'social_auth_user_id'
                social_user_id = request.session.get('social_auth_user_id')
                if social_user_id:
                    user = User.objects.get(id=social_user_id)
                    logger.info(f"Found social auth user: {user.email}")
            except (User.DoesNotExist, KeyError):
                pass
        
        if user:
            # IMPORTANT: Specify the backend when logging in
            # Use the social auth backend
            from django.conf import settings
            backend = 'social_core.backends.google.GoogleOAuth2'
            
            # Manually log the user in with the correct backend
            user.backend = backend  # Set the backend attribute on the user
            auth_login(request, user)
            logger.info(f"✅ Successfully logged in user: {user.email} using backend: {backend}")
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Get or create profile
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Update profile with Google data if new
            if created:
                try:
                    social_auth = UserSocialAuth.objects.get(user=user, provider='google')
                    if social_auth.extra_data.get('name'):
                        profile.fullname = social_auth.extra_data.get('name')
                        profile.save()
                        logger.info(f"Updated profile for {user.email}")
                except UserSocialAuth.DoesNotExist:
                    pass
            
            # Get profile data
            profile_data = {
                'role': profile.role,
                'fullname': profile.fullname,
                'profile_pix': profile.profile_pix.url if profile.profile_pix else None,
                'phone': profile.phone,
                'gender': profile.gender,
            }
            
            # Create redirect URL with tokens
            frontend_url = "https://ettahospitalclone.vercel.app"
            
            tokens = urllib.parse.urlencode({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': str(user.id),
                'email': user.email,
                'username': user.username,
                'is_new_user': str(created).lower(),
            })
            
            redirect_url = f"{frontend_url}/auth/callback?{tokens}"
            
            logger.info(f"✅ Success! Redirecting {user.email} to dashboard")
            logger.info(f"Redirect URL: {redirect_url}")
            
            return redirect(redirect_url)
        else:
            # Debug: list all users with social auth
            logger.error("❌ Could not find authenticated user")
            social_users = UserSocialAuth.objects.all()
            logger.error(f"Total social auth users: {social_users.count()}")
            for su in social_users:
                logger.error(f"  - {su.user.email} ({su.provider})")
            
            # Show debug info
            debug_info = {
                'session_keys': list(request.session.keys()),
                'user_id_in_session': request.session.get('_auth_user_id'),
                'social_auth_user_id': request.session.get('social_auth_user_id'),
                'social_auth_last_login_backend': request.session.get('social_auth_last_login_backend'),
            }
            logger.error(f"Debug info: {debug_info}")
            
            # Redirect to frontend with error
            frontend_url = "https://ettahospitalclone.vercel.app"
            return redirect(f"{frontend_url}/login?error=social_auth_failed&debug=no_user_found")


class SocialAuthErrorView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        error = request.GET.get('error', 'Unknown error occurred')
        message = request.GET.get('message', '')
        
        logger.error(f"Social auth error: {error} - {message}")
        
        frontend_url = "https://ettahospitalclone.vercel.app"
        error_url = f"{frontend_url}/auth/error?message={urllib.parse.quote(message)}"
        
        return redirect(error_url)

class SocialAuthLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Alternative social auth login that returns JWT directly (Google only)"""
        provider = request.data.get('provider')
        access_token = request.data.get('access_token')
        
        if not provider or not access_token:
            return Response(
                {'error': 'Provider and access token required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only allow Google
        if provider != 'google':
            return Response(
                {'error': 'Only Google authentication is supported'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify the Google token and get user data
            user_data = self.verify_google_token(access_token)
            if not user_data:
                return Response(
                    {'error': 'Invalid Google token'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find or create user
            user, created = self.get_or_create_social_user(user_data)
            
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
            logger.error(f"Google auth login error: {str(e)}")
            return Response(
                {'error': 'Google authentication failed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def verify_google_token(self, access_token):
        """Verify Google token with Google API"""
        try:
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
            return None
            
        except Exception as e:
            logger.error(f"Google token verification error: {str(e)}")
            return None
    
    def get_or_create_social_user(self, user_data):
        """Find or create user from Google data"""
        email = user_data.get('email')
        if not email:
            raise ValueError("Email is required for Google authentication")
        
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
                password=None  # No password for Google auth users
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

class SocialAuthUrlsView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        base_url = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
        
        # Return only Google URL
        return Response({
            'google': f"{base_url}/api/users/login/google-oauth2/"
        })
    
class SocialAuthDebugView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Debug view to see what's happening in social auth"""
        response_data = {
            'user': {
                'is_authenticated': request.user.is_authenticated,
                'username': request.user.username if request.user.is_authenticated else 'Anonymous',
                'email': request.user.email if request.user.is_authenticated else None,
            },
            'session_keys': list(request.session.keys()),
            'social_auth_data': None,
        }
        
        if request.user.is_authenticated:
            try:
                social_auth = UserSocialAuth.objects.filter(user=request.user).first()
                if social_auth:
                    response_data['social_auth_data'] = {
                        'provider': social_auth.provider,
                        'uid': social_auth.uid,
                        'extra_data': social_auth.extra_data,
                    }
            except Exception as e:
                response_data['social_auth_error'] = str(e)
        
        return Response(response_data)
    
# In users/views.py - ADD this view
class GoogleOAuthCallbackView(APIView):
    """Direct Google OAuth2 callback handler - bypasses social-auth-app-django"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        code = request.GET.get('code')
        state = request.GET.get('state')
        
        if not code:
            logger.error("No authorization code from Google")
            frontend_url = "https://ettahospitalclone.vercel.app"
            return redirect(f"{frontend_url}/login?error=no_auth_code")
        
        try:
            # Exchange code for tokens
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'code': code,
                'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
                'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
                'redirect_uri': 'https://dhospitalback.onrender.com/api/users/google-callback/',
                'grant_type': 'authorization_code',
            }
            
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_json = token_response.json()
            
            access_token = token_json.get('access_token')
            id_token = token_json.get('id_token')
            
            if not access_token:
                logger.error("No access token from Google")
                frontend_url = "https://ettahospitalclone.vercel.app"
                return redirect(f"{frontend_url}/login?error=no_access_token")
            
            # Get user info from Google
            userinfo_response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            userinfo_response.raise_for_status()
            google_user = userinfo_response.json()
            
            email = google_user.get('email')
            if not email:
                logger.error("No email from Google")
                frontend_url = "https://ettahospitalclone.vercel.app"
                return redirect(f"{frontend_url}/login?error=no_email")
            
            # Find or create user
            try:
                user = User.objects.get(email=email)
                created = False
                logger.info(f"Existing user found: {email}")
            except User.DoesNotExist:
                # Create new user
                username = self.generate_username(google_user.get('name', ''), email)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None  # No password for Google users
                )
                user.first_name = google_user.get('given_name', '')
                user.last_name = google_user.get('family_name', '')
                user.save()
                created = True
                logger.info(f"New user created: {email}")
                
                # Create profile
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.fullname = google_user.get('name', f"{user.first_name} {user.last_name}".strip())
                profile.save()
            
            # Log the user in with the ModelBackend
            from django.contrib.auth import login as auth_login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)
            
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
                profile_data = {
                    'role': 'PATIENT',
                    'fullname': user.get_full_name() or user.username,
                    'profile_pix': None,
                    'phone': None,
                    'gender': None,
                }
            
            # Redirect to frontend with tokens
            frontend_url = "https://ettahospitalclone.vercel.app"
            
            tokens = urllib.parse.urlencode({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': str(user.id),
                'email': user.email,
                'username': user.username,
                'is_new_user': str(created).lower(),
            })
            
            redirect_url = f"{frontend_url}/auth/callback?{tokens}"
            
            logger.info(f"Google direct auth successful for {email}")
            return redirect(redirect_url)
            
        except requests.RequestException as e:
            logger.error(f"Google API error: {str(e)}")
            frontend_url = "https://ettahospitalclone.vercel.app"
            return redirect(f"{frontend_url}/login?error=google_api_error&message={urllib.parse.quote(str(e))}")
        except Exception as e:
            logger.error(f"Unexpected error in Google auth: {str(e)}")
            frontend_url = "https://ettahospitalclone.vercel.app"
            return redirect(f"{frontend_url}/login?error=auth_failed&message={urllib.parse.quote(str(e))}")
    
    def generate_username(self, name, email):
        """Generate unique username from name and email"""
        base_username = name.replace(' ', '_').lower() if name else email.split('@')[0]
        username = base_username
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        return username