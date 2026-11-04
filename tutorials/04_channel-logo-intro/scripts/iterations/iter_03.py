# channel-intro iter 3: white floor = the two rims mirrored at grazing angle; chrome still black because EEVEE's
# screen-space reflections can't see camera-invisible cards -> cards replaced by front area lights (analytic
# highlights on the chrome), rims light-linked to the letters only, sphere reflection probe around the wordmark
import sys, importlib, math, bpy
sys.path.insert(0, __import__('os').path.expanduser("scripts"))
import exlib; importlib.reload(exlib)
from exlib import *

for o in [o for o in bpy.data.objects if o.name.startswith("Card") or o.name.startswith("Soft")]:
    bpy.data.objects.remove(o, do_unlink=True)
lc = bpy.data.collections.get("LetterSet") or bpy.data.collections.new("LetterSet")
for o in bpy.data.objects:
    if o.name.startswith("L") and o.type == 'FONT' and o.name not in lc.objects:
        lc.objects.link(o)
for n in ("RimL", "RimR"):
    r = bpy.data.objects[n]; r.light_linking.receiver_collection = lc; r.location.z = 2.2; aim(r, (0, 0, 1.3))
    r.data.energy = 900
area("Soft1", (-4.5, -11, 5.5), (0, 0, 1.3), energy=700, size=2.5, size_y=7, color=(0.85, 0.92, 1.0))
area("Soft2", (5.5, -10, 2.0), (0, 0, 1.3), energy=350, size=1.2, size_y=5, color=(0.9, 0.95, 1.0))
if not bpy.data.objects.get("Probe"):
    pd = bpy.data.lightprobes.new("Probe", 'SPHERE'); po = link(bpy.data.objects.new("Probe", pd))
    po.location = (0, 0, 1.4); pd.influence_distance = 9
print("ok")
