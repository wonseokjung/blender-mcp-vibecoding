# villa_veg: scatter Poly Haven vegetation with instancing (point clouds + GN Instance on Points) + interior props
import bpy, math, sys
import numpy as np
sys.path.insert(0, 'scripts')
exec(compile(open('scripts/villa_terrain_fn.py').read(), 'tf', 'exec'))
S = bpy.context.scene
CV = bpy.data.collections.get("V_veg")
for o in list(CV.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def gn_instancer(name):
    ng = bpy.data.node_groups.get(name)
    if ng: bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    s = ng.interface.new_socket("Collection", in_out='INPUT', socket_type='NodeSocketCollection')
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    ci = N.new("GeometryNodeCollectionInfo"); ci.transform_space = 'ORIGINAL'
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    L.new(gi.outputs["Collection"], ci.inputs["Collection"])
    iop = N.new("GeometryNodeInstanceOnPoints"); iop.inputs["Pick Instance"].default_value = True
    a_idx = N.new("GeometryNodeInputNamedAttribute"); a_idx.data_type = 'INT'; a_idx.inputs["Name"].default_value = "idx"
    a_rot = N.new("GeometryNodeInputNamedAttribute"); a_rot.data_type = 'FLOAT'; a_rot.inputs["Name"].default_value = "rot"
    a_scl = N.new("GeometryNodeInputNamedAttribute"); a_scl.data_type = 'FLOAT'; a_scl.inputs["Name"].default_value = "scl"
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(a_rot.outputs["Attribute"], cmb.inputs["Z"])
    m2p = N.new("GeometryNodeMeshToPoints")
    L.new(gi.outputs["Geometry"], m2p.inputs["Mesh"])
    L.new(m2p.outputs["Points"], iop.inputs["Points"])
    L.new(ci.outputs["Instances"], iop.inputs["Instance"])
    L.new(a_idx.outputs["Attribute"], iop.inputs["Instance Index"])
    L.new(cmb.outputs[0], iop.inputs["Rotation"])
    L.new(a_scl.outputs["Attribute"], iop.inputs["Scale"])
    L.new(iop.outputs["Instances"], go.inputs["Geometry"])
    return ng

def scatter(name, coll_name, pts, idx, rot, scl):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(pts)); me.vertices.foreach_set("co", pts.astype(np.float32).ravel())
    for an, ty, arr in (("idx", 'INT', idx), ("rot", 'FLOAT', rot), ("scl", 'FLOAT', scl)):
        at = me.attributes.new(an, ty, 'POINT'); at.data.foreach_set("value", arr.astype(np.int32 if ty == 'INT' else np.float32))
    o = bpy.data.objects.new(name, me); CV.objects.link(o)
    md = o.modifiers.new("inst", 'NODES'); md.node_group = gn_instancer("GN_inst_" + name)
    ci = [n for n in md.node_group.nodes if n.type == 'COLLECTION_INFO'][0]
    gi = [n for n in md.node_group.nodes if n.type == 'GROUP_INPUT'][0]
    for l in list(md.node_group.links):
        if l.to_node == ci and l.to_socket.name == "Collection": md.node_group.links.remove(l)
    ci.inputs["Collection"].default_value = bpy.data.collections[coll_name]
    return o

rng = np.random.default_rng(11)
def jitter(x0, x1, y0, y1, spacing):
    xs = np.arange(x0, x1, spacing); ys = np.arange(y0, y1, spacing)
    X, Y = np.meshgrid(xs, ys); X = X.ravel() + rng.uniform(-0.5, 0.5, X.size)*spacing; Y = Y.ravel() + rng.uniform(-0.5, 0.5, Y.size)*spacing
    return X, Y

def slope_at(x, y, e=0.7):
    gx = (height(x + e, y) - height(x - e, y))/(2*e); gy = (height(x, y + e) - height(x, y - e))/(2*e)
    return np.sqrt(gx*gx + gy*gy)

def plaque(x, y):
    return (x > 2.0) & (x < 13.0) & (y > -23.0) & (y < -16.0)

def in_villa(x, y, m=0.0):
    return (x > -12 - m) & (x < 15 + m) & (y > -17.5 - m) & (y < 6.5 + m) | ((x > -23 - m) & (x < -9) & (y > -1.5 - m) & (y < 1 + m))

def landmask(x, y):
    return (y - shore_y(x) > 4.0)

def westview(x, y):
    return (x < 9) & (x > -80) & (y < 3) & (y > -70)

def sightline(x, y):
    # keep the sea-facing view corridor in front of the villa clear of tall trees
    return ((np.abs(x + 4) < 30) & (y < -15) & (y > -60)) | westview(x, y)

# 1 pines on the hills behind + far sides (backdrop, never empty)
X, Y = jitter(-420, 420, -40, 620, 9.0)
keep = landmask(X, Y) & (slope_at(X, Y) < 0.9) & ~in_villa(X, Y, 25) & ~sightline(X, Y) & ((Y > 18) | (np.abs(X) > 45))
X, Y = X[keep], Y[keep]
P = np.stack([X, Y, height(X, Y) - 0.3], 1)
scatter("V_pines", "pine_tree_01_LOD0", P, rng.integers(0, 3, len(P)), rng.uniform(0, 6.283, len(P)), rng.uniform(0.55, 1.0, len(P)))
print("pines", len(P))

