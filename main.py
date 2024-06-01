import boto3
import json
import datetime

INFILE = 'insights.json'
today = datetime.date.today().strftime("%Y%m%d")

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
        'CRITICAL': 0,
        'HIGH': 0,
        'MEDIUM': 0,
        'LOW': 0,
        'INFORMATIONAL': 0
    }

    ## Get information about the current insights and populate dict of results
    response = shclient.get_insight_results(InsightArn=insight['arn'])
    for result in response['InsightResults']['ResultValues']:
        if DEBUG == True: print("%s -> %s" % (result['GroupByAttributeValue'], result['Count']))

        stats[result['GroupByAttributeValue']] = result['Count']

        if DEBUG: print("Stats: %s" % stats)


    ## Deal with CloudWatch Metrics
    metrics = []
    if CWM_OUTPUT == True:
        # Prepare the metrics to be sent to CloudWatch
        # For each severity level, create a metric
        # with the count of findings for that severity
        # and the name of the insight as a dimension
        # (so we can filter by insight name in CloudWatch)
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
        # The namespace should be the overall tool namespace, plus the insight name to help with filtering and organization and dashboards
        thisNamespace = namespace + "/" + today + "/" + insight['name']
        print("-- Sending metrics to CloudWatch... Namespace: %s" % thisNamespace)
        try:
            response = cwclient.put_metric_data(Namespace=thisNamespace, MetricData=metrics)
            print("--- Metrics sent successfully!")
        except Exception as e:
            print("ERROR: Failed to send metrics:", str(e))
    else:
        if DEBUG == True: print("---Skipping CloudWatch output")

    if DEBUG == True:
        print("Discovered metrics:")
        print(metrics)





