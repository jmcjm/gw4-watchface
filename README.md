# Modular 24h

Watch Face Format (v2) watch face for the Galaxy Watch 4 (SM-R870, 450×450).
It follows Samsung's Digital Modular layout: four editable edge arcs, date,
current weather and a 3-hour forecast, with the time as `HH:mm` (always 24h)
and a thin seconds ring at the very edge. In ambient mode only an outlined
`HH:mm` stays on.

## Build

```sh
./build.sh            # -> build/modular24h.apk (debug-signed)
./build.sh install    # build + adb install -r
```

Requirements: Android SDK build-tools 35.0.0 and platform android-34
(default location `~/.local/share/AndroidSDK`, override with `ANDROID_HOME`),
`~/.android/debug.keystore`, Python 3. No Gradle: the APK is resource-only and
is built directly with `aapt2`, `zipalign` and `apksigner`.

Set `WFF_VALIDATOR=/path/to/wff-validator.jar` to validate the generated XML
against the v2 schema during the build (validator from
[google/watchface](https://github.com/google/watchface), `third_party/wff`).

## Layout

| Path | What |
|---|---|
| `tools/gen-watchface.py` | generates `src/main/res/raw/watchface.xml`; edit this, not the XML |
| `tools/make-art.py` | weather icons: SVG sources in `art/weather/`, PNGs in `res/drawable-nodpi/` (needs ImageMagick + librsvg) |
| `tools/make-fonts.py` | static Outfit weights in `res/font/` from the variable font (needs fontTools) |
| `third_party/outfit/` | Outfit variable font and its OFL licence |

Generated PNGs and fonts are committed, so a plain build only needs the SDK and Python.

## Complication slots

| Slot | Arc | Default provider |
|---|---|---|
| 0 top left | 276°–352° | Samsung Health steps (`GOAL_PROGRESS`), fallback system `STEP_COUNT` |
| 1 top right | 8°–82°, segmented | system `WATCH_BATTERY` (`RANGED_VALUE`) |
| 2 bottom left | 190°–260°, gradient | Samsung Health heart rate (`SHORT_TEXT`), fallback system `HEART_RATE` |
| 3 bottom right | 100°–170°, gradient | Samsung Weather UV index (`RANGED_VALUE`) |

Every slot accepts `RANGED_VALUE`, `GOAL_PROGRESS` and `SHORT_TEXT` and can be
re-picked in the watch face editor.
