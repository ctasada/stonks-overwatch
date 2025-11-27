# Contributing to Stonks Overwatch

Thank you for your interest in contributing to Stonks Overwatch! We're excited to have you as part of our community. This guide will help you get started with contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Guidelines](#code-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Community](#community)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to carlos.tasada@gmail.com.

## How Can I Contribute?

There are many ways to contribute to Stonks Overwatch:

### 🐛 Reporting Bugs

Found a bug? Help us fix it!

1. **Check existing issues** - Someone might have already reported it
2. **Use our bug report template** - [Open a bug report](https://github.com/ctasada/stonks-overwatch/issues/new?template=bug_report.md)
3. **Provide details** - The template will guide you through including:
   - Clear, descriptive title
   - Steps to reproduce the problem
   - Expected behavior vs actual behavior
   - Screenshots or error messages
   - Your environment (OS, Python version, etc.)
   - Relevant log entries

The more information you provide, the faster we can identify and fix the issue!

### 💡 Suggesting Features

Have an idea for a new feature?

1. **Check existing feature requests** - It might already be planned
2. **Use our feature request template** - [Open a feature request](https://github.com/ctasada/stonks-overwatch/issues/new?template=feature_request.md)
3. **Describe your idea** - The template will help you include:
   - The problem you're trying to solve
   - Your proposed solution
   - Any alternatives you've considered
   - How it benefits other users
   - Use cases and examples

Well-described feature requests are more likely to be implemented!

### 📝 Improving Documentation

Documentation is crucial! You can help by:
- Fixing typos or clarifying existing docs
- Adding examples and tutorials
- Translating documentation
- Writing guides for new features

### 💻 Contributing Code

Ready to write code? Great! Check out:
- [Good first issues](https://github.com/ctasada/stonks-overwatch/labels/good%20first%20issue) - Perfect for newcomers
- [Help wanted issues](https://github.com/ctasada/stonks-overwatch/labels/help%20wanted) - Where we need assistance

Before starting:
1. Comment on the issue to let others know you're working on it
2. Fork the repository and create a branch
3. Follow our [development workflow](#development-workflow)

### 🏦 Adding Broker Support

Want to add support for a new broker? See our:
- [Broker Architecture Guide](docs/ARCHITECTURE_BROKERS.md)
- [Developer Guide](docs/Developing-Stonks-Overwatch.md)

## Getting Started

### Prerequisites

- **Python 3.13+** - [Download](https://www.python.org/downloads/)
- **Poetry 2.2.1+** - [Install](https://python-poetry.org/docs/#installation)
- **Git** - [Download](https://git-scm.com/downloads)
- **A GitHub account** - [Sign up](https://github.com/join)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork:**

   ```bash
   git clone https://github.com/YOUR-USERNAME/stonks-overwatch.git
   cd stonks-overwatch
   ```

3. **Add upstream remote:**

   ```bash
   git remote add upstream https://github.com/ctasada/stonks-overwatch.git
   ```

### Set Up Development Environment

```bash
# Install dependencies
make start

# Install pre-commit hooks (recommended)
make pre-commit-install

# Verify installation
make test
```

## Development Workflow

### 1. Create a Branch

Always create a new branch for your changes:

```bash
git checkout -b feature/my-new-feature
# or
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### 2. Make Your Changes

Follow our [code guidelines](#code-guidelines) while making changes.

### 3. Test Your Changes

```bash
# Run all tests
make test

# Run specific test file
poetry run pytest tests/path/to/test_file.py

# Run with coverage
make test coverage=true
```

### 4. Check Code Style

```bash
# Check for style issues
make lint-check

# Auto-fix style issues
make lint-fix
```

### 5. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add support for new broker XYZ"
```

**Commit message format:**

```text
type: short description

Longer description if needed

Fixes #123
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

### 6. Keep Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Merge upstream changes
git merge upstream/main

# Update dependencies if needed
make update
```

> **Tip**: Use `make update` to update all dependencies to their latest versions. This ensures you're working with the same versions as other contributors.

### 7. Push Your Changes

```bash
git push origin feature/my-new-feature
```

## Code Guidelines

### Python Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 120 characters max
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Organize with `isort`
- **Formatting**: Use `black` and `ruff`

### Code Quality

- **Type hints**: Use type hints for function parameters and return values
- **Docstrings**: Document all public functions, classes, and modules
- **Comments**: Explain _why_, not _what_
- **Naming**:
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

### Example

```python
from typing import List, Optional

class PortfolioService:
    """Service for managing portfolio operations.

    This service handles all portfolio-related operations including
    fetching, updating, and analyzing portfolio data.
    """

    def get_portfolio_value(self, portfolio_id: str) -> Optional[float]:
        """Calculate the total value of a portfolio.

        Args:
            portfolio_id: Unique identifier for the portfolio

        Returns:
            Total portfolio value in base currency, or None if not found

        Raises:
            PortfolioNotFoundError: If the portfolio doesn't exist
        """
        # Implementation here
        pass
```

### Architecture Guidelines

- **Separation of concerns**: Keep business logic separate from UI
- **Interface-based design**: Use interfaces for services
- **Dependency injection**: Use factories for service creation
- **Error handling**: Use custom exceptions with proper error messages
- **Logging**: Use structured logging with appropriate log levels

## Testing

### Test Requirements

- All new features must include tests
- Bug fixes should include a test that reproduces the bug
- Aim for >80% code coverage

### Writing Tests

```python
import pytest
from stonks_overwatch.services import PortfolioService

class TestPortfolioService:
    """Test suite for PortfolioService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = PortfolioService()

    def test_get_portfolio_value_success(self):
        """Test successful portfolio value calculation."""
        # Arrange
        portfolio_id = "test-123"

        # Act
        value = self.service.get_portfolio_value(portfolio_id)

        # Assert
        assert value > 0
        assert isinstance(value, float)

    def test_get_portfolio_value_not_found(self):
        """Test portfolio value when portfolio doesn't exist."""
        # Arrange
        portfolio_id = "nonexistent"

        # Act & Assert
        with pytest.raises(PortfolioNotFoundError):
            self.service.get_portfolio_value(portfolio_id)
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
poetry run pytest tests/test_portfolio.py

# Run with specific markers
poetry run pytest -m "not slow"

# Run with coverage
poetry run pytest --cov=stonks_overwatch --cov-report=html
```

## Documentation

### Documentation Standards

- **Clear and concise**: Write for your audience
- **Examples**: Include code examples where helpful
- **Updated**: Keep docs in sync with code changes
- **Screenshots**: Add screenshots for UI features

### Documentation Types

1. **Code Documentation**: Docstrings and inline comments
2. **User Documentation**: Guides, tutorials, and how-tos in `docs/`
3. **API Documentation**: Generated from docstrings
4. **README**: Project overview and quick start

### Writing Good Documentation

```markdown
# Feature Name

## Overview

Brief description of what this feature does and why it's useful.

## Usage

### Basic Example

```python
# Simple usage example
from stonks_overwatch import Feature

feature = Feature()
result = feature.do_something()
```

### Advanced Example

```python
# More complex usage
feature = Feature(
    option1=True,
    option2="custom"
)
result = feature.do_something_advanced()
```

## Configuration

Describe any configuration options...

## Troubleshooting

Common issues and solutions...

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass**

   ```bash
   make test
   make lint-check
   ```

2. **Update documentation** if needed

3. **Create a pull request** with a clear title and description
   - Our PR template will help you structure your submission
   - Include type of change, testing performed, and checklist items

4. **Link related issues** in the PR description

5. **Be responsive** to review feedback

### Pull Request Template

When you create a pull request, our template will guide you through providing:

- **Description** - What changes did you make?
- **Type of Change** - Bug fix, feature, documentation, etc.
- **Related Issues** - Link to relevant issues
- **Testing** - What testing did you perform?
- **Code Quality** - Lint checks, formatting, etc.
- **Documentation** - Updated docs if needed
- **Screenshots** - For UI changes
- **Checklist** - Ensure all requirements are met

The template ensures your PR has all necessary information for review.

### Review Process

1. **Automated checks** must pass (tests, linting)
2. **Code review** by maintainers
3. **Discussion** and iteration if needed
4. **Approval** from at least one maintainer
5. **Merge** by maintainers

## Community

### Getting Help

- **Documentation**: Start with the [docs](docs/Home.md)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/ctasada/stonks-overwatch/discussions)
- **Issues**: Search [existing issues](https://github.com/ctasada/stonks-overwatch/issues)
- **Email**: carlos.tasada@gmail.com for sensitive matters

### Communication Guidelines

- **Be respectful**: Treat everyone with kindness and respect
- **Be patient**: Maintainers and contributors volunteer their time
- **Be clear**: Provide context and details in your communications
- **Be constructive**: Focus on solutions, not just problems

### Recognition

All contributors are recognized in:
- GitHub contributors page
- Release notes
- CHANGELOG.md

Significant contributions may be highlighted in project announcements.

## Development Resources

### Useful Commands

```bash
make help                  # Show all available commands
make install              # Install dependencies
make update               # Update all dependencies to latest versions
make run                   # Start development server
make run debug=true        # Start with debug logging
make run demo=true         # Start with demo data
make test                  # Run tests
make lint-check           # Check code style
make lint-fix             # Fix code style issues
make briefcase-run        # Run native app
make docker-run           # Run in Docker
```

### Key Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Broker Integration](docs/ARCHITECTURE_BROKERS.md)
- [Developer Guide](docs/Developing-Stonks-Overwatch.md)
- [Configuration Guide](docs/Configuration-Integration.md)

### External Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)
- [Semantic Versioning](https://semver.org/)

## Questions?

If you have any questions about contributing:

- Check the [FAQ](docs/FAQ.md)
- Ask in [GitHub Discussions](https://github.com/ctasada/stonks-overwatch/discussions)
- Email carlos.tasada@gmail.com

## Thank You!

Your contributions make Stonks Overwatch better for everyone. We appreciate your time and effort in helping improve the project. Welcome to the community! 🎉

---

**Happy Coding!** 🚀
