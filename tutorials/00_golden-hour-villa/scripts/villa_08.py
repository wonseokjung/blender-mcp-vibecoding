# villa_08: sun moved over the sea (WSW) for backlit establishing + sunset in the infinity pool;
# camera = NE high backlit establishing -> clockwise descending orbit -> low along the pool looking at the sunset;
# lettering moved to a terrace parapet facing the drone path; interior lights hidden from camera/reflections.
import bpy, math, sys
import numpy as np
from mathutils import Vector
sys.path.insert(0, 'scripts')
import tlib
S = bpy.context.scene
w = S.world
env = [n for n in w.node_tree.nodes if n.type == 'TEX_ENVIRONMENT'][0]
mpw = [n for n in w.node_tree.nodes if n.type == 'MAPPING'][0]
im = env.image; px = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4)
lum = px[..., :3].sum(-1); iy, ix = np.unravel_index(np.argmax(lum), lum.shape)
u = ix/im.size[0]; v = iy/im.size[1]; hdr_el = (v - 0.5)*math.pi; az_h = (0.5 - u)*2*math.pi
TARGET_AZ = math.radians(203)
mpw.inputs["Rotation"].default_value[2] = TARGET_AZ - az_h
sun = bpy.data.objects["V_sun"]
sd = Vector((math.cos(TARGET_AZ)*math.cos(hdr_el), math.sin(TARGET_AZ)*math.cos(hdr_el), math.sin(hdr_el)))
sun.rotation_euler = (-sd).to_track_quat('-Z', 'Y').to_euler()
sun.data.energy = 5.0; sun.data.color = (1.0, 0.58, 0.32)

# interior/emitter lights: no camera / glossy visibility (no floating white panels)
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name != "V_sun":
        o.visible_camera = False; o.visible_glossy = False

# move lettering: remove cedar-block lettering + graze, add a board-formed parapet with the plaque
for nm in ("V_brand", "V_brand_graze"):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
CB = bpy.data.collections["V_build"]; CL = bpy.data.collections["V_lights"]
for nm in ("V_parapet",):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
me = bpy.data.meshes.new("V_parapet")
x0, x1, y0, y1, z0, z1 = 4.0, 10.6, -16.3, -16.0, -0.6, 1.05
vv = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
me.from_pydata(vv, [], [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
par = bpy.data.objects.new("V_parapet", me); CB.objects.link(par); par.data.materials.append(bpy.data.materials["V_concrete"])
font = bpy.data.fonts.load(tlib.PRET % "Medium", check_existing=True)
cu = bpy.data.curves.new("V_brand", 'FONT'); cu.body = "CONNECT AI LAB"; cu.font = font
cu.size = 0.26; cu.extrude = 0.014; cu.bevel_depth = 0.002; cu.space_character = 1.4; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
cu.materials.append(bpy.data.materials["V_brushed_steel"])
br = bpy.data.objects.new("V_brand", cu); CB.objects.link(br)
br.location = (7.3, -16.33, 0.5); br.rotation_euler = (math.radians(90), 0, 0)

# camera
cam = bpy.data.objects["Cam"]; tgt = bpy.data.objects["CamTarget"]
cam.animation_data_clear(); tgt.animation_data_clear(); cam.data.animation_data_clear()
KEYS = [(1, (36, 30, 38), (-4, -8, 0), 24),
        (75, (52, -6, 25), (-3, -8, 0.5), 24),
        (150, (36, -38, 12), (-2, -9, 0.8), 26),
        (220, (13, -24, 3.2), (-2, -11, 1.0), 26),
        (288, (4.6, -12.6, 0.6), (-14, -15.2, 1.3), 26)]
for f, l, t, lens in KEYS:
    cam.location = l; cam.keyframe_insert("location", frame=f)
    tgt.location = t; tgt.keyframe_insert("location", frame=f)
    cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
print("v8 ok")
