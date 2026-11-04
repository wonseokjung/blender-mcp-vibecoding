# villa_01: site, terrain, sea, villa massing, lights, camera (Cycles). Assets already downloaded into AS collections.
import bpy, bmesh, math, sys, random
import numpy as np
from mathutils import Vector
sys.path.insert(0, 'scripts')
import importlib, tlib; importlib.reload(tlib)
S = bpy.context.scene

# ---------- clean previous build (keep asset collections + PH materials) ----------
for c in list(bpy.data.collections):
    if c.name.startswith("V_"):
        for o in list(c.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(c)
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name.endswith("_LOD0") or lc.name.startswith("AS_") or lc.name in ("rock_moss_set_01", "sofa_03", "dining_table", "modern_ceiling_lamp_01", "dining_chair_02", "modern_coffee_table_02", "coast_land_rocks_04"):
        lc.exclude = True
for c in bpy.data.collections:
    pass

def coll(name):
    c = bpy.data.collections.new(name); S.collection.children.link(c); return c
CB = coll("V_build"); CT = coll("V_terrain"); CV = coll("V_veg"); CL = coll("V_lights"); CI = coll("V_interior")

def mesh_obj(name, verts, faces, c, m=None, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    if m: o.data.materials.append(m)
    return o

def box(name, x0, x1, y0, y1, z0, z1, m, c=CB, bevel=0.0):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    f = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    o = mesh_obj(name, v, f, c, m)
    if bevel:
        md = o.modifiers.new("b", 'BEVEL'); md.width = bevel; md.segments = 2
    return o

# ---------- materials ----------
def ph_world(mname, size_m=None, newname=None, rot=0.0):
    """copy a Poly Haven texture material and map it by world position (box projection)."""
    src = bpy.data.materials[mname]
    m = bpy.data.materials.get(newname or (mname + "_W"))
    if m: bpy.data.materials.remove(m)
    m = src.copy(); m.name = newname or (mname + "_W")
    nt = m.node_tree
    mp = [n for n in nt.nodes if n.type == 'MAPPING'][0]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    sz = size_m or (src["polyhaven_scale_mm"][0] / 1000.0)
    mp.inputs["Scale"].default_value = (1/sz, 1/sz, 1/sz)
    mp.inputs["Rotation"].default_value[2] = rot
    for n in nt.nodes:
        if n.type == 'TEX_IMAGE':
            n.projection = 'BOX'; n.projection_blend = 0.25
    return m

M_conc = ph_world("concrete_wall_008", 3.0, "V_concrete")
M_wood = ph_world("japanese_cedar_planks", 2.0, "V_cedar")
M_deck = ph_world("wood_floor_deck", 2.5, "V_deck")
M_rock = ph_world("dark_rock_02", 4.0, "V_rock")
M_grass = ph_world("aerial_grass_rock", 9.0, "V_grassrock")
M_sand = ph_world("coast_sand_01", 3.0, "V_sand")

M_glass = tlib.mat("V_glass", base=(0.9, 0.95, 0.95), rough=0.0, transmission=1.0, ior=1.45)
M_glass.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.5
M_frame = tlib.mat("V_frame", base=(0.03, 0.03, 0.03), metal=0.8, rough=0.35)
M_inner = tlib.mat("V_interior_wall", base=(0.78, 0.74, 0.68), rough=0.7)
M_floor = tlib.mat("V_floor_stone", base=(0.55, 0.52, 0.48), rough=0.25)
M_tile = tlib.mat("V_pool_tile", base=(0.06, 0.16, 0.17), rough=0.3)
M_white = tlib.mat("V_white", base=(0.85, 0.84, 0.8), rough=0.5)

# pool water
M_water = bpy.data.materials.get("V_water") or bpy.data.materials.new("V_water")
M_water.use_nodes = True; nt = M_water.node_tree; nt.nodes.clear()
o = nt.nodes.new("ShaderNodeOutputMaterial"); p = nt.nodes.new("ShaderNodeBsdfPrincipled")
p.inputs["Base Color"].default_value = (0.55, 0.85, 0.85, 1); p.inputs["Roughness"].default_value = 0.01
p.inputs["Transmission Weight"].default_value = 1.0; p.inputs["IOR"].default_value = 1.333
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 4
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.04
nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
nt.links.new(p.outputs[0], o.inputs[0])

# sea
M_sea = bpy.data.materials.get("V_sea") or bpy.data.materials.new("V_sea")
M_sea.use_nodes = True; nt = M_sea.node_tree; nt.nodes.clear()
o = nt.nodes.new("ShaderNodeOutputMaterial"); p = nt.nodes.new("ShaderNodeBsdfPrincipled")
p.inputs["Base Color"].default_value = (0.010, 0.035, 0.045, 1); p.inputs["Roughness"].default_value = 0.06
p.inputs["IOR"].default_value = 1.333; p.inputs["Specular IOR Level"].default_value = 0.6
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.08, 0.16, 0.08)
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
w1 = nt.nodes.new("ShaderNodeTexNoise"); w1.inputs["Scale"].default_value = 3.0; w1.inputs["Detail"].default_value = 8; w1.inputs["Roughness"].default_value = 0.6
nt.links.new(mp.outputs[0], w1.inputs["Vector"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.3
nt.links.new(w1.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], p.inputs["Normal"])
nt.links.new(p.outputs[0], o.inputs[0])

# ---------- terrain ----------
rng = np.random.default_rng(7)
def shore_y(x):
    x = np.asarray(x, float)
    return -34 + 5*np.sin(x/23.0) + np.maximum(0, -x-22)*1.25 + np.maximum(0, x-60)*0.5

def fbm(x, y, oct=5, base=0.012):
    v = np.zeros_like(x, float); a = 1.0; f = base
    for i in range(oct):
        v += a*np.sin(x*f*6.283 + i*1.7 + np.cos(y*f*4.1 + i)) * np.cos(y*f*6.283*0.83 + i*2.3 + np.sin(x*f*3.3))
        a *= 0.5; f *= 2.03
    return v

SEA = -14.0
def height(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    d = y - shore_y(x)                                  # >0 land
    cliff = SEA - 1.5 + (13.5 + 1.2)*np.clip((d + 1.5)/9.0, 0, 1)**0.7   # rises from sea to plateau (~-0.3)
    behind = np.maximum(0, y - 14)
    hills = 0.16*behind + 0.0009*behind**2 + 9*np.clip(behind/80, 0, 1)*(fbm(x, y)*0.6 + 0.4)
    side = np.clip((np.abs(x) - 22)/40, 0, 1) * 6 * (fbm(x*1.3, y*1.3) * 0.5 + 0.5)
    z = np.where(d < 0, SEA - 2.0 + d*0.08, cliff) + hills + side*np.clip(d/10, 0, 1)
    # villa pad
    pad = np.clip(1 - (np.maximum(np.abs(x) - 18, 0)/6.0), 0, 1) * np.clip(1 - np.maximum(np.abs(y + 2) - 13, 0)/6.0, 0, 1)
    z = z*(1-pad) + (-0.35)*pad
    z += 0.6*fbm(x*4, y*4, 3, 0.05)*np.clip(d/6, 0, 1)*(1-pad)
    return z

def grid(name, x0, x1, y0, y1, nx, ny, c, m):
    xs = np.linspace(x0, x1, nx); ys = np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(xs, ys); Z = height(X, Y)
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    idx = np.arange(nx*ny).reshape(ny, nx)
    f = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel().astype(np.float32))
    me.loops.add(f.size); me.loops.foreach_set("vertex_index", f.ravel().astype(np.int32))
    me.polygons.add(len(f)); me.polygons.foreach_set("loop_start", (np.arange(len(f))*4).astype(np.int32))
    me.update(); me.validate()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); c.objects.link(ob); ob.data.materials.append(m)
    return ob

# terrain material: grass on flats, black volcanic rock on slopes / near sea, sand strip
M_ter = bpy.data.materials.get("V_terrain") or bpy.data.materials.new("V_terrain")
M_ter.use_nodes = True; nt = M_ter.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
gA = nt.nodes.new("ShaderNodeGroup");
def as_group(m, name):
    g = bpy.data.node_groups.get(name)
    if g: bpy.data.node_groups.remove(g)
    g = bpy.data.node_groups.new(name, "ShaderNodeTree")
    g.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
    # copy nodes by re-creating: simpler -> use the material shader via Mix of separate materials impossible; rebuild minimal
    return g
nt.nodes.remove(gA)
def img_branch(src_mat, size_m, loc_y):
    """rebuild color/rough/normal of a PH material inside the terrain tree (world box projection)."""
    sn = src_mat.node_tree.nodes
    imgs = {n.image.name.split("_")[-1]: n.image for n in sn if n.type == 'TEX_IMAGE'}
    geo = nt.nodes.new("ShaderNodeNewGeometry"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1/size_m,)*3
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    res = {}
    for key in ("Diffuse", "Rough", "gl"):
        im = [v for k, v in imgs.items() if k.endswith(key)]
        if not im: continue
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = im[0]; t.projection = 'BOX'; t.projection_blend = 0.3
        nt.links.new(mp.outputs[0], t.inputs["Vector"]); res[key] = t
    return res
G = img_branch(bpy.data.materials["aerial_grass_rock"], 9.0, 0)
R = img_branch(bpy.data.materials["dark_rock_02"], 5.0, 0)
SD = img_branch(bpy.data.materials["coast_sand_01"], 3.0, 0)
geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(geo.outputs["Normal"], sep.inputs[0])
slope = nt.nodes.new("ShaderNodeMapRange"); slope.inputs["From Min"].default_value = 0.78; slope.inputs["From Max"].default_value = 0.9
nt.links.new(sep.outputs["Z"], slope.inputs["Value"])            # 1 = flat (grass), 0 = steep (rock)
sepP = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sepP.inputs[0])
low = nt.nodes.new("ShaderNodeMapRange"); low.inputs["From Min"].default_value = SEA + 3.0; low.inputs["From Max"].default_value = SEA + 6.0
nt.links.new(sepP.outputs["Z"], low.inputs["Value"])              # 0 near sea
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.08; nz.inputs["Detail"].default_value = 6
mixN = nt.nodes.new("ShaderNodeMath"); mixN.operation = 'MULTIPLY'; nt.links.new(slope.outputs[0], mixN.inputs[0]); nt.links.new(low.outputs[0], mixN.inputs[1])
fac = nt.nodes.new("ShaderNodeMapRange"); fac.inputs["From Min"].default_value = 0.35; fac.inputs["From Max"].default_value = 0.65
add = nt.nodes.new("ShaderNodeMath"); add.operation = 'ADD'; nt.links.new(mixN.outputs[0], add.inputs[0])
nzs = nt.nodes.new("ShaderNodeMath"); nzs.operation = 'MULTIPLY_ADD'; nt.links.new(nz.outputs["Fac"], nzs.inputs[0]); nzs.inputs[1].default_value = 0.5; nzs.inputs[2].default_value = -0.25
nt.links.new(nzs.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], fac.inputs["Value"])
def mixc(a, b, f, dtype='RGBA'):
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = dtype
    nt.links.new(f, mx.inputs["Factor"])
    ia, ib = (mx.inputs[6], mx.inputs[7]) if dtype == 'RGBA' else (mx.inputs[2], mx.inputs[3]) if dtype == 'FLOAT' else (mx.inputs[4], mx.inputs[5])
    nt.links.new(a, ia); nt.links.new(b, ib)
    return mx.outputs[2] if dtype == 'RGBA' else mx.outputs[0] if dtype == 'FLOAT' else mx.outputs[1]
