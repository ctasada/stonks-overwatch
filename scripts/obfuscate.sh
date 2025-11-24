#!/bin/bash
set -e

# Directory variables
SRC_DIR="src/stonks_overwatch"
OBFUSCATED_DIR="src/obfuscated"

# Clean previous obfuscated output
rm -rf "$OBFUSCATED_DIR"
mkdir -p "$OBFUSCATED_DIR"

if [ "$OBFUSCATE_MODE" = "true" ]; then
    echo "Obfuscating code for Briefcase..."
    poetry run pyarmor gen -r -O "$OBFUSCATED_DIR" "$SRC_DIR"
    cp -r "$SRC_DIR/static" "$OBFUSCATED_DIR/stonks_overwatch/static"
    cp -r "$SRC_DIR/staticfiles" "$OBFUSCATED_DIR/stonks_overwatch/staticfiles"
    cp -r "$SRC_DIR/templates" "$OBFUSCATED_DIR/stonks_overwatch/templates"
    cp -r "$SRC_DIR/fixtures" "$OBFUSCATED_DIR/stonks_overwatch/fixtures"
    echo "Obfuscation complete. Obfuscated code is in $OBFUSCATED_DIR."
else
    echo "OBFUSCATE_MODE=true: Copying plain sources to $OBFUSCATED_DIR..."
    cp -r "$SRC_DIR" "$OBFUSCATED_DIR/"
    mkdir -p "$OBFUSCATED_DIR/pyarmor_runtime_000000"
    touch "$OBFUSCATED_DIR/pyarmor_runtime_000000/__init__.py"
    echo "Plain sources copied to $OBFUSCATED_DIR."
fi
