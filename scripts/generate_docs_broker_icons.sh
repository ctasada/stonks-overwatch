#!/bin/sh

# Script to convert broker icons from src/icons/brokers to docs/images/brokers
# Generates two sizes:
# - 20x20 for sidebar navigation (small, uniform)
# - 64x64 for documentation pages (larger, more visible)

SOURCE_DIR="src/icons/brokers"
TARGET_DIR="docs/images/brokers"
SIDEBAR_SIZE="20x20"
DOC_SIZE="64x64"

if ! command -v magick >/dev/null 2>&1; then
  echo "Error: ImageMagick is not installed. Please install it using 'brew install imagemagick'."
  exit 1
fi

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

convert_broker_icon() {
  icon_name="$1"
  size="$2"
  output_name="$3"
  vertical_offset="$4"
  source_path="$SOURCE_DIR/$icon_name"
  target_path="$TARGET_DIR/$output_name"

  if [ ! -f "$source_path" ]; then
    echo "Warning: Source icon not found: $source_path"
    return 1
  fi

  echo "Converting $icon_name to $size -> $output_name..."

  # Resize to fit within specified size while maintaining aspect ratio
  if [ -n "$vertical_offset" ] && [ "$vertical_offset" != "0" ]; then
    # Apply vertical offset for visual alignment (DEGIRO and Bitvavo need slight downward shift)
    # Method: Resize logo, trim transparent edges, position from bottom (removes bottom space),
    # then add small offset from bottom for text alignment
    # Extract width and height from size (format: WxH)
    width=$(echo "$size" | cut -dx -f1)
    height=$(echo "$size" | cut -dx -f2)
    magick "$source_path" \
      -resize "${size}>" \
      -trim +repage \
      -background transparent \
      -gravity south \
      -splice "0x${vertical_offset}" \
      -extent "${width}x${height}" \
      "$target_path"
  else
    # Standard centering (IBKR works fine with center gravity)
    magick "$source_path" \
      -resize "${size}>" \
      -background transparent \
      -gravity center \
      -extent "$size" \
      "$target_path"
  fi

  if [ $? -eq 0 ]; then
    echo "  ✓ Created $target_path ($size)"
  else
    echo "  ✗ Failed to convert $icon_name"
    return 1
  fi
}

# Convert all broker icons
echo "Generating broker icons for documentation..."
echo "Source: $SOURCE_DIR"
echo "Target: $TARGET_DIR"
echo "Sizes: $SIDEBAR_SIZE (sidebar) and $DOC_SIZE (documentation)"
echo ""

for icon in bitvavo.png degiro.png ibkr.png; do
  # Extract base name without extension
  base_name=$(basename "$icon" .png)

  # Determine vertical offset for visual alignment (DOCUMENTATION ONLY)
  # DEGIRO and Bitvavo need to sit lower to align with text baseline
  # Note: We use gravity south + splice, so SMALLER offset = logo sits LOWER
  # IBKR is fine with center alignment
  # Small sidebar icons always use center alignment (no offset)
  case "$base_name" in
    degiro)
      doc_offset="2"
      ;;
    bitvavo)
      doc_offset="1"
      ;;
    *)
      doc_offset="0"
      ;;
  esac

  # Generate 64x64 for documentation (default, larger, more visible) - with offset if needed
  convert_broker_icon "$icon" "$DOC_SIZE" "${base_name}.png" "$doc_offset"

  # Generate 20x20 for sidebar (small variant) - always centered, no offset
  convert_broker_icon "$icon" "$SIDEBAR_SIZE" "${base_name}_small.png" "0"
done

echo ""
echo "Broker icon generation completed."
echo "Generated files:"
echo "  - *.png (${DOC_SIZE}) for documentation pages (default)"
echo "  - *_small.png (${SIDEBAR_SIZE}) for sidebar navigation"
