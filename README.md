# shmetrics
Security Hub Metrics Thingy

## What is this?

I needed a way to get finding data from Security Hub into a system we could build dashboards and metrics and alarms and trends on.

## How is this?

I settled on making (Security Hub Insights)[https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-insights.html], which you can (query)[https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/securityhub/client/get_insights.html#] to get something like:

```
$ aws securityhub get-insight-results --insight-arn ${CHECKARN} --query 'InsightResults.ResultValues' --output text
9  MEDIUM
8   HIGH
7    LOW
6     INFORMATIONAL
5     CRITICAL
``` 

SecurityHub doesn't expose the metrics/views that build its console - those are all derived from the same APIs anc calculated in the UI.  So we need to get stats, then do something with them.

So before we can get any metrics, we need to create an Insight that matches the metrics we're looking for.  This can be done with CFN (see `cfnv2sechub/sechub-insights-cfn.yaml`), which deploys
the insight.  You can also clickops insights if you'd rather.  For this tool and at this point in the development, I deploy the CFN, then I run `cfnv2sechub/generate-insights.py` which gets
the outputs from the CFN stacks that include the key details (ARN, check ID, description, name) and writes them to a config file (insights.json).  We'll refernce that in a minute.


Once insights exist, they can be queried, so we move on to our lambda.  The lambda is created, with associated resources, by deploying the two stack sets in `/cfnv2lambda`:

Note: these will need to be updated to reference whatever S3 bucket you use - the files are currently setup referencing an example bucket.

  * aws cloudformation create-stack --stack-name "SHmetrics-Lambda-s3" --template-body file:///workspaces/shmetrics/cfnv2lambda/Resources-s3.yml
  * aws cloudformation create-stack --stack-name "SHmetrics-Lambda" --template-body file:///workspaces/shmetrics/cfnv2lambda/Resources.yml --capabilities CAPABILITY_NAMED_IAM

This wil create the s3 bucket required to store the lambda zip file.  Then you need to build and deploy the lambda into that S3 bucket (See below for more details).  

Then you deploy the Lambda and configuration with the `SHMetrics-Lambda` stack, which points to the zipfile you uploaded.

The lambda will then run hourly, gathering the metrics from the insights, then pushing the results to whichever of the 3 outputs you chose and set via environment variable:

  * Console - write the metrics to STDOUT
  * CloudWatch Metrics - push metrics to CWM, using the configured namespace
  * CloudWatch Logs - push a logline with the metric data to CWL for consumption by other services

From there, you can use the data however you wish.


## Developing

There's a devcontainer, which if you open this project in vscode should give you a useful dev envt.

There's a Makefile in each directory that supports the common operations like `build` and `deploy`

You will need to setup your AWS envrionment with at least a faily privileged IAM user with keys, so that you can run the CFN and lambda deploys.

### Building

There is a Makefile provided within `/lambda` which supports `make build` that will build the project and create a zipfile for distribution
