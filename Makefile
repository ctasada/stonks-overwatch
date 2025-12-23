# Makefile for Django project with Poetry, Docker, and Briefcase support
# Use 'make help' to see all available targets

# GNU Make check (fail early if not GNU Make)
ifeq ($(origin MAKE_VERSION), undefined)
$(error This Makefile requires GNU Make. Please install and use GNU Make.)
endif

# Shell configuration
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Make configuration
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:

#==============================================================================
# Project Configuration
#==============================================================================

PYTHON_VERSION := 3.13
PROJECT_NAME := stonks-overwatch
SRC_DIR := src
WHEEL_DIR := ./wheels
STATIC_DIR := $(SRC_DIR)/stonks_overwatch/static
NODE_MODULES_DIR := $(SRC_DIR)/node_modules
MANAGE_PY := $(SRC_DIR)/manage.py

# Runtime flags (can be overridden via command line)
DEBUG_MODE := $(if $(debug),true,false)
PROFILE_MODE := $(if $(profile),true,false)
DEMO_MODE := $(if $(demo),true,false)

# Export variables for child processes
export DEBUG_MODE PROFILE_MODE DEMO_MODE

#==============================================================================
# CI/CD Configuration
#==============================================================================

ACT_ARCH := linux/arm64
ACT_PLATFORM := macos-latest=self-hosted
WORKFLOWS_DIR := .github/workflows

#==============================================================================
# Color Codes
#==============================================================================

