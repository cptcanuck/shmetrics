import boto3
import json
import datetime

INFILE = 'insights.json'
today = datetime.date.today().strftime("%Y%m%d")

namespace = "shmetrics"
DEBUG = False
CWM_OUTPUT = True
CONSOLE_OUT = True

metrics = []
stats = {}

# Create a session using your AWS credentials
session = boto3.Session(profile_name='shmetrics')

# create a client to talk to securityhub
shclient = session.client('securityhub')

# Open and read the JSON file
with open('insights.json', 'r') as file:
    print ("-- Loading insight check list from file %s" % INFILE)
    data = json.load(file)

# Access and print the 'name' of each insight
for insight in data['insights']:
    if insight['disabled'] == True:
        print('\n-- Skipping disabled insight "%s"' % insight['name'])
        continue

    print('\n-- Getting results for insight "%s"' % insight['name'])


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
    ## https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/client/get_insight_results.html
    ## {'ResponseMetadata': {'RequestId': 'e010faf2-10dd-47a6-9caa-d19c4b20e0c6', 'HTTPStatusCode': 200, 'HTTPHeaders': 
    ## {'date': 'Sun, 02 Jun 2024 00:12:39 GMT', 'content-type': 'application/json', 'content-length': '283', 'connection': 'keep-alive', 
    ## 'x-amzn-requestid': 'e010faf2-10dd-47a6-9caa-d19c4b20e0c6', 'access-control-allow-origin': '*', 
    ## 'access-control-allow-headers': 'Authorization,Date,X-Amz-Date,X-Amz-Security-Token,X-Amz-Target,content-type,x-amz-content-sha256,x-amz-user-agent,x-amzn-platform-id,x-amzn-trace-id', 'x-amz-apigw-id': 'YtnWoEU6IAMEgFQ=', 'cache-control': 'no-cache', 'access-control-allow-methods': 'GET,POST,OPTIONS,PUT,PATCH,DELETE', 'access-control-expose-headers': 'x-amzn-errortype,x-amzn-requestid,x-amzn-errormessage,x-amzn-trace-id,x-amz-apigw-id,date', 'x-amzn-trace-id': 'Root=1-665bb8f6-0ac3ab6c233d295a56dbc65e', 'access-control-max-age': '86400'}, 'RetryAttempts': 0}, 'InsightResults': {'InsightArn': 'arn:aws:securityhub:us-east-1:193203723632:insight/193203723632/custom/e26a12ca-847c-4337-9064-5335ab10056b', 
    ## 'GroupByAttribute': 'SeverityLabel', 'ResultValues': [{'GroupByAttributeValue': 'LOW', 'Count': 17}, {'GroupByAttributeValue': 'MEDIUM', 'Count': 4}]}}

    if DEBUG == True: print("--- DEBUG: Result from get_insight_results for %s - %s" % (insight['arn'], response))

    for result in response['InsightResults']['ResultValues']:
        if DEBUG == True: print("%s -> %s" % (result['GroupByAttributeValue'], result['Count']))

        stats[result['GroupByAttributeValue']] = result['Count']

        if DEBUG: print("Stats: %s" % stats)

    if CONSOLE_OUT: print("--- All insight results: %s" % stats)


    ## Deal with CloudWatch Metrics
    metrics = []
    if CWM_OUTPUT == True:
        cwclient = session.client('cloudwatch')
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
        print("--- Sending metrics to CloudWatch... Namespace: %s" % thisNamespace)
        try:
            response = cwclient.put_metric_data(Namespace=thisNamespace, MetricData=metrics)
            print("---- Metrics sent successfully!")
        except Exception as e:
            print("ERROR: Failed to send metrics:", str(e))
    else:
        if DEBUG == True: print("--- DEBUG: Skipping CloudWatch output")

    if DEBUG == True:
        print("Discovered metrics:")
        print(metrics)





