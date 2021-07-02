pre-commit:
	pre-commit install
	pre-commit autoupdate

isort:
	isort . --profile black

black:
	black .

mypy:
	mypy -p yatracker

flake8:
	flake8 yatracker

lint: isort black mypy flake8

requirements:
	poetry export -E ultra --without-hashes -f requirements.txt -o requirements.txt
	poetry export -E ultra --without-hashes -f requirements.txt -o requirements_dev.txt --dev
