# room-interior iter 5: plant read as flat paddles -> 34 smaller leaves on an upward spiral + 3 stems; F12 previews f1/f168
import bpy, math, random, os, sys, importlib
sys.path.insert(0, os.path.expanduser("scripts"))
import exlib; importlib.reload(exlib)
from exlib import *
g = bpy.data.objects["G_Plant"]
for o in [o for o in bpy.data.objects if o.name.startswith("Leaf") or o.name.startswith("Stem")]:
    bpy.data.objects.remove(o, do_unlink=True)
leaf = bpy.data.materials["Leaf"]; stem_m = mat("Stem", base=(0.25, 0.2, 0.12), rough=0.7)
random.seed(11)
cx, cy = -0.4, -1.55
for k in range(3):
    a = k * 2.1
    st = prim('cylinder', f"Stem{k}", loc=(cx + 0.05 * math.cos(a), cy + 0.05 * math.sin(a), 0.95), scale=(0.025, 0.025, 1.3), rot=(0.12 * math.cos(a + 1.5), 0.12 * math.sin(a), 0), m=stem_m, seg=12)
    st.parent = g
for k in range(34):
    t = k / 33; a = k * 2.4; r = 0.1 + 0.25 * math.sin(t * 3.0) + random.uniform(-0.03, 0.03); z = 0.62 + 1.05 * t
    lf = prim('uvsphere', f"Leaf{k}", loc=(cx + r * math.cos(a), cy + r * math.sin(a), z), scale=(0.24, 0.15, 0.02),
              rot=(random.uniform(-0.4, 0.4), random.uniform(-0.6, -0.2), a), m=leaf, smooth=True, u=24, v=12)
    lf.parent = g
p = leaf.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (0.09, 0.22, 0.07, 1)
for f, tag in ((1, "a"), (168, "b")):
    PREVIEW_FRAME = f; PREVIEW_OUT = os.path.expanduser(f"iters/room-interior/preview_05{tag}.png")
    exec(open(os.path.expanduser("scripts/preview.py")).read())
