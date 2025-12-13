import os
import sys
import django
import boto3
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from django.conf import settings

s3 = boto3.client('s3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

# Correct path to media folder
MEDIA_ROOT = BASE_DIR / 'media'
BLOG_IMAGES_DIR = MEDIA_ROOT / 'blog_images'

print(f'Uploading images from: {BLOG_IMAGES_DIR}')
print('=' * 60)

if BLOG_IMAGES_DIR.exists():
    image_files = list(BLOG_IMAGES_DIR.glob('*'))
    print(f'Found {len(image_files)} image files')
    
    uploaded_count = 0
    for file_path in image_files:
        if file_path.is_file():
            s3_key = f'media/blog_images/{file_path.name}'
            print(f'Uploading: {file_path.name} -> {s3_key}')
            
            try:
                # Determine content type
                content_type = 'application/octet-stream'
                if file_path.suffix.lower() in ['.jpg', '.jpeg']:
                    content_type = 'image/jpeg'
                elif file_path.suffix.lower() == '.png':
                    content_type = 'image/png'
                elif file_path.suffix.lower() == '.gif':
                    content_type = 'image/gif'
                elif file_path.suffix.lower() == '.webp':
                    content_type = 'image/webp'
                
                with open(file_path, 'rb') as f:
                    s3.upload_fileobj(
                        f,
                        settings.AWS_STORAGE_BUCKET_NAME,
                        s3_key,
                        ExtraArgs={
                            'ACL': 'public-read',
                            'ContentType': content_type,
                            'CacheControl': 'max-age=86400'
                        }
                    )
                print(f'  ✅ Uploaded with public-read ACL')
                uploaded_count += 1
                
                # Test the upload
                import requests
                url = f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{s3_key}'
                try:
                    resp = requests.head(url, timeout=5)
                    print(f'  Test status: {resp.status_code}')
                except:
                    print(f'  Could not test URL')
                    
            except Exception as e:
                print(f'  ❌ Error: {str(e)[:100]}')
    
    print('=' * 60)
    print(f'Upload complete: {uploaded_count}/{len(image_files)} files uploaded')
    
else:
    print('❌ Blog images directory not found')
