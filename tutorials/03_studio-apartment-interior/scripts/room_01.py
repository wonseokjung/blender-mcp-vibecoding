# room-interior iter 1: fresh scene; 6x4 m dollhouse studio (back + left walls, window cut in the left wall),
# oak plank floor, furniture blockout with bevels, sun through the window, sky world, overview camera
import sys, importlib, math, bpy, bmesh
sys.path.insert(0, __import__('os').path.expanduser("scripts"))
import exlib; importlib.reload(exlib)
from exlib import *

s = reset()
render_setup("room-interior", samples=64, bloom=None, look='AgX - Base Contrast')
world((0.75, 0.82, 0.95), 0.9)


def box(name, x0, x1, y0, y1, z0, z1, m=None, bev=0.01):
    return prim('cube', name, loc=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), scale=(x1 - x0, y1 - y0, z1 - z0), m=m, bevel=bev, bseg=2)


# materials
oak = mat("OakFloor", base=(0.62, 0.45, 0.30), rough=0.38)
nt = oak.node_tree; p = nt.nodes["Principled BSDF"]
br = nt.nodes.new("ShaderNodeTexBrick"); br.offset = 0.5; br.squash = 1.0
br.inputs["Scale"].default_value = 1.0; br.inputs["Mortar Size"].default_value = 0.004
br.inputs["Brick Width"].default_value = 1.2; br.inputs["Row Height"].default_value = 0.18
br.inputs["Color1"].default_value = (0.62, 0.45, 0.30, 1); br.inputs["Color2"].default_value = (0.55, 0.39, 0.25, 1); br.inputs["Mortar"].default_value = (0.3, 0.2, 0.13, 1)
tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
wallm = mat("WallWhite", base=(0.86, 0.84, 0.8), rough=0.85)
beige = mat("Beige", base=(0.72, 0.64, 0.54), rough=0.8)
linen = mat("Linen", base=(0.9, 0.89, 0.86), rough=0.9)
duvet = mat("Duvet", base=(0.78, 0.76, 0.72), rough=0.95)
wood = mat("WoodLight", base=(0.70, 0.52, 0.35), rough=0.45)
dark = mat("Charcoal", base=(0.05, 0.05, 0.055), rough=0.4)
sofa_m = mat("SofaFabric", base=(0.45, 0.47, 0.42), rough=0.95)
rug_m = mat("Rug", base=(0.82, 0.78, 0.7), rough=1.0)
white = mat("Cabinet", base=(0.92, 0.92, 0.9), rough=0.35)
steel = mat("Steel", base=(0.75, 0.75, 0.75), metal=1.0, rough=0.25)
leaf = mat("Leaf", base=(0.12, 0.28, 0.1), rough=0.6, sss=0.2)
pot = mat("Pot", base=(0.85, 0.82, 0.77), rough=0.6)
glass = mat("WinGlass", base=(0, 0, 0), rough=0.02, alpha=0.08)
screen = emit_mat("Screen", (0.55, 0.7, 0.9), 1.5)
bulb = emit_mat("LampBulb", (1.0, 0.8, 0.55), 6.0)

# shell: floor slab, back wall (y=2), left wall (x=-3) with a window opening
X0, X1, Y0, Y1, H, T = -3.0, 3.0, -2.0, 2.0, 2.6, 0.12
box("Floor", X0 - T, X1, Y0, Y1 + T, -0.12, 0.0, oak, bev=0.0)
box("WallBack", X0 - T, X1, Y1, Y1 + T, 0, H, wallm, bev=0.0)
# left wall pieces around window (window: y -0.9..0.9, z 0.8..2.2)
wy0, wy1, wz0, wz1 = -1.1, 0.9, 0.75, 2.25
box("WallL_a", X0 - T, X0, Y0, wy0, 0, H, wallm, bev=0.0)
box("WallL_b", X0 - T, X0, wy1, Y1 + T, 0, H, wallm, bev=0.0)
box("WallL_c", X0 - T, X0, wy0, wy1, 0, wz0, wallm, bev=0.0)
box("WallL_d", X0 - T, X0, wy0, wy1, wz1, H, wallm, bev=0.0)
box("WinFrameV", X0 - T, X0, -0.12, -0.08, wz0, wz1, white, bev=0.0)
box("WinFrameH", X0 - T, X0, wy0, wy1, 1.48, 1.52, white, bev=0.0)
box("WinGlass", X0 - T * 0.6, X0 - T * 0.4, wy0, wy1, wz0, wz1, glass, bev=0.0)
# skirting
box("SkirtBack", X0, X1, Y1 - 0.015, Y1, 0, 0.08, white, bev=0.0)

# bed: back-left corner, head against the back wall
bx0, bx1 = -2.85, -1.25
box("BedFrame", bx0, bx1, -0.1, 1.98, 0.0, 0.32, wood)
box("Headboard", bx0, bx1, 1.9, 1.98, 0.0, 1.0, wood)
box("Mattress", bx0 + 0.04, bx1 - 0.04, -0.06, 1.88, 0.32, 0.55, linen, bev=0.06)
box("Duvet", bx0 + 0.0, bx1 - 0.0, -0.12, 1.25, 0.50, 0.62, duvet, bev=0.07)
for k, x in enumerate((bx0 + 0.42, bx1 - 0.42)):
    pl = prim('cube', f"Pillow{k}", loc=(x, 1.62, 0.66), scale=(0.62, 0.36, 0.16), m=linen, bevel=0.07, bseg=4)
