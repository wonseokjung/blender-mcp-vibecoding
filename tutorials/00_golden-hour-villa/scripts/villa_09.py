# villa_09: re-height terrain (west side falls to the sea), larger/darker cliff rock w/ variation,
# lights invisible through glass, camera v3 with a plaque pass + crane-up reveal of the infinity pool
import bpy, math, sys
import numpy as np
exec(compile(open('scripts/villa_terrain_fn.py').read(), 'tf', 'exec'))
S = bpy.context.scene
for nm, drop in (("V_terrain_near", 0.0), ("V_terrain_far", 0.6)):
    o = bpy.data.objects[nm]; n = len(o.data.vertices)
    co = np.zeros(n*3, np.float32); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    co[:, 2] = height(co[:, 0], co[:, 1])
    if drop:
        inside = (np.abs(co[:, 0]) < 69) & (co[:, 1] > -59) & (co[:, 1] < 49); co[inside, 2] -= drop
    o.data.vertices.foreach_set("co", co.ravel()); o.data.update()

# terrain rock: bigger scale + darker, break tiling with noise-driven mapping offset
nt = bpy.data.materials["V_terrain"].node_tree
for n in nt.nodes:
    if n.type == 'MAPPING':
        sc = n.inputs["Scale"].default_value[0]
        if abs(sc - 1/5.0) < 1e-4: n.inputs["Scale"].default_value = (1/11.0,)*3
for n in nt.nodes:
    if n.type == 'HUE_SAT' and abs(n.inputs["Value"].default_value - 0.55) < 1e-3:
        n.inputs["Value"].default_value = 0.38; n.inputs["Saturation"].default_value = 0.35

for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name != "V_sun":
        o.visible_camera = False; o.visible_glossy = False; o.visible_transmission = False

cam = bpy.data.objects["Cam"]; tgt = bpy.data.objects["CamTarget"]
cam.animation_data_clear(); tgt.animation_data_clear(); cam.data.animation_data_clear()
KEYS = [(1, (36, 30, 38), (-4, -8, 0), 24),
        (70, (52, -6, 25), (-3, -9, 0.5), 24),
        (140, (34, -36, 11), (-1, -11, 0.8), 26),
        (205, (14.5, -25, 2.6), (6.5, -16.3, 0.6), 30),
        (240, (8.6, -19.4, 0.85), (7.0, -16.3, 0.55), 32),
        (262, (7.6, -16.6, 1.75), (-4, -14.5, 0.9), 28),
        (288, (7.0, -11.4, 1.0), (-14, -15.6, 1.05), 24)]
for f, l, t, lens in KEYS:
    cam.location = l; cam.keyframe_insert("location", frame=f)
    tgt.location = t; tgt.keyframe_insert("location", frame=f)
    cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
print("v9 ok")
