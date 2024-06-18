import boto3
import json
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

INFILE = "insights.json"
logging.info("Reading insights from file %s" % INFILE)
today = datetime.date.today().strftime("%Y%m%d")

namespace = "shmetrics"
CWM_OUTPUT = True
CONSOLE_OUT = True
CWL_OUTPUT = True
CWL_GROUPNAME = "shmetrics"
CWL_STREAM = "shmetrics"


metrics = []
insight_metrics = {}


def put_cwl_data(CWL_GROUPNAME, CWL_STREAM, message):
    # Create a CloudWatch Logs client
    cwlclient = session.client("logs")

    # Create a log group
    try:
        response = cwlclient.create_log_group(logGroupName=CWL_GROUPNAME)
    except cwlclient.exceptions.ResourceAlreadyExistsException:
        logging.info("Log group already exists")
    except Exception as e:
        logging.error("ERROR: Failed to create log group:", str(e))

    # Create a log stream
    try:
        response = cwlclient.create_log_stream(
            logGroupName=CWL_GROUPNAME, logStreamName=CWL_STREAM
        )
    except cwlclient.exceptions.ResourceAlreadyExistsException:
        logging.info("Log stream already exists")
    except Exception as e:
        logging.error("ERROR: Failed to create log stream:", str(e))

    # Put a log event
    try:
        response = cwlclient.put_log_events(
            logGroupName=CWL_GROUPNAME,
            logStreamName=CWL_STREAM,
            logEvents=[
                {
                    "timestamp": int(datetime.datetime.now().timestamp() * 1000),
                    "message": message,
                },
            ],
        )
        logging.info("---- Log event sent successfully!")
    except Exception as e:
        logging.error("ERROR: Failed to put log event:", str(e))

def put_cwmetrics_data(namespace, insight_metrics):
    # Send the metrics to CloudWatch
    cw_metric_data = []

    # The namespace should be the overall tool namespace, plus the insight name to help with filtering and organization and dashboards
    thisNamespace = namespace + "/" + today + "/" + insight["name"]
    cwclient = session.client("cloudwatch")
    # Prepare the metrics to be sent to CloudWatch
    # For each severity level, create a metric
    # with the count of findings for that severity
    # and the name of the insight as a dimension
    # (so we can filter by insight name in CloudWatch)
    for severity in insight_metrics:
        logging.info("adding data for %s" % severity)
        cw_metric_data.append(
            {
                "MetricName": "Count",
                "Dimensions": [
                    {"Name": "Insight", "Value": insight["name"]},
                    {"Name": "Severity", "Value": severity},
                ],
                "Unit": "None",
                "Value": insight_metrics[severity],
            }
        )

    # Send the metrics to CloudWatch
    # The namespace should be the overall tool namespace, plus the insight name to help with filtering and organization and dashboards
    thisNamespace = namespace + "/" + today + "/" + insight["name"]
    logging.debug("--- Sending metrics to CloudWatch... Namespace: %s" % thisNamespace)
    try:
        # Send the metrics to CloudWatch
        cwclient.put_metric_data(Namespace=thisNamespace, MetricData=cw_metric_data)
        logging.info("---- Metrics sent successfully!")
    except Exception as e:
        logging.error("ERROR: Failed to send metrics:", str(e))



##############################################
## Get Data from Security Hub
# Create a session using your AWS credentials
session = boto3.Session(profile_name="shmetrics")

# create a client to talk to securityhub
shclient = session.client("securityhub")

# Open and read the JSON file
with open("insights.json", "r") as file:
    logging.info("-- Loading insight check list from file %s" % INFILE)
    insight_config = json.load(file)

## Iterate over all the configured insights
# Access and print the 'name' of each insight
for insight in insight_config["insights"]:
    if insight["disabled"]:
        logging.info('\n-- Skipping disabled insight "%s"' % insight["name"])
        continue

    logging.info('\n-- Getting results for insight "%s"' % insight["name"])

    # Initialize the stats dictionary with default values
    insight_metrics = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFORMATIONAL": 0}

    # Get information about the current insights and populate dict of results
    response = shclient.get_insight_results(InsightArn=insight["arn"])

    logging.debug("--- DEBUG: Result from get_insight_results for %s - %s" % (insight["arn"], response))

    for result in response["InsightResults"]["ResultValues"]:
        logging.debug("%s -> %s" % (result["GroupByAttributeValue"], result["Count"]))

        # Populate the stats dictionary with the count of findings for each severity level
        insight_metrics[result["GroupByAttributeValue"]] = result["Count"]

        logging.debug("Stats: %s" % insight_metrics)

    if CONSOLE_OUT:
        logging.info("--- All insight results: %s" % insight_metrics)

    # Deal with CloudWatch Metrics
    if CWM_OUTPUT:
        put_cwmetrics_data(namespace, insight_metrics)
        logging.debug("Discovered metrics:")
        logging.debug(metrics)
    else:
        logging.info("--- DEBUG: Skipping CloudWatch Metrics output")

    if CWL_OUTPUT:
        metrics_to_json = json.dumps(insight_metrics)
        metrics_to_json.append(insight["name"])
        put_cwl_data(CWL_GROUPNAME, CWL_STREAM, metrics_to_json)
        logging.debug(metrics)
    else:
        logging.info("--- DEBUG: Skipping CloudWatch Logs output")