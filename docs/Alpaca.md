# # ![Alpaca](images/brokers/alpaca.png) Alpaca Markets Integration Guide

Alpaca Markets is a commission-free US stock broker supported by **Stonks Overwatch**, providing API-first access to your equity positions, orders, dividends, and cash activities.

## Overview

### Features

- ✅ **Commission-free trading** - No fees on US stock orders
- ✅ **Real-time portfolio tracking** - Live position data from the Trading API
- ✅ **Transaction history** - Complete filled-order records
- ✅ **Dividend tracking** - Automatic detection of all dividend types
- ✅ **Deposit & withdrawal tracking** - Cash flow history
- ✅ **Account overview** - Equity, cash, and buying power at a glance
- ✅ **Paper trading support** - Test with a simulated account
- ✅ **API key authentication** - Simple and secure, no session required
- ✅ **Multi-currency** - USD base currency with portfolio conversion

### Supported Markets

Alpaca provides access to:

- **US Equities** - NYSE, NASDAQ, AMEX (all US-listed stocks and ETFs)
- **Fractional shares** - Buy and sell fractional positions

> **Note:** Crypto trading is available on Alpaca but is not yet tracked by Stonks Overwatch.

---

## Prerequisites

Before configuring Alpaca in Stonks Overwatch, you need:

