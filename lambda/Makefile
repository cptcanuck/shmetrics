PROJECT = shmetrics
FUNCTION = $(PROJECT)
AWSACCOUNT = 193203723632
S3BUCKET = 193203723632-${PROJECT}-lambda
REGION = us-east-1
ENVCHAIN = toddco
SHMETRICS_DEPLOY_PROFILE = shmetrics-deploy

# Define the directories or files to format and lint
SRC_DIRS = .

# Command to run black
BLACK_CMD = black $(SRC_DIRS)
# Command to run flake8
FLAKE8_CMD = flake8 --ignore=E501 $(SRC_DIRS)

all: build

.PHONY: clean build deploy

clean:
	rm -rf build

build: clean
	mkdir -p build/site-packages
	zip -r build/$(FUNCTION).zip . -x "*.DS_Store*" "*.git*" "build*" "Makefile" "requirements.txt"
	python3 -m venv build/$(FUNCTION)
	. build/$(FUNCTION)/bin/activate; \
	pip3 install  -r requirements.txt; \
	cp -r $$VIRTUAL_ENV/lib/python3.12/site-packages/ build/site-packages
	cd build/site-packages; zip -g -r ../$(FUNCTION).zip . -x "*__pycache__*"

deploy-s3: build
	aws s3 cp build/$(FUNCTION).zip s3://${S3BUCKET}/deploy/$(FUNCTION)-LATEST.zip --profile ${SHMETRICS_DEPLOY_PROFILE}

deploy: build
	aws lambda update-function-code \
		--region=$(REGION) \
		--function-name $(FUNCTION) \
		--zip-file fileb://build/$(FUNCTION).zip \
		--publish

# Target to format code
format:
	$(BLACK_CMD)
	$(FLAKE8_CMD)