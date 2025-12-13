# test_blog_upload.py
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

print('Creating a new blog post with image...')
print('=' * 60)

# Create test image
with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
    img = Image.new('RGB', (300, 200), color='blue')
    img.save(tmp.name, 'JPEG')
    tmp_path = tmp.name

print(f'Created test image: {tmp_path}')

# Create blog post
timestamp = int(time.time())
try:
    blog_post = BlogPost.objects.create(
        title=f'Test Blog Post {timestamp}',
        slug=f'test-blog-post-{timestamp}',
        content='Test content for new blog post',
        description='Test description',
        published=True,
        author_id=1  # Make sure you have a user with ID 1
    )
    
    print(f'Created blog post: {blog_post.title}')
    
    # Upload image
    with open(tmp_path, 'rb') as f:
        blog_post.featured_image.save(f'test_blog_{timestamp}.jpg', File(f))
        blog_post.save()
    
    print(f'Image uploaded: {blog_post.featured_image.name}')
    print(f'Image URL: {blog_post.featured_image.url}')
    
    # Test the image URL
    url = blog_post.featured_image.url
    
    # Force global URL if needed
    if '.s3.eu-north-1.amazonaws.com' in url:
        url = url.replace('.s3.eu-north-1.amazonaws.com', '.s3.amazonaws.com')
    
    print(f'Testing URL: {url}')
    resp = requests.head(url)
    print(f'Status: {resp.status_code}')
    
    if resp.status_code == 200:
        print('SUCCESS! New blog images will work!')
    else:
        print(f'Failed with status: {resp.status_code}')
    
    # Cleanup
    os.unlink(tmp_path)
    print('Cleaned up temporary file')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
    
    # Cleanup on error
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)