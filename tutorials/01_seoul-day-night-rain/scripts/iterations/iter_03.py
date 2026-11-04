# seoul_02: signage (CONNECT AI LAB fascia), poles + tangled wires, traffic & street lights, trees, sky/sun timelapse, rain, camera
import bpy, bmesh, math, sys, random
import numpy as np
from mathutils import Vector
sys.path.insert(0, 'scripts')
import tlib
exec(compile(open('scripts/seoul_01.py').read().split("# ---------------- ground: roads")[0].split("# ---------------- state channels ----------------")[0], 's1', 'exec')) if False else None
W = '../_workB'
S = bpy.context.scene; NF = S.frame_end
ctrl = bpy.data.objects["CTRL"]
CS, CP, CL, CR = (bpy.data.collections[n] for n in ("K_signs", "K_props", "K_lights", "K_rain"))
for c in (CS, CL, CR):
    for o in list(c.objects): bpy.data.objects.remove(o, do_unlink=True)
for o in list(CP.objects):
    if o.name != "CTRL": bpy.data.objects.remove(o, do_unlink=True)
for o in list(bpy.data.objects):
    if o.name in ("Cam", "CamTarget"): bpy.data.objects.remove(o, do_unlink=True)
rnd = random.Random(5)
def drive(owner, path, expr, props, index=-1):
    fc = owner.driver_add(path, index) if index >= 0 else owner.driver_add(path)
    d = fc.driver; d.type = 'SCRIPTED'
    for p in props:
        v = d.variables.new(); v.name = p; v.type = 'SINGLE_PROP'; v.targets[0].id = ctrl; v.targets[0].data_path = f'["{p}"]'
    d.expression = expr
def val(nt, name, expr, props):
    n = nt.nodes.new("ShaderNodeValue"); n.name = name; drive(n.outputs[0], "default_value", expr, props); return n.outputs[0]
def mesh(name, verts, faces, c, m=None, uvs=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if uvs:
        ul = me.uv_layers.new(name="UVMap")
        for li, l in enumerate(me.loops): ul.data[li].uv = uvs[l.vertex_index]
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    if m: o.data.materials.append(m)
    return o
def box(name, x0, x1, y0, y1, z0, z1, m, c):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    return mesh(name, v, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], c, m)
def sign_mat(name, img, day=0.3, nightk=4.5, at=0.5):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); pb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(f"{W}/assets/signs/{img}.png", check_existing=True)
    uvn = nt.nodes.new("ShaderNodeUVMap"); nt.links.new(uvn.outputs[0], t.inputs[0])
    nt.links.new(t.outputs[0], pb.inputs["Base Color"]); nt.links.new(t.outputs[0], pb.inputs["Emission Color"])
    pb.inputs["Roughness"].default_value = 0.3; pb.inputs["Coat Weight"].default_value = 0.4
    g = val(nt, "glow", f"{day} + {nightk}*min(1.0, max(0.0, (night-{at})*7.0))", ["night"])
    nt.links.new(g, pb.inputs["Emission Strength"]); nt.links.new(pb.outputs[0], o.inputs[0]); return m
def panel(name, center, n, w, h, mat, depth=0.18, frame_mat=None):
    """sign box: dark casing + textured face readable from the normal side"""
    c = Vector(center); n = Vector(n).normalized(); up = Vector((0, 0, 1)); right = (-n).cross(up).normalized()
    f = c + n*(depth/2 + 0.004)
    q = [f - right*w/2 - up*h/2, f + right*w/2 - up*h/2, f + right*w/2 + up*h/2, f - right*w/2 + up*h/2]
    mesh(name, [tuple(p) for p in q], [(0, 1, 2, 3)], CS, mat, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # casing
    b = [c + s1*right*(w/2 + 0.05) + s2*up*(h/2 + 0.05) + s3*n*depth/2 for s3 in (-1, 1) for s2 in (-1, 1) for s1 in (-1, 1)]
    o = mesh(name + "_case", [tuple(p) for p in b], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)], CS, frame_mat or bpy.data.materials["K_dark"])