box("Nightstand", -1.18, -0.75, 1.55, 1.98, 0, 0.5, wood)
prim('cylinder', "LampBase", loc=(-0.97, 1.76, 0.6), scale=(0.1, 0.1, 0.2), m=steel)
prim('cylinder', "LampShade", loc=(-0.97, 1.76, 0.82), scale=(0.26, 0.26, 0.22), m=linen, seg=32)

# desk: back wall, right side
box("DeskTop", 0.6, 2.0, 1.4, 1.98, 0.72, 0.76, wood)
for k, (x, y) in enumerate([(0.65, 1.45), (1.95, 1.45), (0.65, 1.93), (1.95, 1.93)]):
    box(f"DeskLeg{k}", x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0, 0.72, dark, bev=0.0)
box("Monitor", 1.0, 1.6, 1.8, 1.83, 0.92, 1.27, dark)
box("MonitorScreen", 1.02, 1.58, 1.795, 1.80, 0.94, 1.25, screen, bev=0.0)
box("MonitorStand", 1.27, 1.33, 1.83, 1.88, 0.76, 0.95, dark, bev=0.0)
box("ChairSeat", 1.05, 1.55, 0.85, 1.3, 0.44, 0.5, dark, bev=0.02)
box("ChairBack", 1.05, 1.55, 0.82, 0.88, 0.5, 0.95, dark, bev=0.02)
box("ChairPost", 1.27, 1.33, 1.05, 1.11, 0.05, 0.44, steel, bev=0.0)

# kitchenette: along the left wall at the front (y -2..-1.15)
box("KitchenBase", -2.98, -2.38, -1.98, -1.18, 0, 0.86, white)
box("KitchenTop", -3.0, -2.33, -2.0, -1.15, 0.86, 0.9, mat("Counter", base=(0.2, 0.2, 0.21), rough=0.3), bev=0.0)
box("Sink", -2.85, -2.5, -1.75, -1.45, 0.86, 0.905, steel, bev=0.0)
# fridge at the front-right corner of the kitchen? keep it against the left wall front edge
# (fridge would block the window light; place it at the back wall right end instead)
box("Fridge", 2.3, 2.95, 1.3, 1.98, 0, 1.75, white, bev=0.02)

# sofa: front-right, facing the back wall (-> faces +y)
sx0, sx1, sy0, sy1 = 0.2, 2.0, -1.85, -1.0
box("SofaBase", sx0, sx1, sy0, sy1, 0.08, 0.42, sofa_m, bev=0.06)
box("SofaBack", sx0, sx1, sy0, sy0 + 0.22, 0.42, 0.85, sofa_m, bev=0.08)
box("SofaArmL", sx0, sx0 + 0.18, sy0, sy1, 0.42, 0.62, sofa_m, bev=0.07)
box("SofaArmR", sx1 - 0.18, sx1, sy0, sy1, 0.42, 0.62, sofa_m, bev=0.07)
for k, x in enumerate((sx0 + 0.18, (sx0 + sx1) / 2)):
    box(f"Cushion{k}", x, x + (sx1 - sx0 - 0.36) / 2, sy0 + 0.22, sy1 - 0.02, 0.42, 0.52, sofa_m, bev=0.05)
box("Rug", -0.2, 2.4, -1.2, 0.6, 0.0, 0.012, rug_m, bev=0.0)
prim('cylinder', "CoffeeTable", loc=(1.1, -0.25, 0.4), scale=(0.7, 0.7, 0.04), m=wood)
prim('cylinder', "CoffeeLeg", loc=(1.1, -0.25, 0.2), scale=(0.08, 0.08, 0.4), m=dark)

# plant: front-left of the sofa
prim('cylinder', "Pot", loc=(-0.4, -1.55, 0.22), scale=(0.42, 0.42, 0.44), m=pot)
import random
random.seed(5)
for k in range(14):
    a = random.uniform(0, 6.28); r = random.uniform(0.05, 0.3); z = random.uniform(0.75, 1.55)
    lf = prim('uvsphere', f"Leaf{k}", loc=(-0.4 + r * math.cos(a), -1.55 + r * math.sin(a), z), scale=(0.34, 0.18, 0.03),
              rot=(random.uniform(-0.6, 0.6), random.uniform(-0.5, 0.5), a), m=leaf, smooth=True, u=24, v=12)

# light: low afternoon sun through the window (from -x), soft sky
sn = sun("Sun", (55, 0, -100), energy=6.0, color=(1.0, 0.86, 0.68), angle=1.0)
sn.rotation_euler = (math.radians(60), 0, math.radians(-90))
cam, tgt = camera(loc=(7.5, -8.0, 7.0), target=(-0.1, 0.1, 0.6), lens=32)
viewport_camera('RENDERED')
print("ok", len(s.objects))
