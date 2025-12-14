# users/urls.py - UPDATED WITH PROPER SOCIAL AUTH
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
    TokenObtainPairView,
)
from . import views

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Custom endpoints
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('update-profile/', views.UpdateProfileView.as_view(), name='update-profile'),
    
    # Social Auth URLs - MUST come before other social-* paths
    path('', include('social_django.urls', namespace='social')),
    
    # Custom social auth views - IMPORTANT ORDER
    path('social-auth-success/', views.SocialAuthSuccessView.as_view(), name='social-auth-success'),
    path('social-auth-error/', views.SocialAuthErrorView.as_view(), name='social-auth-error'),
    path('social-login/', views.SocialAuthLoginView.as_view(), name='social-login'),
    path('social-auth-urls/', views.SocialAuthUrlsView.as_view(), name='social-auth-urls'),
    path('social-auth-debug/', views.SocialAuthDebugView.as_view(), name='social-auth-debug'),
    path('google-callback/', views.GoogleOAuthCallbackView.as_view(), name='google-callback'),
]