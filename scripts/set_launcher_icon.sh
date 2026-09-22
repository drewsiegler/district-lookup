#!/bin/bash
# Gives "Start District Lookup.command" the app icon in Finder.
#
# A custom file icon lives in the file's resource fork, which git doesn't
# carry — so run this once after cloning if you want the launcher to look
# like the app rather than a generic script. Needs Xcode Command Line Tools
# (xcode-select --install).
set -e
cd "$(dirname "$0")/.."

ICON="assets/AppIcon.icns"
TARGET="Start District Lookup.command"

for tool in Rez DeRez SetFile; do
  if ! xcrun --find "$tool" > /dev/null 2>&1; then
    echo "Needs Xcode Command Line Tools ($tool not found). Run: xcode-select --install"
    exit 1
  fi
done

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cp "$ICON" "$tmp/icon.icns"
sips -i "$tmp/icon.icns" > /dev/null          # give the icns file its own icon resource
"$(xcrun --find DeRez)" -only icns "$tmp/icon.icns" > "$tmp/icon.rsrc"
"$(xcrun --find Rez)" -append "$tmp/icon.rsrc" -o "$TARGET"
"$(xcrun --find SetFile)" -a C "$TARGET"      # mark the file as having a custom icon

echo "Set the app icon on \"$TARGET\"."
