import boto3
import json
import base64
import random
import time
import os
from pinecone import Pinecone
import redis
import pg8000



def s3_file_path(bucket, key):
  return f"s3://{bucket}/{key}"

def describe_image(s3, bedrock, bucket, key):

  
  # Get the image bytes from S3
  _s3_file_path = s3_file_path(bucket, key)
  print(f"New file uploaded: {_s3_file_path}")
  print(f"Getting image bytes from S3: {_s3_file_path}")
  response = s3.get_object(Bucket=bucket, Key=key)
  image_bytes = response["Body"].read()
  image_base64 = base64.b64encode(image_bytes).decode("utf-8")
  print("Image bytes retrieved and encoded to base64.")
  

  payload = json.dumps({
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": 1024,
      "system": """
        You are part of a system that does intelligent image search. Intelligent image search is a system
        that allows you to search for images, based on items in the image, without the need for users explicitly tagging the images.
        Your role in this subsystem is to describe in detail the incoming image, and all the items in the image.
      """,
      "messages": [
          {
              "role": "user",
              "content": [
                  {
                      "type": "text",
                      "text": "Please describe this image in detail. Pay close attention to the items and the colors."
                  },
                  {
                      "type": "image",
                      "source": {
                          "type": "base64",
                          "media_type": "image/png",  
                          "data": image_base64
                      }
                  }
              ]
          }
      ],
      "temperature": 0.5,
      "top_p": 0.9
  })
  
  response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            contentType='application/json',  
            accept='application/json',  
            body=payload  
  )

  response_body = json.loads(response["body"].read())
  image_descriptions = response_body["content"][0]["text"]
  
  
  return image_descriptions if isinstance(image_descriptions, list) else [image_descriptions]

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
  print(response_body)
  
  # Return the embedding (single item from list)
  return response_body

def upsert_embeddings(vector_db, s3_file_path, embeddings, texts):
  vectors = [(
      f"{s3_file_path}-{index}", 
      embedding,
      {
        'text': texts[index],
        's3_file_path': s3_file_path
      }
    ) for index, embedding in enumerate(embeddings['embeddings']['float'])]
  
  vector_db.upsert(vectors)
  
def insert_to_db(s3_file_path, description):
  
  DATABASE_USER=os.environ['DATABASE_USER']
  DATABASE_PASSWORD=os.environ['DATABASE_PASSWORD']
  DATABASE_HOST=os.environ['DATABASE_HOST']
  DATABASE_NAME=os.environ['DATABASE_NAME']
  
    
  conn = pg8000.connect(
      user=DATABASE_USER,
      password=DATABASE_PASSWORD,
      host=DATABASE_HOST,
      database=DATABASE_NAME
  )
  
  cursor = conn.cursor()


  data = (s3_file_path, description)
  cursor.execute(
    """
    INSERT INTO app_image(s3_file_path, description) 
    VALUES(%s, %s)
    ON CONFLICT(s3_file_path) 
    DO UPDATE SET description = excluded.description
    """, 
    data
  )
  
  conn.commit()
  
  # Clean up
  cursor.close()
  conn.close()
      

def main(event, context):
  
  s3 = boto3.client("s3")
  bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
  
  pc = Pinecone(api_key=os.environ['PINECONE_KEY'])
  vector_db = pc.Index(os.environ['PINECONE_INDEX'])

  print("S3 Event Received:", event)
  
  for record in event["Records"]:
      bucket = record["s3"]["bucket"]["name"]
      key = record["s3"]["object"]["key"]      
      image_descriptions = describe_image(s3=s3, bedrock=bedrock, bucket=bucket, key=key)
      
      print(image_descriptions)
      
      insert_to_db(
        s3_file_path=s3_file_path(bucket, key),
        description= "\n".join(image_descriptions)
      )
      
      image_description_embeddings = get_embeddings(bedrock=bedrock, texts=image_descriptions, input_type="search_document")
      
      print(image_description_embeddings)
      
      upsert_embeddings(
        vector_db=vector_db,
        s3_file_path=s3_file_path(bucket, key),
        embeddings=image_description_embeddings,
        texts=image_descriptions
      )
      



