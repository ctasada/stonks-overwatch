.PHONY: install update lint-check lint-fix migrate runserver start run test docker-build docker-run help

ifneq ($(debug),)
    DEBUG_MODE = true
else
    DEBUG_MODE = false
endif

# Export the variable for child processes
export DEBUG_MODE

install: ## Install dependencies
	poetry install
	poetry run src/manage.py npminstall

update: ## Update dependencies
	npm update
	poetry self update
	poetry update

lintcheck: ## Check code style
	poetry run ruff check

lintfix: ## Fix code style issues
	poetry run ruff check --fix

migrate: ## Apply database migrations
	poetry run src/manage.py makemigrations
	poetry run src/manage.py migrate

runserver: ## Run the Django development server. Use `make runserver debug=true` to run in debug mode
	@if [ "$(DEBUG_MODE)" = "true" ]; then \
		DEBUG_MODE=true poetry run src/manage.py runserver; \
	else \
		poetry run src/manage.py runserver; \
	fi

start: install migrate runserver ## Install dependencies, apply migrations, and run the server

run: start ## Alias for start

test: ## Run tests with coverage report
	poetry run pytest --cov --cov-report html

docker-build: ## Build Docker images
	AVX2_ENABLED=$$(if [[ "$$(uname)" == "Linux" ]]; then grep -q 'avx2' /proc/cpuinfo && echo true || echo false; else arch | grep -q 'arm64' && echo true || echo false; fi); \
	export AVX2_ENABLED
	docker compose build

docker-run: docker-build ## Build and run Docker containers
	docker compose up

help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)