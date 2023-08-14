.PHONY: *

pre-commit:
	pre-commit install
	pre-commit autoupdate

black:
	black yatracker
	black tests

mypy:
	mypy -p yatracker

ruff:
	ruff check yatracker --fix
	ruff check tests --fix

lint: ruff black
