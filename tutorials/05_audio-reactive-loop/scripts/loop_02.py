# loop_02: cyclic camera choreography mapped to the song structure (groove -> bullet-time orbit -> drop swoop -> dive into the eye)
import bpy, sys
sys.path.insert(0, 'scripts')
import tlib
S = bpy.context.scene; cam = bpy.data.objects["Cam"]; N = S.frame_end
cam.animation_data_clear(); cam.data.animation_data_clear()
K = [(1, (0.35, -2.75, 2.45), 50), (40, (0.9, -4.2, 2.8), 45), (100, (2.6, -7.2, 3.6), 35), (116, (3.1, -7.3, 3.7), 35),
     (160, (6.8, -2.8, 3.1), 35), (200, (6.0, 3.2, 2.6), 35), (228, (4.4, 5.6, 2.9), 35),
     (252, (3.8, -5.6, 4.3), 30), (292, (1.1, -4.6, 2.85), 42), (N + 1, (0.35, -2.75, 2.45), 50)]
for f, l, lens in K:
    cam.location = l; cam.keyframe_insert("location", frame=f)
    cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
for idb in (cam, cam.data):
    for fc in tlib._fcurves(idb.animation_data.action):
        fc.modifiers.new('CYCLES')
        for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()
for o in bpy.data.objects:
    if o.type == 'LIGHT': o.visible_camera = False
S.frame_set(1); print("cam ok")
