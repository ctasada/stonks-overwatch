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

WHEEL_DIR := ./wheels

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
	@packages=$$(poetry show --only=main | awk '{print $$1}'); \
	poetry run pip-licenses --packages $$packages

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
	poetry run pytest

docker-build: ## Build Docker images
	docker compose build

docker-run: docker-build ## Build and run Docker containers
	docker compose up

docker-shell: docker-build
	docker run -it --rm stonks-overwatch sh

_create-wheels:
	rm -rdf ./wheels
	poetry run pip wheel "peewee>=3.16.2" --wheel-dir $(WHEEL_DIR)
	# This is a hack to rename the wheel so Briefcase doesn't complain
	@for f in $(WHEEL_DIR)/peewee-*-cp*-*.whl; do \
		version=$$(echo $$f | sed -E 's|.*peewee-([0-9.]+)-cp[0-9]+.*\.whl|\1|'); \
		new_name="peewee-$${version}-py3-none-any.whl"; \
		echo "Renaming $$f to $(WHEEL_DIR)/$$new_name"; \
		mv "$$f" "$(WHEEL_DIR)/$$new_name"; \
	done

briefcase-create: install collectstatic _create-wheels ## Create a new Briefcase project
	rm -rdf build
	poetry run briefcase create
	poetry run briefcase build

briefcase-update: install collectstatic _create-wheels ## Update the Briefcase project
	poetry run briefcase update
	poetry run briefcase build

briefcase-run: ## Run the Briefcase project
	poetry run briefcase run

briefcase-package: briefcase-create ## Packages the Briefcase project
	poetry run briefcase package --update --adhoc-sign --no-input

generate-images: ## Generates images to be used by the browsers and Briefcase
	scripts/generate-icons.sh

cicd: ## Run CI/CD pipeline. Indicate the job you want to run with `make cicd job=<job_name>` or `make cicd workflow=<workflow_name>. If no job is specified, it will list all available jobs.
	@if [ -n "$(workflow)" ]; then \
    	act -W ".github/workflows/$(workflow).yml" --container-architecture linux/arm64 -P macos-latest=self-hosted; \
    elif [ -n "$(job)" ]; then \
	  	act --job $(job) --container-architecture linux/arm64 -P macos-latest=self-hosted; \
	else \
		act --list; \
	fi

help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)