import aws_cdk as core
import aws_cdk.assertions as assertions

from intelligent_image_search.intelligent_image_search_stack import IntelligentImageSearchStack

# example tests. To run these tests, uncomment this file along with the example
# resource in intelligent_image_search/intelligent_image_search_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = IntelligentImageSearchStack(app, "intelligent-image-search")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
