# villa_13: back-facade window band (warm glow seen from the backlit establishing shot) + drone auto-exposure ramp
import bpy, math
S = bpy.context.scene
CB = bpy.data.collections["V_build"]; CI = bpy.data.collections["V_interior"]
M = bpy.data.materials
def box(name, x0, x1, y0, y1, z0, z1, m, c=CB):
    if name in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    me = bpy.data.meshes.new(name)
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    me.from_pydata(v, [], [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.data.materials.append(m); o["v13"] = 1; return o
for nm in ("V_ff_back", "V_ff_inner"):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
FF, RF = 3.5, 7.0
box("V_ff_back_lo", -11, 8, 4.6, 5.0, FF + 0.35, FF + 0.9, M["V_concrete"])
box("V_ff_back_hi", -11, 8, 4.6, 5.0, RF - 0.45, RF, M["V_concrete"])
box("V_ff_back_r", 5.0, 8, 4.6, 5.0, FF + 0.9, RF - 0.45, M["V_concrete"])
box("V_ff_back_glass", -10.6, 5.0, 4.78, 4.82, FF + 0.9, RF - 0.45, M["V_glass"])
for i, x in enumerate((-10.8, -7.6, -4.4, -1.2, 2.0)):
    box(f"V_ff_back_mull_{i}", x, x + 0.08, 4.72, 4.88, FF + 0.9, RF - 0.45, M["V_frame"])
box("V_ff_inner_r", 5.0, 7.6, 4.4, 4.6, FF + 0.35, RF, M["V_interior_wall"], CI)
for o in list(bpy.data.objects):
    if o.name.startswith("V_ffslat_") and o.location.x == 0:
        xs = [v.co.x for v in o.data.vertices]
        if min(xs) < 5.0: bpy.data.objects.remove(o, do_unlink=True)
# interior glow seen through the back band: warm pendant strip + bed headboard wall
box("V_ff_head", -7.0, -3.0, 4.2, 4.3, FF + 0.35, FF + 1.6, M["V_cedar"], CI)
# auto-exposure ramp (drone)
vs = S.view_settings
if S.animation_data: S.animation_data_clear()
for f, e in ((1, 0.9), (60, 0.55), (120, 0.15), (160, 0.0)):
    vs.exposure = e; vs.keyframe_insert("exposure", frame=f)
print("v13 ok")
