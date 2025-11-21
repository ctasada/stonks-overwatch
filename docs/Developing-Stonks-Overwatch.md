# Developing Stonks Overwatch

Stonks Overwatch is a portfolio tracker integrating with multiple brokers (DeGiro, Bitvavo, IBKR) using a **unified modern architecture** (2025). The system features factory patterns, dependency injection, interface-based design, and a centralized broker registry that dramatically simplifies development and maintenance.

## First Steps

The first step is to check out the code. It can be done with the GitHub CLI

```sh
gh repo clone ctasada/stonks-overwatch
```

or plain `git`

```sh
git clone ctasada/stonks-overwatch
```

You can execute `make start`, it will install and configure everything needed to run.

Alternatively, you can also use Docker

```shell
make docker-run
```

The application is available at [http://127.0.0.1:8000](http://127.0.0.1:8000) Open your browser in that URL.

If everything goes fine you should see a login screen for your configured brokers.

## Understanding the Modern Architecture (2025)

Before diving into development, it's important to understand the **unified broker architecture** that powers Stonks Overwatch:

### Key Components

- **BrokerRegistry**: Central registry managing all broker configurations and services
- **BrokerFactory**: Unified factory creating services with automatic dependency injection
- **Service Interfaces**: Type-safe contracts ensuring consistent broker implementations
- **Configuration System**: Registry-based configuration supporting multiple brokers

### For New Developers

If you're adding new features or brokers, familiarize yourself with:

1. **Broker Integration Guide**: `docs/BROKER_ARCHITECTURE.md` - Complete guide for adding new brokers
2. **Authentication System**: `docs/DEGIRO_AUTH_ARCHITECTURE.md` - Modern authentication patterns
3. **Architecture Overview**: `docs/ARCHITECTURE_IMPROVEMENTS.md` - System design and improvements

### Service Access Pattern

```python
# Modern service access (recommended)
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.service_types import ServiceType

factory = BrokerFactory()
portfolio_service = factory.create_service("degiro", ServiceType.PORTFOLIO)
```

## Start Developing

### IMPORTANT DEPENDENCIES

To develop the application, it's important to have installed in your system the next dependencies:

- Python 3.13
- Poetry 2.1

### With Docker

The application can run in docker, which will create all the needed dependencies in the container. In this case you only need to have a Docker daemon installed.

```shell
make docker-run
```

### Without Docker

```shell
make run
```

Executing this command should install all the dependencies and run the application

```shell
make help
```

Will show all the available commands. The `Makefile` provides convenient wrappers to simplify the work, check the code if you are interested in the internals.

The most relevant commands are:

### Debugging & Profiling

```shell
make run profile=true debug=true
```

Passing the parameter `profile=true` will enable profiling, and `debug=true` will log in debugging mode

Those parameters are optional, most of the time `make run` is enough

### Linting

```shell
make lint-check
make lint-fix
```

These commands will check the code linting or do the best effort to properly format the code

Make sure to execute `make pre-commit-install` to install the pre-commit hooks, so the code is automatically checked
before committing.

### Test

```shell
make test
```

Will execute the test suite, generating coverage report

### Working with the Modern Architecture

#### Debug Broker Services

```shell
# Check broker registration status
python manage.py shell
>>> from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
>>> registry = BrokerRegistry()
>>> print("Registered brokers:", registry.get_fully_registered_brokers())
>>> print("Broker capabilities:", {name: registry.get_broker_capabilities(name) for name in registry.get_registered_brokers()})
```

#### Test Service Creation

```python
# Verify service factory works correctly
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.service_types import ServiceType

factory = BrokerFactory()
for broker in ["degiro", "bitvavo", "ibkr"]:
    for service_type in [ServiceType.PORTFOLIO, ServiceType.TRANSACTION, ServiceType.ACCOUNT]:
        try:
            service = factory.create_service(broker, service_type)
            print(f"✅ {broker} {service_type.value}: {service}")
        except Exception as e:
            print(f"❌ {broker} {service_type.value}: {e}")
```

The demo database can use used with `make run demo=true`

```shell
make briefcase-package
```

Will create the installer locally. Only the installer for the operating system where the code is being executed will be created. For example, if you are working on macOS, only the macOS package will be created.

### Run the Native Application

```shell
make briefcase-run
```

As before, only the application for the current OS will be created and executed.

### CICD

```shell
make cicd
```

Will execute the GitHub Actions locally. It's a good way of validating changes in the CI/CD code

## Troubleshooting

```shell
make run profile=true debug=true
```

Passing the parameter `profile=true` will enable profiling, and `debug=true` will log in debugging mode.

The `debug=true` parameter is useful to see the logs in the console, but it will also generate a lot of output, so use it only when needed.
The provided information may help you to identify the problem.

To troubleshoot performance issues, you can use the `profile=true` parameter. This parameter enables [Pyinstrument](https://pyinstrument.readthedocs.io/en/latest/guide.html)
to help profiling the application. [Profile a web request in Django](https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-django)
provides the most up-to-date information on how to profile a web request in Django.

> TL;DR: Use `make run profile=true` and add `?profile` to the end of a request URL to activate the profiler

## Database and Configuration

### Create a new Database

```shell
poetry run python ./scripts/init_db.py --help
```

This command will create a new database with the initial data from your configured broker accounts (DeGiro, Bitvavo, IBKR).

> This script expects the `config/config.json` file to be present and properly configured with your broker credentials.

### Configuration File Format

The modern configuration supports multiple brokers:

```json
{
  "degiro": {
    "enabled": true,
    "credentials": {
      "username": "your_username",
      "password": "your_password"
    }
  },
  "bitvavo": {
    "enabled": true,
    "credentials": {
      "key": "your_api_key",
      "secret": "your_api_secret"
    }
  },
  "ibkr": {
    "enabled": false
  }
}
```

### Create a Demo Database

```shell
poetry run python ./scripts/generate_demo_db.py --help
```

This command will create a demo database with sample data for multiple brokers. It is useful for testing purposes or to showcase the application without needing real broker accounts.

> This script expects the `config/config.json` file to be present and properly configured.

The demo database can be used with `make run demo=true`

## Dump and Load a Database

```shell
poetry run python ./scripts/dump_db.py --help
poetry run python ./scripts/dump_db.py dump [--output filename.json]
poetry run python ./scripts/dump_db.py load --input filename.json
```

Allows dumping the current database to a file and loading it back. This is useful for testing purposes or to share the database with other developers.

### Offline Mode

The application can run in offline mode for any broker, without needing to connect to their APIs. This is useful for development and testing.

Example configuration to enable offline mode for multiple brokers:

```json
{
    "degiro": {
      "enabled": true,
      "offline_mode": true
    },
    "bitvavo": {
      "enabled": true,
      "offline_mode": true
    },
    "ibkr": {
      "enabled": true,
      "offline_mode": true
    }
}
```

The offline mode can be used together with `demo=true` to load the demo database and run the application without any external API calls.

### Broker-Specific Development

When developing features for specific brokers, you can selectively enable/disable them:

```json
{
    "degiro": {"enabled": true},
    "bitvavo": {"enabled": false},
    "ibkr": {"enabled": false}
}
```

This allows you to focus on one broker at a time during development.

## Working with the Native App

While working with the Native App, both while running from code with `make briefcase-run` or with the installed application,
the code will create files in the following path:

- STONKS_OVERWATCH_DATA_DIR: `/Users/$USER/Library/Application\ Support/com.caribay.stonks_overwatch`
- STONKS_OVERWATCH_CONFIG_DIR: `/Users/$USER/Library/Preferences/com.caribay.stonks_overwatch`
- STONKS_OVERWATCH_LOGS_DIR: `/Users/$USER/Library/Logs/com.caribay.stonks_overwatch`
- STONKS_OVERWATCH_CACHE_DIR: `/Users/$USER/Library/Caches/com.caribay.stonks_overwatch`

It's possible to easily delete them with `make briefcase-clean`

The Briefcase application is obfuscated with Pyarmor by default, if needed, you can disable it with `make briefcase-package obfuscate=false`

## Debug the Native App

To debug the native application, you can enable debugging mode by setting the environment variable `STONKS_OVERWATCH_DEBUG=true`.

When running the application with `make briefcase-run`, you can do it like this:

```shell
make briefcase-run debug=true demo=true
```

It's also interesting to know that it's possible to debug the UI with:

```shell
defaults write com.caribay.stonks-overwatch WebKitDeveloperExtras -bool true
```

Then, when running your app:
1. Open Safari
2. Go to Develop menu
3. Select your app's window
4. Check the Console for errors when you click export
