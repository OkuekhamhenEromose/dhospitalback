# users/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('update-profile/', views.UpdateProfileView.as_view(), name='update-profile'),
    
    # Social Auth URLs - MUST come before other social-* paths
    path('', include('social_django.urls', namespace='social')),
    
    # Custom social auth views
    path('social-login/', views.SocialAuthLoginView.as_view(), name='social-login'),
    path('social-auth-success/', views.SocialAuthSuccessView.as_view(), name='social-auth-success'),
    path('social-auth-error/', views.SocialAuthErrorView.as_view(), name='social-auth-error'),
    path('social-auth-urls/', views.SocialAuthUrlsView.as_view(), name='social-auth-urls'),
]