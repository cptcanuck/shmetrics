import boto3
import json

INFILE = 'insights.json'

# Create a session using your AWS credentials
session = boto3.Session(profile_name='shmetrics')

# create a client to talk to securityhub
client = session.client('securityhub')

# Open and read the JSON file
with open('insights.json', 'r') as file:
    print ("-- Loading data from fight %s" % INFILE)
    data = json.load(file)

# Access and print the 'name' of each insight
for insight in data['insights']:
    print('-- Getting results for insight "%s"' % insight['name'])

    response = client.get_insight_results(InsightArn=insight['arn'])
    for result in response['InsightResults']['ResultValues']:
        print(result)



