# app/views.py

from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Image
import boto3
import re
import json
from pinecone import Pinecone
from django.conf import settings
import pandas as pd
import time



current_env = settings.ENV

print(current_env)  # 'development'


def get_embeddings(bedrock, texts, input_type):
  
  # Cohere Embed model ID on Bedrock
  MODEL_ID = "cohere.embed-english-v3"
  
  # Prepare the payload following Cohere’s input schema
  payload = {
      "texts": [texts] if isinstance(texts, str) else texts,     
      "input_type": input_type,  
      "embedding_types": ["float"]      
  }

  # Convert payload to JSON string
  body = json.dumps(payload)

  # Invoke the Cohere model on Bedrock
  response = bedrock.invoke_model(
      modelId=MODEL_ID,
      body=body,
      contentType="application/json",
      accept="application/json"
  )

  # Parse the response body
  response_body = json.loads(response['body'].read())
  #print(response_body)
  
  # Return the embedding (single item from list)
  return response_body

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

def search_in_vector_db(vector_db, query_embedding):
  
  # Perform semantic search
  results = vector_db.query(vector=query_embedding, top_k=3, include_metadata=True)

  for match in results['matches']:
      print(f"Score: {match['score']:.4f} | Text: {match['metadata']['text']}")
      print(match['metadata'])
      
  print(len(results['matches']))
  
  match_dict = [{
    's3_file_path': match['metadata']['s3_file_path'],
    'score': match['score']
  } for match in results['matches']]
  
  df = pd.DataFrame(match_dict)
  df.sort_values('score',ascending=False, inplace=True)
  df.drop_duplicates(subset=['s3_file_path'], inplace=True)
  df_subset = df[['s3_file_path']]
  #print(df_subset.head())
  return df['s3_file_path'].to_list()

def get_presigned_upload_url():
  s3 = boto3.client('s3')
  
  timestamp = round(time.time())
  
  
  presigned_post = s3.generate_presigned_post(
    Bucket='intelligent-image-search-bucket.klaudsol.com',
    Key=f'guest/{timestamp}.png',
    Fields={"Content-Type": 'image/png'},
    Conditions=[
        {"Content-Type": 'image/png'},
    ],
    ExpiresIn=300  # 5 minutes
  )
  
  print(presigned_post)
    
  return presigned_post


def home(request):
  if request.method == 'GET':
    
    images = Image.objects.all()
    presigned_urls = {image.s3_file_path: generate_presigned_url(image.s3_file_path) for image in images}
    presigned_upload_url_hash = get_presigned_upload_url()
    print(presigned_upload_url_hash)
    
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print("Running as:")
    print(identity)
    
    return render(request, 'app/index.html', 
    {
      'images': images, 
      'presigned_urls': presigned_urls, 
      'presigned_upload_url': presigned_upload_url_hash['url'],
      'presigned_upload_fields': presigned_upload_url_hash['fields']
    })
  
  elif request.method == 'POST':
    q = request.POST.get('q')
    print(q)
    
    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
    pc = Pinecone(api_key=settings.PINECONE_KEY)
    vector_db = pc.Index(settings.PINECONE_INDEX)
    
    
    query_embedding = get_embeddings(bedrock=bedrock, texts=q, input_type="search_query")['embeddings']['float'][0]
    #print(query_embedding)
    matching_images = search_in_vector_db(vector_db=vector_db, query_embedding=query_embedding)
    print(matching_images)
    images = list(Image.objects.filter(s3_file_path__in=matching_images))
    print(images)
    presigned_urls = {image.s3_file_path: generate_presigned_url(image.s3_file_path) for image in images}
    return render(request, 'app/index.html', {'images': images, 'presigned_urls': presigned_urls})
  
def upload(request):
  return redirect('/')