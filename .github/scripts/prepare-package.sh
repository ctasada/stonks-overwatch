#!/bin/bash
# Prepare package: create launcher, desktop entry, and fix permissions
# Combines create-launcher.sh and fix-permissions.sh functionality

# Enable better error reporting
set -euo pipefail
# Trap errors to show where they occur
trap 'echo "ERROR in prepare-package.sh at line $LINENO: $BASH_COMMAND" >&2' ERR

BUILD_BASE="${1:-}"
APP_DIR="${2:-}"

if [ -z "$BUILD_BASE" ] || [ -z "$APP_DIR" ]; then
    echo "Usage: $0 <build-base-dir> <app-dir>" >&2
    exit 1
fi

# Get the project root directory (where pyproject.toml is located)
# This script is in .github/scripts/, so go up two levels
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Briefcase system format uses system Python, not a bundled Python
# Dependencies are in app_packages/ directory, not site-packages
PYTHON_BIN="/usr/bin/python3"

# Calculate relative paths
APP_DIR_REL=$(echo "$APP_DIR" | sed "s|^$BUILD_BASE||")
APP_CODE_DIR="$APP_DIR_REL/app"

# Find app_packages directory (where Briefcase installs dependencies)
APP_PACKAGES_DIR="$BUILD_BASE/usr/lib/stonks-overwatch/app_packages"
if [ ! -d "$APP_PACKAGES_DIR" ]; then
    APP_PACKAGES_DIR=$(find "$BUILD_BASE/usr/lib/stonks-overwatch" -type d -name "app_packages" -print -quit 2>/dev/null || true)
fi

# Build PYTHONPATH
PYTHONPATH_PARTS=()
if [ -n "$APP_PACKAGES_DIR" ] && [ -d "$APP_PACKAGES_DIR" ]; then
    APP_PACKAGES_REL=$(echo "$APP_PACKAGES_DIR" | sed "s|^$BUILD_BASE||")
    PYTHONPATH_PARTS+=("$APP_PACKAGES_REL")
fi
PYTHONPATH_PARTS+=("$APP_CODE_DIR")
PYTHONPATH_VALUE=$(IFS=:; echo "${PYTHONPATH_PARTS[*]}")

# Create launcher script
mkdir -p "$BUILD_BASE/usr/bin"
cat > "$BUILD_BASE/usr/bin/stonks-overwatch" << EOF
#!/bin/bash
# Launcher script for Stonks Overwatch
# Set up Python path to include app_packages (dependencies) and app directory
export PYTHONPATH="${PYTHONPATH_VALUE}:\${PYTHONPATH}"
# Run the app using Python -m stonks_overwatch (which calls __main__.py)
exec ${PYTHON_BIN} -m stonks_overwatch "\$@"
EOF
chmod +x "$BUILD_BASE/usr/bin/stonks-overwatch"
echo "✓ Created launcher: /usr/bin/stonks-overwatch"

# Create desktop entry
mkdir -p "$BUILD_BASE/usr/share/applications"
cat > "$BUILD_BASE/usr/share/applications/stonks-overwatch.desktop" << 'DESKTOP_EOF'
[Desktop Entry]
Name=Stonks Overwatch
Comment=Privacy-first investment portfolio tracker
Exec=stonks-overwatch
Icon=stonks-overwatch
Terminal=false
Type=Application
Categories=Finance;Office;
URL=https://github.com/ctasada/stonks-overwatch
DESKTOP_EOF
echo "✓ Created desktop entry: /usr/share/applications/stonks-overwatch.desktop"

# Install AppStream metainfo file for better app store integration
echo "Installing AppStream metainfo file..."
mkdir -p "$BUILD_BASE/usr/share/metainfo"
if [ -f "$SCRIPT_DIR/stonks-overwatch.metainfo.xml" ]; then
    # Extract version and date for release information
    VERSION=$(toml get --toml-path "$PROJECT_ROOT/pyproject.toml" project.version 2>/dev/null | tr -d '"' || echo "")
    RELEASE_DATE=$(date -u +%Y-%m-%d)

    TEMP_META=$(mktemp)
    cp "$SCRIPT_DIR/stonks-overwatch.metainfo.xml" "$TEMP_META"

    # Convert CHANGELOG.md to AppStream releases format
    # Extract all releases from CHANGELOG.md and convert to proper XML format
    CHANGELOG_PATH="$PROJECT_ROOT/CHANGELOG.md"
    RELEASES_XML=$(mktemp)

    if [ -f "$CHANGELOG_PATH" ]; then
        # Use Python script to parse CHANGELOG.md and convert to AppStream releases XML
        "$SCRIPT_DIR/changelog-to-releases.py" "$CHANGELOG_PATH" "$VERSION" "$RELEASE_DATE" > "$RELEASES_XML"

        # Insert releases into metainfo if generated
        if [ -s "$RELEASES_XML" ] && grep -q "</releases>" "$TEMP_META" 2>/dev/null; then
            awk -v releases_xml="$RELEASES_XML" '
                /<\/releases>/ {
                    while ((getline line < releases_xml) > 0) {
                        print line
                    }
                    close(releases_xml)
                }
                { print }
            ' "$TEMP_META" > "${TEMP_META}.new" && mv "${TEMP_META}.new" "$TEMP_META"
        fi
    fi

    rm -f "$RELEASES_XML"

    # Replace deprecated <developer_name> with <developer> tag if present
    if grep -q "<developer_name>" "$TEMP_META" 2>/dev/null; then
        DEV_NAME=$(grep -o '<developer_name>[^<]*</developer_name>' "$TEMP_META" | sed 's/<[^>]*>//g' || echo "Carlos Tasada")
        sed -i "s|<developer_name>[^<]*</developer_name>|<developer>\n    <name>${DEV_NAME}</name>\n  </developer>|" "$TEMP_META"
    fi

    mv "$TEMP_META" "$BUILD_BASE/usr/share/metainfo/com.caribay.stonks_overwatch.metainfo.xml"
    echo "✓ Installed AppStream metainfo file"
