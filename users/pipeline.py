# users/pipeline.py
from .models import Profile
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

def create_profile(backend, user, response, *args, **kwargs):
    """
    Pipeline to create or update user profile after social authentication
    """
    try:
        profile, created = Profile.objects.get_or_create(user=user)
        
        if created or not profile.fullname:
            # Set fullname from social auth data
            if backend.name == 'google':
                profile.fullname = response.get('name', '')
            elif backend.name == 'facebook':
                profile.fullname = response.get('name', '')
            elif backend.name == 'linkedin':
                profile.fullname = f"{response.get('firstName', '')} {response.get('lastName', '')}".strip()
            
            # If no name from social auth, use username
            if not profile.fullname:
                profile.fullname = user.username
                
            profile.save()
            logger.info(f"Profile {'created' if created else 'updated'} for user {user.username}")
            
    except Exception as e:
        logger.error(f"Error creating profile for user {user.username}: {str(e)}")