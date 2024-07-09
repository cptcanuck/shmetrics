PROJECT = shmetrics
FUNCTION = $(PROJECT)
AWSACCOUNT = 193203723632
S3BUCKET = ${AWSACCOUNT}-${PROJECT}-lambda
REGION = us-east-1
ENVCHAIN = toddco
SHMETRICS_DEPLOY_PROFILE = shmetrics-deploy
CONFIGFILE=insights.json

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
	#run python script to generate insights.json

deploy-insights:
	aws cloudformation update-stack --stack-name SHmetrics-Lambda-s3 --template-body file:///workspaces/shmetrics/cfnv2lambda/Resources-s3.yml --profile shmetrics-deploy



deploy-s3: 
	aws s3 cp $(CONFIGFILE) s3://${S3BUCKET}/config/$(CONFIGFILE) --profile ${SHMETRICS_DEPLOY_PROFILE}

deploy: build deploy-s3

# Target to format code
format:
	$(BLACK_CMD)
	$(FLAKE8_CMD)
