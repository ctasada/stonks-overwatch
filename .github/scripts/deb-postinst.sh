#!/bin/bash
# Post-installation script for stonks-overwatch Debian package
# This script runs after the package is installed

set -e

# Fix permissions on installed files (in case installation changed them)
if [ -d "/usr/lib/stonks-overwatch" ]; then
    find /usr/lib/stonks-overwatch -type f -exec chmod 644 {} \;
    find /usr/lib/stonks-overwatch -type d -exec chmod 755 {} \;
    find /usr/lib/stonks-overwatch -type f -path "*/bin/*" -exec chmod 755 {} \;
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q || true
fi

# Update AppStream database
# Try multiple methods to refresh AppStream cache
if command -v appstreamcli >/dev/null 2>&1; then
    appstreamcli refresh-cache --force || true
elif command -v update-appstream >/dev/null 2>&1; then
    update-appstream || true
fi

# Also try to refresh desktop database (sometimes helps with AppStream)
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database || true
fi

exit 0
