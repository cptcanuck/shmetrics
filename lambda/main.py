import boto3
import json
import datetime
import logging
import os

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()

if logging.getLogger().hasHandlers():
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    # https://github.com/aws/aws-lambda-python-runtime-interface-client/blob/main/awslambdaric/bootstrap.py#L440
    logging.getLogger().setLevel(LOGLEVEL)
else:
    logging.basicConfig(level=LOGLEVEL)

# Configuration
#INFILE = "insights.json"

LAMBDA_S3_BUCKET = os.environ.get("LAMBDA_S3_BUCKET", "193203723632-shmetrics-lambda")
LAMBDA_S3_KEY = os.environ.get("LAMBDA_CONFIG_FILE", "config/insights.json")
LAMBDA_S3_CONFIG = "s3://" + LAMBDA_S3_BUCKET + "/" + LAMBDA_S3_KEY

SHMETRICS_CONFIG = os.environ.get("SHMETRICS_CONFIG", "insights.json")

# Console output config
CONSOLE_OUTPUT = os.environ.get("CONSOLE_OUTPUT", False)

# CloudWatch Metrics output config
CWM_NAMESPACE = os.environ.get("CWM_NAMESPACE", "shmetrics")
CWM_OUTPUT = os.environ.get("CWM_OUTPUT", True)

# CloudWatch Logs output config
CWL_OUTPUT = os.environ.get("CWL_OUTPUT", True)
CWL_GROUPNAME = os.environ.get("CWL_GROUPNAME", "shmetrics")
CWL_STREAM = os.environ.get("CWL_STREAM", "shmetrics")

logging.info("----------- Configuration:")
logging.info("CONSOLE_OUTPUT: %s" % CONSOLE_OUTPUT)
logging.info("CWM_NAMESPACE: %s" % CWM_NAMESPACE)
logging.info("CWM_OUTPUT: %s" % CWM_OUTPUT)
logging.info("CWL_OUTPUT: %s" % CWL_OUTPUT)
logging.info("CWL_GROUPNAME: %s" % CWL_GROUPNAME)
logging.info("CWL_STREAM: %s" % CWL_STREAM)
logging.info("LOGLEVEL: %s" % LOGLEVEL)
logging.info("LAMBDA_S3_BUCKET: %s" % LAMBDA_S3_BUCKET)
logging.info("LAMBDA_S3_KEY: %s" % LAMBDA_S3_KEY)
logging.info("LAMBDA_S3_CONFIG: s3://" + LAMBDA_S3_BUCKET + "/" + LAMBDA_S3_KEY)
logging.info("SHMETRICS_CONFIG: %s" % SHMETRICS_CONFIG)
logging.info("-----------")

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

def get_insight_config_s3(LAMBDA_S3_BUCKET, LAMBDA_S3_KEY, SHMETRICS_CONFIG):

    # Get the insight configuration from S3
    s3 = boto3.client("s3")
    try:
        logging.info("Getting insight configuration from S3 (%s) and writing to %s" % (LAMBDA_S3_CONFIG,SHMETRICS_CONFIG))
        #s3.download_file(LAMBDA_S3_BUCKET, LAMBDA_S3_PREFIX + "/" + LAMBDA_S3_KEY, SHMETRICS_CONFIG)
        s3.download_file("193203723632-shmetrics-lambda", "config/insights.json", "insights.json")
    except Exception as e:
        logging.error("ERROR: Failed to download configuration file from S3:", str(e))

    #check to make sure the config file actually exists before declaring we're good
    if not os.path.isfile("insights.json"):
        logging.info("Configuration file %s does not exist in the working directory" % SHMETRICS_CONFIG)
        raise Exception("Configuration file %s does not exist in the working directory" % SHMETRICS_CONFIG)

# Main function
def insight_gatherer(SHMETRICS_CONFIG=SHMETRICS_CONFIG, CONSOLE_OUTPUT=CONSOLE_OUTPUT, CWM_OUTPUT=CWM_OUTPUT, CWL_OUTPUT=CWL_OUTPUT, CWL_GROUPNAME=CWL_GROUPNAME, CWL_STREAM=CWL_STREAM, CWM_NAMESPACE=CWM_NAMESPACE):

    # Get Data from Security Hub
    # Create a session using your AWS credentials
    session = boto3.Session()

    # create a client to talk to securityhub
    shclient = session.client("securityhub")

    # Open and read the JSON file
    with open(SHMETRICS_CONFIG, "r") as file:
        logging.info("Loading insight check list from file %s" % SHMETRICS_CONFIG)
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
            "Result from get_insight_results for %s - %s" % (insight["arn"], response)
        )

        for result in response["InsightResults"]["ResultValues"]:
            logging.debug(
                "%s -> %s" % (result["GroupByAttributeValue"], result["Count"])
            )

            # Populate the stats dictionary with the count of findings for each severity level
            insight_data[result["GroupByAttributeValue"]] = result["Count"]

            logging.debug("Stats: %s" % insight_data)

        # Deal with CloudWatch Metrics
        if CONSOLE_OUTPUT.lower() == "true" or CONSOLE_OUTPUT is True:
            logging.info("- Outputting data to console...")
            print(json.dumps(insight_data, indent=4))
        else:
            logging.debug("- Skipping Console output")

        if CWM_OUTPUT.lower() == "true" or CWM_OUTPUT is True:
            logging.info("- Sending metrics to CloudWatch metrics...")
            logging.debug(insight_data)
            put_cwmetrics_data(CWM_NAMESPACE, insight_data, session)
        else:
            logging.debug("- Skipping CloudWatch Metrics output")

        if CWL_OUTPUT.lower() == "true" or CWL_OUTPUT is True:
            logging.info("- Sending logs to CloudWatch Logs...")
            logging.debug(insight_data)
            put_cwl_data(CWL_GROUPNAME, CWL_STREAM, insight_data, session)
        else:
            logging.debug("- Skipping CloudWatch Logs output")


def lambda_handler(event, context):
    get_insight_config_s3(LAMBDA_S3_BUCKET, LAMBDA_S3_KEY, SHMETRICS_CONFIG)
    insight_gatherer()