# Stonks Overwatch

![Stonks Overwatch Logo](src/icons/stonks_overwatch-256.png)

**A privacy-first, open-source investment portfolio tracker**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2+](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)

[Quickstart](docs/Quickstart.md) • [Documentation](docs/Home.md) • [Contributing](CONTRIBUTING.md)

---

## Overview

**Stonks Overwatch** is an open-source investment dashboard that helps you track and manage your portfolio across multiple brokers. Built with privacy and extensibility in mind, all your data stays local on your machine—no cloud services, no data sharing.

### Why Stonks Overwatch?

- **🔒 Privacy First**: Your financial data never leaves your computer
- **📊 Multi-Broker Support**: Unified view across DEGIRO, Bitvavo, IBKR and more to come
- **🎯 Real-Time Tracking**: Live portfolio values, dividends, and performance metrics
- **🔌 Extensible Architecture**: Plugin system for adding new brokers
- **💻 Cross-Platform**: Available on Windows, macOS, and Linux (native and web versions)
- **🆓 100% Free**: No subscriptions, no hidden costs, no data selling

## Features

### Portfolio Management

- **Real-time portfolio tracking** with automatic updates
- **Multi-broker consolidation** for a unified view
- **Performance analytics** with historical data
- **Dividend tracking** and forecasting
- **Fee analysis** across all brokers
- **Asset diversification** visualization

### Supported Brokers

- **DEGIRO** - Full support with real-time data
- **Bitvavo** - Cryptocurrency exchange integration
- **IBKR** (Interactive Brokers) - International markets

### Technical Features

- **Local-first architecture** - All data stored locally
- **Modern web UI** - Built with Bootstrap and Charts.js
- **Native applications** - Desktop apps for all major platforms
- **Offline mode** - Work without internet connection
- **Automated backups** - Never lose your data
- **Demo mode** - Try it out with sample data

## Screenshots

> *Coming soon - Add screenshots showing the dashboard, portfolio view, and analytics*

## Quick Start

### Prerequisites

- Python 3.13 or higher
- Poetry 2.2.1 or higher (for development)
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/ctasada/stonks-overwatch.git
   cd stonks-overwatch
   ```

2. **Configure your brokers** (optional, can be done later)

   ```bash
   cp config/config.json.template config/config.json
   # Edit config.json with your broker credentials
   ```

3. **Install dependencies and start the application**

   ```bash
   make start
   ```

   This command will:
   - Install all Python and Node.js dependencies
   - Initialize the database
   - Collect static files
   - Start the development server

   The application will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000)

> **Alternative**: If you prefer step-by-step setup, you can run `make install` first, then `make collectstatic migrate`, and finally `make run`. However, `make start` handles all of this automatically.

For detailed installation instructions, see the [Quickstart Guide](docs/Quickstart.md).

## Documentation

- **📘 [User Documentation](docs/Home.md)** - Complete guide to using Stonks Overwatch
- **🚀 [Quickstart Guide](docs/Quickstart.md)** - Get up and running in minutes
- **🖥️ [Desktop App Guide](docs/Application.md)** - Native application installation and updates
- **🔧 [Developer Guide](docs/Developing-Stonks-Overwatch.md)** - Contributing and development setup
- **🤖 [AI Agent Guide](AGENTS.md)** - Guidelines for AI assistants working on this project
- **🏦 Broker Setup**: [DEGIRO](docs/DEGIRO.md) • [Bitvavo](docs/Bitvavo.md) • [IBKR](docs/IBKR.md)
- **❓ [FAQ](docs/FAQ.md)** - Frequently asked questions

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

- **🐛 [Report a Bug](https://github.com/ctasada/stonks-overwatch/issues/new?template=bug_report.md)** - Found an issue? Let us know
- **💡 [Request a Feature](https://github.com/ctasada/stonks-overwatch/issues/new?template=feature_request.md)** - Have an idea? Share it
- **👨‍💻 [Contribute Code](CONTRIBUTING.md)** - Ready to code? Check our guidelines
- **📝 [Improve Docs](CONTRIBUTING.md)** - Documentation improvements are always welcome

Please read our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before getting started.

## Community & Support

- **📚 [Documentation](docs/Home.md)** - Comprehensive guides and tutorials
- **💬 [Discussions](https://github.com/ctasada/stonks-overwatch/discussions)** - Ask questions and share ideas
- **🐛 [Issue Tracker](https://github.com/ctasada/stonks-overwatch/issues)** - Report bugs and request features
- **📧 [Email](mailto:carlos.tasada@gmail.com)** - Direct contact for sensitive issues

## Future Development

Stonks Overwatch is under active development. Planned features under consideration:

- Dynamic plugin architecture for brokers
- Mobile app support
- Advanced analytics and reporting
- Additional broker integrations
- Community-driven enhancements

Check the [CHANGELOG](CHANGELOG.md) for release history and [GitHub Issues](https://github.com/ctasada/stonks-overwatch/issues) to track upcoming features.

## License

Stonks Overwatch is released under the [MIT License](LICENSE). You're free to use, modify, and distribute this software.

## Acknowledgments

Built with these amazing open-source projects:
- [Django](https://www.djangoproject.com/) - Web framework
- [DEGIRO Connector](https://github.com/Chavithra/degiro-connector) - DEGIRO API client
- [Bitvavo API](https://github.com/bitvavo/python-bitvavo-api) - Bitvavo integration
- [iBind](https://github.com/Voyz/ibind) - IBKR API client
- [Bootstrap](https://getbootstrap.com/) - UI framework
- [Charts.js](https://www.chartjs.org/) - Data visualization

Special thanks to all [contributors](https://github.com/ctasada/stonks-overwatch/graphs/contributors) who help make this project better!

---

**⭐ If you find Stonks Overwatch useful, please star the project! ⭐**

Made with ❤️ by the Stonks Overwatch community
