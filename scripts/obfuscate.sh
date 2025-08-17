#!/bin/bash
set -e

# Directory variables
SRC_DIR="src/stonks_overwatch"
OBFUSCATED_DIR="src/obfuscated"

# Clean previous obfuscated output
rm -rf "$OBFUSCATED_DIR"
mkdir -p "$(dirname "$OBFUSCATED_DIR")"

# Run Pyarmor 8+ to obfuscate the code
poetry run pyarmor gen -r -O "$OBFUSCATED_DIR" "$SRC_DIR"
cp -r "$SRC_DIR/static" "$OBFUSCATED_DIR/stonks_overwatch/static"
cp -r "$SRC_DIR/staticfiles" "$OBFUSCATED_DIR/stonks_overwatch/staticfiles"
cp -r "$SRC_DIR/templates" "$OBFUSCATED_DIR/stonks_overwatch/templates"

echo "Obfuscation complete. Obfuscated code is in $OBFUSCATED_DIR."
