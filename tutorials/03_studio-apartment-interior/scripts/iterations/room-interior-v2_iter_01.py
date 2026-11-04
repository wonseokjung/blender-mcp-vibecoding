# room-interior v2 iter 1: swap block furniture for Poly Haven photoscans (CC0), scanned floor/wall/fabric/wood
# textures (world-space box mapping at their real-world size), keep cutaway + drop-in groups + labels; Cycles
import bpy, math, os
from mathutils import Vector, Matrix

S = bpy.context.scene
OBJ = bpy.data.objects

def kill(names):
    for n in names:
        o = OBJ.get(n)
        if o: bpy.data.objects.remove(o, do_unlink=True)

# 1) remove v1 blocks that get real scans
kill(["SofaBase", "SofaBack", "SofaArmL", "SofaArmR", "Cushion0", "Cushion1", "CoffeeTable", "CoffeeLeg",
      "ChairSeat", "ChairBack", "ChairPost", "ArtFrame", "ArtCanvas", "ShelfBed", "Book0", "Book1", "Book2", "Vase", "Pot"]
     + [o.name for o in OBJ if o.name.startswith(("Leaf", "Stem"))])
# drop the rigged desk lamp (rig + widgets + helpers); the v1 bedside lamp stays
kill([o.name for o in OBJ if o.name.startswith(("geo_", "cur_", "hlp_", "wdg_", "rig_lamp"))])

def world_tex(mat_name, size_m, plane=None):
    """re-map a Poly Haven texture material to world-space box projection at its real size"""
    m = bpy.data.materials[mat_name]; nt = m.node_tree
    geo = nt.nodes.get("WGeo") or nt.nodes.new("ShaderNodeNewGeometry"); geo.name = "WGeo"
    mp = [n for n in nt.nodes if n.type == 'MAPPING'][0]
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    mp.inputs["Scale"].default_value = (1 / size_m, 1 / size_m, 1 / size_m)
    for n in nt.nodes:
        if n.type == 'TEX_IMAGE':
            n.projection = 'BOX'; n.projection_blend = 0.15
    # bump-only, gentle (scanned displacement maps would push the walls around)
    out = nt.nodes["Material Output"]
    for l in list(out.inputs["Displacement"].links): nt.links.remove(l)
    return m

def size_of(mat_name, default):
    mm = bpy.data.materials[mat_name].get("polyhaven_scale_mm")
    return (mm[0] / 1000.0) if mm else default

floor_m = world_tex("herringbone_parquet", size_of("herringbone_parquet", 2.0))
wall_m = world_tex("white_plaster_02", size_of("white_plaster_02", 2.0))
oak_m = world_tex("oak_veneer_01", size_of("oak_veneer_01", 1.0))
linen_m = world_tex("rough_linen", size_of("rough_linen", 0.5))
duvet_m = world_tex("jersey_melange", size_of("jersey_melange", 0.5))
rug_m = world_tex("wool_boucle", size_of("wool_boucle", 0.5))
print("sizes", [(n, size_of(n, -1)) for n in ("herringbone_parquet", "white_plaster_02", "oak_veneer_01", "rough_linen", "jersey_melange", "wool_boucle")])

def setm(name, m):
    o = OBJ.get(name)
    if o and o.type in ('MESH', 'CURVE', 'FONT'):
        o.data.materials.clear(); o.data.materials.append(m)

setm("Floor", floor_m)
for n in ("WallBack", "WallL_a", "WallL_b", "WallL_c", "WallL_d"): setm(n, wall_m)
for n in ("BedFrame", "Headboard", "Nightstand", "DeskTop", "Wardrobe"): setm(n, oak_m)
for n in ("Mattress", "Pillow0", "Pillow1"): setm(n, linen_m)
setm("Duvet", duvet_m); setm("Rug", rug_m)
# softer bed: subdivide the duvet/pillows a little
for n in ("Duvet", "Pillow0", "Pillow1", "Mattress"):
    o = OBJ[n]
    if not o.modifiers.get("Sub"):
        md = o.modifiers.new("Sub", 'SUBSURF'); md.levels = 1; md.render_levels = 2

