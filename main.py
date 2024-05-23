import boto3

# Create a session using your AWS credentials
session = boto3.Session(profile_name='shmetrics')

# create a client to talk to securityhub
client = session.client('securityhub')

# list the output of security hub insight with the ARN arn:aws:securityhub:us-east-1:193203723632:insight/193203723632/custom/e26a12ca-847c-4337-9064-5335ab10056b
response = client.get_insight_results(
    InsightArn='arn:aws:securityhub:us-east-1:193203723632:insight/193203723632/custom/e26a12ca-847c-4337-9064-5335ab10056b'
)

for result in response['InsightResults']['ResultValues']:
    print(result)
