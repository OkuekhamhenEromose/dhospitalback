import os
import sys
import django
from pathlib import Path
import time
import requests

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from hospital.models import BlogPost
from django.core.files import File

print('Creating a new blog post...')
print('=' * 60)

# Use one of your existing images
MEDIA_ROOT = BASE_DIR / 'media'
BLOG_IMAGES_DIR = MEDIA_ROOT / 'blog_images'

if BLOG_IMAGES_DIR.exists():
    # Get first image file
    image_files = list(BLOG_IMAGES_DIR.glob('*'))
    if image_files:
        image_file = image_files[0]
        print(f'Using image: {image_file.name}')
        
        try:
            # Create blog post
            timestamp = int(time.time())
            blog_post = BlogPost.objects.create(
                title=f'Test Blog Post {timestamp}',
                slug=f'test-blog-post-{timestamp}',
                content='This is a test blog post to verify image uploads work correctly.',
                description='Testing image upload functionality with S3',
                published=True,
                author_id=1  # Make sure you have a user with ID 1
            )
            
            print(f'Created blog post: {blog_post.title}')
            
            # Upload the image
            with open(image_file, 'rb') as f:
                blog_post.featured_image.save(image_file.name, File(f))
                blog_post.save()
            
            print(f'Image uploaded: {blog_post.featured_image.name}')
            
            # Test the URL
            url = blog_post.featured_image.url
            print(f'Image URL: {url}')
            
            # Force global URL if needed
            if '.s3.eu-north-1.amazonaws.com' in url:
                url = url.replace('.s3.eu-north-1.amazonaws.com', '.s3.amazonaws.com')
            
            print(f'Testing URL: {url}')
            resp = requests.head(url)
            print(f'Status: {resp.status_code}')
            
            if resp.status_code == 200:
                print('SUCCESS! Blog post created and image is accessible.')
                print('You can view it at:', f'https://dhospitalback.onrender.com/api/hospital/blog/{blog_post.slug}/')
            else:
                print(f'Failed with status: {resp.status_code}')
            
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
    else:
        print('No image files found in blog_images folder')
else:
    print('Blog images directory not found')