# 2) place the scans (all metric, origin at floor) and put them into the v1 drop-in groups
def place(name, loc, rz=0.0, group=None):
    o = OBJ[name]; o.location = loc; o.rotation_euler = (0, 0, math.radians(rz))
    if group:
        g = OBJ[group]; o.parent = g; o.matrix_parent_inverse = Matrix.Identity(4)
    return o

place("sofa_03", (1.15, -1.45, 0.0), 0, "G_Sofa")                 # faces +y (into the room)
place("modern_coffee_table_01", (1.15, -0.25, 0.0), 0, "G_Rug")
place("modern_arm_chair_01", (-1.9, -0.85, 0.0), -60, "G_Kitchen")
place("side_table_01", (-2.55, -0.25, 0.0), 0, "G_Kitchen")
ps = OBJ.get("PlantScan") or bpy.data.objects.new("PlantScan", None)
if ps.name not in S.collection.objects: S.collection.objects.link(ps)
for n in ("potted_plant_02_pot", "potted_plant_02_leaves", "potted_plant_02_dirt"):
    o = OBJ[n]
    if o.parent != ps: o.parent = ps; o.matrix_parent_inverse = Matrix.Identity(4)
ps.scale = (1.6, 1.6, 1.6)
place("PlantScan", (-0.45, -1.6, 0.0), 0, "G_Plant")
place("dining_chair_02", (1.3, 1.0, 0.0), 180, "G_Desk")
place("hanging_picture_frame_01", (1.3, 1.985, 1.45), 180, "G_Decor")
place("wooden_display_shelves_01", (-0.1, 1.8, 0.0), 0, "G_Decor")
for k in (1, 2, 3):
    d = OBJ[f"wooden_display_shelves_01_drawer_0{k}"]
    if d.parent is None:
        d.parent = OBJ["wooden_display_shelves_01"]; d.matrix_parent_inverse = Matrix.Identity(4)

# 3) Cycles + world: Poly Haven sky lights the room, camera rays keep the warm off-white backdrop
S.render.engine = 'CYCLES'
S.cycles.device = 'CPU'           # look-dev previews on CPU (GPU is reserved for the locked batch)
S.cycles.samples = 96; S.cycles.use_adaptive_sampling = True; S.cycles.adaptive_threshold = 0.03
S.cycles.use_denoising = True; S.cycles.denoiser = 'OPENIMAGEDENOISE'
S.cycles.max_bounces = 8; S.cycles.caustics_reflective = False; S.cycles.caustics_refractive = False
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'
w = bpy.data.worlds["PolyHaven kloofendal_48d_partly_cloudy_puresky"]; nt = w.node_tree
bg = [n for n in nt.nodes if n.type == 'BACKGROUND'][0]; bg.inputs["Strength"].default_value = 1.0
out = [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0]
if "CamMix" not in nt.nodes:
    lp = nt.nodes.new("ShaderNodeLightPath"); bb = nt.nodes.new("ShaderNodeBackground"); bb.name = "Backdrop"
    mx = nt.nodes.new("ShaderNodeMixShader"); mx.name = "CamMix"
    bb.inputs[0].default_value = (0.93, 0.91, 0.88, 1); bb.inputs[1].default_value = 1.0
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); nt.links.new(bg.outputs[0], mx.inputs[1]); nt.links.new(bb.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
mpw = [n for n in nt.nodes if n.type == 'MAPPING'][0]; mpw.inputs["Rotation"].default_value[2] = math.radians(200)
S.world = w
for n in ("Bounce",):
    o = OBJ.get(n)
    if o: o.data.energy = 60
S.frame_set(168)
print("ok")
