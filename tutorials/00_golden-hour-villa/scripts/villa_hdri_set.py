import bpy, math, numpy as np
from mathutils import Vector
S = bpy.context.scene
imgname = S["hdri_img"]; T = math.radians(S.get("sun_az", 203.0))
w = None
for x in bpy.data.worlds:
    if "qwantani" in x.name: w = x
S.world = w
env = mpw = bg = None
for n in w.node_tree.nodes:
    if n.type == 'TEX_ENVIRONMENT': env = n
    if n.type == 'MAPPING': mpw = n
    if n.type == 'BACKGROUND': bg = n
bg.inputs["Strength"].default_value = S.get("hdri_str", 0.8)
env.image = bpy.data.images[imgname]; im = env.image
px = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4)
lum = px[..., :3].sum(-1); iy, ix = np.unravel_index(np.argmax(lum), lum.shape)
u = ix/im.size[0]; v = iy/im.size[1]; el = (v - 0.5)*math.pi; az_h = (0.5 - u)*2*math.pi
mpw.inputs["Rotation"].default_value[2] = T - az_h
sun = bpy.data.objects["V_sun"]
sd = Vector((math.cos(T)*math.cos(el), math.sin(T)*math.cos(el), math.sin(el)))
sun.rotation_euler = (-sd).to_track_quat('-Z', 'Y').to_euler()
c = px[iy, ix, :3]; print(imgname, "sun el %.1f" % math.degrees(el), "col", np.round(c/c.max(), 2))
