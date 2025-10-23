# Changelog

All notable changes to this project are documented in this file.

_This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html)._

---

## [Unreleased] - yyyy-mm-dd

### Added

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

- Updated internal dependencies

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

### Changed

- Installers now include OS name in filenames
- Update Download dialog shows percentage and downloaded size
- Unified icons in Diversification section across the application
- Added page size selector to the Fees, Deposits, Transactions and Account Statement tables

### Fixed

- Logs streamlined for readability
- Sidebar portfolio selector only clickable with multiple portfolios
- **DEGIRO**:
    - Fixed portfolio data fetching issue
    - Fixed bug showing forecasted dividends
- Application: "License Expiration" dialog now displays correctly

### Security

- Updated internal dependencies

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

- Updated internal dependencies

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

- Updated internal dependencies

---

## [0.1.1] - 2025-08-13

### Added

- **DEGIRO Credentials:**
    - "Settings" dialog for credentials and 2FA token
    - "Remember me" checkbox in login dialog
    - Credentials stored securely with AES-128 key
- **Updates:**
    - "Check for updates" menu item
    - "Update available" notification

### Changed

- Internal refactor to support more brokers

### Security

- Updated internal dependencies

---

## [0.1.0] - 2025-07-15

### Initial Release

- Connect to DEGIRO with credentials and 2FA
- Automatic DEGIRO information updates
- Dashboard with portfolio growth
- Portfolio, Dividends, Fees, Deposits, Transactions, and full Account Statement
- Diversification information
- Installers for macOS, Windows, and Linux

---