GF = 0.15
# ---- hero fascia: CONNECT AI LAB on both street faces of the corner shop
mcal = sign_mat("K_s_cal", "cal_fascia", day=0.35, nightk=5.5, at=0.25)
panel("K_cal_S", (14.3, 9.6 - 0.12, GF + 3.75), (0, -1, 0), 8.6, 1.2, mcal)
panel("K_cal_W", (8.6 - 0.12, 15.0, GF + 3.75), (-1, 0, 0), 8.6, 1.2, mcal)
# vertical signs (perpendicular to facades, readable from the camera side)
def vsign(name, img, base, n, w, h, at):
    m = sign_mat("K_s_" + img, img, at=at)
    panel(name, base, n, w, h, m, depth=0.22)
vsign("K_v_cafe", "v_cafe", (9.1, 9.6 - 0.55, GF + 9.6), (-1, 0, 0), 0.9, 4.6, 0.35)
vsign("K_v_piano", "v_piano", (8.6 - 0.55, 20.3, GF + 9.4), (0, -1, 0), 0.85, 4.3, 0.55)
vsign("K_v_dental", "v_dental", (22.5, 9.6 - 0.55, GF + 10.5), (-1, 0, 0), 0.85, 3.7, 0.45)
vsign("K_v_karaoke", "v_karaoke", (34.5, 9.6 - 0.55, GF + 8.0), (-1, 0, 0), 0.9, 4.6, 0.65)
vsign("K_v_pc", "v_pc", (-9.1, 9.6 - 0.55, GF + 7.4), (1, 0, 0), 0.85, 3.0, 0.3)
def hsign(name, img, center, n, w, h, at):
    panel(name, center, n, w, h, sign_mat("K_s_" + img, img, at=at))
hsign("K_h_bunsik", "h_bunsik", (8.6 - 0.12, 27.2, GF + 3.7), (-1, 0, 0), 7.0, 1.3, 0.4)
hsign("K_h_laundry", "h_laundry", (25.0, 9.6 - 0.12, GF + 3.7), (0, -1, 0), 5.0, 1.1, 0.6)
hsign("K_h_pharm", "h_pharm", (30.6, 9.6 - 0.12, GF + 3.7), (0, -1, 0), 4.6, 1.1, 0.5)
hsign("K_h_chicken", "h_chicken", (40.0, 9.6 - 0.12, GF + 3.7), (0, -1, 0), 6.0, 1.25, 0.7)
hsign("K_h_mart", "h_mart", (-14.8, 9.6 - 0.12, GF + 3.7), (0, -1, 0), 8.0, 1.3, 0.3)
hsign("K_h_realty", "h_realty", (-27.7, 9.6 - 0.12, GF + 3.7), (0, -1, 0), 6.0, 1.2, 0.5)
hsign("K_h_flower", "h_flower", (8.6 - 0.12, -15.3, GF + 3.6), (-1, 0, 0), 6.0, 1.2, 0.45)
hsign("K_w_academy", "w_academy", (8.6 - 0.05, 15.0, GF + 5.6), (-1, 0, 0), 5.0, 0.9, 0.5)

# ---- utility poles + tangled wires
M_pole = bpy.data.materials["K_pole"]; M_wire = bpy.data.materials["K_wire"]; M_dark = bpy.data.materials["K_dark"]
def cyl(name, p, r, h, m, c=CP, seg=16):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r*0.85, depth=h); bm.to_mesh(me); bm.free()
    for pz in me.polygons: pz.use_smooth = True
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.location = (p[0], p[1], p[2] + h/2); o.data.materials.append(m); return o
POLES = [(5.75, 7.0), (5.75, 23.0), (5.75, 39.0), (20.0, 6.75), (36.0, 6.75), (-5.75, 7.0), (-20.0, 6.75), (-5.75, -24.0), (5.75, -7.0), (5.75, -23.0)]
tops = []
for i, (x, y) in enumerate(POLES):
    cyl(f"K_pole_{i}", (x, y, GF), 0.17, 10.8, M_pole)
    for k, z in enumerate((9.6, 10.4)):
        box(f"K_arm_{i}_{k}", x - 0.9, x + 0.9, y - 0.05, y + 0.05, GF + z, GF + z + 0.1, M_pole, CP) if abs(y) < abs(x) or True else None
    if i % 3 == 0: cyl(f"K_trans_{i}", (x + 0.35, y + 0.3, GF + 7.6), 0.26, 1.0, M_dark)
    tops.append(Vector((x, y, GF + 10.4)))
