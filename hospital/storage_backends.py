# hospital/storage_backends.py - SIMPLEST WORKING VERSION
from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'
    
    def __init__(self, *args, **kwargs):
        kwargs['default_acl'] = 'public-read'
        super().__init__(*args, **kwargs)
    
    def _get_write_parameters(self, name, content=None):
        """
        Override to ensure ACL is always set to public-read
        """
        params = super()._get_write_parameters(name, content)
        
        # Force ACL to public-read
        params['ACL'] = 'public-read'
        
        return params
