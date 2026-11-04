# channel-intro iter 2: floor blew out white (top/key area lights mirrored in the gloss), chrome faces black
# (nothing to reflect), green read mint (AgX desaturates hot emission) -> no top light, key moved high/back,
# camera-invisible emissive reflection cards (soft strips) for the chrome, green strength 1.6, tighter word space
import sys, importlib, math, bpy
sys.path.insert(0, __import__('os').path.expanduser("scripts"))
import exlib; importlib.reload(exlib)
from exlib import *

for n in ("Top",):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)
k = bpy.data.objects["Key"]; k.location = (-5, -4, 9); aim(k, (0, 0, 1)); k.data.energy = 500
bpy.data.materials["Green"].node_tree.nodes["Emission"].inputs[1].default_value = 1.6
fl = bpy.data.materials["Floor"].node_tree.nodes["Principled BSDF"]
fl.inputs["Roughness"].default_value = 0.22; fl.inputs["Specular IOR Level"].default_value = 0.35

# shift the right part ("AI LAB") left to close the double-wide gap
names = sorted([o.name for o in bpy.data.objects if o.name.startswith("L")])
shift = 0.18
for n in names:
    o = bpy.data.objects[n]; idx = int(n[1:3])
    hx = o["home"][0]
    if idx >= 8: hx -= shift            # after the first space
    if idx >= 11: hx -= shift           # after the second space
    o.location.x = hx; o["home"] = (hx, 0.0, 1.0)
xs = [bpy.data.objects[n].location.x for n in names]
mid = (min(xs) + max(xs) + bpy.data.objects[names[-1]].dimensions.x) / 2
for n in names:
    o = bpy.data.objects[n]; o.location.x -= mid; o["home"] = (o.location.x, 0.0, 1.0)
right = max(bpy.data.objects[n].location.x + bpy.data.objects[n].dimensions.x for n in names)
left = min(bpy.data.objects[n].location.x for n in names)
ul = bpy.data.objects["Underline"]; ul.scale.x = right - left; ul.location.x = (right + left) / 2
bpy.data.objects["Cursor"].location.x = right + 0.28

# reflection cards (camera-invisible): big soft strips the chrome can mirror
card = emit_mat("Card", (0.85, 0.92, 1.0), 2.5)
for o in [o for o in bpy.data.objects if o.name.startswith("Card")]:
    bpy.data.objects.remove(o, do_unlink=True)
for i, (x, z, sx) in enumerate([(-7, 5, 2.2), (0, 7, 14), (7, 4, 1.4)]):
    c = prim('plane', f"Card{i}", loc=(x, -12, z), scale=(sx, 6 if i != 1 else 1.2, 1), m=card)
    aim(c, (0, 0, 1.0)); c.rotation_euler.rotate_axis('X', math.radians(180))
    c.visible_camera = False; c.visible_shadow = False
print("ok", round(left, 2), round(right, 2))
