from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_s3 as s3,
)
from constructs import Construct

class IntelligentImageSearchStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        queue = sqs.Queue(
            self, "IntelligentImageSearchQueue",
            visibility_timeout=Duration.seconds(300),
        )
        bucket = s3.Bucket(
            self, 
            "IntelligentImageSearchBucket",
            versioned=True,
            bucket_name="intelligent-image-search-bucket.klaudsol.com",
        )
        
