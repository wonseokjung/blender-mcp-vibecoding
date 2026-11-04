# villa_cam: camera path over the sea -> descend orbit -> 1.2 m before the living-room glass; interior props
import bpy, math
from mathutils import Vector
S = bpy.context.scene
cam = bpy.data.objects["Cam"]; tgt = bpy.data.objects["CamTarget"]
cam.animation_data_clear(); tgt.animation_data_clear(); cam.data.animation_data_clear()
KEYS = [(1, (-46, -44, 26), (0, -3, 1.5), 24),
        (80, (-40, -52, 17), (0, -4, 1.6), 24),
        (160, (-22, -40, 7.5), (0, -4, 1.6), 26),
        (225, (-10.5, -22, 2.6), (0.5, -4, 1.6), 28),
        (288, (-5.6, -15.6, 1.15), (2.5, -2.5, 1.75), 30)]
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