def catenary(name, a, b, sag, n=24):
    pts = []
    for k in range(n + 1):
        t = k/n; p = a.lerp(b, t); p.z -= sag*4*t*(1 - t); pts.append(p)
    return pts
cu = bpy.data.curves.new("K_wires", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.011; cu.bevel_resolution = 2
pairs = [(0, 1), (1, 2), (0, 3), (3, 4), (0, 5), (5, 6), (8, 9), (8, 0)]
for (a, b) in pairs:
    for w in range(rnd.randint(3, 6)):
        off = Vector((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.1, 0.1), rnd.uniform(-0.9, 0.1)))
        pts = catenary("w", tops[a] + off, tops[b] + off*0.7, rnd.uniform(0.5, 1.6))
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts): sp.points[i].co = (p.x, p.y, p.z, 1)
# service drops to building facades
for (pi, tgt) in [(0, (8.6, 12.0, 7.5)), (0, (8.6, 9.8, 10.5)), (1, (8.6, 24.0, 8.0)), (3, (21.9, 9.6, 9.0)), (5, (-8.6, 12.0, 8.0)), (6, (-21.0, 9.6, 9.5)), (8, (8.6, -12.0, 7.0))]:
    for w in range(2):
        pts = catenary("d", tops[pi] + Vector((0, 0, -0.6*w)), Vector(tgt) + Vector((0, 0, -0.3*w)), 0.6)
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts): sp.points[i].co = (p.x, p.y, p.z, 1)
wo = bpy.data.objects.new("K_wires", cu); CP.objects.link(wo); cu.materials.append(M_wire)

# ---- traffic signal over road B (faces the camera side), pedestrian signals
cyl("K_sigpole", (6.1, -7.3, GF), 0.14, 6.6, M_pole)
box("K_sigarm", -1.5, 6.1, -7.36, -7.24, GF + 6.1, GF + 6.25, M_pole, CP)
box("K_sighead", -1.4, 1.2, -7.55, -7.2, GF + 5.4, GF + 6.05, M_dark, CP)
def lamp_mat(name, col, expr):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*col, 1)
    nt.links.new(val(nt, "s", expr, ["night"]), e.inputs["Strength"]); nt.links.new(e.outputs[0], o.inputs[0]); return m
# green until f190, amber f190-206, red after (signal life)
ctrl["sig"] = 0.0
for f, v in ((1, 0.0), (190, 0.0), (191, 1.0), (206, 1.0), (207, 2.0), (NF, 2.0)):
    ctrl["sig"] = v; ctrl.keyframe_insert('["sig"]', frame=f)
def sig_mat(name, col, idx):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*col, 1)
    n = nt.nodes.new("ShaderNodeValue"); fc = n.outputs[0].driver_add("default_value"); d = fc.driver
    for p in ("sig", "night"):
        v = d.variables.new(); v.name = p; v.targets[0].id = ctrl; v.targets[0].data_path = f'["{p}"]'
    d.expression = f"(abs(sig-{idx})<0.5)*(14+30*night) + 0.05"
    nt.links.new(n.outputs[0], e.inputs["Strength"]); nt.links.new(e.outputs[0], o.inputs[0]); return m
