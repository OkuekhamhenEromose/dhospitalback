# test_s3_fix.py
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from hospital.models import BlogPost
from django.core.files import File
import tempfile
from PIL import Image
import time
import requests

print('Testing S3 upload and access...')

# Create test image
with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
    img = Image.new('RGB', (100, 100), color='red')
    img.save(tmp.name, 'JPEG')
    tmp_path = tmp.name

print(f'Created test image: {tmp_path}')

# Get or create test blog post
timestamp = int(time.time())
blog_post, created = BlogPost.objects.get_or_create(
    title=f'Test S3 Fix {timestamp}',
    defaults={
        'slug': f'test-s3-fix-{timestamp}',
        'content': 'Test content',
        'author_id': 1  # Make sure you have a user with ID 1
    }
)

print(f'Using blog post: {blog_post.title} ({"Created" if created else "Existing"})')

# Upload the image
try:
    with open(tmp_path, 'rb') as f:
        blog_post.featured_image.save(f'test_fix_{timestamp}.jpg', File(f))
        blog_post.save()
    
    print(f'Uploaded file to S3')
    print(f'File URL: {blog_post.featured_image.url}')
    print(f'File path: {blog_post.featured_image.name}')
    
    # Test URL access
    url = blog_post.featured_image.url
    print(f'\nTesting URL: {url}')
    
    # Try both regional and global endpoints
    if 's3.eu-north-1.amazonaws.com' in url:
        global_url = url.replace('s3.eu-north-1.amazonaws.com', 's3.amazonaws.com')
        print(f'Also testing global URL: {global_url}')
        
        try:
            response = requests.head(global_url, timeout=5)
            print(f'Global URL Status: {response.status_code}')
        except Exception as e:
            print(f'Global URL Error: {e}')
    
    try:
        response = requests.head(url, timeout=5)
        print(f'Regional URL Status: {response.status_code}')
    except Exception as e:
        print(f'Regional URL Error: {e}')
    
    # Cleanup
    os.unlink(tmp_path)
    print(f'\nCleaned up temporary file')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()