#!/usr/bin/env bash
# Build (and optionally install) the resource-only Watch Face Format APK.
#   ./build.sh            -> build/modular24h.apk, signed with the debug key
#   ./build.sh install    -> build, then adb install -r
# Environment overrides: ANDROID_HOME, BUILD_TOOLS, PLATFORM, KEYSTORE, WFF_VALIDATOR.
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
"$BUILD_TOOLS/apksigner" sign --ks "$KEYSTORE" --ks-key-alias androiddebugkey \
  --ks-pass pass:android --key-pass pass:android --out "$APK" "$OUT/aligned.apk"
rm -f "$OUT/unaligned.apk" "$OUT/aligned.apk" "$OUT/res.zip" "$APK.idsig"
echo "built $APK"

if [[ "${1:-}" == "install" ]]; then
  adb install -r "$APK"
fi