for k, (col, idx) in enumerate((((1.0, 0.08, 0.04), 2), ((1.0, 0.55, 0.02), 1), ((0.1, 1.0, 0.45), 0))):
    me = bpy.data.meshes.new(f"K_siglamp_{k}"); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=0.17); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(f"K_siglamp_{k}", me); CP.objects.link(o); o.location = (-1.0 + k*0.75, -7.57, GF + 5.72); o.rotation_euler = (math.radians(90), 0, 0)
    o.data.materials.append(sig_mat(f"K_sig_{k}", col, idx))

# ---- street lights (LED cobra heads) with warm-white spots at night
for i, (x, y, rz) in enumerate([(5.9, 16.0, 180), (-5.9, -16.0, 0), (16.0, -6.9, 90), (-16.0, 6.9, -90), (5.9, 34.0, 180)]):
    cyl(f"K_sl_{i}", (x, y, GF), 0.1, 8.0, M_pole)
    d = Vector((math.cos(math.radians(rz)), math.sin(math.radians(rz)), 0))
    hx, hy = x + d.x*1.6, y + d.y*1.6
    box(f"K_slh_{i}", hx - 0.35, hx + 0.35, hy - 0.18, hy + 0.18, GF + 7.85, GF + 8.05, M_dark, CP)
    l = bpy.data.lights.new(f"K_sll_{i}", 'SPOT'); l.spot_size = math.radians(115); l.spot_blend = 0.6; l.color = (1.0, 0.86, 0.7); l.shadow_soft_size = 0.25
    lo = bpy.data.objects.new(f"K_sll_{i}", l); CL.objects.link(lo); lo.location = (hx, hy, GF + 7.8)
    drive(l, "energy", "1600*night", ["night"])
    lo.visible_camera = False
# soft spill from shop interiors onto the sidewalk (area lights behind storefronts)
for i, (x, y, rz) in enumerate([(14.3, 10.4, 90), (9.4, 15.0, 0), (-14.8, 10.4, 90), (27.0, 10.4, 90), (9.4, 27.0, 0)]):
    l = bpy.data.lights.new(f"K_shop_{i}", 'AREA'); l.size = 6.0; l.size_y = 2.6; l.shape = 'RECTANGLE'; l.color = (1.0, 0.78, 0.55)
    lo = bpy.data.objects.new(f"K_shop_{i}", l); CL.objects.link(lo); lo.location = (x, y, GF + 1.6)
    lo.rotation_euler = (math.radians(90), 0, math.radians(rz + 180))
    drive(l, "energy", "80+700*night", ["night"]); lo.visible_camera = False

# ---- trees along the kerbs
tc = [c for c in bpy.data.collections if c.name.startswith("tree_small_02")][0]
for i, (x, y) in enumerate([(6.9, 30.5), (6.9, 45.0), (-6.9, 26.0), (-6.9, 40.0), (28.0, 7.7), (44.0, 7.7), (-28.0, 7.7), (-12.0, 7.7), (6.9, -16.0), (-6.9, -22.0)]):
    e = bpy.data.objects.new(f"K_tree_{i}", None); e.instance_type = 'COLLECTION'; e.instance_collection = tc; CP.objects.link(e)
    e.location = (x, y, GF); e.rotation_euler.z = rnd.uniform(0, 6.28); e.scale = (1.55,)*3
# bollards
for i, (x, y) in enumerate([(5.4, 6.4 + k*0.0) for k in range(1)] + [(5.45, 6.6), (5.45, 9.4), (6.6, 6.4), (9.3, 6.4), (-5.45, 6.6), (-6.6, 6.4)]):
    cyl(f"K_bol_{i}", (x, y, GF), 0.08, 0.9, M_dark)

# ---- sky / sun: daylight -> dusk time-lapse -> night -> overcast rain
w = bpy.data.worlds.get("K_world") or bpy.data.worlds.new("K_world"); w.use_nodes = True; S.world = w
nt = w.node_tree; nt.nodes.clear()
sky = nt.nodes.new("ShaderNodeTexSky"); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_disc = False; sky.aerosol_density = 1.6
SUN_AZ = math.radians(235)
sky.sun_rotation = (math.pi/2 - SUN_AZ) % (2*math.pi)
for f, el in ((1, 34.0), (84, 30.0), (128, 1.5), (146, -4.0)):
    sky.sun_elevation = math.radians(el); sky.keyframe_insert("sun_elevation", frame=f)
