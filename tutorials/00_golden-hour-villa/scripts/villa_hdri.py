import bpy, math, numpy as np
from mathutils import Vector
def use_hdri(imgname, target_az_deg=203, strength=0.8):
    S = bpy.context.scene; w = [x for x in bpy.data.worlds if "qwantani" in x.name][0]; S.world = w
    env = [n for n in w.node_tree.nodes if n.type == 'TEX_ENVIRONMENT'][0]
    mpw = [n for n in w.node_tree.nodes if n.type == 'MAPPING'][0]
    bg = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND'][0]; bg.inputs["Strength"].default_value = strength
    env.image = bpy.data.images[imgname]; im = env.image
    px = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4)
    lum = px[..., :3].sum(-1); iy, ix = np.unravel_index(np.argmax(lum), lum.shape)
    u = ix/im.size[0]; v = iy/im.size[1]; el = (v - 0.5)*math.pi; az_h = (0.5 - u)*2*math.pi
    T = math.radians(target_az_deg)
    mpw.inputs["Rotation"].default_value[2] = T - az_h
    sun = bpy.data.objects["V_sun"]
    sd = Vector((math.cos(T)*math.cos(el), math.sin(T)*math.cos(el), math.sin(el)))
    sun.rotation_euler = (-sd).to_track_quat('-Z', 'Y').to_euler()
    c = px[iy, ix, :3]; print(imgname, "sun el %.1f" % math.degrees(el), "col", np.round(c/c.max(), 2))
    return el
