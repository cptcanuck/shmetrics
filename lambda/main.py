import boto3
import json
import datetime
import logging
import os

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()

if logging.getLogger().hasHandlers():
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(LOGLEVEL)
else:
    logging.basicConfig(level=LOGLEVEL)

INFILE = "insights.json"

# Console output config
CONSOLE_OUTPUT = os.environ.get("CONSOLE_OUTPUT", False)

# CloudWatch Metrics output config
CWM_NAMESPACE = os.environ.get("CWM_NAMESPACE", "shmetrics")
CWM_OUTPUT = os.environ.get("CWM_OUTPUT", True)

# CloudWatch Logs output config
CWL_OUTPUT = os.environ.get("CWL_OUTPUT", True)
CWL_GROUPNAME = os.environ.get("CWL_GROUPNAME", "shmetrics")
CWL_STREAM = os.environ.get("CWL_STREAM", "shmetrics")


metrics = []
insight_data = {}


###################################################
def put_cwl_data(CWL_GROUPNAME, CWL_STREAM, insight_data, session):
    cw_log_data = []
    # Create a CloudWatch Logs client
    cwlclient = session.client("logs")

    # Create a log group
    try:
        cwlclient.create_log_group(logGroupName=CWL_GROUPNAME)
    except cwlclient.exceptions.ResourceAlreadyExistsException:
        logging.debug("Log group already exists")
    except Exception as e:
        logging.error("ERROR: Failed to create log group:", str(e))

    # Create a log stream
    try:
        cwlclient.create_log_stream(
            logGroupName=CWL_GROUPNAME, logStreamName=CWL_STREAM
        )
    except cwlclient.exceptions.ResourceAlreadyExistsException:
        logging.debug("Log stream already exists")
    except Exception as e:
        logging.error("ERROR: Failed to create log stream:", str(e))

    for KEY in insight_data:
        if KEY == "INSIGHT_NAME" or KEY == "INSIGHT_ARN":
            continue

        logging.debug("adding data for %s -> %s" % (KEY, insight_data[KEY]))
        cw_log_data.append(
            {
                "shmetrics_schema_version": "1.0",
                "shmetrics_schema_type": "KVInsight",
                "MetricName": "Count",
                "Dimensions": [
                    {"Name": "Insight", "Value": insight_data["INSIGHT_NAME"]},
                    {"Name": "Severity", "Value": KEY},
                ],
                "Unit": "None",
                "Value": insight_data[KEY],
            }
        )

    # Put a log event
    try:
        cwlclient.put_log_events(
            logGroupName=CWL_GROUPNAME,
            logStreamName=CWL_STREAM,
            logEvents=[
                {
                    "timestamp": int(datetime.datetime.now().timestamp() * 1000),
                    "message": json.dumps(cw_log_data),
                },
            ],
        )
        logging.info("-- Log writen to CWL successfully!")
    except Exception as e:
        logging.error("Failed to put log event:", str(e))


def put_cwmetrics_data(CWM_NAMESPACE, insight_data, session):
    # Send the metrics to CloudWatch
    cw_metric_data = []

    try:
        cwclient = session.client("cloudwatch")
    except Exception as e:
        logging.error("ERROR: Failed to create CloudWatch client:", str(e))

    # Prepare the metrics to be sent to CloudWatch
    for KEY in insight_data:
        if KEY == "INSIGHT_NAME" or KEY == "INSIGHT_ARN":
            continue

        logging.debug("adding data for %s" % KEY)
        cw_metric_data.append(
            {
                "MetricName": "Count",
                "Dimensions": [
                    {"Name": "Insight", "Value": insight_data["INSIGHT_NAME"]},
                    {"Name": "Severity", "Value": KEY},
                ],
                "Unit": "None",
                "Value": insight_data[KEY],
            }
        )
    logging.debug("Metric data:\n%s" % cw_metric_data)

    # Send the metrics to CloudWatch
    thisNamespace = CWM_NAMESPACE + "/" + insight_data["INSIGHT_NAME"]

    logging.debug("- Sending metrics to CloudWatch... Namespace: %s" % thisNamespace)
    try:
        # Send the metrics to CloudWatch
        cwclient.put_metric_data(Namespace=thisNamespace, MetricData=cw_metric_data)
        logging.info("-- Metrics sent successfully!")
    except Exception as e:
        logging.error("ERROR: Failed to send metrics:", str(e))


def lambda_handler(event, context):

    # Get Data from Security Hub
    # Create a session using your AWS credentials
    session = boto3.Session()

    # create a client to talk to securityhub
    shclient = session.client("securityhub")

    # Open and read the JSON file
    with open(INFILE, "r") as file:
        logging.info("Loading insight check list from file %s" % INFILE)
        insight_config = json.load(file)

    # Iterate over all the configured insights
    for insight in insight_config["insights"]:
        if insight["disabled"]:
            logging.info('Skipping disabled insight "%s"' % insight["name"])
            continue

        logging.info('Getting results for insight "%s"' % insight["name"])

        # Initialize the stats dictionary with default values
        insight_data = {
            "INSIGHT_NAME": insight["name"],
            "INSIGHT_ARN": insight["arn"],
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFORMATIONAL": 0,
        }

        # Get information about the current insights and populate dict of results
        response = shclient.get_insight_results(InsightArn=insight["arn"])

        logging.debug(
            "Result from get_insight_results for %s - %s"
            % (insight["arn"], response)
        )

        for result in response["InsightResults"]["ResultValues"]:
            logging.debug(
                "%s -> %s" % (result["GroupByAttributeValue"], result["Count"])
            )

            # Populate the stats dictionary with the count of findings for each severity level
            insight_data[result["GroupByAttributeValue"]] = result["Count"]

            logging.debug("Stats: %s" % insight_data)

        # Deal with CloudWatch Metrics
        if CONSOLE_OUTPUT == "True" or CONSOLE_OUTPUT == True:
            logging.info("- Outputting data to console...")
            print(json.dumps(insight_data, indent=4))
        else:
            logging.debug("- Skipping Console output")

        if CWM_OUTPUT == "True" or CWM_OUTPUT == True:
            logging.info("- Sending metrics to CloudWatch metrics...")
            logging.debug(insight_data)
            put_cwmetrics_data(CWM_NAMESPACE, insight_data, session)
        else:
            logging.debug("- Skipping CloudWatch Metrics output")

        if CWL_OUTPUT == "True" or CWL_OUTPUT == True:
            logging.info("- Sending logs to CloudWatch Logs...")
            logging.debug(insight_data)
            put_cwl_data(CWL_GROUPNAME, CWL_STREAM, insight_data, session)
        else:
            logging.debug("- Skipping CloudWatch Logs output")


