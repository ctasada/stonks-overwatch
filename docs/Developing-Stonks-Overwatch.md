# Developing Stonks Overwatch

> **Audience:** Developers, contributors
>
> **Summary:** This guide explains how to set up the development environment and contribute to Stonks Overwatch.

Stonks Overwatch is a portfolio tracker integrating with multiple brokers (DEGIRO, Bitvavo, IBKR). The system features a **unified broker architecture** with factory patterns, dependency injection, interface-based design, and a centralized broker registry that simplifies development and maintenance.

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

### Updating Dependencies

To update all dependencies to their latest versions:

```shell
make update
```

This command will:

- Update Poetry itself
- Update all Python dependencies
- Update Node.js dependencies
- Regenerate third-party licenses file

> **Note**: Use `make update` instead of `poetry update` directly to ensure all dependencies and licenses are properly updated.

Alternatively, you can also use Docker

```shell
make docker-run
```

The application is available at [http://127.0.0.1:8000](http://127.0.0.1:8000) Open your browser in that URL.

If everything goes fine you should see a login screen for your configured brokers.

## Understanding the Architecture

Before diving into development, it's important to understand the **unified broker architecture** that powers Stonks Overwatch:

### Key Components

- **BrokerRegistry**: Central registry managing all broker configurations and services
- **BrokerFactory**: Unified factory creating services with automatic dependency injection
- **Service Interfaces**: Type-safe contracts ensuring consistent broker implementations
- **Configuration System**: Registry-based configuration supporting multiple brokers

### For New Developers

If you're adding new features or brokers, familiarize yourself with these key documents:

- **[Broker Integration Guide](ARCHITECTURE_BROKERS.md)** - Complete guide for adding new brokers
- **[Architecture Overview](ARCHITECTURE.md)** - System design and improvements
- **[Authentication System](ARCHITECTURE_AUTHENTICATION.md)** - Authentication patterns and flows

### Service Access Pattern

The unified broker architecture uses a factory pattern for creating broker services:

```python
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.service_types import ServiceType

# Create a factory instance
factory = BrokerFactory()

# Request a specific service for a broker
portfolio_service = factory.create_service("degiro", ServiceType.PORTFOLIO)
```

This pattern ensures consistent service creation across all brokers with automatic dependency injection.

## Start Developing

### IMPORTANT DEPENDENCIES

To develop the application, it's important to have installed in your system the next dependencies:

- Python 3.13 or higher
- Poetry 2.2.1 or higher

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

### Working with Broker Services

#### Debug Broker Registration

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

The demo database can be used with `make run demo=true`. The application will automatically route all database operations to the demo database using the built-in database routing system.

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

This command will create a new database with the initial data from your configured broker accounts (DEGIRO, Bitvavo, IBKR).

> This script expects the `config/config.json` file to be present and properly configured with your broker credentials.

### Configuration File Format

The configuration system supports multiple brokers simultaneously:

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

The demo database allows users to explore the application features without connecting to real broker accounts. It contains synthetic transaction data and market information for demonstration purposes.

#### For Developers: Generating the Demo Database

To regenerate the demo database from scratch:

```shell
poetry run python -m scripts.generate_demo_db \
    --start-date "2024-01-01" \
    --num-transactions 150 \
    --initial-deposit 10000 \
    --monthly-deposit 500
```

This command will:
1. Create a fresh demo database with synthetic transaction data
2. Generate realistic market data for popular stocks and ETFs
3. Copy the database to `src/stonks_overwatch/fixtures/demo_db.sqlite3` for bundling with Briefcase distributions
4. The bundled template should be committed to version control

For more details on available parameters:

```shell
poetry run python -m scripts.generate_demo_db --help
```

> **Important**: After generating a new demo database, commit the updated `src/stonks_overwatch/fixtures/demo_db.sqlite3` file to git. This ensures the latest demo data is bundled with all distributions.

#### For Users: Demo Mode in the Native App

When users activate demo mode via the application menu:
1. The application checks if a demo database exists in the user's data directory
2. If the bundled demo database is different (detected by comparing SHA256 hashes):
   - The existing demo database is backed up to `demo_db.sqlite3.backup`
   - The new demo database is copied from the application bundle
   - This ensures users always get the latest demo data after app updates
3. The application switches to demo mode and applies any pending migrations
4. All broker API connections are disabled in demo mode

The demo database is distributed as a pre-populated SQLite file (approximately 384KB), providing instant access to demo features.

> **Note**: When updating the application to a new version with updated demo data, the old demo database is automatically backed up. Users' actual portfolio data in the production database is never affected by demo mode operations.

#### Demo Database Location

- **Bundled template**: `src/stonks_overwatch/fixtures/demo_db.sqlite3` (read-only, in git)
- **User's working copy**: `$STONKS_OVERWATCH_DATA_DIR/demo_db.sqlite3` (created on first demo activation)

The demo database can be used with `make run demo=true`. The application will automatically route all database operations to the demo database using the built-in database routing system.

### Demo Mode Database Routing

The application features an advanced database routing system that allows seamless switching between production and demo databases without requiring server restarts.

#### How It Works

The application supports two database configurations:
- **Production Database** (`db.sqlite3`): Contains real user data
- **Demo Database** (`demo_db.sqlite3`): Contains demo/sample data for testing

The `DatabaseRouter` class automatically routes all database operations to the appropriate database based on the `DEMO_MODE` environment variable:

- When `DEMO_MODE=False` (or unset): Routes to the production database
- When `DEMO_MODE=True`: Routes to the demo database

#### Database Configuration

Both databases are defined in `settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(STONKS_OVERWATCH_DATA_DIR).resolve().joinpath("db.sqlite3"),
        # ... production database settings
    },
    "demo": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(STONKS_OVERWATCH_DATA_DIR).resolve().joinpath("demo_db.sqlite3"),
        # ... demo database settings
    },
}

DATABASE_ROUTERS = ["stonks_overwatch.utils.database.db_router.DatabaseRouter"]
```

#### Benefits of Database Routing

1. **No Server Restart Required**: Database switching happens instantly
2. **Data Isolation**: Production and demo data are completely separate
3. **Transparent Operation**: All existing code works without modification
4. **Consistent Schema**: Both databases maintain the same structure through migrations

#### Migration Handling

Both databases support migrations independently:

```shell
# Apply migrations to production database
python manage.py migrate --database=default

# Apply migrations to demo database
python manage.py migrate --database=demo
```

The router ensures migrations can be applied to both databases as needed, maintaining schema consistency.

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

The offline mode can be used together with `demo=true` to load the demo database and run the application without any external API calls. The database routing system ensures that demo data is completely isolated from production data, making it safe to experiment with different configurations.

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
