Stonks Overwatch is a portfolio tracker integrating with multiple trackers. That generates, by itself, some complexities.

# First Steps

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

If everything goes fine you should see a DEGIRO Login screen.

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

### Build Native Applications
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

## Create a new Database
```shell
poetry run python ./scripts/init_db.py --help
```
This command will create a new database with the initial data from the configured DEGIRO account.

> This script expects the `config/config.json` file to be present and properly configured.

## Create a Demo Database
```shell
poetry run python ./scripts/generate_demo_db.py --help
```
This command will create a demo database with some sample data. It is useful for testing purposes or to showcase the application without needing a real DEGIRO account.
> This script expects the `config/config.json` file to be present and properly configured.

The demo database can use used with `make run demo=true`

## Dump and Load a Database
```shell
poetry run python ./scripts/dump_db.py --help
poetry run python ./scripts/dump_db.py dump [--output filename.json]
poetry run python ./scripts/dump_db.py load --input filename.json
```
Allows dumping the current database to a file and load it back. This is useful for testing purposes or to share the database with other developers.

Now it's possible to run the application in offline mode, without needing to connect to DEGIRO.
```json
{
    "degiro": {
      "enabled": true,
      "offline_mode": true
    }
}
```
This parameter can be use together with `demo=true` to load the demo database and run the application in offline mode.