# grass tint toward golden/olive
hue = nt.nodes.new("ShaderNodeHueSaturation"); hue.inputs["Saturation"].default_value = 0.85; hue.inputs["Value"].default_value = 0.85
nt.links.new(G["Diffuse"].outputs["Color"], hue.inputs["Color"])
rockc = nt.nodes.new("ShaderNodeHueSaturation"); rockc.inputs["Value"].default_value = 0.55; rockc.inputs["Saturation"].default_value = 0.6
nt.links.new(R["Diffuse"].outputs["Color"], rockc.inputs["Color"])
col = mixc(rockc.outputs[0], hue.outputs[0], fac.outputs[0])
rgh = mixc(R["Rough"].outputs["Color"], G["Rough"].outputs["Color"], fac.outputs[0])
pb = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(col, pb.inputs["Base Color"]); nt.links.new(rgh, pb.inputs["Roughness"])
nmA = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(R["gl"].outputs["Color"], nmA.inputs["Color"]); nmA.inputs["Strength"].default_value = 1.0
nt.links.new(nmA.outputs[0], pb.inputs["Normal"])
nt.links.new(pb.outputs[0], out.inputs[0])
for i in ("Diffuse", "Rough", "gl"):
    for d in (G, R, SD):
        if i in d and i != "Diffuse": d[i].image.colorspace_settings.name = 'Non-Color'

