.PHONY: install update lint-check lint-fix migrate runserver

ifneq ($(debug),)
    DEBUG_MODE = true
else
    DEBUG_MODE = false
endif

# Export the variable for child processes
export DEBUG_MODE

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
	@if [ "$(DEBUG_MODE)" = "true" ]; then \
		STONKS_LOG_LEVEL=DEBUG poetry run src/manage.py runserver; \
	else \
  		poetry run src/manage.py runserver; \
	fi

start: install migrate runserver

run: start

docker-build:
	docker compose build

docker-run: docker-build
	docker compose up