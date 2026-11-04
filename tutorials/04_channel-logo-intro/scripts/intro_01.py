# channel-intro iter 1: fresh scene; per-letter 3D metal wordmark laid out by measured glyph widths; glossy black
# floor; green underline + cursor; slogan; key + rim lights; camera
import sys, importlib, math, bpy
sys.path.insert(0, __import__('os').path.expanduser("scripts"))
import exlib; importlib.reload(exlib)
from exlib import *
from mathutils import Vector

s = reset()
render_setup("channel-intro", samples=64, bloom=(0.9, 0.35, 0.55), look='AgX - Punchy')
world((0.004, 0.005, 0.006), 1.0)

metal = mat("Chrome", base=(0.78, 0.82, 0.86), metal=1.0, rough=0.16)
floor_m = mat("Floor", base=(0.008, 0.009, 0.01), rough=0.12, spec=0.6)
green = emit_mat("Green", (0.0, 1.0, 0.255), 6.0)
slog_m = mat("Slogan", base=(0.75, 0.78, 0.8), rough=0.5, alpha=1.0)
slog_m.surface_render_method = 'BLENDED'

prim('plane', "Floor", loc=(0, 4, 0), scale=(80, 60, 1), m=floor_m)

FONT = PRET % "Black"
WORD = "CONNECT AI LAB"
SIZE, EXT, GAP, SPACE = 1.25, 0.22, 0.10, 0.42
letters, x = [], 0.0
dg = bpy.context.evaluated_depsgraph_get()
for i, ch in enumerate(WORD):
    if ch == " ":
        x += SPACE; continue
    o = text(ch, f"L{i:02d}_{ch}", FONT, size=SIZE, extrude=EXT, bevel=0.025, align='LEFT', valign='BOTTOM', loc=(x, 0, EXT + 0.0), m=metal)
    bpy.context.view_layer.update()
    w = o.dimensions.x
    letters.append((o, x, w)); x += w + GAP
total = x - GAP
for o, x0, w in letters:
    o.location.x = x0 - total / 2
    o.location.z = 1.0
    o.location.y = 0.0
    o["home"] = (o.location.x, 0.0, 1.0)

# letters stand on the floor: text in XZ plane (rot x 90), extruded along -Y/+Y
for o, _, _ in letters:
    o.rotation_euler = (math.radians(90), 0, 0)

# underline + cursor (green), slogan
ul = prim('cube', "Underline", loc=(0, -0.3, -0.0), scale=(total, 0.05, 0.02), m=green)
ul.location = (0, 0, 0.72); ul.scale = (total, 0.04, 0.035)
cur = prim('cube', "Cursor", loc=(total / 2 + 0.3, 0, 1.0 + 0.45), scale=(0.14, 0.14, 0.9), m=green)
slog = text("AI를 배우는 가장 멋진 방법", "Slogan", PRET % "Medium", size=0.34, extrude=0.0, bevel=0.0, align='CENTER',
            loc=(0, 0, 0.32), rot=(math.radians(90), 0, 0), m=slog_m, spacing=1.08)

# lights: cool key high front-left, two rims behind, soft top
area("Key", (-6, -7, 6), (0, 0, 0.6), energy=900, size=5, color=(0.85, 0.92, 1.0))
area("RimL", (-7, 6, 3), (0, 0, 0.6), energy=1200, size=3, color=(0.7, 0.85, 1.0))
area("RimR", (7, 6, 3), (0, 0, 0.6), energy=1200, size=3, color=(0.7, 0.85, 1.0))
area("Top", (0, -2, 8), (0, 0, 0), energy=300, size=8)

cam, tgt = camera(loc=(0, -14, 1.6), target=(0, 0, 1.2), lens=45)
viewport_camera('RENDERED')
print("ok total width", round(total, 2))
