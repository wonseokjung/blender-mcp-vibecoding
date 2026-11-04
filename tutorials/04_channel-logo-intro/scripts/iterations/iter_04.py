# channel-intro iter 4: animation. letters tumble in from the dark (staggered, expo ease-out), light sweep
# across the chrome, green underline draws left->right, cursor blinks, slogan fades up, camera arcs low-left -> front
import sys, importlib, math, random, bpy
sys.path.insert(0, __import__('os').path.expanduser("scripts"))
import exlib; importlib.reload(exlib)
from exlib import *

s = sc()
bpy.data.materials["Green"].node_tree.nodes["Emission"].inputs[1].default_value = 0.9
names = sorted([o.name for o in bpy.data.objects if o.name.startswith("L") and o.type == 'FONT'])
random.seed(3)
for j, n in enumerate(names):
    o = bpy.data.objects[n]; o.animation_data_clear()
    hx, hy, hz = o["home"]; f0 = 3 + j * 3; f1 = f0 + 26
    o.location = (hx + random.uniform(-1.5, 1.5), 16 + random.uniform(0, 6), hz + random.uniform(1.0, 4.0))
    o.rotation_euler = (math.radians(90 + random.choice([-1, 1]) * random.uniform(100, 200)), math.radians(random.uniform(-60, 60)), math.radians(random.uniform(-90, 90)))
    o.keyframe_insert("location", frame=f0); o.keyframe_insert("rotation_euler", frame=f0)
    o.location = (hx, hy, hz); o.rotation_euler = (math.radians(90), 0, 0)
    o.keyframe_insert("location", frame=f1); o.keyframe_insert("rotation_euler", frame=f1)
    for fc in exlib._fcurves(o.animation_data.action):
        kp = fc.keyframe_points[0]; kp.interpolation = 'EXPO'; kp.easing = 'EASE_OUT'

# light sweep (letters only)
lc = bpy.data.collections["LetterSet"]
sw = bpy.data.objects.get("Sweep") or area("Sweep", (-12, -5, 3), (0, 0, 1.3), energy=2500, size=0.6, size_y=6, color=(0.9, 0.96, 1.0))
sw.light_linking.receiver_collection = lc; sw.animation_data_clear()
key(sw, "location", [(58, (-14, -6, 3)), (104, (14, -6, 3))])
for fc in exlib._fcurves(sw.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'SINE'; kp.easing = 'EASE_IN_OUT'
s.frame_set(1)

# underline draws from the left
ul = bpy.data.objects["Underline"]; ul.animation_data_clear()
W = ul.scale.x if ul.scale.x > 1 else ul.get("W", 10.0); ul["W"] = W
L = ul.location.x - W / 2
ul.scale = (0.0001, 0.04, 0.022); ul.location.x = L
ul.keyframe_insert("scale", frame=68); ul.keyframe_insert("location", frame=68)
ul.scale = (W, 0.04, 0.022); ul.location.x = L + W / 2
ul.keyframe_insert("scale", frame=94); ul.keyframe_insert("location", frame=94)
for fc in exlib._fcurves(ul.animation_data.action):
    kp = fc.keyframe_points[0]; kp.interpolation = 'EXPO'; kp.easing = 'EASE_OUT'

# cursor: hidden until the line is done, then blinks
cu = bpy.data.objects["Cursor"]; cu.animation_data_clear()
on = (0.14, 0.14, 0.9); off = (0.0001, 0.0001, 0.0001)
seq = [(1, off), (92, on)] + [(f, off if k % 2 == 0 else on) for k, f in enumerate(range(108, 169, 12))]
for f, v in seq:
    cu.scale = v; cu.keyframe_insert("scale", frame=f)
for fc in exlib._fcurves(cu.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# slogan fades + rises
sl = bpy.data.objects["Slogan"]; sl.animation_data_clear()
sp = bpy.data.materials["Slogan"].node_tree.nodes["Principled BSDF"].inputs["Alpha"]
sp.default_value = 0.0; sp.keyframe_insert("default_value", frame=98)
sp.default_value = 1.0; sp.keyframe_insert("default_value", frame=122)
sl.location.z = 0.2; sl.keyframe_insert("location", frame=98)
sl.location.z = 0.32; sl.keyframe_insert("location", frame=124)

# camera arc: low left -> front
cam = bpy.data.objects["Cam"]; cam.animation_data_clear(); tg = bpy.data.objects["CamTarget"]
key(cam, "location", [(1, (-7.5, -10.5, 0.45)), (168, (0.0, -14.0, 1.55))])
for fc in exlib._fcurves(cam.animation_data.action):
    kp = fc.keyframe_points[0]; kp.interpolation = 'SINE'; kp.easing = 'EASE_OUT'
tg.location = (0, 0, 1.15)
s.frame_set(40)
print("ok")