# 2 island (windswept coastal) trees, mid distance, also on the headland
X, Y = jitter(-150, 150, -45, 140, 5.0)
d = np.hypot(X, Y + 4)
keep = landmask(X, Y) & (slope_at(X, Y) < 0.75) & ~in_villa(X, Y, 3) & ~sightline(X, Y) & (d > 16) & (rng.random(X.size) < np.clip(1.2 - d/150, 0.15, 1))
X, Y = X[keep], Y[keep]
P = np.stack([X, Y, height(X, Y) - 0.15], 1)
scatter("V_island_trees", "island_tree_01_LOD0", P, np.zeros(len(P), int), rng.uniform(0, 6.283, len(P)), rng.uniform(1.1, 2.0, len(P))*np.clip(np.hypot(P[:,0],P[:,1]+4)/45, 0.55, 1))
# second/third variants via separate collections (01/02/03 are separate collections)
X2, Y2 = jitter(-150, 150, -45, 140, 6.5)
d2 = np.hypot(X2, Y2 + 4)
k2 = landmask(X2, Y2) & (slope_at(X2, Y2) < 0.75) & ~in_villa(X2, Y2, 3) & ~sightline(X2, Y2) & (d2 > 14) & (rng.random(X2.size) < np.clip(1.2 - d2/150, 0.15, 1))
X2, Y2 = X2[k2], Y2[k2]
P2 = np.stack([X2, Y2, height(X2, Y2) - 0.15], 1)
half = len(P2)//2
scatter("V_island_trees2", "island_tree_02_LOD0", P2[:half], np.zeros(half, int), rng.uniform(0, 6.283, half), rng.uniform(1.2, 2.2, half))
scatter("V_island_trees3", "island_tree_03_LOD0", P2[half:], np.zeros(len(P2) - half, int), rng.uniform(0, 6.283, len(P2) - half), rng.uniform(1.4, 2.6, len(P2) - half))
print("island", len(P), len(P2))

# 3 shrubs (searsia) – landscaping + cliff tops
X, Y = jitter(-90, 90, -45, 80, 2.6)
d = np.hypot(X, Y + 4)
keep = landmask(X, Y) & (slope_at(X, Y) < 1.1) & ~in_villa(X, Y, 0.3) & ~plaque(X, Y) & (rng.random(X.size) < np.clip(1.1 - d/90, 0.1, 1))
X, Y = X[keep], Y[keep]
P = np.stack([X, Y, height(X, Y) - 0.1], 1)
wv = westview(P[:,0], P[:,1])
scatter("V_shrubs", "searsia_lucida_LOD0", P, np.where(wv, rng.integers(4, 7, len(P)), rng.integers(0, 7, len(P))), rng.uniform(0, 6.283, len(P)), np.where(wv, rng.uniform(0.5, 0.8, len(P)), rng.uniform(0.7, 1.5, len(P))))
print("shrubs", len(P))

# 4 tall grass tufts (억새 feel) near the villa
X, Y = jitter(-60, 60, -42, 45, 0.62)
d = np.hypot(X, Y + 4)
keep = landmask(X, Y) & ~in_villa(X, Y, -0.2) & (d < 60) & (slope_at(X, Y) < 1.3) & (rng.random(X.size) < np.clip(1.15 - d/60, 0, 1))
X, Y = X[keep], Y[keep]
P = np.stack([X, Y, height(X, Y) - 0.03], 1)
gi = rng.choice([0, 1, 2, 3, 4, 5, 8, 9, 10], len(P))
scatter("V_grass", "grass_medium_01_LOD0", P, gi, rng.uniform(0, 6.283, len(P)), rng.uniform(2.6, 4.2, len(P)))
print("grass", len(P))
X, Y = jitter(-30, 30, -30, 22, 0.38)
d = np.hypot(X, Y + 4)
keep = landmask(X, Y) & ~in_villa(X, Y, -0.2) & (d < 26) & (slope_at(X, Y) < 1.3) & (rng.random(X.size) < np.clip(1.25 - d/26, 0, 1))
X, Y = X[keep], Y[keep]
P = np.stack([X, Y, height(X, Y) - 0.03], 1)
pq = plaque(P[:,0], P[:,1])
scatter("V_grass_near", "grass_medium_01_LOD0", P, np.where(pq, rng.choice([0, 1, 2, 3, 4, 5], len(P)), rng.choice([0, 1, 2, 3, 4, 5, 8, 9, 10], len(P))), rng.uniform(0, 6.283, len(P)), np.where(pq, rng.uniform(1.3, 2.0, len(P)), rng.uniform(2.2, 3.6, len(P))))
print("grass near", len(P))

# 5 coastal rocks along the shoreline
xs = np.arange(-120, 140, 7.0) + rng.uniform(-2, 2, 38)
ys = shore_y(xs) + rng.uniform(-3, 1.5, xs.size)
P = np.stack([xs, ys, np.full(xs.size, -14.6)], 1)
scatter("V_coast_rocks", "coast_land_rocks_04_LOD0" if "coast_land_rocks_04_LOD0" in bpy.data.collections else "coast_land_rocks_04", P, np.zeros(len(P), int), rng.uniform(0, 6.283, len(P)), rng.uniform(0.8, 1.4, len(P)))
print("done veg")
