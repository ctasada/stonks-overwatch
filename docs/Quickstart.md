# Quickstart Guide

Get Stonks Overwatch up and running in less than 10 minutes!

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.13 or higher** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Poetry 2.2.1+** (for development) - [Install Poetry](https://python-poetry.org/docs/#installation)

### Verify Installation

```bash
python --version  # Should show 3.13 or higher
git --version     # Should show git version
```

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/ctasada/stonks-overwatch.git
cd stonks-overwatch
```

### Step 2: Install Dependencies

Run the setup command which will install all required dependencies:

```bash
make start
```

This command will:
- Install Python dependencies via Poetry
- Set up the database
- Install Node.js dependencies for the UI
- Configure the environment

**Expected output:** You should see progress messages and finally "Setup complete!"

> **Note:** On first run, this may take 5-10 minutes depending on your internet connection.

### Step 3: Configure Brokers (Optional)

To track your actual portfolios, configure your broker credentials:

```bash
cp config/config.json.template config/config.json
```

Edit `config/config.json` with your broker credentials. See broker-specific setup:
- [DEGIRO Configuration](DEGIRO.md)
- [Bitvavo Configuration](Bitvavo.md)
- [IBKR Configuration](IBKR.md)

**Example configuration:**

```json
{
  "base_currency": "EUR",
  "degiro": {
    "enabled": true,
    "credentials": {
      "username": "your_username",
      "password": "your_password"
    }
  },
  "bitvavo": {
    "enabled": false
  },
  "ibkr": {
    "enabled": false
  }
}
```

> **Security Note:** Never commit your `config.json` file to version control. It's already in `.gitignore`.

### Step 4: Start the Application

```bash
make run
```

The application will start and you should see output like:

```text
Starting Stonks Overwatch...
Performing system checks...
Django version 5.2.8, using settings 'stonks_overwatch.settings'
Starting development server at http://127.0.0.1:8000/
```

### Step 5: Access the Dashboard

Open your web browser and navigate to:

```text
http://127.0.0.1:8000
```

🎉 **Congratulations!** You now have Stonks Overwatch running locally.

## First Time Setup

When you access the dashboard for the first time:

1. **Login**: If you configured broker credentials, you'll see a login page
2. **Data Import**: The application will fetch your portfolio data (this may take a few minutes)
3. **Dashboard**: You'll see your portfolio overview with charts and statistics

## Quick Tips

### Try Demo Mode

Want to explore without configuring brokers? Run in demo mode:

```bash
make run demo=true
```

This loads sample data so you can see all features without real credentials.

### Enable Debug Mode

For troubleshooting, run with debug logging:

```bash
make run debug=true
```

### Stop the Application

Press `Ctrl+C` in the terminal where the application is running.

## Common Commands

| Command | Description |
|---------|-------------|
| `make start` | Initial setup and installation |
| `make run` | Start the application |
| `make run demo=true` | Run with demo data |
| `make run debug=true` | Run with debug logging |
| `make test` | Run tests |
| `make lint-check` | Check code style |
| `make help` | Show all available commands |

## Docker Alternative

Prefer Docker? You can run Stonks Overwatch in a container:

```bash
make docker-run
```

This builds and runs the application in Docker without needing to install Python or dependencies locally.

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, you'll see an error. Stop any other services using that port or change the port in settings.

### Python Version Error

Stonks Overwatch requires Python 3.13+. If you have an older version:

1. Install Python 3.13 from [python.org](https://www.python.org/downloads/)
2. Update your PATH to use the new version
3. Run `python --version` to verify

### Dependencies Not Installing

If `make start` fails:

1. Ensure you have internet connection
2. Try updating Poetry: `poetry self update`
3. Clear Poetry cache: `poetry cache clear . --all`
4. Run `make start` again

### Database Errors

If you see database-related errors:

```bash
# Reset the database
rm data/db.sqlite3
make start
```

### Still Having Issues?

- Check the [FAQ](FAQ.md) for more solutions
- Search [existing issues](https://github.com/ctasada/stonks-overwatch/issues)
- Ask in [Discussions](https://github.com/ctasada/stonks-overwatch/discussions)
- Report a [new issue](https://github.com/ctasada/stonks-overwatch/issues/new)

## Next Steps

Now that you have Stonks Overwatch running:

- **Configure Brokers**: See broker-specific guides for detailed setup
  - [DEGIRO Setup](DEGIRO.md)
  - [Bitvavo Setup](Bitvavo.md)
  - [IBKR Setup](IBKR.md)
- **Explore Features**: Check the [User Guide](Home.md) for feature walkthroughs
- **Customize**: Learn about configuration options in [Configuration Guide](Configuration-Integration.md)
- **Contribute**: Want to help? See [Contributing Guidelines](../CONTRIBUTING.md)

## Update Stonks Overwatch

To update to the latest version:

```bash
cd stonks-overwatch
git pull origin main
make update  # Update all dependencies (Python, Node.js, and third-party licenses)
make run     # Start with new version
```

> **Note**: `make update` will update Poetry, all Python packages, Node.js dependencies, and regenerate the third-party licenses file. If you just need to reinstall existing versions, use `make install` instead.

---

**Need Help?** Check our [FAQ](FAQ.md) or join the [community discussions](https://github.com/ctasada/stonks-overwatch/discussions)!
