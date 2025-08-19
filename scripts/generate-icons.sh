#!/bin/sh

ICON_DIR="src/icons"
ICON_NAME="stonks_overwatch"
ICON_PATH="$ICON_DIR/$ICON_NAME.png"

if ! command -v magick >/dev/null 2>&1; then
  echo "Error: ImageMagick is not installed. Please install it using 'brew install imagemagick'."
  exit 1
fi

generate_rounded_icon() {
  echo "Generating rounded icon..."
  size=$(identify -format "%wx%h" "$ICON_DIR/stonks_overwatch.svg")
  width=$(echo "$size" | cut -dx -f1)
  height=$(echo "$size" | cut -dx -f2)
  margin_w=$((width / 10))
  margin_h=$((height / 10))
  rect_x2=$((width - margin_w))
  rect_y2=$((height - margin_h))
  radius=$((width / 6))

#  magick \
#    \( -size "$size" gradient:"#5cacee-#3b5998" \) \
#    \( -background none "$ICON_DIR/stonks_overwatch.svg" -density 300 -resize "$size" \) \
#    -compose over -composite "$ICON_DIR/original.png"
  magick "$ICON_DIR/original.png" -resize "$size" "$ICON_DIR/original.png"
  magick -size "$size" xc:none -draw "roundrectangle $margin_w,$margin_h,$rect_x2,$rect_y2,$radius,$radius" png:- | \
  magick "$ICON_DIR/original.png" -alpha Set - -compose DstIn -composite "$ICON_PATH"
#  rm -f "$ICON_DIR/original.png"
}

generate_icns() {
  echo "Generating .icns file..."
  ICONSET_DIR="$ICON_NAME.iconset"
  mkdir "$ICONSET_DIR" >/dev/null 2>&1
  cp "$ICON_PATH" "$ICONSET_DIR/" >/dev/null 2>&1
  for size in 16 32 64 128 256 512 1024; do
    sips -z "$size" "$size" "$ICON_PATH" --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null 2>&1
  done
  iconutil -c icns "$ICONSET_DIR" >/dev/null 2>&1
  mv "$ICON_NAME.icns" "$ICON_DIR/" >/dev/null 2>&1
  rm -rf "$ICONSET_DIR"
}

generate_ico() {
  echo "Generating .ico file..."
  magick "$ICON_PATH" -define png:format=png32 -define icon:auto-resize=256,128,96,64,48,32,24,16 "$ICON_DIR/favicon.ico" >/dev/null 2>&1
}

generate_apple_icons() {
  echo "Generate Apple Touch icons..."
  magick "$ICON_PATH" -resize x180 "$ICON_DIR/apple-touch-icon.png"

  cp "$ICON_DIR/apple-touch-icon.png" "$ICON_DIR/apple-touch-icon-precomposed.png"
}

generate_linux_icons() {
  echo "Generate Linux FlatPack icons..."
  for size in 16 32 64 128 256 512; do
    magick "$ICON_PATH" -resize x${size} "$ICON_DIR/${ICON_NAME}-${size}.png"
  done
}

generate_windows_icons() {
  echo "Generate Windows icons..."
  magick "$ICON_PATH" -define png:format=png32 -define icon:auto-resize=256,64,48,32,16 "$ICON_DIR/stonks_overflow.ico" >/dev/null 2>&1
}

generate_rounded_icon
generate_icns
generate_ico
generate_apple_icons
generate_linux_icons
generate_windows_icons

echo "Icon generation completed."