T_near = grid("V_terrain_near", -70, 70, -60, 50, 281, 221, CT, M_ter)
T_far = grid("V_terrain_far", -400, 400, -60, 600, 161, 133, CT, M_ter)
# avoid overlap: drop far terrain slightly where near exists
fv = np.zeros(len(T_far.data.vertices)*3, np.float32); T_far.data.vertices.foreach_get("co", fv); fv = fv.reshape(-1, 3)
inside = (np.abs(fv[:, 0]) < 69) & (fv[:, 1] > -59) & (fv[:, 1] < 49)
fv[inside, 2] -= 0.6; T_far.data.vertices.foreach_set("co", fv.ravel()); T_far.data.update()

sea = mesh_obj("V_sea", [(-3000, -3000, SEA), (3000, -3000, SEA), (3000, 3000, SEA), (-3000, 3000, SEA)], [(0, 1, 2, 3)], CT, M_sea)

# ---------- villa ----------
GF, FF, RF = 0.0, 3.5, 7.0          # ground floor, first floor, roof levels
box("V_slab_ground", -9, 9, -4.5, 5, -0.45, 0.0, M_conc)
box("V_floor_in", -8.8, 8.8, -4.4, 4.8, 0.0, 0.02, M_floor, CI)
box("V_wall_back", -9, 9, 4.6, 5.0, 0, FF, M_conc)
box("V_wall_left", -9, -8.6, -4.5, 5, 0, FF, M_conc)
box("V_wall_right_core", 5.0, 9, -1.0, 5, 0, FF, M_conc)              # closed core on the right
box("V_wall_in_back", -8.6, 5.0, 4.45, 4.6, 0, FF, M_inner, CI)
# glass front + mullions
box("V_glass_front", -8.6, 5.0, -4.42, -4.38, 0.02, FF - 0.05, M_glass)
for i, x in enumerate(np.linspace(-8.6, 5.0, 6)):
    box(f"V_mullion_{i}", x - 0.04, x + 0.04, -4.48, -4.32, 0.0, FF, M_frame)
