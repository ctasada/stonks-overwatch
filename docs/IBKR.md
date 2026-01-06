# IBKR (Interactive Brokers) Integration Guide

> **⚠️ IBKR integration is not yet stable. Features and reliability may change in future releases. Use with caution.**

Interactive Brokers (IBKR) is a global broker supported by **Stonks Overwatch**, providing access to international markets and securities.

## Overview

### Features

- ✅ **International markets** - Access to 150+ markets worldwide
- ✅ **Portfolio tracking** - Monitor your global investments
- ✅ **Position management** - Track all your positions
- ✅ **Multi-asset support** - Stocks, options, futures, forex, bonds
- ✅ **OAuth authentication** - Secure OAuth 1.0a authentication
- ✅ **Real-time data** - Live portfolio updates
- ✅ **Multi-currency** - Support for multiple currencies

### Supported Markets

IBKR provides access to:
- **US Markets** - NYSE, NASDAQ, AMEX
- **European Markets** - LSE, XETRA, Euronext, etc.
- **Asian Markets** - HKEX, TSE, SGX, etc.
- **Canadian Markets** - TSX, TSX-V
- **Australian Markets** - ASX

And many more globally!

---

## Prerequisites

Before configuring IBKR in Stonks Overwatch, you need to:

1. **Have an IBKR account** - [Open an account](https://www.interactivebrokers.com/) if you don't have one
2. **Enable Web API access** - Contact IBKR support to enable
3. **Generate OAuth credentials** - Follow the iBind setup process
4. **Have certificates ready** - Generate signature and encryption keys

---

## Creating OAuth Credentials

IBKR uses OAuth 1.0a authentication which requires generating certificates. Follow the comprehensive guide:

### Step-by-Step Setup

Follow the detailed instructions at [iBind - OAuth-1.0a Guide](https://github.com/Voyz/ibind/wiki/OAuth-1.0a)

### Quick Summary

1. **Request Web API Access**
   - Contact IBKR support
   - Request OAuth access for your account

2. **Generate Keys**
   - Create RSA key pairs for signature and encryption
   - Generate DH prime number for encryption

3. **Register with IBKR**
   - Submit your public keys to IBKR
   - Get consumer key and access tokens

4. **Save Credentials**
   - Store private keys securely
   - Note down access token and secret
   - Save DH prime value

> **Important:** Keep your private keys secure! Never share them or commit to version control.

### Required Files

After setup, you'll have:
- `private_signature.pem` - Signature private key
- `private_encryption.pem` - Encryption private key
- Access token and secret (strings)
- Consumer key (string)
- DH prime (long number string)

---

## Configuration

### Directory Structure

Create a directory for your IBKR certificates:

```bash
mkdir -p config/ibkr_certs
# Copy your .pem files here
```

### Basic Configuration

**Minimal setup with OAuth credentials:**

```json
{
  "ibkr": {
    "enabled": true,
    "credentials": {
      "access_token": "YOUR_ACCESS_TOKEN",
      "access_token_secret": "YOUR_ACCESS_TOKEN_SECRET",
      "consumer_key": "YOUR_CONSUMER_KEY",
      "dh_prime": "YOUR_DH_PRIME_NUMBER",
      "encryption_key_fp": "~/Documents/ibkr/private_encryption.pem",
      "signature_key_fp": "~/Documents/ibkr/private_signature.pem"
    }
  }
}
```

### Advanced Configuration

**Complete configuration with all options:**

```json
{
  "ibkr": {
    "enabled": true,
    "credentials": {
      "access_token": "YOUR_ACCESS_TOKEN",
      "access_token_secret": "YOUR_ACCESS_TOKEN_SECRET",
      "consumer_key": "YOUR_CONSUMER_KEY",
      "dh_prime": "YOUR_DH_PRIME_NUMBER",
      "encryption_key_fp": "~/Documents/ibkr/private_encryption.pem",
      "signature_key_fp": "~/Documents/ibkr/private_signature.pem"
    },
    "start_date": "2020-01-01",
    "update_frequency_minutes": 15
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable IBKR integration |
| `credentials.access_token` | string | *required* | OAuth access token |
| `credentials.access_token_secret` | string | *required* | OAuth access token secret |
| `credentials.consumer_key` | string | *required* | OAuth consumer key |
| `credentials.dh_prime` | string | *required* | Diffie-Hellman prime number |
| `credentials.encryption_key_fp` | string | *optional* | **Option 1:** Path to encryption private key (supports `~/path`, `./path`, or `/absolute/path`) |
| `credentials.encryption_key` | string | *optional* | **Option 2:** Direct PEM key content for encryption |
| `credentials.signature_key_fp` | string | *optional* | **Option 1:** Path to signature private key (supports `~/path`, `./path`, or `/absolute/path`) |
| `credentials.signature_key` | string | *optional* | **Option 2:** Direct PEM key content for signature |
| `start_date` | string | `2020-01-01` | Portfolio tracking start date |
| `update_frequency_minutes` | integer | `15` | Data refresh interval in minutes (minimum 15) |

**Note:** For encryption and signature keys, provide **either** the file path (`*_fp`) **or** the direct key content (`*_key`), not both. Direct key values take precedence if both are provided.

---

## Setup Instructions

### 1. Complete OAuth Setup

Follow the [iBind OAuth Guide](https://github.com/Voyz/ibind/wiki/OAuth-1.0a) to generate your credentials and keys.

### 2. Organize Certificate Files

```bash
# Create directory
mkdir -p config/ibkr_certs

# Copy your private keys
cp /path/to/private_signature.pem config/ibkr_certs/
cp /path/to/private_encryption.pem config/ibkr_certs/

# Secure the files (Unix/Mac)
chmod 600 config/ibkr_certs/*.pem
```

### 3. Copy Configuration Template

```bash
cp config/config.json.template config/config.json
```

### 4. Edit Configuration

Open `config/config.json` and add your IBKR credentials:

```json
{
  "ibkr": {
    "enabled": true,
    "credentials": {
      "access_token": "abc123...",
      "access_token_secret": "xyz789...",
      "consumer_key": "TESTCONS",
      "dh_prime": "234892349823...",
      "encryption_key_fp": "config/ibkr_certs/private_encryption.pem",
      "signature_key_fp": "config/ibkr_certs/private_signature.pem"
    }
  }
}
```

### 5. Restart Application

```bash
make run
```

### 6. Verify Connection

Check the dashboard - you should see your IBKR portfolio data.

---

## Features & Usage

### Portfolio Tracking

View your global portfolio:
- Current positions across all markets
- Multi-currency support
- Real-time valuations
- Position P&L tracking

### Update Frequency

Control how often data is refreshed:

```json
{
  "ibkr": {
    "update_frequency_minutes": 30
  }
}
```

**Recommendations:**
- **15 minutes** (default) - Good balance
- **5-10 minutes** - Active trading
- **30-60 minutes** - Long-term investing
- **Higher frequency** - May hit API rate limits

### Unified Dashboard

IBKR integrates seamlessly with other brokers:
- Combined portfolio view
- Total value across all accounts
- Comprehensive asset allocation
- Global diversification analysis

---

## Troubleshooting

### Common Issues

#### OAuth Authentication Failed

**Symptoms:** "Authentication failed" or "Invalid credentials"

**Solutions:**
1. Verify all OAuth credentials in `config.json`
2. Check that private key files exist and are readable
3. Ensure paths to .pem files are correct
4. Verify access token hasn't expired
5. Check that Web API access is enabled for your account

#### Cannot Find Certificate Files

**Symptoms:** "File not found" error for .pem files

**Solutions:**
1. Check file paths in configuration
2. Verify files exist: `ls -l config/ibkr_certs/`
3. Ensure file permissions: `chmod 600 config/ibkr_certs/*.pem`
4. Use absolute paths if relative paths don't work

#### No Data Showing

**Symptoms:** IBKR enabled but no portfolio data

**Solutions:**
1. Check if you have open positions on IBKR
2. Verify Web API is enabled for your account
3. Check logs: `data/logs/stonks-overwatch.log`
4. Contact IBKR support if API access isn't working

#### Connection Timeout

**Symptoms:** "Connection timeout" or "Cannot reach IBKR"

**Solutions:**
1. Check internet connection
2. Verify IBKR Web API is operational
3. Check if using VPN (may cause issues)
4. Wait and retry - might be temporary API issue
5. Increase timeout in settings

#### Rate Limiting

**Symptoms:** "Rate limit exceeded" or "Too many requests"

**Solutions:**
1. Increase `update_frequency_minutes` to reduce API calls
2. Default 15 minutes is usually safe
3. Wait before retrying
4. Check if other applications are using the same credentials

### Debug Mode

Enable debug logging for troubleshooting:

```bash
make run debug=true
```

Check logs at: `data/logs/stonks-overwatch.log`

### Test Configuration

**Verify your configuration:**

```bash
# Check if config file is valid JSON
cat config/config.json | python -m json.tool

# Verify certificate files exist
ls -l config/ibkr_certs/

# Run with debug mode
make run debug=true
```

---

## Technical Details

### API Client

The application uses [iBind](https://github.com/Voyz/ibind), a Python client for IBKR's [Web API](https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/).

**Stonks Overwatch** fetches data from IBKR and stores it locally, providing real-time insights into your global portfolio.

### Database Model

The database model is defined in:
- `src/stonks_overwatch/services/brokers/ibkr/repositories/models.py`

### Architecture

```text
┌─────────────┐      ┌──────────────────┐      ┌──────────────┐
│   Stonks    │─────▶│     iBind        │─────▶│   IBKR Web   │
│  Overwatch  │◀─────│  (Python OAuth)  │◀─────│     API      │
└─────────────┘      └──────────────────┘      └──────────────┘
       │
       ▼
┌─────────────┐
│   Local     │
│  Database   │
│  (SQLite)   │
└─────────────┘
```

### Data Flow

1. **Authenticate** - OAuth 1.0a with signature verification
2. **Fetch** - Retrieve positions and account data
3. **Transform** - Convert to internal format
4. **Store** - Save to local database
5. **Display** - Show in dashboard

### API Limitations

> **Note:** IBKR Web API has some limitations:

- **Transaction History**: Only last 90 days available
- **Deposits/Withdrawals**: Not provided by API
- **Fee Information**: Limited fee data available
- **Historical Data**: Depends on your account data subscription

These are API limitations, not application limitations.

---

## Advanced Topics

### Testing New iBind Versions

To test a development version of iBind:

1. **Clone iBind:**

   ```bash
   git clone https://github.com/Voyz/ibind
   cd ibind
   ```

2. **Make your changes**

3. **Update version in `pyproject.toml`:**

   ```toml
   [tool.poetry]
   version = "0.1.15.dev1"
   ```

4. **Build and install:**

   ```bash
   # Build the package
   poetry build

   # Install in Stonks Overwatch
   cd /path/to/stonks-overwatch
   poetry add path/to/ibind/dist/ibind-0.1.15.dev1-py3-none-any.whl
   ```

### Using a Fork

To use a forked version of iBind:

**Update `pyproject.toml`:**

```toml
[tool.poetry.dependencies]
ibind = { git = "https://github.com/YOUR_USERNAME/ibind.git", branch = "main" }
```

**Then reinstall:**

```bash
poetry lock
poetry install
```

---

## Security & Privacy

### Data Security

- **OAuth 1.0a** - Industry-standard secure authentication
- **RSA encryption** - Private keys for secure communication
- **Local storage** - All data stored on your computer
- **No cloud sync** - Data never sent to external servers
- **HTTPS only** - All IBKR API calls use HTTPS

### Security Best Practices

1. **Protect private keys** - Never share or commit .pem files
2. **Secure file permissions** - `chmod 600` on certificate files
3. **Use strong encryption** - Keep your private keys secure
4. **Regular updates** - Keep iBind and Stonks Overwatch updated
5. **Backup certificates** - Keep secure backup of your keys

### Permissions

Stonks Overwatch requires **read-only** access to your IBKR account. It can:
- ✅ View portfolio and positions
- ✅ View account information
- ✅ View available transaction data (last 90 days)
- ❌ Cannot execute trades
- ❌ Cannot withdraw funds
- ❌ Cannot change account settings

---

## FAQ

### How complex is IBKR setup?

IBKR setup is more involved than other brokers due to OAuth requirements. Follow the [iBind guide](https://github.com/Voyz/ibind/wiki/OAuth-1.0a) carefully.

### Can I use multiple IBKR accounts?

Currently, one IBKR account per configuration. Multi-account support is planned for a future release.

### Why only 90 days of transaction history?

This is an IBKR Web API limitation. The API only provides the last 90 days of transactions.

### Does this work with IBKR Lite?

Yes, it works with both IBKR Pro and IBKR Lite accounts, subject to Web API availability.

### What if my credentials expire?

OAuth credentials should not expire unless revoked. If they do, regenerate them following the setup process.

---

## Support & Resources

### Documentation

- **[Quickstart Guide](Quickstart.md)** - Get started quickly
- **[FAQ](FAQ.md)** - Common questions
- **[Troubleshooting](#troubleshooting)** - Fix common issues

### IBKR Resources

- **[IBKR Website](https://www.interactivebrokers.com/)** - Official site
- **[IBKR Web API Docs](https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/)** - API documentation
- **[iBind GitHub](https://github.com/Voyz/ibind)** - OAuth client
- **[iBind OAuth Guide](https://github.com/Voyz/ibind/wiki/OAuth-1.0a)** - Setup instructions
- **[IBKR Support](https://www.interactivebrokers.com/en/support/cstools/cstools.php)** - IBKR help

### Community Support

- **[GitHub Discussions](https://github.com/ctasada/stonks-overwatch/discussions)** - Ask questions
- **[GitHub Issues](https://github.com/ctasada/stonks-overwatch/issues)** - Report bugs
- **Email** - carlos.tasada@gmail.com

---

## Next Steps

After setting up IBKR:

1. **Configure other brokers** - [DEGIRO](DEGIRO.md) • [Bitvavo](Bitvavo.md)
2. **Explore features** - Check the [User Guide](Home.md)
3. **Customize settings** - Adjust update frequency
4. **Set up backups** - Backup your `data/` directory and certificates

---

**Need help?** Check the [FAQ](FAQ.md) or [open an issue](https://github.com/ctasada/stonks-overwatch/issues)!
