# Stonks Overwatch Documentation

Welcome to the Stonks Overwatch documentation! This guide will help you get started with using and developing Stonks Overwatch.

## What is Stonks Overwatch?

Stonks Overwatch is an open-source investment portfolio tracker that helps you manage and monitor your investments across multiple brokers. It runs entirely on your local machine, ensuring your financial data remains private and secure.

### Key Features

- **🔒 Privacy-First**: All data stored locally on your computer
- **📊 Multi-Broker**: Track portfolios from DEGIRO, Bitvavo, and IBKR
- **⚡ Real-Time**: Live portfolio updates and analytics
- **🎯 Comprehensive**: Dividends, fees, deposits, and diversification tracking
- **🔌 Extensible**: Plugin architecture for adding new brokers
- **💻 Cross-Platform**: Web and native apps for all major platforms

---

## 🎯 Quick Navigation

Find what you need by task:

### "I want to..."

#### Install and Use

- **Install Stonks Overwatch** → [Quickstart Guide](Quickstart.md)
- **Install desktop app** → [Application Guide](Application.md)
- **Configure my broker** → [DEGIRO](DEGIRO.md), [Bitvavo](Bitvavo.md), or [IBKR](IBKR.md)
- **Troubleshoot issues** → [FAQ](FAQ.md) or [Troubleshooting](#troubleshooting)

#### Develop

- **Set up development environment** → [Developer Guide](Developing-Stonks-Overwatch.md)
- **Understand the architecture** → [Architecture Overview](ARCHITECTURE.md)
- **Add a new broker** → [Broker Integration](ARCHITECTURE_BROKERS.md)
- **Work on authentication** → [Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md)
- **Contribute code** → [Contributing Guidelines](../CONTRIBUTING.md)

#### Learn

- **Understand the system** → [Architecture Overview](ARCHITECTURE.md)
- **See what's planned** → [Pending Tasks](PENDING_TASKS.md)
- **Learn about plugins** → [Plugin Architecture](PLUGIN_ARCHITECTURE.md)

---

## Getting Started

### New Users

Start here if you're new to Stonks Overwatch:

1. **[Quickstart Guide](Quickstart.md)** - Install and run in 10 minutes
2. **[Broker Setup](#broker-documentation)** - Configure your brokers
3. **[FAQ](FAQ.md)** - Common questions answered

### For Developers

Contributing to Stonks Overwatch? Check these guides:

1. **[Developer Guide](Developing-Stonks-Overwatch.md)** - Development environment setup
2. **[Contributing Guidelines](../CONTRIBUTING.md)** - How to contribute
3. **[Broker Architecture](ARCHITECTURE_BROKERS.md)** - Adding new brokers

---

## 📚 Documentation Index

### User Guides

| Document | Description | Audience |
|----------|-------------|----------|
| **[Quickstart Guide](Quickstart.md)** | Install and run in 10 minutes | New users |
| **[Application Guide](Application.md)** | Native desktop app installation and usage | End users |
| **[DEGIRO Setup](DEGIRO.md)** | Complete DEGIRO broker configuration | DEGIRO users |
| **[Bitvavo Setup](Bitvavo.md)** | Complete Bitvavo exchange configuration | Bitvavo users |
| **[IBKR Setup](IBKR.md)** | Complete Interactive Brokers configuration | IBKR users |
| **[FAQ](FAQ.md)** | Frequently asked questions | All users |

### Developer Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| **[Developer Guide](Developing-Stonks-Overwatch.md)** | Development environment setup | Developers |
| **[Architecture Overview](ARCHITECTURE.md)** | System architecture and design patterns | Developers |
| **[Broker Integration](ARCHITECTURE_BROKERS.md)** | Step-by-step guide for adding brokers | Developers |
| **[Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md)** | Authentication system details | Developers |
| **[Configuration Integration](Configuration-Integration.md)** | Configuration system guide | Developers |
| **[User Interface](User-Interface.md)** | Frontend development guide | UI developers |

### Advanced Topics

| Document | Description | Audience |
|----------|-------------|----------|
| **[Pending Tasks](PENDING_TASKS.md)** | Current improvements and technical debt | Maintainers |
| **[Plugin Architecture](PLUGIN_ARCHITECTURE.md)** | Future plugin system proposal | Architects |

### Contributing

| Document | Description | Audience |
|----------|-------------|----------|
| **[Contributing Guidelines](../CONTRIBUTING.md)** | How to contribute to the project | Contributors |
| **[Code of Conduct](../CODE_OF_CONDUCT.md)** | Community guidelines | All contributors |

---

## Broker Documentation

### DEGIRO

**[Full DEGIRO Documentation](DEGIRO.md)**

DEGIRO is the primary broker supported by Stonks Overwatch with complete feature support.

**Features:**

- Real-time portfolio data
- Transaction history
- Dividend tracking
- Fee analysis
- 2FA support (TOTP and In-App)
- Offline mode

**Getting Started:** Select DEGIRO from the broker selection screen, enter your credentials, and configure additional settings via the Settings page.

### Bitvavo

**[Full Bitvavo Documentation](Bitvavo.md)**

Bitvavo is a cryptocurrency exchange integration for tracking crypto assets.

**Features:**

- Crypto portfolio tracking
- Trade history
- Asset information
- Real-time prices

**Getting Started:** Select Bitvavo from the broker selection screen, enter your API credentials, and configure via the Settings page.

### IBKR (Interactive Brokers)

**[Full IBKR Documentation](IBKR.md)**

Interactive Brokers integration for international markets.

**Features:**

- International markets support
- Portfolio tracking
- Position management

**Getting Started:** Select IBKR from the broker selection screen, enter your OAuth credentials and certificates, and configure via the Settings page.

---

## Common Tasks

### Installation

```bash
# Clone repository
git clone https://github.com/ctasada/stonks-overwatch.git
cd stonks-overwatch

# Install and setup
make start

# Run application
make run
```

See [Quickstart Guide](Quickstart.md) for detailed instructions.

### Broker Configuration

1. Launch the application
2. Select your broker from the broker selection screen
3. Enter your credentials
4. Configure additional settings via the Settings page (sidebar menu)

See broker-specific documentation: [DEGIRO](DEGIRO.md), [Bitvavo](Bitvavo.md), or [IBKR](IBKR.md)

### Running with Demo Data

```bash
make run demo=true
```

Perfect for testing without real broker credentials.

### Development Setup

```bash
# Clone and setup
make start

# Install pre-commit hooks
make pre-commit-install

# Run tests
make test

# Start development server
make run debug=true
```

See [Developer Guide](Developing-Stonks-Overwatch.md) for complete development setup.

### Adding a New Broker

1. Review [Broker Architecture](ARCHITECTURE_BROKERS.md)
2. Implement required service interfaces
3. Register broker in `registry_setup.py`
4. Add tests and documentation
5. Submit pull request

---

## Troubleshooting

### Common Issues

**Application won't start**
- Check Python version (`python --version` should be 3.13+)
- Reinstall dependencies: `make start`
- Check logs in `data/logs/stonks-overwatch.log`

**Can't login to broker**

- Verify credentials in the Settings page
- Check broker-specific documentation
- Enable debug mode: `make run debug=true`

**Port 8000 already in use**
- Stop other services using port 8000
- Or change port in settings

**Database errors**
- Backup data: `cp data/db.sqlite3 data/db.sqlite3.backup`
- Reset database: `rm data/db.sqlite3 && make start`

See [FAQ](FAQ.md) for more troubleshooting help.

---

## Architecture Overview

Stonks Overwatch uses a modern, modular architecture:

### Core Components

- **Broker Services**: Interface-based broker implementations
- **Service Factory**: Dependency injection and service creation
- **Configuration System**: Centralized configuration management
- **Repository Layer**: Data access and persistence
- **Aggregator Services**: Cross-broker data aggregation

### Key Patterns

- **Factory Pattern**: Service creation and dependency injection
- **Interface-Based Design**: Type-safe service contracts
- **Repository Pattern**: Data access abstraction
- **Plugin Architecture**: Extensible broker system

See [Architecture Overview](ARCHITECTURE.md) for detailed architecture documentation.

---

## Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

- **🐛 Report Bugs** - [Open a bug report](https://github.com/ctasada/stonks-overwatch/issues/new?template=bug_report.md)
- **💡 Suggest Features** - [Request a feature](https://github.com/ctasada/stonks-overwatch/issues/new?template=feature_request.md)
- **💬 Ask Questions** - [Open a question](https://github.com/ctasada/stonks-overwatch/issues/new?template=question.md)
- **📝 Improve Documentation** - Submit documentation PRs
- **💻 Contribute Code** - Check [good first issues](https://github.com/ctasada/stonks-overwatch/labels/good%20first%20issue)
- **🏦 Add Brokers** - Implement new broker integrations

### Getting Started with Contributing

1. Read [Contributing Guidelines](../CONTRIBUTING.md)
2. Review [Code of Conduct](../CODE_OF_CONDUCT.md)
3. Check [Developer Guide](Developing-Stonks-Overwatch.md)
4. Fork and clone the repository
5. Create a branch and make your changes
6. Submit a pull request

---

## Support & Sponsorship

Stonks Overwatch is a free, open-source project built and maintained by volunteers. Your support helps ensure the project continues to grow and improve.

### Why Sponsor?

Stonks Overwatch was created to solve a real problem: managing investments across multiple brokers while maintaining complete privacy. The project represents over a year of dedicated development work, including:

- Full broker integrations (DEGIRO, Bitvavo, IBKR)
- Native desktop applications for all platforms
- Comprehensive documentation and developer guides
- Privacy-first architecture with local data storage

**Your sponsorship enables:**
- More time dedicated to development and maintenance
- Faster broker integrations and feature development
- Better infrastructure (CI/CD, testing, code signing)
- Long-term sustainability of the project

### How to Support

**GitHub Sponsors** (Recommended):
👉 [Sponsor via GitHub Sponsors](https://github.com/sponsors/ctasada)

**Other Ways to Help:**
- ⭐ **Star the repository** - Helps others discover the project
- 🐛 **Report bugs** - [Open an issue](https://github.com/ctasada/stonks-overwatch/issues)
- 💡 **Suggest features** - [Request a feature](https://github.com/ctasada/stonks-overwatch/issues/new?template=feature_request.md)
- 📝 **Contribute code** - See [Contributing Guidelines](../CONTRIBUTING.md)
- 📢 **Share with others** - Spread the word about Stonks Overwatch

For more details about the project's story and what sponsorship enables, see the [README sponsorship section](https://github.com/ctasada/stonks-overwatch?tab=readme-ov-file#how-to-support) on GitHub.

---

## Project Resources

### Links

- **GitHub**: [github.com/ctasada/stonks-overwatch](https://github.com/ctasada/stonks-overwatch)
- **Issues**: [Report bugs and request features](https://github.com/ctasada/stonks-overwatch/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/ctasada/stonks-overwatch/discussions)
- **Releases**: [Latest releases and changelogs](https://github.com/ctasada/stonks-overwatch/releases)

### Community

- **💬 Discussions** - [GitHub Discussions](https://github.com/ctasada/stonks-overwatch/discussions)
- **📧 Email** - carlos.tasada@gmail.com
- **🐛 Issues** - [Issue Tracker](https://github.com/ctasada/stonks-overwatch/issues)

### Development

- **🔧 Architecture** - [Architecture Docs](ARCHITECTURE.md)
- **🏦 Broker Integration** - [Broker Architecture](ARCHITECTURE_BROKERS.md)
- **🧪 Testing** - Run `make test`

---

## License

Stonks Overwatch is released under the [MIT License](../LICENSE). You're free to use, modify, and distribute this software for any purpose, including commercial applications.

---

## Quick Reference

### Essential Commands

```bash
make start              # Initial setup
make run                # Start application
make run demo=true      # Run with demo data
make run debug=true     # Debug mode
make test               # Run tests
make lint-check         # Check code style
make help               # Show all commands
```

### Key Files

- `data/db.sqlite3` - Local database (includes encrypted credentials)
- `data/logs/` - Application logs
- `Makefile` - Build and run commands
- `config/config.json` - Optional manual configuration (for developers)

### Important Links

- [Quickstart](Quickstart.md) - Get started in 10 minutes
- [FAQ](FAQ.md) - Common questions
- [Contributing](../CONTRIBUTING.md) - How to contribute
- [DEGIRO Setup](DEGIRO.md) - Configure DEGIRO

---

## Need Help?

If you can't find what you're looking for:

1. **Check the [FAQ](FAQ.md)** - Most common questions are answered there
2. **Search [existing issues](https://github.com/ctasada/stonks-overwatch/issues)** - Someone might have asked before
3. **Ask in [Discussions](https://github.com/ctasada/stonks-overwatch/discussions)** - Community Q&A
4. **[Open an issue](https://github.com/ctasada/stonks-overwatch/issues/new)** - Report bugs or request features
5. **Email us** - carlos.tasada@gmail.com for sensitive matters

---

## 📋 Documentation Status

Our documentation is actively maintained. Current status:

| Document | Status | Last Updated |
|----------|--------|--------------|
| Home | ✅ Complete | November 2025 |
| Quickstart | ✅ Complete | November 2025 |
| Architecture | ✅ Complete | November 2025 |
| Broker Integration | ✅ Complete | November 2025 |
| Authentication | ✅ Complete | November 2025 |
| DEGIRO Setup | ✅ Complete | November 2025 |
| Bitvavo Setup | ✅ Complete | November 2025 |
| IBKR Setup | ✅ Complete | November 2025 |
| Configuration | ✅ Complete | November 2025 |
| Developer Guide | ✅ Complete | November 2025 |
| Application Guide | ✅ Complete | November 2025 |
| User Interface | ✅ Complete | November 2025 |
| FAQ | ✅ Complete | November 2025 |
| Pending Tasks | 🔄 In Progress | November 2025 |
| Plugin Architecture | 📋 Proposed | November 2025 |

**Legend:** ✅ Complete | 🔄 In Progress | 📋 Proposed

### Documentation Standards

Our documentation follows these principles:
- **Clear and Concise**: Easy to understand for the target audience
- **Well-Organized**: Logical structure with consistent formatting
- **Up-to-Date**: Synchronized with codebase changes
- **Cross-Referenced**: Links between related documents
- **Example-Rich**: Code examples and screenshots where helpful

### Report Issues

Found a documentation issue?
- [Open an issue](https://github.com/ctasada/stonks-overwatch/issues/new) to report errors
- [Start a discussion](https://github.com/ctasada/stonks-overwatch/discussions) to suggest improvements
- [Submit a PR](../CONTRIBUTING.md) to contribute fixes

---

**Thank you for using Stonks Overwatch!** 🎉

If you find this project useful, please ⭐ star it on [GitHub](https://github.com/ctasada/stonks-overwatch)!
