# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - yyyy-mm-dd

### Added

### Changed

* Installers: Added OS name to the installer filenames

### Deprecated

### Removed

### Fixed

* Streamline logs to make them easier to read
* Sidebar: Portfolio selector is only clickable when there are multiple portfolios

### Security

## [0.1.3] - 2025-08-30

### Added

* DEGIRO: Added support to use 'In App' 2FA authentication

### Changed

* Navigation sidebar has been redesigned to improve usability
* Navigation sidebar is now collapsible
* Internal code improvements

### Fixed

* Fixed some default values in the Broker configurations
* Fixed bug showing the Fee amount

### Security

* Updated internal dependencies

## [0.1.2] - 2025-08-22

### Added

* Updates are automatically checked

### Changed

* Improved License dialog
* Internal code improvements

### Fixed

* Windows:
  * Fixed crash while opening the application
  * Properly show the application icon
  * Properly show the main menu
  * Installer: Fixed issue with the installation path

### Security

* Updated internal dependencies

## [0.1.1] - 2025-08-13

### Added

* Added support to remember DEGIRO login credentials
  * Added "Settings" dialog to store DEGIRO credentials, including 2FA token
  * Added "Remember me" checkbox to the DEGIRO login dialog
  * Credentials are stored securely using a locally generated AES-128 key
* Added support to check for updates
  * Added "Check for updates" menu item to the main menu
  * Added "Update available" notification when a new version is detected

### Changed

* Internal refactor to allow adding more brokers

### Security

* Updated internal dependencies

## [0.1.0] - 2025-07-15

* Initial release
  * Provides support to connect to DEGIRO using login credentials and 2FA
  * Keeps DEGIRO information automatically up to date
  * Shows Dashboard with Portfolio growth over time
  * Shows Portfolio, Dividends, Fees, Deposits, Transactions, and full Account Statement
  * Shows Diversification information
  * Provides installers for macOS, Windows, and Linux