1. **An Alpaca account** - [Sign up for free](https://app.alpaca.markets/signup)
2. **API keys** - Generated from the Alpaca dashboard (see below)

No special access requests or approval processes are needed — API keys are available immediately after signing up.

---

## Creating API Keys

Alpaca uses a single API key pair that authenticates against both the Trading API and the Market Data API. You do **not** need separate keys for market data.

### Step-by-Step

1. Log in to [app.alpaca.markets](https://app.alpaca.markets)
2. Click your account name in the top-right corner → **Your API Keys**
3. Under **Live Trading** (or **Paper Trading** for a simulated account), click **Generate New Key**
4. Copy both the **API Key ID** and the **Secret Key** — the secret is only shown once

> **Keep your Secret Key safe!** It cannot be retrieved after the initial display. If lost, generate a new key pair.

### Live vs Paper Trading

Alpaca issues separate key pairs for live and paper accounts:

| Environment | Purpose | Key source |
|---|---|---|
| **Live** | Real money, real positions | Live keys from the dashboard |
| **Paper** | Simulated trading, test data | Paper keys from the dashboard |

Set `paper_trading: true` in the configuration to connect to the paper trading environment. All API calls will use `paper-api.alpaca.markets` automatically.

---

## Getting Started

### Initial Setup

When you first launch Stonks Overwatch, you'll be presented with a broker selection screen. Select Alpaca to begin the authentication process.

### Authentication

1. Enter your **API Key ID**
2. Enter your **Secret Key**
3. Choose whether this is a **Paper Trading** account
4. Click **Login**

Your credentials are validated by calling the Alpaca account endpoint. On success, you'll be redirected to the dashboard and an immediate data sync will begin.

---

## Configuring Credentials

After your initial login, you can configure Alpaca to automatically authenticate on startup.

### Via Settings (Web Application)

1. Navigate to the **Settings** page (sidebar menu)
2. Locate the **Alpaca** section
3. Enter your credentials:
   - API Key ID
   - Secret Key
   - Paper Trading toggle (on/off)
4. Configure additional options:
   - Enable/disable the broker
   - Set update frequency
5. Click **Save**

### Via Preferences (Native Application)

1. Open **Preferences** from the application menu
2. Select the **Brokers** tab
3. Configure Alpaca credentials and settings
4. Click **Save**

Your credentials are encrypted and stored securely in the local database.

---

## Advanced Settings

### Paper Trading Mode

When `paper_trading` is enabled, all API calls route to Alpaca's paper trading environment (`paper-api.alpaca.markets`). This is useful for:

- Testing the integration without risking real money
- Validating configuration before going live
- Development and debugging

Switch between paper and live by toggling the **Paper Trading** option in Settings and re-authenticating.

### Update Frequency

Control how often data is refreshed from Alpaca. Configure this in Settings (default: 15 minutes).

**Recommendations:**

- **15 minutes** (default) - Good balance for most investors
- **5-10 minutes** - More active monitoring
- **30-60 minutes** - Passive, long-term investing
- Avoid very short intervals to stay within Alpaca rate limits

### Market Data Tier

Alpaca provides two market data feeds:

| Feed | Tier | Coverage |
|---|---|---|
| **IEX** | Free | IEX Exchange quotes (sufficient for portfolio valuation) |
| **SIP** | Algo Trader Plus ($99/mo) | All US exchanges consolidated |

Stonks Overwatch always requests the **IEX feed** explicitly, which works on free accounts and avoids subscription errors. If you have a paid plan, SIP data is automatically used by Alpaca when it is the better source.

---

## Troubleshooting

### Common Issues

#### Invalid Credentials

**Symptoms:** "Invalid API credentials" or login fails immediately

**Solutions:**

1. Verify the API Key ID and Secret Key are entered correctly (no extra spaces)
2. Confirm the key is for the correct environment (live vs paper)
3. Regenerate the key from [app.alpaca.markets](https://app.alpaca.markets) if it was lost
4. Check if the key has been revoked or deleted

#### No Portfolio Data

**Symptoms:** Alpaca is enabled but the portfolio is empty

**Solutions:**

1. Confirm you have open positions on Alpaca
2. Trigger a manual sync via the update button in the dashboard
3. Check logs: `data/logs/stonks-overwatch.log`
4. Verify the API key has the correct permissions (paper keys can only see paper positions)

#### Market Data Errors

**Symptoms:** Prices show as 0 or "subscription does not permit querying recent SIP data"

**Solutions:**

1. Ensure you are using live API keys (not paper keys for the data endpoint)
2. This error is expected on free accounts when SIP data is requested — Stonks Overwatch uses IEX by default to avoid it
3. If the error persists, check your [Alpaca subscription level](https://alpaca.markets/data)

#### Rate Limiting

**Symptoms:** "Too many requests" or errors on rapid updates

**Solutions:**

1. Increase the update frequency in Settings (minimum 15 minutes recommended)
2. Wait a few minutes and retry
3. Check if another application is using the same API key simultaneously

#### Connection Timeout

**Symptoms:** "Connection timeout" or "Cannot reach Alpaca"

**Solutions:**

1. Check your internet connection
2. Verify [Alpaca's status page](https://status.alpaca.markets)
3. Disable any VPN or proxy that may be blocking the connection
4. Check for firewall rules blocking outbound HTTPS

### Debug Mode

Enable debug logging for troubleshooting:

```bash
make run debug=true
```

Check logs at: `data/logs/stonks-overwatch.log`

---

## For Developers

### Manual Configuration via config.json

Developers can configure Alpaca credentials directly in the `config/config.json` file for testing and development purposes.

#### Basic Configuration

**Minimal setup (live account):**

```json
{
  "alpaca": {
    "enabled": true,
    "credentials": {
      "api_key": "YOUR_ALPACA_API_KEY_ID",
      "secret_key": "YOUR_ALPACA_SECRET_KEY",
      "paper_trading": false
    }
  }
}
```

#### Paper Trading Configuration

**For simulated accounts:**

```json
{
  "alpaca": {
    "enabled": true,
    "credentials": {
      "api_key": "YOUR_PAPER_API_KEY_ID",
      "secret_key": "YOUR_PAPER_SECRET_KEY",
      "paper_trading": true
    }
  }
}
```

#### Advanced Configuration

**Complete configuration with all options:**

```json
{
  "alpaca": {
    "enabled": true,
    "offline_mode": false,
    "credentials": {
      "api_key": "YOUR_ALPACA_API_KEY_ID",
      "secret_key": "YOUR_ALPACA_SECRET_KEY",
      "paper_trading": false
    },
    "start_date": "2020-01-01",
    "update_frequency_minutes": 15
  }
}
```

#### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable Alpaca integration |
| `offline_mode` | boolean | `false` | Use cached data only (no API calls) |
| `credentials.api_key` | string | *required* | Your Alpaca API Key ID |
| `credentials.secret_key` | string | *required* | Your Alpaca Secret Key |
| `credentials.paper_trading` | boolean | `false` | Connect to the paper trading environment |
| `start_date` | string | `2020-01-01` | Portfolio tracking start date (YYYY-MM-DD) |
| `update_frequency_minutes` | integer | `15` | Data refresh interval in minutes |

#### Setup Steps

1. Copy the configuration template:

   ```bash
   cp config/config.json.template config/config.json
   ```

2. Edit `config/config.json` with your Alpaca credentials

3. Start the application:

   ```bash
   make run
   ```

**Note:** The `config.json` file is encrypted and never committed to version control. For production use, configure credentials via the Settings UI instead.

### Configuration Validation

**Verify your configuration:**

```bash
# Check if config file is valid JSON
cat config/config.json | python -m json.tool

# Test with demo mode first
make run demo=true
```

---

## Technical Details

### API Client

The application uses [alpaca-py](https://github.com/alpacahq/alpaca-py), the official Python SDK for the Alpaca Markets API.

Three mechanisms are used — all with the same API key pair:

| Mechanism | Used for |
|---|---|
| `alpaca-py TradingClient` | Positions, orders, account info |
| `alpaca-py StockHistoricalDataClient` | Latest stock prices (IEX feed) |
| Raw HTTP `GET /v2/account/activities` | Dividends, deposits, withdrawals |

**Stonks Overwatch** fetches data from Alpaca and stores it locally in SQLite, providing portfolio insights without requiring a live connection for every page view.

### Database Models

The database models are defined in:

- `src/stonks_overwatch/services/brokers/alpaca/repositories/models.py`

| Model | Description |
|---|---|
| `AlpacaPosition` | Open positions synced from the Trading API |
| `AlpacaOrder` | Filled orders (completed buy/sell transactions) |
| `AlpacaActivity` | Account activities: dividends, deposits, withdrawals |

### Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                  Stonks Overwatch                       │
│                                                         │
│  PortfolioService  TransactionService  DividendService  │
│  DepositService    AccountService      UpdateService     │
│         │                │                  │           │
│         └────────────────┼──────────────────┘           │
│                          │                              │
│              AlpacaClient (singleton)                   │
└──────────────┬───────────┴───────────────┬──────────────┘
               │                           │
      ┌────────▼────────┐        ┌─────────▼─────────┐
      │  alpaca-py SDK  │        │   Raw HTTP         │
      │  TradingClient  │        │   /v2/account/     │
      │  DataClient     │        │   activities       │
      └────────┬────────┘        └─────────┬──────────┘
               │                           │
               └──────────┬────────────────┘
                          │ HTTPS
               ┌──────────▼──────────┐
               │   Alpaca Markets    │
               │   Trading API       │
               │   Market Data API   │
               └─────────────────────┘
```

### Data Flow

1. **Authenticate** - API key pair validated via `GET /v2/account`
2. **Sync** - `UpdateService` fetches positions, orders, and activities from Alpaca
3. **Store** - Data saved to local SQLite database
4. **Read** - Portfolio/transaction/dividend services read from the local DB
5. **Prices** - Latest prices fetched live from the Market Data API when viewing the portfolio
6. **Display** - Dashboard shows your Alpaca portfolio alongside other brokers

### Dividend Activity Types

Alpaca reports dividends through account activities. Stonks Overwatch captures all standard types:

| Activity Type | Description |
|---|---|
| `DIV` | Regular cash dividend |
| `DIVCGL` | Capital gain — long term |
| `DIVCGS` | Capital gain — short term |
| `DIVFT` | Foreign tax withheld |
| `DIVNRA` | Non-resident alien tax withheld |
| `DIVROC` | Return of capital |
| `DIVTXEX` | Tax-exempt dividend |

### Services Registered

| Service | Status |
|---|---|
| Portfolio | Registered |
| Transaction | Registered |
| Account | Registered |
| Deposit | Registered |
| Dividend | Registered |
| Authentication | Registered |
| Update | Registered |
| Fee | Not applicable (Alpaca is commission-free) |

---

## Security & Privacy

### Data Security

- **Local storage** - All data stored on your computer
- **Encrypted credentials** - Config file credentials are encrypted
- **No cloud sync** - Data never sent to external servers
- **HTTPS only** - All Alpaca API calls use HTTPS
- **Read-only access** - API keys are used only to read account data

### Security Best Practices

1. **Protect your Secret Key** - Never share it or commit it to version control
2. **Revoke unused keys** - Delete old keys from [app.alpaca.markets](https://app.alpaca.markets)
3. **Use paper keys for testing** - Avoid using live keys in development
4. **Enable 2FA on Alpaca** - Protect your Alpaca account with two-factor authentication
5. **Backup data** - Regular backups of the `data/` directory

### Permissions

Stonks Overwatch requires **read-only** access to your Alpaca account. It can:

- ✅ View portfolio positions
- ✅ View filled orders (transaction history)
- ✅ View account information (equity, cash, buying power)
- ✅ View account activities (dividends, deposits, withdrawals)
- ✅ Fetch current market prices
- ❌ Cannot execute trades
- ❌ Cannot withdraw funds
- ❌ Cannot change account settings

---

## FAQ

### Do I need a paid Alpaca subscription?

No. A free account is sufficient for portfolio tracking. The IEX market data feed is used for price quotes, which is included in the free tier.

### What is the difference between live and paper trading keys?

Alpaca issues two separate key pairs per account — one for the live (real money) environment and one for the paper (simulated) environment. They are not interchangeable. Make sure to use the correct pair and enable the `paper_trading` flag accordingly.

### Can I use multiple Alpaca accounts?

Currently, one Alpaca account per configuration. Multi-account support is planned for a future release.

### Why does my portfolio show no prices?

If latest prices cannot be fetched (e.g., during market hours with network issues), Stonks Overwatch falls back to the last stored price from the most recent sync. This is expected behavior.

### Is my data shared with anyone?

No. All data stays on your local computer. No telemetry or analytics are collected.

### What happens if I regenerate my API key on Alpaca?

Your old key becomes invalid immediately. Update the key in Stonks Overwatch Settings and re-authenticate to restore the connection.

---

## Support & Resources

### Documentation

- **[Quickstart Guide](Quickstart.md)** - Get started quickly
- **[FAQ](FAQ.md)** - Common questions
- **[Troubleshooting](#troubleshooting)** - Fix common issues

### Alpaca Resources

- **[Alpaca Website](https://alpaca.markets)** - Official site
- **[Alpaca Dashboard](https://app.alpaca.markets)** - Manage your account and API keys
- **[Alpaca API Docs](https://docs.alpaca.markets)** - Full API reference
- **[alpaca-py SDK](https://github.com/alpacahq/alpaca-py)** - Official Python SDK
- **[Alpaca Status](https://status.alpaca.markets)** - API status page

### Community Support

- **[GitHub Discussions](https://github.com/ctasada/stonks-overwatch/discussions)** - Ask questions
- **[GitHub Issues](https://github.com/ctasada/stonks-overwatch/issues)** - Report bugs
- **Email** - carlos.tasada@gmail.com

---

## Next Steps

After setting up Alpaca:

1. **Configure other brokers** - [DEGIRO](DEGIRO.md) • [Bitvavo](Bitvavo.md) • [IBKR](IBKR.md)
2. **Explore features** - Check the [User Guide](Home.md)
3. **Customize settings** - Adjust update frequency and preferences
4. **Set up backups** - Backup your `data/` directory regularly

---

**Need help?** Check the [FAQ](FAQ.md) or [open an issue](https://github.com/ctasada/stonks-overwatch/issues)!