BOLD := \033[1m
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
RESET := \033[0m

#==============================================================================
# PHONY Targets
#==============================================================================

.PHONY: help install update clean
.PHONY: lint lint-check lint-fix markdown-check markdown-fix license-check generate-third-party check-dependencies scan
.PHONY: migrate collectstatic runserver start run test coverage
.PHONY: docker-build docker-run docker-shell docker-clean
.PHONY: briefcase-create briefcase-update briefcase-run briefcase-package briefcase-clean
.PHONY: generate-images cicd cicd-restore pre-commit-install pre-commit-run pre-commit-update
.PHONY: _check-poetry _check-node _check-docker _check-act _create-wheels

#==============================================================================
# Help and Information
#==============================================================================

help: ## Show this help message
	@echo -e "$(BOLD)$(BLUE)Available targets:$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "$(BOLD)Usage:$(RESET)\n  make $(CYAN)<target>$(RESET)\n\n$(BOLD)Targets:$(RESET)\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(BOLD)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo -e "$(BOLD)Examples:$(RESET)"
	@echo -e "  make install                    # Install dependencies"
	@echo -e "  make runserver debug=true       # Run server in debug mode"
	@echo -e "  make test                       # Run tests"
	@echo -e "  make docker-run                 # Build and run with Docker"
	@echo -e "  make cicd workflow=package target=deb  # Test deb build locally"
	@echo -e "  make cicd-restore                     # Restore environment after cicd"

#==============================================================================
##@ Development Environment
#==============================================================================

install: ## Install all dependencies (including optional dependencies for native apps)
	@echo -e  "$(BOLD)$(GREEN)Installing dependencies...$(RESET)"
	poetry install --no-root --all-extras
	poetry run python $(SRC_DIR)/manage.py npminstall

update: ## Update all dependencies
	@echo -e "$(BOLD)$(YELLOW)Updating dependencies...$(RESET)"
	cd $(SRC_DIR) && npm update
	poetry self update
	poetry update
	$(MAKE) generate-third-party

clean: ## Clean temporary files and caches
	@echo -e "$(BOLD)$(YELLOW)Cleaning temporary files...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf $(WHEEL_DIR) build dist
	rm -rf $(STATIC_DIR)
	rm -rf $(NODE_MODULES_DIR)

#==============================================================================
##@ Code Quality
#==============================================================================

lint: lint-check ## Alias for lint-check

lint-check: ## Check code style and quality
	@echo -e "$(BOLD)$(BLUE)Checking code style...$(RESET)"
	poetry run ruff check .

lint-fix: ## Fix code style issues automatically
	@echo -e "$(BOLD)$(GREEN)Fixing code style issues...$(RESET)"
	poetry run ruff check . --fix
	poetry run ruff format .

markdown-check: ## Check Markdown files for style issues
	@echo -e "$(BOLD)$(BLUE)Checking Markdown files...$(RESET)"
	poetry run pymarkdown --config=pyproject.toml scan -r README.md CHANGELOG.md ./docs

markdown-fix: ## Fix Markdown files automatically
	@echo -e "$(BOLD)$(GREEN)Fixing Markdown files...$(RESET)"
	poetry run pymarkdown --config=pyproject.toml fix -r README.md CHANGELOG.md ./docs

license-check: ## Check license compatibility
	@echo -e "$(BOLD)$(BLUE)Checking license compatibility...$(RESET)"
	poetry run licensecheck

generate-third-party: ## Generate third-party licenses file
	@poetry run python scripts/generate_licenses.py

check-dependencies: ## Check for dependency issues
	@echo -e "$(BOLD)$(BLUE)Checking dependencies...$(RESET)"
	poetry run deptry .

scan: ## Run security scans
	@echo -e "$(BOLD)$(BLUE)Running security scans...$(RESET)"
	poetry run bandit -c pyproject.toml -ll -r .

#==============================================================================
##@ Database Operations
#==============================================================================

migrate: ## Apply database migrations
	@echo -e "$(BOLD)$(GREEN)Applying database migrations...$(RESET)"
	poetry run python $(MANAGE_PY) makemigrations
	poetry run python $(MANAGE_PY) migrate

#==============================================================================
##@ Django Operations
#==============================================================================

npminstall: _check-node ## Install Node.js dependencies
	@echo -e "$(BOLD)$(GREEN)Installing Node.js dependencies...$(RESET)"
	poetry run python $(MANAGE_PY) npminstall

collectstatic: npminstall ## Collect static files
	@echo -e "$(BOLD)$(BLUE)Collecting static files...$(RESET)"
	rm -rf $(STATIC_DIR)
	poetry run python $(MANAGE_PY) collectstatic --noinput

runserver: ## Run Django development server (supports debug=true, profile=true, demo=true)
	@echo -e "$(BOLD)$(GREEN)Starting Django development server...$(RESET)"
	@echo -e "$(YELLOW)Debug mode: $(DEBUG_MODE)$(RESET)"
	@echo -e "$(YELLOW)Profile mode: $(PROFILE_MODE)$(RESET)"
	@echo -e "$(YELLOW)Demo mode: $(DEMO_MODE)$(RESET)"
	poetry run python $(MANAGE_PY) runserver

start: install collectstatic migrate runserver ## Full setup: install, collect static, migrate, and run server

run: start ## Alias for start

#==============================================================================
##@ Testing
#==============================================================================

test: ## Run tests
	@echo -e "$(BOLD)$(GREEN)Running tests...$(RESET)"
	poetry run pytest

coverage: ## Run tests with coverage report
	@echo -e "$(BOLD)$(GREEN)Running tests with coverage...$(RESET)"
	poetry run pytest --cov=$(SRC_DIR)/stonks_overwatch --cov-report=html --cov-report=term-missing
	@echo -e "$(BOLD)$(GREEN)Coverage report generated in htmlcov/index.html$(RESET)"

#==============================================================================
##@ Docker Operations
#==============================================================================

docker-build: _check-docker ## Build Docker images
	@echo -e "$(BOLD)$(BLUE)Building Docker images...$(RESET)"
	docker compose build

docker-run: docker-build ## Build and run Docker containers
	@echo -e "$(BOLD)$(GREEN)Starting Docker containers...$(RESET)"
	docker compose up

docker-shell: docker-build ## Open shell in Docker container
	@echo -e "$(BOLD)$(BLUE)Opening shell in Docker container...$(RESET)"
	docker run -it --rm $(PROJECT_NAME) sh

docker-clean: ## Clean Docker images and containers
	@echo -e "$(BOLD)$(YELLOW)Cleaning Docker resources...$(RESET)"
	docker compose down --remove-orphans
	docker system prune -f

#==============================================================================
##@ Briefcase Operations
#==============================================================================

# Helper shell function to map target to platform and output_format
# This function is defined inline in each target that needs it
define _get_briefcase_args
	case "$(target)" in \
		flatpak) \
			platform="Linux"; \
			output_format="Flatpak"; \
			;; \
		macos) \
			platform="macos"; \
			output_format="app"; \
			;; \
		windows) \
			platform="windows"; \
			output_format="app"; \
			;; \
		*) \
			echo -e "$(RED)Error: Invalid target '$(target)'. Valid targets: macos, windows, flatpak$(RESET)"; \
			exit 1; \
			;; \
	esac