box("V_glass_side", 5.0, 9.0, -4.42, -4.38, 0.02, FF - 0.05, M_glass)
box("V_glass_core_front", 5.0, 9.0, -1.05, -0.95, 0.0, FF, M_conc)
# first floor cantilever box
box("V_ff_slab", -11, 8, -8.0, 5, FF, FF + 0.35, M_conc)
box("V_ff_back", -11, 8, 4.6, 5.0, FF + 0.35, RF, M_conc)
box("V_ff_left", -11, -10.6, -8.0, 5, FF + 0.35, RF, M_conc)
box("V_ff_right", 7.6, 8, -8.0, 5, FF + 0.35, RF, M_conc)
box("V_ff_front_low", -10.6, 7.6, -8.0, -7.7, FF + 0.35, FF + 1.0, M_conc)
box("V_ff_front_glass", -10.6, 7.6, -7.88, -7.84, FF + 1.0, RF - 0.5, M_glass)
box("V_ff_front_top", -10.6, 7.6, -8.0, -7.7, RF - 0.5, RF, M_conc)
box("V_ff_inner", -10.6, 7.6, 4.4, 4.6, FF + 0.35, RF, M_inner, CI)
box("V_roof", -11.4, 8.4, -8.4, 5.4, RF, RF + 0.4, M_conc)
# vertical cedar louvers in front of upper glass (left 60%)
for i, x in enumerate(np.arange(-10.4, 1.0, 0.32)):
    box(f"V_louver_{i}", x, x + 0.07, -8.35, -8.15, FF + 1.0, RF - 0.5, M_wood)
