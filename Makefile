.PHONY: *

pre-commit:
	pre-commit install
	pre-commit autoupdate

isort:
	isort yatracker --profile black
	isort tests --profile black

black:
	black yatracker
	black tests

mypy:
	mypy -p yatracker

flake8:
	flake8 yatracker
	flake8 tests

pylint:
	pylint yatracker
	pylint tests

lint: isort black pylint flake8 mypy
