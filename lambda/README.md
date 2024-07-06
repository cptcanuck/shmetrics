# testing lambda on command line

* `python-lambda-local -t 30 -f lambda_handler -e tests/python-lambda-local/env.json main.py tests/python-lambda-local/test_event.json`

* `aws lambda get-function --function-name shmetrics-lambda --profile shmetrics-deploy`