# right block: cedar clad box to break the mass
box("V_cedar_block", 9.0, 13.5, -2.0, 5.0, 0, 4.2, M_wood)
box("V_cedar_roof", 8.8, 13.8, -2.3, 5.3, 4.2, 4.45, M_conc)
# terrace deck + pool
box("V_deck", -9.5, 11, -16.0, -4.5, -0.25, 0.0, M_deck)
box("V_pool_rim_back", -6.5, 2.5, -10.7, -10.4, -0.25, 0.02, M_conc)
box("V_pool_shell", -6.5, 2.5, -14.6, -10.4, -1.6, -1.35, M_tile)
box("V_pool_wall_l", -6.5, -6.2, -14.6, -10.4, -1.6, 0.02, M_conc)
box("V_pool_wall_r", 2.2, 2.5, -14.6, -10.4, -1.6, 0.02, M_conc)
box("V_pool_edge", -6.5, 2.5, -14.6, -14.45, -1.6, -0.04, M_conc)        # infinity edge
box("V_pool_inner_l", -6.2, -6.15, -14.45, -10.7, -1.35, -0.02, M_tile)
box("V_pool_inner_r", 2.15, 2.2, -14.45, -10.7, -1.35, -0.02, M_tile)
box("V_pool_inner_b", -6.2, 2.2, -10.75, -10.7, -1.35, -0.02, M_tile)
box("V_pool_inner_f", -6.2, 2.2, -14.45, -14.4, -1.35, -0.06, M_tile)
water = box("V_pool_water", -6.2, 2.2, -14.45, -10.7, -1.35, -0.03, M_water)
box("V_catch_basin", -6.5, 2.5, -15.6, -14.6, -1.6, -1.2, M_conc)
box("V_retaining", -9.5, 11, -16.3, -16.0, -3.5, 0.0, M_conc)
# deck cut for pool (deck covers pool area -> make deck two parts instead)
bpy.data.objects.remove(bpy.data.objects["V_deck"], do_unlink=True)
box("V_deck_a", -9.5, 11, -10.4, -4.5, -0.25, 0.0, M_deck)
box("V_deck_b", -9.5, -6.5, -16.0, -10.4, -0.25, 0.0, M_deck)
box("V_deck_c", 2.5, 11, -16.0, -10.4, -0.25, 0.0, M_deck)
# garden wall extending into landscape
box("V_garden_wall", -22, -9.5, -0.5, -0.1, -0.5, 1.6, M_conc)

# ---------- lights ----------
w = S.world = bpy.data.worlds["PolyHaven qwantani_sunset_puresky"]
env = [n for n in w.node_tree.nodes if n.type == 'TEX_ENVIRONMENT'][0]
mpw = [n for n in w.node_tree.nodes if n.type == 'MAPPING'][0]
bgw = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND'][0]
bgw.inputs["Strength"].default_value = 0.8
# find sun azimuth in the HDRI: brightest pixel
im = env.image; px = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4)
lum = px[..., :3].sum(-1); iy, ix = np.unravel_index(np.argmax(lum), lum.shape)
u = ix/im.size[0]; v = iy/im.size[1]
hdr_az = (u - 0.5)*2*math.pi           # equirect: u=0.5 -> -Y? (blender: u=0.5 is +X... handled by rotation below)
hdr_el = (v - 0.5)*math.pi
print("HDRI sun px", ix, iy, "el(deg)", round(math.degrees(hdr_el), 2))
# we want the sun behind the villa (+Y) slightly to the left: azimuth target
TARGET_AZ = math.radians(100)          # direction angle in XY plane measured from +X (100deg = +Y, a bit to -X)
# Blender equirect: direction angle = atan2(dir.y, dir.x); u = (atan2(dir.y,-dir.x) ... ) -> solve rotation empirically:
# u = -atan2(d.y, d.x)/(2pi) + 0.5  -> az_hdri = (0.5 - u)*2pi
az_h = (0.5 - u)*2*math.pi
mpw.inputs["Rotation"].default_value[2] = TARGET_AZ - az_h
SUN_EL = math.radians(7.0)
sun = tlib.sun("V_sun", (0, 0, 0), energy=4.5, color=(1.0, 0.62, 0.36), angle=1.2)
sd = Vector((math.cos(TARGET_AZ)*math.cos(SUN_EL), math.sin(TARGET_AZ)*math.cos(SUN_EL), math.sin(SUN_EL)))
sun.rotation_euler = (-sd).to_track_quat('-Z', 'Y').to_euler()
for c in sun.users_collection: c.objects.unlink(sun)
CL.objects.link(sun)

