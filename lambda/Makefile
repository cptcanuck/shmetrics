PROJECT = shmetrics
FUNCTION = $(PROJECT)
AWSACCOUNT = 193203723632
S3BUCKET = ${AWSACCOUNT}-${PROJECT}-lambda
REGION = us-east-1
ENVCHAIN = toddco
SHMETRICS_DEPLOY_PROFILE = shmetrics-deploy

# Define the directories or files to format and lint
SRC_DIRS = .

# Command to run black
BLACK_CMD = black $(SRC_DIRS)
# Command to run flake8
FLAKE8_CMD = flake8 --ignore=E501 $(SRC_DIRS) --exclude .git,__pycache__,build,dist,venv


all: build

.PHONY: clean build deploy

clean:
	rm -rf build

build:
	mkdir -p build/site-packages
	zip -r build/$(FUNCTION).zip . -x "*.DS_Store*" "*.git*" "build*" "Makefile" "requirements.txt"
	python3 -m venv build/$(FUNCTION)
	. build/$(FUNCTION)/bin/activate; \
	pip3 install  -r requirements.txt; \
	cp -r $$VIRTUAL_ENV/lib/python3.12/site-packages/ build/site-packages
	cd build/site-packages; zip -g -r ../$(FUNCTION).zip . -x "*__pycache__*"

deploy-s3: 
	aws s3 cp build/$(FUNCTION).zip s3://${S3BUCKET}/deploy/$(FUNCTION)-LATEST.zip --profile ${SHMETRICS_DEPLOY_PROFILE}

deploy: build deploy-s3
	aws lambda update-function-code \
		--region=$(REGION) \
		--function-name $(FUNCTION)-lambda \
		--s3-bucket ${S3BUCKET} \
		--s3-key deploy/$(FUNCTION)-LATEST.zip \
		--publish \
		--profile ${SHMETRICS_DEPLOY_PROFILE}

distrib: deploy-s3
	aws lambda update-function-code \
		--region=$(REGION) \
		--function-name $(FUNCTION)-lambda \
		--s3-bucket ${S3BUCKET} \
		--s3-key deploy/$(FUNCTION)-LATEST.zip \
		--publish \
		--profile ${SHMETRICS_DEPLOY_PROFILE}

test:
	python-lambda-local -t 30 -f lambda_handler -e tests/python-lambda-local/env.json main.py tests/python-lambda-local/test_event.json

# Target to format code
format:
	$(BLACK_CMD)
	$(FLAKE8_CMD)
