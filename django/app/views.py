# app/views.py

from django.http import HttpResponse
from django.shortcuts import render
from .models import Image
import boto3
import re


def generate_presigned_url(s3_file_path, expiration=3600):
    """Generate a pre-signed URL to share an S3 object."""
    s3 = boto3.client('s3')


    # Generate the pre-signed URL
    pattern = r"s3://([^/]+(?:\.[^/]+)+)/(.+)"

    # Apply the regex
    match = re.match(pattern, s3_file_path)
    
    if match:
        # Extract the bucket name and path
        bucket_name = match.group(1)
        object_key = match.group(2)

    else:
        raise ValueError("No match found.")
    
    url = s3.generate_presigned_url('get_object',
                                            Params={'Bucket': bucket_name, 'Key': object_key},
                                            ExpiresIn=expiration)
    return url
\

def home(request):
  if request.method == 'GET':
    images = Image.objects.all()
    presigned_urls = {image.s3_file_path: generate_presigned_url(image.s3_file_path) for image in images}
    return render(request, 'app/index.html', {'images': images, 'presigned_urls': presigned_urls})
  elif request.method == 'POST':
    pass