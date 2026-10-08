#!/bin/bash
# Packages dist/District Lookup/ (built on Linux) two ways:
#   district-lookup_<version>_<arch>.deb — for Debian, Ubuntu and a Chromebook's
#     Linux, where double-clicking it in the Files app installs it;
#   District-Lookup-<version>-linux-<arch>.tar.gz — for other Linux systems.
#     packaging/linux/build_linux.sh [dist-dir]
set -euo pipefail
cd "$(dirname "$0")/../.."
DIST="${1:-dist}"
VERSION=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' src/about.py)
ARCH=$(dpkg --print-architecture)  # amd64 or arm64

PKG="$(mktemp -d)/district-lookup"
mkdir -p "$PKG/DEBIAN" "$PKG/opt/district-lookup" "$PKG/usr/bin" \
         "$PKG/usr/share/applications" "$PKG/usr/share/icons/hicolor/256x256/apps"
cp -a "$DIST/District Lookup/." "$PKG/opt/district-lookup/"
ln -s /opt/district-lookup/district-lookup "$PKG/usr/bin/district-lookup"
cp packaging/linux/district-lookup.desktop "$PKG/usr/share/applications/"
cp assets/AppIcon.png "$PKG/usr/share/icons/hicolor/256x256/apps/district-lookup.png"
# The app window is Tk, which draws through these; the rest is bundled.
cat > "$PKG/DEBIAN/control" <<CONTROL
Package: district-lookup
Version: $VERSION
Architecture: $ARCH
Maintainer: Drew Siegler <https://github.com/drewsiegler/district-lookup/issues>
Homepage: https://github.com/drewsiegler/district-lookup
Section: utils
Priority: optional
Depends: libx11-6, libxft2, libxss1, libfontconfig1
Installed-Size: $(du -sk "$PKG" | cut -f1)
Description: Find every electoral district for a list of addresses
 Give it a list of people and addresses; it adds every electoral district
 each person lives in, from city council and county supervisor to school
 trustee areas. Covers Santa Clara County, California. Runs entirely on
 this computer; only addresses are sent to the U.S. Census geocoder.
CONTROL

DEB="$DIST/district-lookup_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$PKG" "$DEB"
TAR="$DIST/District-Lookup-$VERSION-linux-$ARCH.tar.gz"
tar -C "$DIST" -czf "$TAR" "District Lookup"
rm -rf "$(dirname "$PKG")"
echo "$DEB"
echo "$TAR"
