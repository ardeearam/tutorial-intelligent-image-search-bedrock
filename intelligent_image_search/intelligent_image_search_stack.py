from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_lambda as _lambda,
    aws_iam as iam,
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
        
        my_lambda = _lambda.Function(
          self, "OnUploadLambdaFunction",
          runtime=_lambda.Runtime.PYTHON_3_11,
          handler="handler.main",
          code=_lambda.Code.from_asset("lambda"),
          timeout=Duration.seconds(900)
        )
        
        my_lambda.role.add_managed_policy(
          iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        )
        
        bucket = s3.Bucket(
            self, 
            "IntelligentImageSearchBucket",
            versioned=True,
            bucket_name="intelligent-image-search-bucket.klaudsol.com",
        )
        
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(my_lambda)
        )


        bucket.grant_read(my_lambda)
        bucket.grant_write(my_lambda)
        
