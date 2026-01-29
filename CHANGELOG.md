# Changelog

All notable changes to this project are documented in this file.

_This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html)._

---

## [0.3.0] - 2026-01-29

### Added

- **Configuration:** Added support to configure IBKR broker
- **Broker Selector:**
  - When starting now it's possible to choose the broker. This allows to use any of the available brokers, and removes
  a limitation that was enforcing to have a DEGIRO account
  - Adds possibility to use *only** DEGIRO, Bitvavo or IBKR
- **UI:**
  - Added a new Dark theme. Now it's possible to choose between dark/light/system themes

### Changed

- **Configuration:** Different UI/UX improvements
- **Brokers:** Hidden not supported broker capabilities
  - When a broker does not support a certain feature, it will not be shown in the UI
- **Demo Mode:** Demo mode has now some minor visual improvements

### Fixed

- **Configuration Menu:** Cosmetic fix to guarantee the Configuration menu is drawn properly

### Security

- Routine dependency updates for security and stability

---

## [0.2.1] - 2025-12-26

### Fixed

- **Flatpak version crashes on startup:**
    - Executing the Flatpak application was crashing due to mismanaged Linux loading configuration ([#256](https://github.com/ctasada/stonks-overwatch/issues/256))
- **Login:**
    - Fixed race condition in the login screen. After introducing the credentials, the "2FA" screen could stay stuck or the "Loading" screen may not be shown
- **Native Application:**
    - Application Settings were not being shown correctly in some cases
- **Settings:**
    - Cosmetic fix to the TOTP progress bar

### Security

- Routine dependency updates for security and stability

---

## [0.2.0] - 2025-12-05

### Added

- **Application:**
    - Added "Demo Mode" for exploring the application without a broker connection
    - Added "Configuration" submenu to the sidebar
        - Added option to see the release notes
        - Added option to report issues on GitHub
        - Added Broker configuration settings
- **Dividends**:
    - Added diversification filter by year
    - Added calendar navigation bars to quickly switch between years
    - Added total dividends per year in the calendar view
- Enhanced table functionality at **Deposits**, **Fees**, **Trades**, and **Account Statement** sections:
    - Added ability to show/hide columns
    - Added ability to show all the rows in a single page

### Removed

- Removed license controls to make the application open source and free to use

### Changed

- Add stability indicators for broker integrations and tooltips for unstable portfolios
- **Portfolio**:
    - Minor terminology changes for better clarity
- **Diversification**:
    - Show "Crypto" after "Sectors" to keep all "Stocks" related data together

### Fixed

- **Portfolio**:
    - Exchanges: Fixed bug skipping the Exchange name in some cases
- **Diversification**:
    - Percentages are now properly based on the type
- **Dividends**:
    - Correctly display selected year in dividends calendar dropdown
- **DEGIRO**:
    - Fixed bug wrongly calculating the Realised Gains for some transactions

### Security

- Routine dependency updates for security and stability
- Fixed permission issue when downloading Stonks Overwatch update installers

---

## [0.1.5] - 2025-10-27

### Changed

- Enhanced the style of the diversification icons

### Fixed

- Multiple sidebar style fixes
- Fixed some style inconsistencies across the application
- Fixed sector handling: Unknown sectors are now properly group under "Unknown"
- **DEGIRO**:
    - Fixed calculation of daily cash
    - Fixed sorting of cash movements

### Security

- Routine dependency updates for security and stability

---

## [0.1.4] - 2025-09-25

### Added

- **DEGIRO Crypto:**
    - Support for crypto assets and product types
    - Internal database now stores crypto decimals
- **Dividends:**
    - Added 'Ex-Dividend' date
    - Added tooltip showing the Gross/Tax dividend breakdown
- **Application:**
    - Added "Release Notes" information
    - Added "Demo Mode" for exploring the application without a broker connection

### Changed

- Installers now include OS name in filenames
- Update Download dialog shows percentage and downloaded size
- Unified icons in Diversification section across the application
- Added page size selector to the Fees, Deposits, Trades and Account Statement tables

### Fixed

- Logs streamlined for readability
- Sidebar portfolio selector only clickable with multiple portfolios
- **DEGIRO**:
    - Fixed portfolio data fetching issue
    - Fixed bug showing forecasted dividends
- Application: "License Expiration" dialog now displays correctly

### Security

- Routine dependency updates for security and stability

---

## [0.1.3] - 2025-08-30

### Added

- **DEGIRO:** 'In App' 2FA authentication support

### Changed

- Redesigned and collapsible navigation sidebar for improved usability
- Internal code improvements

### Fixed

- Default values in broker configurations
- Fee amount display bug

### Security

- Routine dependency updates for security and stability

---

## [0.1.2] - 2025-08-22

### Added

- Automatic update checks

### Changed

- Improved License dialog
- Internal code improvements

### Fixed

- **Windows:**
    - Crash on application open
    - Application icon display
    - Main menu display
    - Installer path issue

### Security

- Routine dependency updates for security and stability

---

## [0.1.1] - 2025-08-13

### Added

- **DEGIRO Credentials:**
    - "Settings" dialog for credentials and 2FA token
    - "Remember me" checkbox in login dialog
    - Credentials stored securely with AES-128-CBC encryption
- **Updates:**
    - "Check for updates" menu item
    - "Update available" notification

### Changed

- Internal refactor to support more brokers

### Security

- Routine dependency updates for security and stability

---

## [0.1.0] - 2025-07-15

### Initial Release

- Connect to DEGIRO with credentials and 2FA
- Automatic DEGIRO information updates
- Dashboard with portfolio growth
- Portfolio, Dividends, Fees, Deposits, Trades, and full Account Statement
- Diversification information
- Installers for macOS, Windows, and Linux

---

<!-- Version Comparison Links -->
[Unreleased]: https://github.com/ctasada/stonks-overwatch/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/ctasada/stonks-overwatch/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/ctasada/stonks-overwatch/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/ctasada/stonks-overwatch/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/ctasada/stonks-overwatch/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ctasada/stonks-overwatch/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ctasada/stonks-overwatch/releases/tag/v0.1.0
