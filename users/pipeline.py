# users/pipeline.py
from .models import Profile
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

def create_profile(backend, user, response, *args, **kwargs):
    """
    Pipeline to create or update user profile after social authentication
    (Google only now)
    """
    try:
        profile, created = Profile.objects.get_or_create(user=user)
        
        if created or not profile.fullname:
            # Set fullname from Google data
            if backend.name == 'google':
                profile.fullname = response.get('name', '')
            # Remove Facebook and LinkedIn logic
            
            # If no name from social auth, use username
            if not profile.fullname:
                profile.fullname = user.username
                
            profile.save()
            logger.info(f"Profile {'created' if created else 'updated'} for user {user.username}")
            
    except Exception as e:
        logger.error(f"Error creating profile for user {user.username}: {str(e)}")