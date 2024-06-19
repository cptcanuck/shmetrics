# shmetrics
Security Hub Metrics Thingy


## CloudFormation run
    *  aws cloudformation create-stack --stack-name "SH-Insights" --template-body file:///workspaces/shmetrics/sechub-insights-cfn.yaml
    *  aws cloudformation describe-stacks --stack-name SH-Insights
    *  aws cloudformation delete-stacks --stack-name SH-Insights