b1 = nt.nodes.new("ShaderNodeBackground"); nt.links.new(sky.outputs[0], b1.inputs[0]); drive(b1.inputs[1], "default_value", "0.42*(1-night*0.92)", ["night"])
# night sky: deep blue with sodium/orange city glow near the horizon
tcx = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tcx.outputs["Generated"], sx.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
e[0].position = 0.0; e[0].color = (0.05, 0.028, 0.03, 1); e[1].position = 0.45; e[1].color = (0.004, 0.006, 0.014, 1)
x = e.new(0.12); x.color = (0.016, 0.014, 0.03, 1)
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; nt.links.new(sx.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs[0], cr.inputs[0])
b2 = nt.nodes.new("ShaderNodeBackground"); nt.links.new(cr.outputs[0], b2.inputs[0]); drive(b2.inputs[1], "default_value", "1.0+0.6*rain", ["rain"])
mx = nt.nodes.new("ShaderNodeMixShader"); drive(mx.inputs[0], "default_value", "min(1, night*1.15)", ["night"])
nt.links.new(b1.outputs[0], mx.inputs[1]); nt.links.new(b2.outputs[0], mx.inputs[2])
o_ = nt.nodes.new("ShaderNodeOutputWorld"); nt.links.new(mx.outputs[0], o_.inputs[0])
sun = tlib.sun("K_sun", (0, 0, 0), energy=4.0, color=(1.0, 0.93, 0.85), angle=0.6)
for c in list(sun.users_collection): c.objects.unlink(sun)
CL.objects.link(sun)
for f, el in ((1, 34.0), (84, 30.0), (128, 1.5), (146, -4.0)):
    e_ = math.radians(max(el, 0.5))
    sd = Vector((math.cos(SUN_AZ)*math.cos(e_), math.sin(SUN_AZ)*math.cos(e_), math.sin(e_)))
    sun.rotation_euler = (-sd).to_track_quat('-Z', 'Y').to_euler(); sun.keyframe_insert("rotation_euler", frame=f)
for f, en, col in ((1, 4.2, (1.0, 0.95, 0.88)), (84, 4.0, (1.0, 0.9, 0.8)), (118, 2.2, (1.0, 0.58, 0.3)), (134, 0.0, (1.0, 0.4, 0.2))):
    sun.data.energy = en; sun.data.keyframe_insert("energy", frame=f); sun.data.color = col; sun.data.keyframe_insert("color", frame=f)