endef

_create-wheels: ## Internal: Create wheel files for Briefcase
	@echo -e "$(BOLD)$(BLUE)Creating wheel files...$(RESET)"
	rm -rf $(WHEEL_DIR)
	@packages="peewee>=3.18.2 ibind>=0.1.18"; \
	for pkg in $$packages; do \
	  poetry run pip wheel "$$pkg" --wheel-dir $(WHEEL_DIR); \
	done; \
	for pkg in peewee ibind; do \
	  for f in $(WHEEL_DIR)/$$pkg-*-cp*-*.whl; do \
	    if [ -f "$$f" ]; then \
	      version=$$(echo $$f | sed -E "s|.*$$pkg-([0-9.]+)-cp[0-9]+.*\\.whl|\\1|"); \
	      new_name="$$pkg-$${version}-py3-none-any.whl"; \
	      echo -e "$(YELLOW)Renaming $$(basename $$f) to $$new_name$(RESET)"; \
	      mv "$$f" "$(WHEEL_DIR)/$$new_name"; \
	    fi; \
	  done; \
	done

briefcase-create: install collectstatic _create-wheels ## Create Briefcase project (supports target=macos|windows|flatpak)
	@echo -e "$(BOLD)$(GREEN)Creating Briefcase project...$(RESET)"
	@if [ -n "$(target)" ]; then \
		$(_get_briefcase_args); \
		echo -e "$(YELLOW)Target: $(target) (platform: $$platform, output-format: $$output_format)$(RESET)"; \
		rm -rf build; \
		poetry run briefcase create $$platform $$output_format; \
		poetry run briefcase build $$platform $$output_format; \
	else \
		rm -rf build; \
		poetry run briefcase create; \
		poetry run briefcase build; \
	fi

briefcase-update: install collectstatic _create-wheels ## Update Briefcase project (supports target=macos|windows|flatpak)
	@echo -e "$(BOLD)$(YELLOW)Updating Briefcase project...$(RESET)"
	@if [ -n "$(target)" ]; then \
		$(_get_briefcase_args); \
		echo -e "$(YELLOW)Target: $(target) (platform: $$platform, output-format: $$output_format)$(RESET)"; \
		poetry run briefcase update $$platform $$output_format; \
		poetry run briefcase build $$platform $$output_format; \
	else \
		poetry run briefcase update; \
		poetry run briefcase build; \
	fi

briefcase-run: ## Run Briefcase project (supports debug=true, profile=true, demo=true, target=macos|windows|flatpak)
	@echo -e "$(BOLD)$(GREEN)Running Briefcase project...$(RESET)"
	@if [ -n "$(target)" ]; then \
		$(_get_briefcase_args); \
		poetry run briefcase run $$platform $$output_format; \
	else \
		poetry run briefcase run; \
	fi

briefcase-package: briefcase-create ## Package Briefcase project (supports target=macos|windows|flatpak)
	@echo -e "$(BOLD)$(BLUE)Packaging Briefcase project...$(RESET)"
	@if [ -n "$(target)" ]; then \
		$(_get_briefcase_args); \
		echo -e "$(YELLOW)Packaging for target: $(target) (platform: $$platform, output-format: $$output_format)$(RESET)"; \
		poetry run briefcase package $$platform $$output_format --update --adhoc-sign --no-input; \
	else \
		poetry run briefcase package --update --adhoc-sign --no-input; \
	fi

