import boto3
import json
import base64
import random
import time


def describe_image(s3, bedrock, bucket, key):

  
  # Get the image bytes from S3
  s3_file_path = f"s3://{bucket}/{key}"
  print(f"New file uploaded: {s3_file_path}")
  print(f"Getting image bytes from S3: {s3_file_path}")
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
  
  # if isinstance(image_description, list):
  #     image_description = image_description.join("\n")
  
  return image_descriptions

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

def main(event, context):
  
  s3 = boto3.client("s3")
  bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

  print("S3 Event Received:", event)
  
  for record in event["Records"]:
      bucket = record["s3"]["bucket"]["name"]
      key = record["s3"]["object"]["key"]      
      image_descriptions = describe_image(s3=s3, bedrock=bedrock, bucket=bucket, key=key)
      print(image_descriptions)
      image_description_embeddings = get_embeddings(bedrock=bedrock, texts=image_descriptions, input_type="search_document")
      print(image_description_embeddings)
      



