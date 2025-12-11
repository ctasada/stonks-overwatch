#!/bin/bash
# Build Debian package from Briefcase build directory

# Enable better error reporting
set -euo pipefail
# Trap errors to show where they occur
trap 'echo "ERROR: Command failed at line $LINENO: $BASH_COMMAND" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Extract version from pyproject.toml
VERSION=$(toml get --toml-path pyproject.toml project.version | tr -d '"')

# Detect architecture for Debian
ARCH=$(uname -m)
case "$ARCH" in
    aarch64|arm64) DEB_ARCH="arm64" ;;
    x86_64|amd64) DEB_ARCH="amd64" ;;
    *) DEB_ARCH="$ARCH" ;;
esac

# Find build directory
BUILD_BASE=$(find build/stonks-overwatch -type d -path "*/ubuntu/*/stonks-overwatch-*" -print -quit 2>/dev/null)
if [ -z "$BUILD_BASE" ]; then
    echo "Error: Could not find build directory for deb" >&2
    exit 1
fi

# Find app directory
# Use -print -quit to avoid pipe issues
APP_DIR=$(find "$BUILD_BASE/usr" -type d -path "*/lib/*/stonks-overwatch" -print -quit 2>/dev/null || true)
if [ -z "$APP_DIR" ]; then
    APP_DIR=$(find "$BUILD_BASE/usr" -type d -name "stonks-overwatch" -path "*/lib/*" -print -quit 2>/dev/null || true)
fi
if [ -z "$APP_DIR" ]; then
    echo "Error: Could not find app directory in $BUILD_BASE/usr" >&2
    echo "Available directories:" >&2
    find "$BUILD_BASE/usr" -type d -print -quit 2>/dev/null | while read -r dir; do
        echo "  $dir" >&2
    done || true
    # Also try to list first 20 without pipe
    COUNT=0
    while IFS= read -r dir && [ $COUNT -lt 20 ]; do
        echo "  $dir" >&2
        COUNT=$((COUNT + 1))
    done < <(find "$BUILD_BASE/usr" -type d 2>/dev/null || true) || true
    exit 1
fi

echo "Building .deb package:"
echo "  Build directory: $BUILD_BASE"
echo "  Version: $VERSION"
echo "  Architecture: $DEB_ARCH"

# Install dpkg-deb if not present
sudo apt-get update -qq && sudo apt-get install -y dpkg-dev > /dev/null 2>&1

# Create DEBIAN control directory
mkdir -p "$BUILD_BASE/DEBIAN"

# Calculate installed size (in KB)
echo "Calculating installed size..."
# Use du with -s (summary) and parse output without pipes
set +e  # Temporarily disable exit on error for size calculation
DU_OUTPUT=$(du -sk "$BUILD_BASE" 2>/dev/null)
DU_EXIT=$?
set -e

if [ $DU_EXIT -eq 0 ] && [ -n "$DU_OUTPUT" ]; then
    # Parse du output: "12345    /path" -> extract first field
    INSTALLED_SIZE=$(echo "$DU_OUTPUT" | awk '{print $1; exit}')
    echo "  du result: ${INSTALLED_SIZE} KB"
else
    echo "  du failed, using default size..."
    INSTALLED_SIZE=1000  # Default to 1MB if calculation fails
fi

# Ensure minimum size of 1KB and reasonable maximum
if [ -z "$INSTALLED_SIZE" ] || [ "$INSTALLED_SIZE" -lt 1 ]; then
    INSTALLED_SIZE=1
fi
echo "  Final installed size: ${INSTALLED_SIZE} KB"

# Extract release notes from CHANGELOG if available
RELEASE_NOTES=""
if [ -f "$SCRIPT_DIR/../../CHANGELOG.md" ]; then
    # Extract latest version section (first version block)
    # Use awk with built-in limit instead of pipe to head
    RELEASE_NOTES=$(awk '/^## \[/{p=1; count=0} p && /^## \[/{if(p>1) exit; p++} p && count++ < 50' "$SCRIPT_DIR/../../CHANGELOG.md" || echo "")
