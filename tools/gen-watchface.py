#!/usr/bin/env python3
"""Generate res/raw/watchface.xml (Watch Face Format v2) for the Modular 24h face.

Geometry is computed here rather than typed by hand: four edge arcs, their
labels and icons, the seconds ring and the forecast row all derive from the
constants below. Angles follow the WFF convention: 0 degrees at 12 o'clock,
increasing clockwise.
"""
import math
import pathlib
from xml.sax.saxutils import quoteattr

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src/main/res/raw/watchface.xml"

SIZE = 450
C = SIZE / 2
R = 207            # centre line of the complication arcs
ARC_W = 13         # arc stroke thickness
LABEL_R = 181      # radius of the arc labels
ICON_R = 211       # radius of the slot icons at the cardinal points
ICON = 24          # icon box size
RING_R = 221.5     # seconds ring centre line
RING_W = 3

FONT_LIGHT = "outfit_light"
FONT_THIN = "outfit_thin"
FONT_SEMI = "outfit_semibold"

TIME_COLOR = "#FFE6E6E6"
DIM_TEXT = "#FFC4C9CC"


def f(v):
    """Format a number for XML without pointless trailing zeros."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def polar(angle, r):
    a = math.radians(angle)
    return C + r * math.sin(a), C - r * math.cos(a)


def a(**attrs):
    return " ".join(f"{k}={quoteattr(str(v))}" for k, v in attrs.items())


# --- Complication slots -----------------------------------------------------
# Tap handling: Samsung's WFF runtime (2.0.32) hit-tests a tap against the
# ComplicationSlot element's own x/y/width/height rectangle, not against its
# bounding shape, and fires the tap action of every slot that contains the
# point. Rendering, on the other hand, is clipped only to the bounding shape,
# and the editor outline comes from the bounding shape too. So every slot is
# a 1x1 rectangle in the top-left corner (outside the round display, so it
# cannot be touched) while its content and bounding shape are laid out in
# face coordinates. Result: the face opens nothing when tapped, and the slots
# stay visible and customizable in the editor.
SLOT_TAP_RECT = dict(x=0, y=0, width=1, height=1)
# style: "fill"     track + filled arc
#        "segments" track + filled arc, both dashed into segments
#        "dot"      full gradient arc + knob at the value
SLOTS = [
    dict(id=0, name="top_left", display="Top left", start=276, end=352,
         label_angle=297, label_rot=-63, icon_angle=270, style="fill",
         track="#FF262A2D", fill="#FF23B35F", text="#FF2CC46C", icon_tint="#FFF06A12",
         policy=dict(defaultSystemProvider="STEP_COUNT", defaultSystemProviderType="SHORT_TEXT",
                     primaryProvider="com.samsung.android.wear.shealth/"
                                     "com.samsung.android.wear.shealth.complications.steps."
                                     "StepsComplicationProviderService",
                     primaryProviderType="GOAL_PROGRESS")),
    dict(id=1, name="top_right", display="Top right", start=8, end=82,
         label_angle=64, label_rot=64, icon_angle=0, style="segments",
         track="#FF173B49", fill="#FF36A9D3", text="#FF3FB3DC", icon_tint="#FF36A9D3",
         policy=dict(defaultSystemProvider="WATCH_BATTERY", defaultSystemProviderType="RANGED_VALUE")),
    dict(id=2, name="bottom_left", display="Bottom left", start=190, end=260,
         label_angle=212, label_rot=32, icon_angle=180, style="dot",
         gradient=(["#FFE2542E", "#FFD6342E"], [0, 1]), text="#FFE0503A", icon_tint="#FFE0473A",
         policy=dict(defaultSystemProvider="HEART_RATE", defaultSystemProviderType="SHORT_TEXT",
                     primaryProvider="com.samsung.android.wear.shealth/"
                                     "com.samsung.android.wear.shealth.complications.heartrate."
                                     "HeartrateComplicationProviderService",
                     primaryProviderType="SHORT_TEXT")),
    dict(id=3, name="bottom_right", display="Bottom right", start=100, end=170,
         label_angle=117, label_rot=-63, icon_angle=90, style="dot",
         gradient=(["#FF3CBE5A", "#FFC8C828", "#FFDE5A28", "#FFD6323C", "#FF963CDC"],
                   [0, 0.25, 0.5, 0.75, 1]),
         text="#FF2CC46C", icon_tint="#FFE0B23A",
         policy=dict(defaultSystemProvider="EMPTY", defaultSystemProviderType="RANGED_VALUE",
                     primaryProvider="com.samsung.android.watch.weather/"
                                     "com.samsung.android.watch.weather.complication."
                                     "UvIndexComplicationService",
                     primaryProviderType="RANGED_VALUE")),
]

SEGMENTS = 22


def arc(start, end, stroke, end_expr=None, indent="        "):
    span_attrs = dict(centerX=f(C), centerY=f(C), width=f(2 * R), height=f(2 * R),
                      startAngle=f(start), endAngle=f(end))
    inner = stroke
    if end_expr:
        inner += f'\n{indent}  <Transform target="endAngle" value={quoteattr(end_expr)}/>'
    return f"{indent}<Arc {a(**span_attrs)}>\n{indent}  {inner}\n{indent}</Arc>"


def stroke(color, cap="ROUND", dash=None, gradient=None, start=0, end=360, thickness=ARC_W):
    attrs = dict(color=color, thickness=f(thickness), cap=cap)
    if dash:
        attrs["dashIntervals"] = dash
    if not gradient:
        return f"<Stroke {a(**attrs)}/>"
    colors, positions = gradient
    grad = a(centerX=f(C), centerY=f(C), startAngle=f(start), endAngle=f(end),
             colors=" ".join(colors), positions=" ".join(f(p) for p in positions))
    return f"<Stroke {a(**attrs)}><SweepGradient {grad}/></Stroke>"


def frac_expr(kind):
    if kind == "RANGED_VALUE":
        return ("clamp(([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / "
                "([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1)")
    return ("clamp([COMPLICATION.GOAL_PROGRESS_VALUE] / "
            "[COMPLICATION.GOAL_PROGRESS_TARGET_VALUE], 0, 1)")


def dash_pattern(s):
    seg_len = 2 * math.pi * R * (s["end"] - s["start"]) / 360 / SEGMENTS
    on = seg_len * 0.5
    return f"{f(on)} {f(seg_len - on)}"


def slot_track(s):
    if s["style"] == "dot":
        return arc(s["start"], s["end"],
                   stroke("#FFFFFFFF", cap="ROUND", gradient=s["gradient"],
                          start=s["start"], end=s["end"]))
    dash = dash_pattern(s) if s["style"] == "segments" else None
    cap = "BUTT" if dash else "ROUND"
    return arc(s["start"], s["end"], stroke(s["track"], cap=cap, dash=dash))


def slot_value(s, kind):
    span = s["end"] - s["start"]
    frac = frac_expr(kind)
    if s["style"] == "dot":
        knob_x, knob_y = C - 9.5, C - R - 9.5
        return (f'        <Group {a(name=s["name"] + "_knob", x=0, y=0, width=SIZE, height=SIZE, pivotX=0.5, pivotY=0.5)}>\n'
                f'          <Transform target="angle" value={quoteattr(f"{s["start"]} + {span} * {frac}")}/>\n'
                f'          <PartDraw {a(x=0, y=0, width=SIZE, height=SIZE)}>\n'
                f'            <Ellipse {a(x=f(knob_x), y=f(knob_y), width=19, height=19)}>\n'
                f'              <Fill color="#FFE6E6E6"/>\n'
                f'            </Ellipse>\n'
                f'          </PartDraw>\n'
                f'        </Group>')
    dash = dash_pattern(s) if s["style"] == "segments" else None
    cap = "BUTT" if dash else "ROUND"
    # endAngle starts equal to startAngle and is driven by the value.
    return (f'        <PartDraw {a(x=0, y=0, width=SIZE, height=SIZE)}>\n'
            + arc(s["start"], s["start"], stroke(s["fill"], cap=cap, dash=dash),
                  end_expr=f"{s['start']} + {span} * {frac}", indent="          ")
            + "\n        </PartDraw>")


def slot_label(s):
    x, y = polar(s["label_angle"], LABEL_R)
    w, h = 110, 32
    return (f'        <PartText {a(x=round(x - w / 2), y=round(y - h / 2), width=w, height=h, pivotX=0.5, pivotY=0.5, angle=s["label_rot"])}>\n'
            f'          <Text align="CENTER" ellipsis="TRUE">\n'
            f'            <Font {a(family=FONT_SEMI, size=22, color=s["text"])}>\n'
            f'              <Template>%s<Parameter expression="[COMPLICATION.TEXT]"/></Template>\n'
            f'            </Font>\n'
            f'          </Text>\n'
            f'        </PartText>')


def slot_icon(s):
    x, y = polar(s["icon_angle"], ICON_R)
    return (f'        <PartImage {a(x=round(x - ICON / 2), y=round(y - ICON / 2), width=ICON, height=ICON, tintColor=s["icon_tint"])}>\n'
            f'          <Image resource="[COMPLICATION.MONOCHROMATIC_IMAGE]"/>\n'
            f'        </PartImage>')


def complication_slot(s):
    track = f'        <PartDraw {a(x=0, y=0, width=SIZE, height=SIZE)}>\n{slot_track(s)}\n        </PartDraw>'
    parts = []
    for kind in ("RANGED_VALUE", "GOAL_PROGRESS"):
        parts.append(f'      <Complication type="{kind}">\n{track}\n{slot_value(s, kind)}\n'
                     f'{slot_label(s)}\n{slot_icon(s)}\n      </Complication>')
    # SHORT_TEXT has no value: draw the track (or the full gradient) only.
    parts.append(f'      <Complication type="SHORT_TEXT">\n{track}\n{slot_label(s)}\n{slot_icon(s)}\n      </Complication>')
    # The runtime clips slot content to the BoundingArc's box, so the arc must
    # span the whole face or the outer half of the stroke and the icons vanish.
    bounding = a(centerX=f(C), centerY=f(C), width=SIZE, height=SIZE, thickness=60,
                 startAngle=f(s["start"] - 6), endAngle=f(s["end"] + 6), isRoundEdge="TRUE")
    return (f'    <ComplicationSlot {a(slotId=s["id"], name=s["name"], displayName=s["display"], **SLOT_TAP_RECT, supportedTypes="RANGED_VALUE GOAL_PROGRESS SHORT_TEXT", isCustomizable="TRUE")}>\n'
            f'      <Variant mode="AMBIENT" target="alpha" value="0"/>\n'
            f'      <DefaultProviderPolicy {a(**s["policy"])}/>\n'
            f'      <BoundingArc {bounding}/>\n'
            + "\n".join(parts) + "\n    </ComplicationSlot>")


# --- Weather ----------------------------------------------------------------
WEATHER_NAMES = ["unknown", "clear", "cloudy", "fog", "heavy_rain", "heavy_snow", "rain",
                 "snow", "sunny", "thunderstorm", "sleet", "light_snow", "light_rain",
                 "mist", "partly_cloudy", "windy"]
DAY_NIGHT = {"clear", "sunny", "partly_cloudy"}


def bitmap_fonts():
    out = ["  <BitmapFonts>"]
    for variant in ("day", "night"):
        out.append(f'    <BitmapFont name="weather_{variant}">')
        for i, n in enumerate(WEATHER_NAMES):
            res = f"wx_{n}"
            if n in DAY_NIGHT:
                res = "wx_clear_" + variant if n in ("clear", "sunny") else f"wx_{n}_{variant}"
            tag = "Character" if i < 10 else "Word"
            out.append(f'      <{tag} {a(name=i, resource=res, width=96, height=96)}/>')
        out.append("    </BitmapFont>")
    out.append("  </BitmapFonts>")
    return "\n".join(out)


def weather_icon(prefix, x, y, size, indent):
    cond = f"[WEATHER.{prefix}CONDITION]"
    is_day = f"[WEATHER.{prefix}IS_DAY]"
    expr = f"{cond} &gt;= 0 &amp;&amp; {cond} &lt;= 15 ? {cond} : 0"

    def part(variant):
        return (f'{indent}    <PartText {a(x=f(x), y=f(y), width=size, height=size)}>\n'
                f'{indent}      <Text align="CENTER">\n'
                f'{indent}        <BitmapFont {a(family="weather_" + variant, size=size)}>\n'
                f'{indent}          <Template>%s<Parameter expression="{expr}"/></Template>\n'
                f'{indent}        </BitmapFont>\n'
                f'{indent}      </Text>\n'
                f'{indent}    </PartText>')
    return (f'{indent}<Condition>\n'
            f'{indent}  <Expressions><Expression name="day">{is_day}</Expression></Expressions>\n'
            f'{indent}  <Compare expression="day">\n{part("day")}\n{indent}  </Compare>\n'
            f'{indent}  <Default>\n{part("night")}\n{indent}  </Default>\n'
            f'{indent}</Condition>')


def forecast_column(n, cx):
    # WFF has no per-hour feels-like source; the label is the plain forecast
    # temperature for that hour, in the user's preferred unit.
    icon = 40
    ind = "            "
    return (f'      <Group {a(name=f"forecast_{n}", x=round(cx - 40), y=290, width=80, height=74)}>\n'
            f'        <Condition>\n'
            f'          <Expressions><Expression name="avail">[WEATHER.HOURS.{n}.IS_AVAILABLE]</Expression></Expressions>\n'
            f'          <Compare expression="avail">\n'
            f'{weather_icon(f"HOURS.{n}.", 20, 0, icon, ind)}\n'
            f'            <PartText {a(x=0, y=46, width=80, height=26)}>\n'
            f'              <Text align="CENTER">\n'
            f'                <Font {a(family=FONT_SEMI, size=21, color=DIM_TEXT)}>\n'
            f'                  <Template>%s°<Parameter expression="[WEATHER.HOURS.{n}.TEMPERATURE]"/></Template>\n'
            f'                </Font>\n'
            f'              </Text>\n'
            f'            </PartText>\n'
            f'          </Compare>\n'
            f'        </Condition>\n'
            f'      </Group>')


# Current weather: icon plus the feels-like temperature on its right. WFF has
# no feels-like data source (only WEATHER.TEMPERATURE), so the value comes from
# Samsung Weather's feels-like complication bound to a small text-only slot.
WX_ICON_X = 168
FEELS_SLOT = dict(id=4, name="feels_like", display="Next to weather icon",
                  x=WX_ICON_X + 54, y=58, width=96, height=44,
                  policy=dict(defaultSystemProvider="EMPTY", defaultSystemProviderType="SHORT_TEXT",
                              primaryProvider="com.samsung.android.watch.weather/"
                                              "com.samsung.android.watch.weather.complication."
                                              "FeelsLikeTempComplicationService",
                              primaryProviderType="SHORT_TEXT"))


def feels_like_slot():
    s = FEELS_SLOT
    w, h = s["width"], s["height"]
    return f"""    <ComplicationSlot {a(slotId=s["id"], name=s["name"], displayName=s["display"], **SLOT_TAP_RECT, supportedTypes="SHORT_TEXT", isCustomizable="TRUE")}>
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <DefaultProviderPolicy {a(**s["policy"])}/>
      <BoundingBox {a(x=s["x"], y=s["y"], width=w, height=h)}/>
      <Complication type="SHORT_TEXT">
        <PartText {a(x=s["x"], y=s["y"], width=w, height=h)}>
          <Text align="START" ellipsis="TRUE">
            <Font {a(family=FONT_SEMI, size=26, color="#FFD0D4D6")}>
              <Template>%s<Parameter expression="[COMPLICATION.TEXT]"/></Template>
            </Font>
          </Text>
        </PartText>
      </Complication>
    </ComplicationSlot>"""


# --- Assembly ---------------------------------------------------------------
def seconds_ring():
    d = 2 * RING_R
    ring = dict(centerX=f(C), centerY=f(C), width=f(d), height=f(d))
    dot_r = 3.2
    dot_y = C - RING_R - dot_r
    return f"""    <Group {a(name="seconds_ring", x=0, y=0, width=SIZE, height=SIZE)}>
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <PartDraw {a(x=0, y=0, width=SIZE, height=SIZE)}>
        <Arc {a(**ring, startAngle=0, endAngle=360)}>
          <Stroke {a(color="#FF1B2023", thickness=RING_W)}/>
        </Arc>
        <Arc {a(**ring, startAngle=0, endAngle=0)}>
          <Stroke {a(color="#FF8E9AA1", thickness=RING_W, cap="ROUND")}/>
          <Transform target="endAngle" value="[SECOND] * 6"/>
        </Arc>
      </PartDraw>
      <Group {a(name="seconds_marker", x=0, y=0, width=SIZE, height=SIZE, pivotX=0.5, pivotY=0.5)}>
        <Transform target="angle" value="[SECOND] * 6"/>
        <PartDraw {a(x=0, y=0, width=SIZE, height=SIZE)}>
          <Ellipse {a(x=f(C - dot_r), y=f(dot_y), width=f(2 * dot_r), height=f(2 * dot_r))}>
            <Fill color="#FFE8ECEE"/>
          </Ellipse>
        </PartDraw>
      </Group>
    </Group>"""


def active_group():
    return f"""    <Group {a(name="active", x=0, y=0, width=SIZE, height=SIZE)}>
      <Variant mode="AMBIENT" target="alpha" value="0"/>
      <Group {a(name="current_weather", x=WX_ICON_X, y=56, width=48, height=48)}>
        <Condition>
          <Expressions><Expression name="avail">[WEATHER.IS_AVAILABLE]</Expression></Expressions>
          <Compare expression="avail">
{weather_icon("", 0, 0, 48, "            ")}
          </Compare>
        </Condition>
      </Group>
      <PartText {a(name="date", x=75, y=113, width=300, height=50)}>
        <Text align="CENTER">
          <Font {a(family=FONT_SEMI, size=38, color="#FF1D8DB8")}>
            <Upper><Template>%s<Parameter expression="[DAY_OF_WEEK_S]"/></Template></Upper>
          </Font>
          <Font {a(family=FONT_LIGHT, size=38, color="#FFD2D6D8")}>
            <Template> %s<Parameter expression="[DAY]"/></Template>
          </Font>
        </Text>
      </PartText>
      <DigitalClock {a(x=25, y=160, width=400, height=124)}>
        <TimeText {a(format="hh:mm", hourFormat="24", align="CENTER", x=0, y=0, width=400, height=124)}>
          <Font {a(family=FONT_LIGHT, size=108, color=TIME_COLOR)}/>
        </TimeText>
      </DigitalClock>
{chr(10).join(forecast_column(n, cx) for n, cx in ((1, 160), (2, 225), (3, 290)))}
    </Group>"""


def ambient_group():
    # Samsung runtime 2.0.32 ignores the <Outline> text decoration (nothing is
    # drawn with a transparent or black fill), so AOD uses thin filled digits.
    return f"""    <Group {a(name="ambient", x=0, y=0, width=SIZE, height=SIZE, alpha=0)}>
      <Variant mode="AMBIENT" target="alpha" value="255"/>
      <PartText {a(name="ambient_time", x=15, y=160, width=420, height=130)}>
        <Text align="CENTER">
          <Font {a(family=FONT_THIN, size=112, color="#FF7F8F99")}>
            <Template>%s:%s<Parameter expression="[HOUR_0_23_Z]"/><Parameter expression="[MINUTE_Z]"/></Template>
          </Font>
        </Text>
      </PartText>
    </Group>"""


def main():
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<!-- Generated by tools/gen-watchface.py. Edit the generator, not this file. -->
<WatchFace width="{SIZE}" height="{SIZE}">
  <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
  <Metadata key="PREVIEW_TIME" value="19:43:07"/>
{bitmap_fonts()}
  <Scene backgroundColor="#FF000000">
{seconds_ring()}
{active_group()}
{chr(10).join(complication_slot(s) for s in SLOTS)}
{feels_like_slot()}
{ambient_group()}
  </Scene>
</WatchFace>
"""
    OUT.write_text(xml)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(xml)} bytes)")


if __name__ == "__main__":
    main()
