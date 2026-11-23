#!/usr/bin/env bash
# Build (and optionally install) the resource-only Watch Face Format APK.
#   ./build.sh            -> build/modular24h.apk, signed with the debug key
#   ./build.sh install    -> build, then adb install -r
#
# Signing: the debug key (~/.android/debug.keystore) by default. To sign with
# a release key instead, set all three of
#   RELEASE_KEYSTORE           path to the keystore (PKCS12 or JKS)
#   RELEASE_KEYSTORE_PASSWORD  keystore password (also used as the key password)
#   RELEASE_KEY_ALIAS          key alias
# Other overrides: ANDROID_HOME, BUILD_TOOLS, PLATFORM, KEYSTORE, WFF_VALIDATOR.
set -euo pipefail
cd "$(dirname "$0")"

ANDROID_HOME="${ANDROID_HOME:-$HOME/.local/share/AndroidSDK}"
BUILD_TOOLS="${BUILD_TOOLS:-$ANDROID_HOME/build-tools/35.0.0}"
PLATFORM="${PLATFORM:-$ANDROID_HOME/platforms/android-34/android.jar}"
KEYSTORE="${KEYSTORE:-$HOME/.android/debug.keystore}"
OUT=build
APK="$OUT/modular24h.apk"

python3 tools/gen-watchface.py

if [[ -n "${WFF_VALIDATOR:-}" ]]; then
  java -jar "$WFF_VALIDATOR" 2 src/main/res/raw/watchface.xml
fi

rm -rf "$OUT" && mkdir -p "$OUT"
"$BUILD_TOOLS/aapt2" compile --dir src/main/res -o "$OUT/res.zip"
"$BUILD_TOOLS/aapt2" link -o "$OUT/unaligned.apk" -I "$PLATFORM" \
  --manifest src/main/AndroidManifest.xml \
  --min-sdk-version 33 --target-sdk-version 34 \
  "$OUT/res.zip"
"$BUILD_TOOLS/zipalign" -f -p 4 "$OUT/unaligned.apk" "$OUT/aligned.apk"
if [[ -n "${RELEASE_KEYSTORE:-}" ]]; then
  : "${RELEASE_KEYSTORE_PASSWORD:?RELEASE_KEYSTORE_PASSWORD is required with RELEASE_KEYSTORE}"
  : "${RELEASE_KEY_ALIAS:?RELEASE_KEY_ALIAS is required with RELEASE_KEYSTORE}"
  "$BUILD_TOOLS/apksigner" sign --ks "$RELEASE_KEYSTORE" --ks-key-alias "$RELEASE_KEY_ALIAS" \
    --ks-pass env:RELEASE_KEYSTORE_PASSWORD --key-pass env:RELEASE_KEYSTORE_PASSWORD \
    --out "$APK" "$OUT/aligned.apk"
  echo "signed with release key ($RELEASE_KEY_ALIAS)"
else
  "$BUILD_TOOLS/apksigner" sign --ks "$KEYSTORE" --ks-key-alias androiddebugkey \
    --ks-pass pass:android --key-pass pass:android --out "$APK" "$OUT/aligned.apk"
  echo "signed with debug key"
fi
rm -f "$OUT/unaligned.apk" "$OUT/aligned.apk" "$OUT/res.zip" "$APK.idsig"
echo "built $APK"

if [[ "${1:-}" == "install" ]]; then
  adb install -r "$APK"
fi
