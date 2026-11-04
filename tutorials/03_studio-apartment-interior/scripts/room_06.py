# room-interior iter 6: F12 read flat + cold grey -> sky light down/warmer, stronger sun, warm ceiling bounce fill,
# AgX Medium High Contrast, warmer walls; F12 previews again
import bpy, os, sys, importlib
sys.path.insert(0, os.path.expanduser("scripts"))
import exlib; importlib.reload(exlib)
from exlib import *
s = sc()
bgs = [n for n in s.world.node_tree.nodes if n.type == 'BACKGROUND']
bgs[0].inputs[0].default_value = (0.78, 0.8, 0.85, 1); bgs[0].inputs[1].default_value = 0.45
bgs[1].inputs[0].default_value = (0.95, 0.93, 0.9, 1)
bpy.data.objects["Sun"].data.energy = 9.0
if not bpy.data.objects.get("Bounce"):
    area("Bounce", (0, 0, 2.55), (0, 0, 0), energy=220, size=5, size_y=3.5, color=(1.0, 0.88, 0.74))
s.view_settings.look = 'AgX - Medium High Contrast'
p = bpy.data.materials["WallWhite"].node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (0.93, 0.88, 0.8, 1)
for f, tag in ((1, "a"), (168, "b")):
    PREVIEW_FRAME = f; PREVIEW_OUT = os.path.expanduser(f"iters/room-interior/preview_06{tag}.png")
    exec(open(os.path.expanduser("scripts/preview.py")).read())
