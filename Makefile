.PHONY: install update lint-check lint-fix migrate runserver

install:
	poetry install
	poetry run src/manage.py npminstall

update:
	npm update
	poetry self update
	poetry update

lintcheck:
	poetry run ruff check

lintfix:
	poetry run ruff check --fix

migrate:
	poetry run src/manage.py makemigrations
	poetry run src/manage.py migrate

runserver:
	poetry run src/manage.py runserver

start: install migrate runserver

run: start

docker-build:
	docker compose build

docker-run: docker-build
	docker compose up