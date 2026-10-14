#!/bin/bash
# Wraps dist/District Lookup.app in a disk image to drag it out of:
#     packaging/macos/build_dmg.sh [dist-dir]
# Produces District-Lookup-<version>-mac-<apple-silicon|intel>.dmg in dist-dir.
# With MACOS_SIGN_IDENTITY set (see district_lookup.spec), the app inside is
# already signed, so the disk image is signed too, and its note says so.
set -euo pipefail
cd "$(dirname "$0")/../.."
DIST="${1:-dist}"
VERSION=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' src/about.py)
case "$(uname -m)" in
  arm64) CHIP=apple-silicon ;;
  x86_64) CHIP=intel ;;
  *) echo "unexpected processor: $(uname -m)" >&2; exit 1 ;;
esac

STAGE=$(mktemp -d)
ditto "$DIST/District Lookup.app" "$STAGE/District Lookup.app"
ln -s /Applications "$STAGE/Applications"
if [ -n "${MACOS_SIGN_IDENTITY:-}" ]; then
  cp packaging/macos/first-open-signed.txt "$STAGE/Opening it the first time.txt"
else
  cp packaging/macos/first-open.txt "$STAGE/Opening it the first time.txt"
fi

OUT="$DIST/District-Lookup-$VERSION-mac-$CHIP.dmg"
hdiutil create -volname "District Lookup" -srcfolder "$STAGE" -ov -format UDZO "$OUT"
rm -rf "$STAGE"
if [ -n "${MACOS_SIGN_IDENTITY:-}" ]; then
  codesign --sign "$MACOS_SIGN_IDENTITY" --timestamp "$OUT"
fi
echo "$OUT"
