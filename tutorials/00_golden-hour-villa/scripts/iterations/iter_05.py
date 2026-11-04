# villa_05: modern interior, roof terrace, slim fascia, CONNECT AI LAB brushed-steel lettering, new camera end on pool/interior/lettering
import bpy, math, sys
import numpy as np
from mathutils import Vector
sys.path.insert(0, 'scripts')
import importlib, tlib; importlib.reload(tlib)
S = bpy.context.scene
CB = bpy.data.collections["V_build"]; CI = bpy.data.collections["V_interior"]; CL = bpy.data.collections["V_lights"]
for c in (CB, CI, CL):
    for o in list(c.objects):
        if o.get("v5"): bpy.data.objects.remove(o, do_unlink=True)
for o in list(CI.objects):
    if o.get("prop"): bpy.data.objects.remove(o, do_unlink=True)

def mesh_obj(name, verts, faces, c, m=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); c.objects.link(o); o["v5"] = 1
    if m: o.data.materials.append(m)
    return o
def box(name, x0, x1, y0, y1, z0, z1, m, c=CB, bevel=0.0, seg=2):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    o = mesh_obj(name, v, f, c, m)
    if bevel:
        md = o.modifiers.new("b", 'BEVEL'); md.width = bevel; md.segments = seg
        for p in o.data.polygons: p.use_smooth = True
        o.modifiers.new("wn", 'WEIGHTED_NORMAL') if hasattr(bpy.types, "WeightedNormalModifier") else None
    return o
def place(src, loc, rotz=0.0, scale=1.0, c=CI):
    so = bpy.data.objects[src]
    o = so.copy(); o["v5"] = 1; c.objects.link(o)
    o.location = loc; o.rotation_euler = (0, 0, math.radians(rotz)); o.scale = (scale,)*3; o.parent = None
    return o

M = bpy.data.materials
M_conc = M["V_concrete"]; M_wood = M["V_cedar"]; M_deck = M["V_deck"]; M_glass = M["V_glass"]; M_frame = M["V_frame"]
M_fab = tlib.mat("V_fabric", base=(0.62, 0.58, 0.52), rough=0.95, sss=0.0)
M_fab2 = tlib.mat("V_fabric_dark", base=(0.18, 0.16, 0.14), rough=0.9)
M_trav = tlib.mat("V_travertine", base=(0.78, 0.70, 0.58), rough=0.45)
M_oak = M["V_cedar"]
M_rug = tlib.mat("V_rug", base=(0.42, 0.38, 0.33), rough=1.0)
M_steel = bpy.data.materials.get("V_brushed_steel") or bpy.data.materials.new("V_brushed_steel")
M_steel.use_nodes = True
p = M_steel.node_tree.nodes["Principled BSDF"]
p.inputs["Base Color"].default_value = (0.82, 0.80, 0.76, 1); p.inputs["Metallic"].default_value = 1.0
p.inputs["Roughness"].default_value = 0.22
try:
    p.inputs["Anisotropic"].default_value = 0.85
except Exception:
    pass
M_gravel = tlib.mat("V_gravel", base=(0.32, 0.31, 0.29), rough=0.9)
M_warmglow = tlib.emit_mat("V_cove", (1.0, 0.62, 0.3), 6.0)
# deck: desaturate the reddish PH deck toward silver-grey teak
nt = M_deck.node_tree
if not any(n.name == "deck_desat" for n in nt.nodes):
    pb = nt.nodes["Principled BSDF"]
    lk = [l for l in nt.links if l.to_socket == pb.inputs["Base Color"]][0]
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.name = "deck_desat"
    hs.inputs["Saturation"].default_value = 0.45; hs.inputs["Value"].default_value = 0.9
    nt.links.new(lk.from_socket, hs.inputs["Color"]); nt.links.new(hs.outputs[0], pb.inputs["Base Color"])

FF, RF = 3.5, 7.0
# ---------- interior: living room ----------
for nm in ("sofa_03.001", "modern_coffee_table_02.001"):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
# low modular sofa (faces the sea, -Y), L-shaped
box("V_sofa_base", -4.2, 0.6, 0.0, 1.05, 0.02, 0.38, M_fab, CI, bevel=0.04)
box("V_sofa_back", -4.2, 0.6, 0.75, 1.05, 0.38, 0.82, M_fab, CI, bevel=0.06, seg=3)
for i, x in enumerate(np.linspace(-4.15, 0.55, 4)[:-1]):
    box(f"V_sofa_cush_{i}", x + 0.02, x + 1.55, 0.02, 0.76, 0.38, 0.52, M_fab, CI, bevel=0.06, seg=3)
box("V_sofa_L", 0.6, 1.6, -1.2, 1.05, 0.02, 0.38, M_fab, CI, bevel=0.04)
box("V_sofa_L_cush", 0.62, 1.58, -1.18, 0.74, 0.38, 0.52, M_fab, CI, bevel=0.06, seg=3)
box("V_sofa_L_arm", 1.35, 1.6, -1.2, 1.05, 0.38, 0.75, M_fab, CI, bevel=0.06, seg=3)
for i, (x, y) in enumerate([(-3.6, 0.85), (-0.3, 0.85)]):
    box(f"V_pillow_{i}", x, x + 0.5, y - 0.12, y + 0.02, 0.52, 0.95, M_fab2, CI, bevel=0.08, seg=3)
