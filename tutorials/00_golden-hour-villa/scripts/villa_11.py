# villa_11: golden-hour physical sky (sun 4.5deg WSW, aerosol 3), greener ground scan, camera v4 (13 s) ending on the interior
import bpy, math
S = bpy.context.scene
S["sky_str"] = 0.12; S["sun_el"] = 4.5; S["aero"] = 3.0; S["sun_az"] = 203.0
exec(compile(open('scripts/villa_sky.py').read(), 'sky', 'exec'))

# ground: swap the flat-area scan (aerial_grass_rock -> leafy_grass) and scale
nt = bpy.data.materials["V_terrain"].node_tree
for n in nt.nodes:
    if n.type == 'TEX_IMAGE' and n.image and n.image.name.startswith("aerial_grass_rock_"):
        suf = n.image.name[len("aerial_grass_rock_"):]
        n.image = bpy.data.images["leafy_grass_" + suf]
        mp = n.inputs["Vector"].links[0].from_node
        mp.inputs["Scale"].default_value = (1/4.0,)*3
for n in nt.nodes:
    if n.type == 'HUE_SAT' and abs(n.inputs["Saturation"].default_value - 0.85) < 1e-3:
        n.inputs["Saturation"].default_value = 0.9; n.inputs["Value"].default_value = 0.8

cam = bpy.data.objects["Cam"]; tgt = bpy.data.objects["CamTarget"]
cam.animation_data_clear(); tgt.animation_data_clear(); cam.data.animation_data_clear()
KEYS = [(1, (36, 30, 38), (-4, -8, 0), 24),
        (70, (52, -6, 25), (-3, -9, 0.5), 24),
        (135, (34, -36, 11), (-1, -11, 0.8), 26),
        (195, (14.5, -25, 2.6), (6.5, -16.3, 0.6), 30),
        (228, (8.6, -19.4, 0.85), (7.0, -16.3, 0.55), 32),
        (252, (7.4, -16.6, 1.9), (-2, -9, 0.9), 26),
        (282, (2.0, -12.6, 1.15), (-1.6, 0, 1.15), 26),
        (312, (-1.8, -8.4, 1.25), (-1.8, 4, 1.15), 30)]
for f, l, t, lens in KEYS:
    cam.location = l; cam.keyframe_insert("location", frame=f)
    tgt.location = t; tgt.keyframe_insert("location", frame=f)
    cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
S.frame_end = 312
print("v11 ok")
