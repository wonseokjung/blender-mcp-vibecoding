# villa v2: after the plaque, crane over the parapet into a low sunset-over-the-infinity-pool beat, then swing to the interior
import bpy, sys
sys.path.insert(0, 'scripts'); import tlib
cam = bpy.data.objects["Cam"]; tgt = bpy.data.objects["CamTarget"]
for idb in (cam, tgt, cam.data):
    for fc in tlib._fcurves(idb.animation_data.action):
        idx = [i for i, kp in enumerate(fc.keyframe_points) if kp.co[0] > 229]
        for i in reversed(idx): fc.keyframe_points.remove(fc.keyframe_points[i])
def k(f, l, t, lens):
    cam.location = l; cam.keyframe_insert("location", frame=f); tgt.location = t; tgt.keyframe_insert("location", frame=f)
    cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
k(242, (7.2, -16.4, 1.75), (-4, -15.5, 0.8), 28)
k(258, (4.4, -12.5, 0.72), (-14, -16.4, 0.65), 24)
k(272, (2.9, -12.3, 0.70), (-14, -16.0, 0.65), 24)
k(292, (0.2, -10.9, 1.05), (-1.7, 0, 1.15), 26)
k(312, (-1.8, -8.4, 1.25), (-1.8, 4, 1.15), 30)
print("v2cam ok")
