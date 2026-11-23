#!/usr/bin/env python3
"""Generate the weather icon set (SVG sources in art/, PNGs in res/drawable-nodpi).

Icons are monochrome line art on a 96x96 canvas. Indices follow the
[WEATHER.CONDITION] enum of Watch Face Format v2:
 0 UNKNOWN  1 CLEAR  2 CLOUDY  3 FOG  4 HEAVY_RAIN  5 HEAVY_SNOW  6 RAIN
 7 SNOW  8 SUNNY  9 THUNDERSTORM  10 SLEET  11 LIGHT_SNOW  12 LIGHT_RAIN
 13 MIST  14 PARTLY_CLOUDY  15 WINDY
CLEAR, SUNNY and PARTLY_CLOUDY get a night variant (moon instead of sun).
Requires ImageMagick with the librsvg delegate (`magick`).
"""
import math
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "art/weather"
PNG_DIR = ROOT / "src/main/res/drawable-nodpi"
INK = "#D0D4D6"
SW = 5  # stroke width

CLOUD = (
    "M28 70 H70 A15 15 0 0 0 70 40 A21 21 0 0 0 30.5 36"
    " A17 17 0 0 0 28 70 Z"
)


def cloud(dy=0, fill=False):
    style = f'fill="{INK}"' if fill else f'fill="#000000" stroke="{INK}" stroke-width="{SW}"'
    return f'<path d="{CLOUD}" transform="translate(0 {dy})" {style} stroke-linejoin="round"/>'


def line(x1, y1, x2, y2, w=SW):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" '
            f'stroke-width="{w}" stroke-linecap="round"/>')


def flake(cx, cy, r):
    out = []
    for a in (0, 60, 120):
        dx, dy = r * math.sin(math.radians(a)), r * math.cos(math.radians(a))
        out.append(line(cx - dx, cy - dy, cx + dx, cy + dy, 4))
    return "".join(out)


def drops(xs, y=74, length=12):
    return "".join(line(x, y, x - 4, y + length) for x in xs)


def sun(cx, cy, r, rays=True):
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{INK}" stroke-width="{SW}"/>']
    if rays:
        for i in range(8):
            a = math.radians(i * 45)
            r0, r1 = r + 7, r + 14
            out.append(line(cx + r0 * math.cos(a), cy + r0 * math.sin(a),
                            cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
    return "".join(out)


def moon(cx, cy, r):
    # Crescent: outer circle minus an offset circle, drawn as a single path.
    return (f'<path d="M{cx + r * 0.2} {cy - r} A{r} {r} 0 1 0 {cx + r} {cy + r * 0.25}'
            f' A{r * 0.8} {r * 0.8} 0 0 1 {cx + r * 0.2} {cy - r} Z" fill="none" '
            f'stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')


ICONS = {
    "unknown": f'<text x="48" y="66" font-family="sans-serif" font-size="52" font-weight="600" '
               f'text-anchor="middle" fill="{INK}">?</text>',
    "clear_day": sun(48, 48, 15),
    "clear_night": moon(46, 50, 24),
    "cloudy": cloud(),
    "fog": line(16, 36, 80, 36) + line(10, 50, 86, 50) + line(16, 64, 80, 64),
    "heavy_rain": cloud(-10) + drops((34, 48, 62), 70, 16),
    "heavy_snow": flake(48, 26, 11) + flake(30, 56, 11) + flake(66, 56, 11),
    "rain": cloud(-10) + drops((40, 58), 70, 12),
    "snow": cloud(-12) + flake(38, 76, 7) + flake(60, 76, 7),
    "sunny": sun(48, 48, 15),
    "thunderstorm": cloud(-10) + f'<path d="M52 62 L42 78 H54 L46 92" fill="none" stroke="{INK}" '
                                 f'stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>',
    "sleet": cloud(-12) + drops((38,), 70, 12) + flake(60, 77, 7),
    "light_snow": cloud(-10) + flake(48, 78, 7),
    "light_rain": cloud(-10) + drops((48,), 72, 10),
    "mist": line(20, 38, 60, 38) + line(70, 38, 76, 38) + line(14, 52, 82, 52)
            + line(20, 66, 30, 66) + line(40, 66, 76, 66),
    "partly_cloudy_day": sun(36, 34, 11, rays=False)
                         + "".join(line(36 + 17 * math.cos(math.radians(a)), 34 + 17 * math.sin(math.radians(a)),
                                        36 + 23 * math.cos(math.radians(a)), 34 + 23 * math.sin(math.radians(a)))
                                   for a in (135, 180, 225, 270, 315))
                         + cloud(10),
    "partly_cloudy_night": moon(34, 34, 15) + cloud(10),
    "windy": f'<path d="M12 40 H58 A10 10 0 1 0 48 30" fill="none" stroke="{INK}" stroke-width="{SW}" '
             f'stroke-linecap="round"/>'
             f'<path d="M12 56 H72 A10 10 0 1 1 62 66" fill="none" stroke="{INK}" stroke-width="{SW}" '
             f'stroke-linecap="round"/>'
             + line(12, 72, 40, 72),
}


def main():
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    for name, body in ICONS.items():
        svg = SVG_DIR / f"{name}.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">'
            f"{body}</svg>\n")
        png = PNG_DIR / f"wx_{name}.png"
        subprocess.run(["magick", "-background", "none", str(svg),
                        "-depth", "8", "-strip", f"PNG32:{png}"], check=True)
        print(png.name)


if __name__ == "__main__":
    main()
