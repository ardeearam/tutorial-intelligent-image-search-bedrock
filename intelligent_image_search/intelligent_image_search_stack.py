from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from aws_cdk.aws_s3 import BlockPublicAccess
from constructs import Construct
from dotenv import dotenv_values

class IntelligentImageSearchStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        env_vars = dotenv_values(".env") 
        
        print(env_vars)
        
        my_lambda = _lambda.Function(
          self, "OnUploadLambdaFunction",
          runtime=_lambda.Runtime.PYTHON_3_11,
          handler="handler.main",
          code=_lambda.Code.from_asset("lambda"),
          timeout=Duration.seconds(900),  #IMPORTANT
          environment=env_vars 
        )
        
        my_lambda.role.add_managed_policy(
          iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        )
        
        bucket = s3.Bucket(
            self, 
            "IntelligentImageSearchBucket",
            versioned=True,
            bucket_name=env_vars['S3_BUCKET_NAME'],
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.HEAD
                    ],
                    allowed_origins=["*"],  
                    allowed_headers=["*"],
                    exposed_headers=["ETag"]
                )
            ],
            block_public_access=BlockPublicAccess(
                block_public_acls=False,
                ignore_public_acls=True,
                block_public_policy=True,
                restrict_public_buckets=True
            )
        )
        
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(my_lambda)
        )


        bucket.grant_read(my_lambda)
        bucket.grant_write(my_lambda)
        
        # 
        
