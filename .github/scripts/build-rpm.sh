#!/bin/bash
# Build RPM package from Briefcase build directory

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Extract version from pyproject.toml
VERSION=$(toml get --toml-path pyproject.toml project.version | tr -d '"')

# Detect architecture for RPM
ARCH=$(uname -m)
case "$ARCH" in
    aarch64) RPM_ARCH="aarch64" ;;
    x86_64) RPM_ARCH="x86_64" ;;
    *) RPM_ARCH="$ARCH" ;;
esac

# Find build directory
BUILD_BASE=$(find build/stonks-overwatch -type d -path "*/fedora/*/stonks-overwatch-*" -print -quit 2>/dev/null)
if [ -z "$BUILD_BASE" ]; then
    echo "Error: Could not find build directory for rpm" >&2
    exit 1
fi

# Find app directory
APP_DIR=$(find "$BUILD_BASE/usr" -type d -path "*/lib/*/stonks-overwatch" | head -1)
if [ -z "$APP_DIR" ]; then
    APP_DIR=$(find "$BUILD_BASE/usr" -type d -name "stonks-overwatch" -path "*/lib/*" | head -1)
fi
if [ -z "$APP_DIR" ]; then
    echo "Error: Could not find app directory in $BUILD_BASE/usr" >&2
    find "$BUILD_BASE/usr" -type d | head -20 >&2
    exit 1
fi

BUILD_DIR=$(realpath "$BUILD_BASE")

echo "Building .rpm package:"
echo "  Build directory: $BUILD_BASE"
echo "  Version: $VERSION"
echo "  Architecture: $RPM_ARCH"

# Install rpm tools if not present
sudo apt-get update -qq && sudo apt-get install -y rpm > /dev/null 2>&1

# Prepare package (launcher, desktop entry, permissions)
"$SCRIPT_DIR/prepare-package.sh" "$BUILD_BASE" "$APP_DIR"

# Create RPM build structure
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create spec file
cat > ~/rpmbuild/SPECS/stonks-overwatch.spec << SPEC_EOF
Name:           stonks-overwatch
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        Privacy-first investment portfolio tracker
License:        MIT
URL:            https://github.com/ctasada/stonks-overwatch
BuildArch:      ${RPM_ARCH}

%description
Stonks Overwatch is an open-source, privacy-first investment portfolio
tracker that consolidates data from multiple brokers.

%install
mkdir -p %{buildroot}/usr
cp -r ${BUILD_DIR}/usr/* %{buildroot}/usr/
find %{buildroot}/usr/lib/stonks-overwatch -type f -exec chmod 644 {} \;
find %{buildroot}/usr/lib/stonks-overwatch -type d -exec chmod 755 {} \;
find %{buildroot}/usr/lib/stonks-overwatch -type f -path "*/bin/*" -exec chmod 755 {} \;

%post
if [ -d "/usr/lib/stonks-overwatch" ]; then
    find /usr/lib/stonks-overwatch -type f -exec chmod 644 {} \;
    find /usr/lib/stonks-overwatch -type d -exec chmod 755 {} \;
    find /usr/lib/stonks-overwatch -type f -path "*/bin/*" -exec chmod 755 {} \;
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q || true
fi

%files
/usr/*

%changelog
* $(date '+%a %b %d %Y') Carlos Tasada <ctasada@gmail.com> - ${VERSION}-1
- Release version ${VERSION}
SPEC_EOF

# Build the RPM
mkdir -p dist
rpmbuild -bb ~/rpmbuild/SPECS/stonks-overwatch.spec 2>&1 | grep -v "^+"

# Copy RPM to dist
find ~/rpmbuild/RPMS -name "*.rpm" -exec cp {} dist/ \; 2>/dev/null

echo "✓ Created RPM packages:"
ls -lh dist/*.rpm
