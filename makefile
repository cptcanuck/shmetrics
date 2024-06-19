.PHONY: format lint

# Define the directories or files to format and lint
SRC_DIRS = .

# Command to run black
BLACK_CMD = black $(SRC_DIRS)

# Command to run flake8
FLAKE8_CMD = flake8 --ignore=E501 $(SRC_DIRS)

# Target to format code
format:
	$(BLACK_CMD)
	$(FLAKE8_CMD)

