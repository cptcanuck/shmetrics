import boto3
import json

INFILE = 'insights.json'
namespace = "shmetrics"
DEBUG = True
CWM_OUTPUT = True

metrics = []
stats = {}

# Create a session using your AWS credentials
session = boto3.Session(profile_name='shmetrics')

# create a client to talk to securityhub
shclient = session.client('securityhub')
cwclient = session.client("cloudwatch")


# Open and read the JSON file
with open('insights.json', 'r') as file:
    print ("-- Loading data from file %s" % INFILE)
    data = json.load(file)

# Access and print the 'name' of each insight
for insight in data['insights']:
    if insight['disabled'] == True:
        print('-- Skipping disabled insight "%s"' % insight['name'])
        continue

    print('-- Getting results for insight "%s"' % insight['name'])


    # Initialize the stats dictionary with default values
    stats = {
        'Critical': 0,
        'High': 0,
        'Medium': 0,
        'Low': 0,
        'Informational': 0
    }

    ## Get information about the current insights and populate dict of results
    response = shclient.get_insight_results(InsightArn=insight['arn'])
    for result in response['InsightResults']['ResultValues']:
        if DEBUG == True: print("%s -> %s" % (result['GroupByAttributeValue'], result['Count']))

        stats[result['GroupByAttributeValue']] = result['Count']

        if DEBUG: print("Stats: %s" % stats)


    ## Deal with CloudWatch Metrics
    if CWM_OUTPUT == True:
        for severity in stats:
            metrics.append(
                {
                    "MetricName": "Count",
                    "Dimensions": [
                        {"Name": "Insight", "Value": insight['name']},
                        {"Name": "Severity", "Value": severity},
                    ],
                    "Unit": "None",
                    "Value":  stats[severity],
                }
            )
        
        # Send the metrics to CloudWatch
        print("-- Sending metrics to CloudWatch... Namespace: %s" % namespace)
        try:
            response = cwclient.put_metric_data(Namespace=namespace, MetricData=metrics)
            print("--- Metrics sent successfully!")
        except Exception as e:
            print("ERROR: Failed to send metrics:", str(e))
    else:
        if DEBUG == True: print("---Skipping CloudWatch output")

    if DEBUG == True:
        print("Discovered metrics:")
        print(metrics)





