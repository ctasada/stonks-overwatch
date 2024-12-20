.PHONY: install update migrate runserver

install:
	poetry install
	poetry run src/manage.py npminstall

update:
	npm update
	poetry update

migrate:
	poetry run src/manage.py makemigrations
	poetry run src/manage.py migrate

runserver:
	poetry run src/manage.py runserver

start: install migrate runserver

run: start