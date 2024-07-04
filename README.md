# shmetrics
Security Hub Metrics Thingy


## CloudFormation for insights
    *  aws cloudformation create-stack --stack-name "SH-Insights" --template-body file:///workspaces/shmetrics/sechub-insights-cfn.yaml
    *  aws cloudformation update-stack --stack-name SH-Insights --template-body file:///workspaces/shmetrics/sechub-insights-cfn.yaml
    *  aws cloudformation describe-stacks --stack-name SH-Insights
    *  aws cloudformation delete-stack --stack-name SH-Insights

## CloudFormation for s3 bucket - first

    * aws cloudformation create-stack --stack-name "SHmetrics-Lambda-s3" --template-body file:///workspaces/shmetrics/cfnv2lambda/Resources-s3.yml --profile shmetrics-deploy
    * aws cloudformation describe-stacks --stack-name SHmetrics-Lambda-s3 --profile shmetrics-deploy
    * aws cloudformation update-stack --stack-name SHmetrics-Lambda-s3 --template-body file:///workspaces/shmetrics/cfnv2lambda/Resources-s3.yml


## Lambda and related resources
    * aws cloudformation create-stack --stack-name "SHmetrics-Lambda" --template-body file:///workspaces/shmetrics/cfnv2lambda/Resources.yml --capabilities CAPABILITY_NAMED_IAM
    * aws cloudformation update-stack --stack-name "SHmetrics-Lambda" --template-body file:///workspaces/shmetrics/cfnv2lambda/Resources.yml --capabilities CAPABILITY_NAMED_IAM --profile shmetrics-deploy
    * aws cloudformation describe-stacks --stack-name SHmetrics-Lambda
    * aws cloudformation delete-stack --stack-name SHmetrics-Lambda --profile shmetrics-deploy
