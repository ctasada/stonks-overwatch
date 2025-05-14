.PHONY: install update lint-check lint-fix migrate runserver start run test docker-build docker-run help

ifneq ($(debug),)
    DEBUG_MODE = true
else
    DEBUG_MODE = false
endif

ifneq ($(profile),)
    PROFILE_MODE = true
else
    PROFILE_MODE = false
endif


# Export the variable for child processes
export DEBUG_MODE
export PROFILE_MODE

install: ## Install dependencies
	poetry install
	poetry run src/manage.py npminstall

update: ## Update dependencies
	cd src && npm update
	poetry self update
	poetry update

lintcheck: ## Check code style
	poetry run ruff check

lintfix: ## Fix code style issues
	poetry run ruff check --fix

licensecheck: ## Checks the licenses are compatible
	poetry run licensecheck

generate-third-party: ## Generate third-party licenses file
	poetry run pip-licenses --format=plain-vertical --with-license-file --no-license-path --output-file=THIRD_PARTY_LICENSES.txt

migrate: ## Apply database migrations
	poetry run src/manage.py makemigrations
	poetry run src/manage.py migrate

collectstatic:
	rm -rdf src/stonks_overwatch/static
	poetry run src/manage.py collectstatic

runserver: ## Run the Django development server. Supports `make runserver debug=true profile=true` to run in debug or profile mode
	DEBUG_MODE="$(DEBUG_MODE)" PROFILE_MODE="$(PROFILE_MODE)" poetry run src/manage.py runserver

start: install collectstatic migrate runserver ## Install dependencies, apply migrations, and run the server

run: start ## Alias for start

test: ## Run tests with coverage report
	poetry run pytest --cov --cov-report html

docker-build: ## Build Docker images
	docker compose build

docker-run: docker-build ## Build and run Docker containers
	docker compose up

docker-shell: docker-build
	docker run -it --rm stonks-overwatch sh

update-package-images: ## Update package images used by Briefcase
	src/scripts/generate-icons.sh

cicd: ## Run CI/CD pipeline. Indicate the job you want to run with `make cicd job=<job_name>`. If no job is specified, it will list all available jobs.
	@if [ -z "$(job)" ]; then \
		act --list; \
	else \
		act --job $(job) --container-architecture linux/arm64; \
	fi

help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)