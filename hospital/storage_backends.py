# blogc/storage_backends.py
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    custom_domain = f"{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com"
    default_acl = None
    querystring_auth = False

    def get_object_parameters(self, name):
        # Get the default parameters from parent class
        params = super().get_object_parameters(name)
        if 'ACL' in params:
            del params['ACL']
        # Remove BucketOwnerEnforced if present
        if 'BucketOwnerEnforced' in params:
            del params['BucketOwnerEnforced']
        
        return params