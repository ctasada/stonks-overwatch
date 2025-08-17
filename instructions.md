# Project Overview

This project is a Python-based application that allows users to manage their investment portfolios across multiple brokers, including DEGIRO, Bitvavo, and IBKR.

## Project Setup
- Install [Poetry](https://python-poetry.org/) if not already installed.
- Run `poetry install` to install dependencies.
- Copy `config/config.json.template` to `config/config.json` and update as needed.
- Set up environment variables as described in `docs/Configuration-Integration.md`.
- To run the application:
  - For the web app: `poetry run python src/manage.py runserver`
  - For scripts: `poetry run python scripts/<script_name>.py`
- To run tests: `poetry run pytest`

## Folder Structure
- `config/`: Configuration files. Used only for local development.
- `data/`: Database, logs and data files
- `docs/`: Project documentation
- `scripts/`: Utility scripts
- `tests/`: Unit and integration tests
- `src/`: Main application code
- `src/icons/`: Folder with the icons to use in the local application
- `src/stonks_overwatch/`: Main application package
- `src/stonks_overwatch/app/`: Folder for the local application logic and UI. This folder mainly uses Toga for the UI.
- `src/stonks_overwatch/config/`: Configuration data for the different brokers
- `src/stonks_overwatch/core/`: Core logic of the application
- `src/stonks_overwatch/staticfiles/`: Static files for the web application. Includes icons, stylesheets, and JavaScript files.
- `src/stonks_overwatch/templates/`: Django HTML templates for the web application.
- `src/stonks_overwatch/utils/`: Utility functions and classes.
- `src/stonks_overwatch/views/`: Views for the web application.

## Coding Standards
- **Language:** Python 3.9+
- **Formatting:** Use [PEP8](https://www.python.org/dev/peps/pep-0008/) style. Auto-format with `ruff`.
- **Type Hints:** Use type annotations where possible.
- **Naming:**
  - Variables/functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`
- **Comments:** Write clear, concise docstrings for all public functions and classes.

## Libraries and Frameworks
- **Web Framework:** Django (for web application)
- **Database:** SQLite (default), can be changed to PostgreSQL or MySQL if needed
- **Asynchronous Tasks:** Celery (if needed for background tasks)
- **API Requests:** `requests` for HTTP requests
- **Data Processing:** `pandas` for data manipulation and analysis
- **Logging:** Use Python's built-in `logging` module for logging errors and information.
- **Environment Variables:** Use `python-dotenv` to manage environment variables in development.
- **Testing:** Use `pytest` for unit and integration tests.
- **Dependency Management:** Use [Poetry](https://python-poetry.org/) for managing project dependencies.
- **Linting:** Use `ruff` for linting the codebase.
- **HTML Framework:** Use Bootstrap for HTML widgets and styling.
- **UI Framework:** Use Toga for the native application UI.

## Best Practices
- Write tests for all new features and bug fixes.
- Handle exceptions gracefully and log errors.
- Use environment variables for secrets and credentials.
- Keep functions small and focused.
- Document all public APIs and modules.

## Copilot Usage
- Use Copilot to generate code, tests, and documentation following the standards above.
- Example prompts:
  - "Add a function to fetch account balance from the database."
  - "Write a pytest for the currency converter service."
  - "Document the Bitvavo integration module."
- Avoid using deprecated libraries or hardcoding secrets.
- Prefer modular, well-documented code and small, focused functions.

## Contribution Guidelines
- Fork the repository and create a feature branch.
- Write or update tests for all new features.
- Ensure all tests pass with `pytest` before submitting a PR.
- Open a pull request and request review.
- Follow the coding standards and best practices outlined above.

## Restrictions
- Do not use deprecated or unmaintained libraries.
- Avoid hardcoding secrets or credentials.
- Do not commit generated data or secrets to version control.
- Follow the existing project structure and conventions.

---
