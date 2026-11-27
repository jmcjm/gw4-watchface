#!/usr/bin/env python3
"""Render the ambient-mode time digits as a bitmap font (res/drawable-nodpi).

Samsung's WFF runtime hands the AOD time to the display offload hardware only
when it is a <DigitalClock>/<TimeText> drawn with a <BitmapFont> whose digits
0-9 are all exactly the same size (a "uniform atlas"). TrueType fonts are never
offloaded. So the digits of Outfit Thin are rendered here into fixed-size,
white PNG cells; the face tints them with the BitmapFont color.

Requires ImageMagick 7 (`magick`).
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = ROOT / "src/main/res/font/outfit_thin.ttf"
PNG_DIR = ROOT / "src/main/res/drawable-nodpi"

POINTSIZE = 112    # same size as the former PartText time
BAND_TOP = 26      # rows of the label canvas kept: from just above the digit
CELL_H = 96        # tops down to just below the baseline
DIGIT_W = 68       # widest digit ink ("0", 60 px) plus 4 px on each side
COLON_W = 24

GLYPHS = {str(d): (f"time_{d}", DIGIT_W) for d in range(10)}
GLYPHS[":"] = ("time_colon", COLON_W)


def render(char, name, width):
    out = PNG_DIR / f"{name}.png"
    subprocess.run([
        "magick", "-background", "none", "-fill", "white",
        "-font", str(FONT), "-pointsize", str(POINTSIZE), f"label:{char}",
        # Keep a fixed horizontal band so every glyph shares the baseline.
        "-crop", f"0x{CELL_H}+0+{BAND_TOP}", "+repage",
        # Centre the ink horizontally in a fixed-width cell.
        "-define", "trim:edges=east,west", "-trim", "+repage",
        "-background", "none", "-gravity", "center", "-extent", f"{width}x{CELL_H}",
        "-strip", f"PNG32:{out}",
    ], check=True)
    print(f"{out.relative_to(ROOT)}  {width}x{CELL_H}")


for char, (name, width) in GLYPHS.items():
    render(char, name, width)