# ---- rain: instanced streaks falling with scene time, density driven by CTRL.rain
rng = np.random.default_rng(3); NPT = 14000
P = np.stack([rng.uniform(-14, 22, NPT), rng.uniform(-16, 26, NPT), rng.uniform(0, 15, NPT)], 1)
me = bpy.data.meshes.new("K_rain"); me.vertices.add(NPT); me.vertices.foreach_set("co", P.astype(np.float32).ravel())
ro = bpy.data.objects.new("K_rain", me); CR.objects.link(ro)
ng = bpy.data.node_groups.new("K_rain_gn", 'GeometryNodeTree')
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'); ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
N_, L_ = ng.nodes, ng.links
gi = N_.new("NodeGroupInput"); go = N_.new("NodeGroupOutput")
m2p = N_.new("GeometryNodeMeshToPoints"); L_.new(gi.outputs[0], m2p.inputs["Mesh"])
pos = N_.new("GeometryNodeInputPosition"); sx_ = N_.new("ShaderNodeSeparateXYZ"); L_.new(pos.outputs[0], sx_.inputs[0])
tm = N_.new("GeometryNodeInputSceneTime")
sp_ = N_.new("ShaderNodeMath"); sp_.operation = 'MULTIPLY'; sp_.inputs[1].default_value = 9.5; L_.new(tm.outputs["Seconds"], sp_.inputs[0])
sb = N_.new("ShaderNodeMath"); sb.operation = 'SUBTRACT'; L_.new(sx_.outputs["Z"], sb.inputs[0]); L_.new(sp_.outputs[0], sb.inputs[1])
md_ = N_.new("ShaderNodeMath"); md_.operation = 'FLOORED_MODULO'; md_.inputs[1].default_value = 15.0; L_.new(sb.outputs[0], md_.inputs[0])
cb = N_.new("ShaderNodeCombineXYZ"); L_.new(sx_.outputs["X"], cb.inputs["X"]); L_.new(sx_.outputs["Y"], cb.inputs["Y"]); L_.new(md_.outputs[0], cb.inputs["Z"])
spos = N_.new("GeometryNodeSetPosition"); L_.new(m2p.outputs[0], spos.inputs["Geometry"]); L_.new(cb.outputs[0], spos.inputs["Position"])
rv = N_.new("FunctionNodeRandomValue"); rv.data_type = 'FLOAT'
rain_v = N_.new("ShaderNodeValue"); rain_v.name = "rain"; drive(rain_v.outputs[0], "default_value", "rain", ["rain"])
lt = N_.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; L_.new(rv.outputs["Value"], lt.inputs[0]); L_.new(rain_v.outputs[0], lt.inputs[1])
cy = N_.new("GeometryNodeMeshCylinder"); cy.inputs["Vertices"].default_value = 5; cy.inputs["Radius"].default_value = 0.0045; cy.inputs["Depth"].default_value = 0.42
iop = N_.new("GeometryNodeInstanceOnPoints"); L_.new(spos.outputs[0], iop.inputs["Points"]); L_.new(cy.outputs["Mesh"], iop.inputs["Instance"]); L_.new(lt.outputs[0], iop.inputs["Selection"])
rot = N_.new("ShaderNodeCombineXYZ"); rot.inputs["X"].default_value = math.radians(4); L_.new(rot.outputs[0], iop.inputs["Rotation"])
L_.new(iop.outputs[0], go.inputs[0])
ro.modifiers.new("rain", 'NODES').node_group = ng
mrain = bpy.data.materials.get("K_rainmat") or bpy.data.materials.new("K_rainmat"); mrain.use_nodes = True
prn = mrain.node_tree.nodes["Principled BSDF"]; prn.inputs["Base Color"].default_value = (0.9, 0.93, 1.0, 1); prn.inputs["Roughness"].default_value = 0.05
prn.inputs["Transmission Weight"].default_value = 1.0; prn.inputs["IOR"].default_value = 1.33; prn.inputs["Alpha"].default_value = 0.55
ro.data.materials.append(mrain); ro.visible_shadow = False

# ---- camera: pedestrian height, SW corner, slow push
cam, tgt = tlib.camera((-9.6, -11.8, 1.62), (10.6, 11.6, 6.3), lens=26)
cam.data.clip_end = 600
for f, l, t in ((1, (-9.6, -11.8, 1.62), (10.6, 11.6, 6.3)), (NF, (-8.1, -10.2, 1.74), (10.6, 11.6, 6.8))):
    cam.location = l; cam.keyframe_insert("location", frame=f); tgt.location = t; tgt.keyframe_insert("location", frame=f)
for idb in (cam, tgt):
    for fc in tlib._fcurves(idb.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---- render
S.render.engine = 'CYCLES'; S.cycles.device = 'GPU'
S.cycles.samples = 40; S.cycles.use_adaptive_sampling = True; S.cycles.adaptive_threshold = 0.03; S.cycles.use_denoising = True
S.cycles.max_bounces = 6; S.cycles.glossy_bounces = 3; S.cycles.diffuse_bounces = 2; S.cycles.transmission_bounces = 4; S.cycles.transparent_max_bounces = 8
S.render.resolution_x, S.render.resolution_y, S.render.resolution_percentage = 1920, 1080, 100
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'; S.view_settings.exposure = 0.0
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.5
S.render.use_persistent_data = True
S.frame_set(1); print("seoul_02 ok")
