# room-interior iter 3: backdrop still grey -> brighter camera-ray backdrop; warmer walls; fridge -> wardrobe
# (door seam + handles); bigger title label; furniture grouped under empties that drop in one after another
# (the "layout simulation" beat), labels fade out as the camera glides down to eye level behind the sofa
import sys, importlib, math, bpy
sys.path.insert(0, __import__('os').path.expanduser("scripts"))
import exlib; importlib.reload(exlib)
from exlib import *

s = sc()
w = s.world.node_tree
bgs = [n for n in w.nodes if n.type == 'BACKGROUND']; bgs[1].inputs[1].default_value = 1.75
p = bpy.data.materials["WallWhite"].node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (0.9, 0.86, 0.8, 1)
bpy.data.objects["Sun"].data.color = (1.0, 0.82, 0.6)

# wardrobe instead of the fridge
fr = bpy.data.objects.get("Fridge")
if fr: fr.name = "Wardrobe"
dark = bpy.data.materials["Charcoal"]
for nm, loc, sc_ in [("WardSeam", (2.625, 1.295, 0.9), (0.006, 0.01, 1.7)), ("WardH0", (2.58, 1.285, 1.0), (0.012, 0.02, 0.28)), ("WardH1", (2.67, 1.285, 1.0), (0.012, 0.02, 0.28))]:
    if not bpy.data.objects.get(nm): prim('cube', nm, loc=loc, scale=sc_, m=dark)

t = bpy.data.objects["LblT"]; t.data.size = 0.55; t.location = (-3.1, -3.25, 0.001)
lp = bpy.data.materials["Label"].node_tree.nodes["Principled BSDF"]; lp.inputs["Base Color"].default_value = (0.06, 0.06, 0.065, 1)

# groups -> empties at floor level, children keep their place
groups = {
    "G_Bed": ["BedFrame", "Headboard", "Mattress", "Duvet", "Pillow0", "Pillow1", "Nightstand", "LampBase", "LampShade"],
    "G_Desk": ["DeskTop", "DeskLeg0", "DeskLeg1", "DeskLeg2", "DeskLeg3", "Monitor", "MonitorScreen", "MonitorStand", "ChairSeat", "ChairBack", "ChairPost"],
    "G_Kitchen": ["KitchenBase", "KitchenTop", "Sink"],
    "G_Wardrobe": ["Wardrobe", "WardSeam", "WardH0", "WardH1"],
    "G_Rug": ["Rug", "CoffeeTable", "CoffeeLeg"],
    "G_Sofa": ["SofaBase", "SofaBack", "SofaArmL", "SofaArmR", "Cushion0", "Cushion1"],
    "G_Plant": ["Pot"] + [o.name for o in bpy.data.objects if o.name.startswith("Leaf")],
    "G_Decor": ["ArtFrame", "ArtCanvas", "ShelfBed", "Book0", "Book1", "Book2", "Vase"],
}
order = ["G_Bed", "G_Wardrobe", "G_Desk", "G_Kitchen", "G_Rug", "G_Sofa", "G_Plant", "G_Decor"]
for g in order:
    e = bpy.data.objects.get(g)
    if not e:
        e = link(bpy.data.objects.new(g, None)); e.empty_display_size = 0.3
    e.animation_data_clear(); e.location = (0, 0, 0)
    for n in groups[g]:
        o = bpy.data.objects[n]
        if o.parent != e:
            mw = o.matrix_world.copy(); o.parent = e; o.matrix_world = mw
for k, g in enumerate(order):
    e = bpy.data.objects[g]; f0 = 2 + k * 6
    e.location = (0, 0, 2.2); e.keyframe_insert("location", frame=f0)
    e.location = (0, 0, 0); e.keyframe_insert("location", frame=f0 + 16)
    for fc in exlib._fcurves(e.animation_data.action):
        kp = fc.keyframe_points[0]; kp.interpolation = 'EXPO'; kp.easing = 'EASE_OUT'
    e.scale = (0.001,) * 3; e.keyframe_insert("scale", frame=1)
    e.scale = (1, 1, 1); e.keyframe_insert("scale", frame=f0)
    for fc in exlib._fcurves(e.animation_data.action):
        if fc.data_path == "scale":
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for g in order:
    for n in groups[g]:
        o = bpy.data.objects[n]; o.animation_data_clear(); o.hide_render = o.hide_viewport = False

# labels fade
lp.inputs["Alpha"].default_value = 1.0; lp.inputs["Alpha"].keyframe_insert("default_value", frame=70)
lp.inputs["Alpha"].default_value = 0.0; lp.inputs["Alpha"].keyframe_insert("default_value", frame=100)
lp.inputs["Alpha"].default_value = 1.0

# camera: overview -> glide down to eye level behind the sofa, looking at bed + window
cam = bpy.data.objects["Cam"]; tg = bpy.data.objects["CamTarget"]; cam.animation_data_clear(); tg.animation_data_clear(); cam.data.animation_data_clear()
key(cam, "location", [(1, (7.3, -7.9, 7.0)), (60, (6.9, -7.6, 6.2)), (168, (2.35, -3.05, 1.45))])
key(tg, "location", [(1, (-0.1, 0.1, 0.5)), (60, (-0.15, 0.15, 0.5)), (168, (-1.6, 1.0, 0.9))])
cam.data.lens = 32; cam.data.keyframe_insert("lens", frame=60); cam.data.lens = 24; cam.data.keyframe_insert("lens", frame=168)
s.frame_set(1)
print("ok")
