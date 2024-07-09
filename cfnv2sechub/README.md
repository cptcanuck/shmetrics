## CloudFormation for insights

    *  aws cloudformation create-stack --stack-name "SH-Insights" --template-body file:///workspaces/shmetrics/sechub-insights-cfn.yaml
    *  aws cloudformation update-stack --stack-name SH-Insights --template-body file:///workspaces/shmetrics/sechub-insights-cfn.yaml
    *  aws cloudformation describe-stacks --stack-name SH-Insights
    *  aws cloudformation delete-stack --stack-name SH-Insights
