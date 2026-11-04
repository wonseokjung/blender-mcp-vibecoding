# villa_cam: camera path over the sea -> descend orbit -> 1.2 m before the living-room glass; interior props
import bpy, math
from mathutils import Vector
S = bpy.context.scene
cam = bpy.data.objects["Cam"]; tgt = bpy.data.objects["CamTarget"]
cam.animation_data_clear(); tgt.animation_data_clear(); cam.data.animation_data_clear()
KEYS = [(1, (-58, -26, 27), (0, -3, 1.0), 24),
        (75, (-50, -47, 19), (-0.5, -4, 1.2), 24),
        (150, (-28, -45, 9.5), (-1, -4, 1.4), 26),
        (215, (-8, -25, 3.2), (-1.5, -2, 1.5), 30),
        (288, (-1.8, -5.65, 1.42), (-1.8, 4, 1.32), 34)]
for f, l, t, lens in KEYS:
    cam.location = l; cam.keyframe_insert("location", frame=f)
    tgt.location = t; tgt.keyframe_insert("location", frame=f)
    cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
def fcs(idb):
    ad = idb.animation_data
    out = []
    try:
        out = list(ad.action.fcurves)
    except Exception:
        for layer in ad.action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags: out += list(cb.fcurves)
    return out
for idb in (cam, tgt, cam.data):
    for fc in fcs(idb):
        for i, kp in enumerate(fc.keyframe_points):
            kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        fc.keyframe_points[0].handle_right_type = 'AUTO_CLAMPED'
        fc.update()
cam.data.dof.use_dof = False

# ---- interior props (linked duplicates of Poly Haven objects) ----
CI = bpy.data.collections["V_interior"]
for o in list(CI.objects):
    if o.get("prop"): bpy.data.objects.remove(o, do_unlink=True)
def place(src, loc, rotz=0.0, scale=1.0):
    so = bpy.data.objects[src]
    o = so.copy(); o["prop"] = 1; CI.objects.link(o)
    o.location = loc; o.rotation_euler = (0, 0, math.radians(rotz)); o.scale = (scale,)*3; o.parent = None
    return o
place("sofa_03", (-1.8, 0.6, 0.02), 180)
place("modern_coffee_table_02", (-1.8, -1.2, 0.02), 0)
place("dining_table", (-6.3, 2.2, 0.02), 90)
place("dining_table_cloth", (-6.3, 2.2, 0.02), 90) if "dining_table_cloth" in bpy.data.objects else None
for i, (x, y, r) in enumerate([(-7.0, 1.3, 0), (-5.6, 1.3, 0), (-7.0, 3.1, 180), (-5.6, 3.1, 180)]):
    place("dining_chair_02", (x, y, 0.02), r)
for i, x in enumerate((-7.0, -5.6)):
    place("modern_ceiling_lamp_01", (x, 2.2, 2.45), 0)
print([ (o.name, tuple(round(v, 2) for v in o.dimensions)) for o in CI.objects if o.get("prop")])
S.frame_set(288)
