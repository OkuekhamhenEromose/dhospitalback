# test_s3.py
import boto3
import os
from decouple import config

# Load environment variables
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')

print("🔍 Testing AWS S3 Connection...")
print(f"Bucket: {AWS_STORAGE_BUCKET_NAME}")
print(f"Region: {AWS_S3_REGION_NAME}")

try:
    # Create S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION_NAME
    )
    
    # Test connection by listing buckets
    response = s3.list_buckets()
    buckets = [bucket['Name'] for bucket in response['Buckets']]
    
    print(f"✅ Connected to AWS S3 successfully!")
    print(f"Available buckets: {buckets}")
    
    # Check if our bucket exists
    if AWS_STORAGE_BUCKET_NAME in buckets:
        print(f"✅ Bucket '{AWS_STORAGE_BUCKET_NAME}' exists!")
        
        # List objects in the bucket
        objects = s3.list_objects_v2(Bucket=AWS_STORAGE_BUCKET_NAME, Prefix='media/')
        if 'Contents' in objects:
            print(f"✅ Found {len(objects['Contents'])} objects in bucket")
            for obj in objects['Contents'][:5]:  # Show first 5
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("ℹ️  No objects found in bucket yet")
    else:
        print(f"❌ Bucket '{AWS_STORAGE_BUCKET_NAME}' not found!")
        print("You need to create the bucket first.")
        
except Exception as e:
    print(f"❌ AWS S3 Connection Failed: {str(e)}")