def main(event, context):
    print("S3 Event Received:", event)
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        print(f"New file uploaded: s3://{bucket}/{key}")