briefcase-clean: ## Clean Briefcase build artifacts
	@echo -e "$(BOLD)$(YELLOW)Cleaning Briefcase build artifacts...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info/ logs/ wheels/
	poetry run pip uninstall stonks-overwatch -y || true
	poetry run pip cache purge || true
	@if [ "$$(uname)" == "Darwin" ]; then \
		rm -rf "$(HOME)/Library/Application Support/com.caribay.stonks_overwatch"; \
		rm -rf "$(HOME)/Library/Preferences/com.caribay.stonks_overwatch"; \
		rm -rf "$(HOME)/Library/Logs/com.caribay.stonks_overwatch"; \
		rm -rf "$(HOME)/Library/Caches/com.caribay.stonks_overwatch"; \
	elif [ "$$(uname)" == "Linux" ]; then \
		rm -rf "$(HOME)/.var/app/com.caribay.stonks_overwatch"; \
		rm -rf "$(HOME)/.local/share/stonks_overwatch"; \
	else \
		echo -e "$(RED)Some files are not deleted. This target doesn't support this OS.$(RESET)"; \
	fi

#==============================================================================
##@ Asset Generation
#==============================================================================

generate-images: ## Generate images for browsers and Briefcase
	@echo -e "$(BOLD)$(BLUE)Generating images...$(RESET)"
	@if [ -f "scripts/generate-icons.sh" ]; then \
		chmod +x scripts/generate-icons.sh; \
		./scripts/generate-icons.sh; \
	else \
		echo -e "$(RED)Error: scripts/generate-icons.sh not found$(RESET)"; \
		exit 1; \
	fi

#==============================================================================
##@ Git Hooks
#==============================================================================

pre-commit-install: ## Install pre-commit hooks
	@echo -e "$(BOLD)$(GREEN)Installing pre-commit hooks...$(RESET)"
	poetry run pre-commit install

pre-commit-run: ## Run pre-commit hooks on all files
	@echo -e "$(BOLD)$(BLUE)Running pre-commit hooks...$(RESET)"
	poetry run pre-commit run --all-files

pre-commit-update: ## Update pre-commit hook versions
	@echo -e "$(BOLD)$(YELLOW)Updating pre-commit hooks...$(RESET)"
	poetry run pre-commit autoupdate

#==============================================================================
##@ CI/CD Operations
#==============================================================================

cicd: _check-docker _check-act ## Run CI/CD pipeline (use job=<name> or workflow=<name>)
	@echo -e  "$(BOLD)$(BLUE)Running CI/CD pipeline...$(RESET)"
	@if [ -n "$(workflow)" ]; then \
		echo -e "$(YELLOW)Running workflow: $(workflow)$(RESET)"; \
		act -W "$(WORKFLOWS_DIR)/$(workflow).yml" --container-architecture $(ACT_ARCH) -P $(ACT_PLATFORM); \
	elif [ -n "$(job)" ]; then \
		echo -e "$(YELLOW)Running job: $(job)$(RESET)"; \
		act --job $(job) --container-architecture $(ACT_ARCH) -P $(ACT_PLATFORM); \
	else \
		echo -e "$(YELLOW)Available jobs and workflows:$(RESET)"; \
		act --list --container-architecture $(ACT_ARCH); \
		echo -e "$(YELLOW)Use 'make cicd job=<jobId>' or 'make cicd workflow=<workflowFile>' to run specific jobs or workflows$(RESET)"; \
	fi

#==============================================================================
# Internal Utilities
#==============================================================================

_check-poetry:
	@command -v poetry >/dev/null 2>&1 || (echo -e "$(RED)Error: Poetry not found. Please install Poetry first.$(RESET)" && exit 1)

_check-docker:
	@docker info > /dev/null 2>&1 || (echo -e "$(RED)Error: Docker is not running$(RESET)" && exit 1)

_check-node:
	@command -v node >/dev/null 2>&1 || (echo -e "$(RED)Error: Node.js not found. Please install Node.js first.$(RESET)" && exit 1)
	@command -v npm >/dev/null 2>&1 || (echo -e "$(RED)Error: npm not found. Please install npm first.$(RESET)" && exit 1)

_check-act:
	@command -v act >/dev/null 2>&1 || (echo -e "$(RED)Error: 'act' not found. Install 'nektos/act' to run workflows locally: https://github.com/nektos/act$(RESET)" && exit 1)
