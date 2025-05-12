import boto3
import json

def main(event, context):
    print("S3 Event Received:", event)
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        print(f"New file uploaded: s3://{bucket}/{key}")
        
    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")

    payload = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": """
          You are a poet. Your task is to write a haiku poem about the beauty of nature.
        """,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Write a haiku poem about the beauty of nature."
                    }
                ]
            }
        ],
        "temperature": 0.5,
        "top_p": 0.9
    })
    
    response = bedrock_client.invoke_model(
      modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
      contentType='application/json',  # Depending on your model input format
      accept='application/json',  # Accepting output in JSON format
      body=payload  # Input text to the model
    )

    response_body = json.loads(response["body"].read())
    print("Claude 3 response:", response_body["content"][0]["text"])


