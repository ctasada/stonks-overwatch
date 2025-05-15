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
  magick -size 1024x1024 xc:none -draw "roundrectangle 100,100,924,924,170,170" png:- | \
  magick "$ICON_DIR/original.png" -alpha Set - -compose DstIn -composite $ICON_PATH
}

generate_icns() {
  echo "Generating .icns file..."
  ICONSET_DIR="$ICON_NAME.iconset"
  mkdir $ICONSET_DIR >/dev/null 2>&1
  cp $ICON_PATH $ICONSET_DIR/ >/dev/null 2>&1
  for size in 16 32 64 128 256 512 1024; do
    sips -z $size $size $ICON_PATH --out $ICONSET_DIR/icon_${size}x${size}.png >/dev/null 2>&1
  done
  iconutil -c icns $ICONSET_DIR >/dev/null 2>&1
  mv $ICON_NAME.icns $ICON_DIR/ >/dev/null 2>&1
  rm -rf $ICONSET_DIR
}

generate_ico() {
  echo "Generating .ico file..."
  magick $ICON_PATH -define png:format=png32 -define icon:auto-resize=256,128,96,64,48,32,24,16 $ICON_DIR/favicon.ico >/dev/null 2>&1
}

generate_apple_icons() {
  echo "Generate Apple Touch icons..."
  magick $ICON_PATH -resize x180 $ICON_DIR/apple-touch-icon.png

  cp $ICON_DIR/apple-touch-icon.png $ICON_DIR/apple-touch-icon-precomposed.png
}

generate_linux_icons() {
  echo "Generate Linux FlatPack icons..."
  for size in 16 32 64 128 256 512; do
    magick $ICON_PATH -resize x${size} $ICON_DIR/${ICON_NAME}-${size}.png
  done
}

generate_rounded_icon
generate_icns
generate_ico
generate_apple_icons
generate_linux_icons

echo "Icon generation completed."