fi

# Create control file
cat > "$BUILD_BASE/DEBIAN/control" << CONTROL_EOF
Package: stonks-overwatch
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${DEB_ARCH}
Installed-Size: ${INSTALLED_SIZE}
Maintainer: Carlos Tasada <ctasada@gmail.com>
Homepage: https://github.com/ctasada/stonks-overwatch
Description: Privacy-first investment portfolio tracker
 Stonks Overwatch is an open-source, privacy-first investment portfolio
 tracker that consolidates data from multiple brokers.
 .
 Features:
  - Real-time portfolio tracking with automatic updates
  - Multi-broker consolidation for a unified view
  - Performance analytics with historical data
  - Dividend tracking and forecasting
  - Fee analysis across all brokers
  - Asset diversification visualization
 .
 Supported brokers: DEGIRO, Bitvavo, Interactive Brokers (IBKR)
CONTROL_EOF

# Prepare package (launcher, desktop entry, permissions)
echo "Running prepare-package.sh..."
if ! "$SCRIPT_DIR/prepare-package.sh" "$BUILD_BASE" "$APP_DIR"; then
    echo "ERROR: prepare-package.sh failed with exit code $?" >&2
    exit 1
fi
echo "prepare-package.sh completed successfully"

# Create postinst script to ensure permissions are correct after installation
cp "$SCRIPT_DIR/deb-postinst.sh" "$BUILD_BASE/DEBIAN/postinst"
chmod 755 "$BUILD_BASE/DEBIAN/postinst"

# Build the .deb package
echo "Building .deb package..."
mkdir -p dist
PACKAGE_NAME="stonks-overwatch_${VERSION}_${DEB_ARCH}.deb"
echo "  Package name: $PACKAGE_NAME"
echo "  Build base: $BUILD_BASE"

# Build with explicit error handling and detailed output
echo "Running dpkg-deb --build..."
echo "  Command: dpkg-deb --build \"$BUILD_BASE\" \"dist/$PACKAGE_NAME\""

# Capture both stdout and stderr separately to avoid pipe issues
DPKG_STDOUT=$(mktemp)
DPKG_STDERR=$(mktemp)

set +e  # Temporarily disable exit on error to capture the actual error
dpkg-deb --build "$BUILD_BASE" "dist/$PACKAGE_NAME" > "$DPKG_STDOUT" 2> "$DPKG_STDERR"
DPKG_EXIT=$?
set -e  # Re-enable exit on error

# Output the results
if [ -s "$DPKG_STDOUT" ]; then
    cat "$DPKG_STDOUT"
fi
if [ -s "$DPKG_STDERR" ]; then
    cat "$DPKG_STDERR" >&2
fi

# Clean up temp files
rm -f "$DPKG_STDOUT" "$DPKG_STDERR"

if [ $DPKG_EXIT -ne 0 ]; then
    echo "ERROR: dpkg-deb failed with exit code $DPKG_EXIT" >&2
    echo "Build base directory exists: $([ -d "$BUILD_BASE" ] && echo 'yes' || echo 'no')" >&2
    echo "DEBIAN directory exists: $([ -d "$BUILD_BASE/DEBIAN" ] && echo 'yes' || echo 'no')" >&2
    if [ -d "$BUILD_BASE/DEBIAN" ]; then
        echo "DEBIAN/control exists: $([ -f "$BUILD_BASE/DEBIAN/control" ] && echo 'yes' || echo 'no')" >&2
    fi
    exit $DPKG_EXIT
fi

if [ ! -f "dist/$PACKAGE_NAME" ]; then
    echo "ERROR: Package file was not created" >&2
    echo "dist directory contents:" >&2
    ls -la dist/ >&2 || true
    exit 1
fi

echo "✓ Created: dist/$PACKAGE_NAME"
ls -lh "dist/$PACKAGE_NAME" || true