else
    echo "⚠ Warning: AppStream metainfo file not found at $SCRIPT_DIR/stonks-overwatch.metainfo.xml"
fi

# Find and install PNG icon
# Briefcase may place icons in hicolor directories or use underscore naming (stonks_overwatch)
# Search for PNG files with both hyphen and underscore patterns

# First, search for PNG files in hicolor directories (Briefcase's standard location)
# Use find with -print -quit to avoid pipe issues
ICON_SRC=$(find "$BUILD_BASE/usr/share/icons" -type f \( -name "stonks-overwatch.png" -o -name "stonks_overwatch.png" \) -print -quit 2>/dev/null || true)

# If no PNG found in hicolor, search elsewhere for PNG
if [ -z "$ICON_SRC" ]; then
    ICON_SRC=$(find "$BUILD_BASE/usr" -type f \( -name "stonks-overwatch.png" -o -name "stonks_overwatch.png" -o -name "*.png" -path "*/resources/*" \) -print -quit 2>/dev/null || true)
fi

# If still not found, use source PNG file
if [ -z "$ICON_SRC" ] && [ -f "$PROJECT_ROOT/src/icons/stonks_overwatch.png" ]; then
    ICON_SRC="$PROJECT_ROOT/src/icons/stonks_overwatch.png"
fi

if [ -n "$ICON_SRC" ] && [ -f "$ICON_SRC" ]; then
    ICON_BASE_NAME="stonks-overwatch"

    # If icon is already in hicolor directory, Briefcase has installed it correctly
    if echo "$ICON_SRC" | grep -q "/usr/share/icons/hicolor"; then
        ICON_BASE=$(basename "$ICON_SRC" | sed 's/\.[^.]*$//')
        sed -i "s|Icon=stonks-overwatch|Icon=$ICON_BASE|" "$BUILD_BASE/usr/share/applications/stonks-overwatch.desktop"
    else
        # Icon found but not in standard location - copy to pixmaps
        mkdir -p "$BUILD_BASE/usr/share/pixmaps"
        cp "$ICON_SRC" "$BUILD_BASE/usr/share/pixmaps/${ICON_BASE_NAME}.png"
        sed -i "s|Icon=stonks-overwatch|Icon=${ICON_BASE_NAME}|" "$BUILD_BASE/usr/share/applications/stonks-overwatch.desktop"
    fi
    echo "✓ Installed application icon"
fi

# Fix file permissions (ensure all files are readable by all users)
find "$BUILD_BASE/usr/lib/stonks-overwatch" -type f -exec chmod 644 {} \;
find "$BUILD_BASE/usr/lib/stonks-overwatch" -type d -exec chmod 755 {} \;
find "$BUILD_BASE/usr/lib/stonks-overwatch" -type f -path "*/bin/*" -exec chmod 755 {} \;
[ -f "$BUILD_BASE/usr/bin/stonks-overwatch" ] && chmod 755 "$BUILD_BASE/usr/bin/stonks-overwatch"
[ -f "$BUILD_BASE/usr/share/applications/stonks-overwatch.desktop" ] && chmod 644 "$BUILD_BASE/usr/share/applications/stonks-overwatch.desktop"
[ -d "$BUILD_BASE/usr/share/pixmaps" ] && find "$BUILD_BASE/usr/share/pixmaps" -type f -exec chmod 644 {} \;
[ -d "$BUILD_BASE/usr/share/metainfo" ] && find "$BUILD_BASE/usr/share/metainfo" -type f -exec chmod 644 {} \;
echo "✓ Package preparation complete"
