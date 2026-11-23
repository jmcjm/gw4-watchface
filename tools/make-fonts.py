#!/usr/bin/env python3
"""Instantiate static Outfit weights from the variable font into res/font.

The WFF runtime selects a font by resource file name, so each weight we use
gets its own static TTF. Requires fontTools (pip install fonttools).
"""
import pathlib
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "third_party/outfit/Outfit-VF.ttf"
OUT = ROOT / "src/main/res/font"
WEIGHTS = {"outfit_thin": 100, "outfit_light": 300, "outfit_semibold": 600}

for name, wght in WEIGHTS.items():
    font = instantiateVariableFont(TTFont(SRC), {"wght": wght}, updateFontNames=False)
    font.save(OUT / f"{name}.ttf")
    print(f"{name}.ttf  wght={wght}")
