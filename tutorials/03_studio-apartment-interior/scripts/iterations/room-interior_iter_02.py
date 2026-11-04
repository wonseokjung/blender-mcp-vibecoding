# room-interior iter 2: planks were 6x too big (object coords on a scaled slab) -> mapping in metres; sun hit from the
# front, never through the window -> aimed from outside the left wall; grey void -> warm off-white backdrop for camera
# rays only (world lighting stays a soft sky); wall art + floating shelf over the desk; dimension labels
import sys, importlib, math, bpy
sys.path.insert(0, __import__('os').path.expanduser("scripts"))
import exlib; importlib.reload(exlib)
from exlib import *
from mathutils import Vector

nt = bpy.data.materials["OakFloor"].node_tree
br = [n for n in nt.nodes if n.type == 'TEX_BRICK'][0]; tc = [n for n in nt.nodes if n.type == 'TEX_COORD'][0]
mp = nt.nodes.get("PlankMap") or nt.nodes.new("ShaderNodeMapping"); mp.name = "PlankMap"
mp.inputs["Scale"].default_value = (6.12, 4.12, 1.0)
nt.links.new(tc.outputs["Object"], mp.inputs[0]); nt.links.new(mp.outputs[0], br.inputs["Vector"])
br.inputs["Brick Width"].default_value = 1.1; br.inputs["Row Height"].default_value = 0.19

sn = bpy.data.objects["Sun"]
d = Vector((0.75, -0.15, -0.55)).normalized()
sn.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); sn.data.energy = 7.0

# world: soft sky light, warm off-white backdrop for the camera
w = bpy.context.scene.world; nt = w.node_tree; nt.nodes.clear()
lp = nt.nodes.new("ShaderNodeLightPath"); b1 = nt.nodes.new("ShaderNodeBackground"); b2 = nt.nodes.new("ShaderNodeBackground")
mx = nt.nodes.new("ShaderNodeMixShader"); out = nt.nodes.new("ShaderNodeOutputWorld")
b1.inputs[0].default_value = (0.70, 0.78, 0.92, 1); b1.inputs[1].default_value = 0.8
b2.inputs[0].default_value = (0.93, 0.91, 0.88, 1); b2.inputs[1].default_value = 1.0
nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); nt.links.new(b1.outputs[0], mx.inputs[1]); nt.links.new(b2.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs[0])

def box(name, x0, x1, y0, y1, z0, z1, m=None, bev=0.01):
    o = bpy.data.objects.get(name)
    if o: bpy.data.objects.remove(o, do_unlink=True)
    return prim('cube', name, loc=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), scale=(x1 - x0, y1 - y0, z1 - z0), m=m, bevel=bev, bseg=2)

wood = bpy.data.materials["WoodLight"]; dark = bpy.data.materials["Charcoal"]
art = mat("Art", base=(0.55, 0.42, 0.32), rough=0.9)
box("ArtFrame", 0.85, 1.75, 1.975, 2.0, 1.45, 2.05, dark, bev=0.0)
box("ArtCanvas", 0.9, 1.7, 1.965, 1.98, 1.5, 2.0, art, bev=0.0)
box("ShelfBed", -2.7, -1.4, 1.84, 2.0, 1.55, 1.58, wood, bev=0.0)
for k, (x, h, c) in enumerate([(-2.55, 0.22, (0.3, 0.35, 0.3)), (-2.45, 0.18, (0.8, 0.75, 0.66)), (-2.36, 0.24, (0.2, 0.22, 0.28))]):
    box(f"Book{k}", x - 0.035, x + 0.035, 1.86, 1.98, 1.58, 1.58 + h, mat(f"Book{k}", base=c, rough=0.7), bev=0.0)
prim('cylinder', "Vase", loc=(-1.8, 1.92, 1.68), scale=(0.12, 0.12, 0.2), m=bpy.data.materials["Pot"])

# floor-plan labels (lie flat beside the slab; fade out when the camera descends)
lab = mat("Label", base=(0.12, 0.12, 0.13), rough=0.6, alpha=1.0); lab.surface_render_method = 'BLENDED'
for o in [o for o in bpy.data.objects if o.name.startswith("Lbl")]:
    bpy.data.objects.remove(o, do_unlink=True)
text("6.0 m", "LblW", PRET % "SemiBold", size=0.28, extrude=0.0, bevel=0.0, align='CENTER', loc=(0, -2.45, 0.001), rot=(0, 0, 0), m=lab)
text("4.0 m", "LblD", PRET % "SemiBold", size=0.28, extrude=0.0, bevel=0.0, align='CENTER', loc=(3.45, 0, 0.001), rot=(0, 0, math.radians(90)), m=lab)
text("원룸 · 약 24㎡", "LblT", PRET % "Bold", size=0.42, extrude=0.0, bevel=0.0, align='LEFT', loc=(-3.1, -3.0, 0.001), rot=(0, 0, 0), m=lab)
lm = mat("LabelLine", base=(0.12, 0.12, 0.13), rough=0.6);
for o in [o for o in bpy.data.objects if o.name.startswith("Dim")]:
    bpy.data.objects.remove(o, do_unlink=True)
for nm, loc, sc_ in [("DimW", (0, -2.25, 0.001), (6.0, 0.012, 0.002)), ("DimD", (3.25, 0, 0.001), (0.012, 4.0, 0.002))]:
    prim('cube', nm, loc=loc, scale=sc_, m=lab)
print("ok")
