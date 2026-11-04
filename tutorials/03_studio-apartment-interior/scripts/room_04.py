# room-interior iter 4: the black cube mid-room = wardrobe seam/handles parented before their matrix_world existed
# (identity -> 1 m cube at the origin) -> reset their local transforms; wardrobe check; end framing a bit higher so the
# sofa back doesn't fill the bottom third
import bpy
from mathutils import Matrix
for nm, loc, sc_ in [("WardSeam", (2.625, 1.295, 0.9), (0.006, 0.01, 1.7)), ("WardH0", (2.58, 1.285, 1.0), (0.012, 0.02, 0.28)), ("WardH1", (2.67, 1.285, 1.0), (0.012, 0.02, 0.28))]:
    o = bpy.data.objects[nm]; o.matrix_parent_inverse = Matrix.Identity(4); o.location = loc; o.scale = sc_; o.rotation_euler = (0, 0, 0)
cam = bpy.data.objects["Cam"]
for f in cam.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
    kp = f.keyframe_points[-1]
    kp.co.y = (2.45, -3.25, 1.62)[f.array_index]
    f.update()
bpy.context.scene.frame_set(1)
print("ok")