def K(t):   # kelvin -> rgb approx
    t /= 100
    r = 1.0 if t <= 66 else max(0, min(1, 329.698727446*((t-60)**-0.1332047592)/255))
    g = (99.4708025861*math.log(t) - 161.1195681661)/255 if t <= 66 else 288.1221695283*((t-60)**-0.0755148492)/255
    b = 1.0 if t >= 66 else (0 if t <= 19 else (138.5177312231*math.log(t-10) - 305.0447927307)/255)
    return (max(0, min(1, r)), max(0, min(1, g)), max(0, min(1, b)))
warm = K(2700)
for i, x in enumerate((-6.0, -2.0, 2.2)):
    l = tlib.area(f"V_in_area_{i}", (x, 0.5, FF - 0.15), (x, 0.5, 0), energy=260, size=2.2, color=warm)
    for c in l.users_collection: c.objects.unlink(l)
    CL.objects.link(l)
for i, x in enumerate((-8.0, -3.0, 2.0, 6.0)):
    l = tlib.area(f"V_ff_area_{i}", (x, -1.5, RF - 0.15), (x, -1.5, FF), energy=180, size=2.5, color=warm)
    for c in l.users_collection: c.objects.unlink(l)
    CL.objects.link(l)
# pool underwater light
pl = bpy.data.lights.new("V_pool_light", 'AREA'); pl.energy = 120; pl.color = (0.75, 0.95, 1.0); pl.size = 6; pl.size_y = 2.5
po = bpy.data.objects.new("V_pool_light", pl); CL.objects.link(po); po.location = (-2, -12.5, -1.3)
# deck uplights (small warm points) along the cedar block and garden wall
for i, (x, y) in enumerate([(-20, -0.8), (-16, -0.8), (-12, -0.8), (9.6, -2.6), (11.5, -2.6), (13.2, -2.6)]):
    l = bpy.data.lights.new(f"V_up_{i}", 'SPOT'); l.energy = 60; l.color = warm; l.spot_size = math.radians(50); l.shadow_soft_size = 0.05
    ob = bpy.data.objects.new(f"V_up_{i}", l); CL.objects.link(ob); ob.location = (x, y, -0.3); ob.rotation_euler = (0, 0, 0)

# ---------- camera ----------
for o in list(bpy.data.objects):
    if o.name.startswith("Cam"):
        bpy.data.objects.remove(o, do_unlink=True)
cam, tgt = tlib.camera((-52, 2, 26), (0, -2, 2), lens=24)
cam.data.sensor_width = 36; cam.data.clip_end = 3000
KEYS = [(1, (-52, 2, 26), (0, -2, 2.0), 24), (80, (-42, -27, 17), (0, -3, 1.8), 24),
        (160, (-20, -33, 8), (0, -4, 1.6), 28), (225, (-4.5, -19, 2.6), (0, -2, 1.4), 32), (288, (0.0, -5.7, 1.45), (0, 4, 1.35), 35)]
for f, l, t, lens in KEYS:
    cam.location = l; cam.keyframe_insert("location", frame=f)
    tgt.location = t; tgt.keyframe_insert("location", frame=f)
    cam.data.lens = lens; cam.data.keyframe_insert("lens", frame=f)
S.frame_start, S.frame_end = 1, 288
S.render.fps = 24

# ---------- render ----------
S.render.engine = 'CYCLES'
S.cycles.device = 'GPU'
S.cycles.samples = 64; S.cycles.use_adaptive_sampling = True; S.cycles.adaptive_threshold = 0.03
S.cycles.use_denoising = True
S.cycles.max_bounces = 6; S.cycles.diffuse_bounces = 3; S.cycles.glossy_bounces = 3; S.cycles.transmission_bounces = 6; S.cycles.transparent_max_bounces = 12
S.cycles.caustics_reflective = False; S.cycles.caustics_refractive = False
S.render.resolution_x, S.render.resolution_y = 1920, 1080
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'
S.render.use_persistent_data = True
S.frame_set(1)
print("built", len(bpy.data.objects))