box("V_rug", -4.8, 1.9, -2.6, 1.3, 0.02, 0.035, M_rug, CI)
box("V_coffee", -2.6, -0.9, -1.6, -0.75, 0.035, 0.38, M_trav, CI, bevel=0.015)
place("mid_century_lounge_chair", (-5.3, -1.9, 0.02), 140)
def place_coll(cn, loc, rotz=0, scale=1.0, c=CI):
    e = bpy.data.objects.new("V_ci_" + cn, None); e.instance_type = 'COLLECTION'; e.instance_collection = bpy.data.collections[cn]
    c.objects.link(e); e["v5"] = 1; e.location = loc; e.rotation_euler = (0, 0, math.radians(rotz)); e.scale = (scale,)*3
    return e
place_coll("potted_plant_01", (-7.9, -3.6, 0.02), 0, 1.6)
place_coll("potted_plant_02", (3.9, 3.6, 0.02), 30, 3.0)
# cedar slat feature wall on the back wall + warm cove light
for i, x in enumerate(np.arange(-8.4, 4.8, 0.14)):
    box(f"V_slat_{i}", x, x + 0.07, 4.32, 4.45, 0.02, FF - 0.02, M_wood, CI)
cove = box("V_cove_strip", -8.5, 4.9, 4.25, 4.3, FF - 0.12, FF - 0.08, M_warmglow, CI)
# wall-wash area light grazing the slats
l = bpy.data.lights.new("V_slat_wash", 'AREA'); l.energy = 400; l.color = (1.0, 0.68, 0.42); l.shape = 'RECTANGLE'; l.size = 13; l.size_y = 0.2
o = bpy.data.objects.new("V_slat_wash", l); CL.objects.link(o); o["v5"] = 1; o.location = (-1.8, 3.7, FF - 0.12)
o.rotation_euler = (math.radians(30), 0, 0)
# dining: oak slab table (replace classic table)
for nm in list(bpy.data.objects.keys()):
    if nm.startswith("dining_table") and "." in nm: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
box("V_dtable_top", -7.6, -5.0, 1.75, 2.75, 0.72, 0.78, M_oak, CI, bevel=0.01)
box("V_dtable_leg1", -7.3, -7.2, 1.85, 2.65, 0.02, 0.72, M_frame, CI)
box("V_dtable_leg2", -5.4, -5.3, 1.85, 2.65, 0.02, 0.72, M_frame, CI)
# floor lamp (arc) glow
box("V_lamp_pole", 1.95, 2.0, 1.15, 1.2, 0.02, 1.6, M_frame, CI)
sph = bpy.data.meshes.new("V_lampshade")
import bmesh
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.22); bm.to_mesh(sph); bm.free()
for pz in sph.polygons: pz.use_smooth = True
ls = bpy.data.objects.new("V_lampshade", sph); CI.objects.link(ls); ls["v5"] = 1; ls.location = (1.97, 1.17, 1.7)
ls.data.materials.append(tlib.emit_mat("V_lampglow", (1.0, 0.7, 0.42), 12.0))
# pendant lamp globes emissive
for o in bpy.data.objects:
    if o.name.startswith("modern_ceiling_lamp_01.") and o.users_collection and o.users_collection[0] == CI:
        pass
# upper floor: bedroom glow + cedar wall
for i, x in enumerate(np.arange(-10.4, 7.4, 0.16)):
    box(f"V_ffslat_{i}", x, x + 0.08, 4.28, 4.4, FF + 0.35, RF - 0.02, M_wood, CI)
box("V_bed", -6.5, -3.5, 1.6, 4.2, FF + 0.35, FF + 0.85, M_fab, CI, bevel=0.05)
box("V_ffcove", -10.5, 7.5, 4.15, 4.2, RF - 0.12, RF - 0.08, M_warmglow, CI)

# ---------- roof: thin fascia, roof terrace ----------
for nm in ("V_roof",):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
box("V_roof2", -11.8, 8.8, -8.8, 5.6, RF, RF + 0.22, M_conc)
box("V_roof_deck", -10.6, -1.0, -7.6, 4.4, RF + 0.22, RF + 0.3, M_deck)
box("V_roof_gravel", -1.0, 7.6, -7.6, 4.4, RF + 0.22, RF + 0.27, M_gravel)
box("V_roof_glassrail", -11.7, 8.7, -8.72, -8.68, RF + 0.22, RF + 1.25, M_glass)
box("V_roof_planter", -10.6, -1.0, 3.3, 4.4, RF + 0.3, RF + 0.75, M_conc)
box("V_skylight", 2.0, 5.5, -3.0, 1.0, RF + 0.27, RF + 0.33, M_glass)
# ground-floor slim canopy over the terrace (wood soffit)
box("V_canopy_soffit", -11.0, 8.0, -8.0, 5.0, FF - 0.02, FF, M_wood)

# ---------- brand lettering: CONNECT AI LAB (brushed steel) on the cedar block ----------
for nm in list(bpy.data.objects.keys()):
    if nm.startswith("V_brand"): bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
font = bpy.data.fonts.load(tlib.PRET % "Medium", check_existing=True)
cu = bpy.data.curves.new("V_brand", 'FONT'); cu.body = "CONNECT AI LAB"; cu.font = font
cu.size = 0.30; cu.extrude = 0.012; cu.bevel_depth = 0.002; cu.space_character = 1.35; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
cu.materials.append(M_steel)
br = bpy.data.objects.new("V_brand", cu); CB.objects.link(br); br["v5"] = 1
br.location = (11.25, -2.035, 2.2); br.rotation_euler = (math.radians(90), 0, 0)
# small grazing uplight under the lettering
l = bpy.data.lights.new("V_brand_graze", 'AREA'); l.energy = 40; l.color = (1.0, 0.72, 0.48); l.size = 4.0; l.size_y = 0.06
o = bpy.data.objects.new("V_brand_graze", l); CL.objects.link(o); o["v5"] = 1
o.location = (11.25, -2.45, 0.2); o.rotation_euler = (math.radians(168), 0, 0)
print("v5 ok")
