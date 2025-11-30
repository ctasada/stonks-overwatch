# Native Application Guide

> **Audience:** End users
>
> **Summary:** Guide for installing and using the Stonks Overwatch native desktop application

---

## Overview

Stonks Overwatch is available as a **native desktop application** for Windows, macOS, and Linux. The native app provides a seamless, OS-integrated experience while maintaining the same functionality as the web version.

### Why Use the Native App?

- **🖥️ Native Experience** - Feels like a true desktop application
- **🚀 No Setup Required** - No Python, Poetry, or dependencies needed
- **🔔 System Notifications** - Get alerts for portfolio updates
- **⚡ Faster Startup** - Optimized for quick access
- **📱 System Integration** - Menus, shortcuts, and OS features
- **🔒 Same Privacy** - All data stays local on your machine

---

## Installation

### Download

Download the latest version for your operating system:

- **macOS** - `Stonks_Overwatch-{version}-macos.dmg` - [Download](https://github.com/ctasada/stonks-overwatch/releases/latest)
- **Windows** - `Stonks_Overwatch-{version}-windows.msi` - [Download](https://github.com/ctasada/stonks-overwatch/releases/latest)
- **Linux** - `Stonks_Overwatch-{version}-x86_64-linux.flatpak` - [Download](https://github.com/ctasada/stonks-overwatch/releases/latest)

### Install Instructions

#### macOS

1. Download `Stonks_Overwatch-{version}-macos.dmg` (e.g., `Stonks_Overwatch-0.1.5-macos.dmg`)
2. Open the DMG file
3. Drag **Stonks Overwatch** to your Applications folder
4. Open from Applications (first launch may require security approval)

**Security Note**: On first launch, macOS may show a security warning. Go to **System Preferences → Security & Privacy** and click "Open Anyway".

#### Windows

1. Download `Stonks_Overwatch-{version}-windows.msi` (e.g., `Stonks_Overwatch-0.1.5-windows.msi`)
2. Double-click to run the installer
3. Follow the installation wizard
4. Launch from Start Menu or Desktop shortcut

**Security Note**: Windows SmartScreen may show a warning. Click "More info" and then "Run anyway".

#### Linux (Flatpak)

1. Download `Stonks_Overwatch-{version}-x86_64-linux.flatpak` (e.g., `Stonks_Overwatch-0.1.5-x86_64-linux.flatpak`)

2. Install the Flatpak:

   ```bash
   flatpak install Stonks_Overwatch-0.1.5-x86_64-linux.flatpak
   ```

3. Run the application:

   ```bash
   flatpak run com.caribay.stonks_overwatch
   ```

Or launch from your application menu.

**Note**: If you don't have Flatpak installed, install it first:

```bash
# Ubuntu/Debian
sudo apt install flatpak

# Fedora
sudo dnf install flatpak

# Arch Linux
sudo pacman -S flatpak
```

---

## First Launch

### Initial Setup

On first launch, you'll be prompted to configure your brokers:

1. **Welcome Screen** - Introduction and overview
2. **Broker Configuration** - Set up your broker credentials
3. **Initial Sync** - Download your portfolio data
4. **Dashboard** - View your investments

### Configuration Files

The native app stores data in OS-specific locations:

**macOS:**

```text
~/Library/Application Support/com.caribay.stonks_overwatch/  # Data
~/Library/Preferences/com.caribay.stonks_overwatch/          # Config
~/Library/Logs/com.caribay.stonks_overwatch/                 # Logs
~/Library/Caches/com.caribay.stonks_overwatch/               # Cache
```

**Windows:**

```text
%APPDATA%\Stonks Overwatch\            # Data & Config
%LOCALAPPDATA%\Stonks Overwatch\Logs\  # Logs
%LOCALAPPDATA%\Stonks Overwatch\Cache\ # Cache
```

**Linux:**

```text
~/.local/share/stonks-overwatch/   # Data
~/.config/stonks-overwatch/        # Config
~/.cache/stonks-overwatch/         # Cache
~/.local/share/stonks-overwatch/logs/ # Logs
```

---

## Features

### Main Features

- **📊 Dashboard** - Portfolio overview with performance charts
- **💼 Portfolio View** - Detailed holdings across all brokers
- **💰 Dividends** - Track dividend payments and forecasts
- **📈 Trades** - Transaction history and analysis
- **💸 Fees & Deposits** - Monitor costs and contributions
- **📑 Account Statement** - Complete transaction log
- **🎯 Diversification** - Asset allocation by sector, region, and type

### Native App Exclusive Features

- **🔔 Update Notifications** - Get alerts when updates are available
- **⚙️ Settings Dialog** - Manage broker credentials securely
- **📤 Export Database** - Backup your data with one click
- **🗑️ Clear Cache** - Free up space and reset data
- **📋 System Logs** - View application logs for troubleshooting
- **🔄 Auto-Updates** - Stay current with the latest features

---

## Using the Application

### Navigation

The application uses a **sidebar navigation** to access different sections:

- **Dashboard** - Main overview
- **Portfolio** - Current holdings
- **Dividends** - Dividend tracking
- **Trades** - Transaction history
- **Fees** - Fee analysis
- **Deposits** - Cash movements
- **Statement** - Complete account history

### Broker Switching

If you have multiple brokers configured, use the **broker selector** at the top of the sidebar to switch between them or view all portfolios combined.

### Refreshing Data

- **Manual Refresh** - Click the refresh icon in the toolbar
- **Auto-Refresh** - Data automatically updates every 15 minutes (configurable)

---

## Configuration

### Broker Settings

Access broker configuration through:

1. **Menu Bar** → **Preferences** (macOS) / **Settings** (Windows/Linux)
2. Select the broker tab
3. Enter or update credentials
4. Save changes

### Application Settings

Configure application behavior:

- **Auto-refresh interval** - How often to sync data
- **Startup behavior** - Launch on system startup
- **Notifications** - Enable/disable alerts
- **Theme** - Light/dark mode (follows system)

---

## Troubleshooting

### Debug Mode

Run the application in debug mode to get detailed logs:

**macOS:**

```bash
DEBUG=true open -n /Applications/Stonks\ Overwatch.app/
```

**Windows:**

```cmd
set DEBUG=true && "C:\Program Files\Stonks Overwatch\Stonks Overwatch.exe"
```

**Linux:**

```bash
DEBUG=true flatpak run com.caribay.stonks_overwatch
```

### View Logs

Access application logs:

- **macOS**: Menu → **Help** → **Show Logs**
- **Windows**: Menu → **Help** → **Show Logs**
- **Linux**: Help menu → Show Logs

Or manually navigate to the logs directory (see [Configuration Files](#configuration-files)).

### Common Issues

#### Application Won't Start

**Problem**: App crashes or doesn't launch

**Solutions**:
1. Check system requirements (see below)
2. Run in debug mode to see error messages
3. Clear cache: Delete cache directory
4. Reinstall the application

#### Can't Login to Broker

**Problem**: Broker authentication fails

**Solutions**:
1. Verify credentials in Settings
2. Check if 2FA is required (DEGIRO)
3. Ensure internet connection is working
4. Check logs for specific error messages

#### Database Errors

**Problem**: Data not loading or corrupting

**Solutions**:
1. Export current database (backup)
2. Clear cache
3. Force refresh data
4. If persistent, delete database and re-sync

#### Performance Issues

**Problem**: Application is slow or unresponsive

**Solutions**:
1. Clear cache
2. Reduce auto-refresh frequency
3. Check system resources (RAM, CPU)
4. Update to latest version

---

## Advanced Features

### Exporting Data

Export your database for backup or analysis:

1. **Menu** → **Tools** → **Export Database**
2. Choose save location
3. Database saved as JSON file

### Importing Data

Restore from a previous export:

1. **Menu** → **Tools** → **Import Database**
2. Select JSON file
3. Confirm import (this replaces current data)

### Web Inspector (Debug UI)

Enable web inspector for debugging the UI (developers):

**macOS:**

```bash
defaults write com.caribay.stonks-overwatch WebKitDeveloperExtras -bool true
```

Then:
1. Open the application
2. Open Safari
3. Go to **Develop** menu
4. Select your app's window
5. Inspect the console for errors

---

## Updates

> **Note:** Automatic updates are only available in the native desktop application. If you're running the web version (via `make run`), you'll need to update manually using `git pull` and `make install`.

### How Updates Work

Stonks Overwatch automatically checks for new releases on [GitHub](https://github.com/ctasada/stonks-overwatch/releases). When a new version is available, you'll receive a notification in the app.

### Automatic Updates

The native application checks for updates automatically:

1. When an update is available, you'll see a notification
2. Click **Download Update**
3. Update downloads in the background (shows progress)
4. Restart the application to install

### Manual Update Check

Check for updates manually:

- **Menu** → **Help** → **Check for Updates**

Configure in Settings.

---

## System Requirements

### Minimum Requirements

**All Platforms:**
- 2 GB RAM
- 500 MB disk space
- Internet connection (for broker data sync)

**macOS:**
- macOS 10.14 (Mojave) or later
- 64-bit Intel or Apple Silicon

**Windows:**
- Windows 10 or later
- 64-bit processor

**Linux:**
- Modern 64-bit distribution
- GTK+ 3.0 or later
- X11 or Wayland

### Recommended

- 4 GB RAM
- 1 GB disk space
- Broadband internet connection

---

## Security & Privacy

### Data Storage

All data is stored **locally** on your computer:
- Portfolio data
- Transaction history
- Broker credentials (encrypted)

**No data is sent to external servers** except when syncing with your configured brokers.

### Credential Security

Broker credentials are:
- Encrypted using **AES-128-CBC** (via Python Fernet)
- Stored in OS keychain when available
- Never transmitted except to your broker

### Network Access

The application only connects to:
- Your configured broker APIs
- GitHub (for update checks)

No analytics or tracking.

---

## Uninstalling

### macOS

1. Open Applications folder
2. Drag **Stonks Overwatch** to Trash
3. To remove all data:

   ```bash
   rm -rf ~/Library/Application\ Support/com.caribay.stonks_overwatch
   rm -rf ~/Library/Preferences/com.caribay.stonks_overwatch
   rm -rf ~/Library/Caches/com.caribay.stonks_overwatch
   rm -rf ~/Library/Logs/com.caribay.stonks_overwatch
   ```

### Windows

1. **Settings** → **Apps** → **Stonks Overwatch**
2. Click **Uninstall**
3. To remove all data, delete:
   - `%APPDATA%\Stonks Overwatch\`
   - `%LOCALAPPDATA%\Stonks Overwatch\`

### Linux

1. Uninstall the Flatpak:

   ```bash
   flatpak uninstall com.caribay.stonks_overwatch
   ```

2. Remove data directories (optional):

   ```bash
   rm -rf ~/.local/share/stonks-overwatch
   rm -rf ~/.config/stonks-overwatch
   rm -rf ~/.cache/stonks-overwatch
   ```

---

## FAQ

### Can I use both web and native apps?

Yes! Both use the same data if pointed to the same database file. However, the native app stores data in OS-specific locations by default.

### How do I migrate from web to native?

1. Export database from web version (`make run` → export)
2. Import into native app (**Tools** → **Import Database**)

### Does the native app work offline?

Yes, with limitations. You can view existing data offline, but syncing with brokers requires an internet connection.

### How often does data refresh?

Default is every 15 minutes. You can configure this in Settings or manually refresh anytime.

### Where can I report bugs?

[Open an issue](https://github.com/ctasada/stonks-overwatch/issues/new?template=bug_report.md) on GitHub.

---

## Support

Need help? Here's where to get support:

- **📚 Documentation** - [Read the docs](Home.md)
- **❓ FAQ** - [Check the FAQ](FAQ.md)
- **🐛 Bug Reports** - [Open an issue](https://github.com/ctasada/stonks-overwatch/issues)
- **💬 Discussions** - [GitHub Discussions](https://github.com/ctasada/stonks-overwatch/discussions)
- **📧 Email** - carlos.tasada@gmail.com

---

## See Also

- **[Quickstart Guide](Quickstart.md)** - Install and run from source
- **[Developer Guide](Developing-Stonks-Overwatch.md)** - Build the app yourself
- **[Broker Setup](Home.md#broker-documentation)** - Configure your brokers

---

**Enjoy using Stonks Overwatch!** 🚀

If you find the app useful, please ⭐ [star it on GitHub](https://github.com/ctasada/stonks-overwatch)!
