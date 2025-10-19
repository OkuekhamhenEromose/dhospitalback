# users/utils.py
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def SendMail(email):
    try:
        subject = "Welcome to nile website"
        message = '''This is we saying a big welcome to you
Thanks for registering.'''

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {str(e)}")
        # Don't raise the exception, just log it
        return False