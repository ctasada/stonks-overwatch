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
  sips -z 16 16 $ICON_PATH --out $ICONSET_DIR/icon_16x16.png >/dev/null 2>&1
  sips -z 32 32 $ICON_PATH --out $ICONSET_DIR/icon_16x16@2x.png >/dev/null 2>&1
  sips -z 32 32 $ICON_PATH --out $ICONSET_DIR/icon_32x32.png >/dev/null 2>&1
  sips -z 64 64 $ICON_PATH --out $ICONSET_DIR/icon_32x32@2x.png >/dev/null 2>&1
  sips -z 128 128 $ICON_PATH --out $ICONSET_DIR/icon_128x128.png >/dev/null 2>&1
  sips -z 256 256 $ICON_PATH --out $ICONSET_DIR/icon_128x128@2x.png >/dev/null 2>&1
  sips -z 256 256 $ICON_PATH --out $ICONSET_DIR/icon_256x256.png >/dev/null 2>&1
  sips -z 512 512 $ICON_PATH --out $ICONSET_DIR/icon_256x256@2x.png >/dev/null 2>&1
  sips -z 512 512 $ICON_PATH --out $ICONSET_DIR/icon_512x512.png >/dev/null 2>&1
  sips -z 1024 1024 $ICON_PATH --out $ICONSET_DIR/icon_512x512@2x.png >/dev/null 2>&1
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
#  magick $ICON_PATH -resize x180 $ICON_DIR/apple-touch-icon-180x180.png
#  magick $ICON_PATH -resize x152 $ICON_DIR/apple-touch-icon-152x152.png
#  magick $ICON_PATH -resize x120 $ICON_DIR/apple-touch-icon-120x120.png
#  magick $ICON_PATH -resize x76 $ICON_DIR/apple-touch-icon-76x76.png
#  magick $ICON_PATH -resize x60 $ICON_DIR/apple-touch-icon-60x60.png

  cp $ICON_DIR/apple-touch-icon.png $ICON_DIR/apple-touch-icon-precomposed.png
}

generate_rounded_icon
generate_icns
generate_ico
generate_apple_icons

echo "Icon generation completed."