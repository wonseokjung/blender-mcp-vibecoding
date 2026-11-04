# seoul_01: one Seoul street corner, three states (day -> night -> rain) driven by CTRL channels night/rain/wet.
import bpy, bmesh, math, sys, random
import numpy as np
from mathutils import Vector
sys.path.insert(0, 'scripts')
import importlib, tlib; importlib.reload(tlib)
W = '../_workB'
S = bpy.context.scene
for o in list(bpy.data.objects):
    if not any(c.name.startswith("tree_small_02") for c in o.users_collection):
        bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    if c.name.startswith("K_"): bpy.data.collections.remove(c)
for ng in list(bpy.data.node_groups):
    if ng.name.startswith("K_"): bpy.data.node_groups.remove(ng)
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name.startswith("tree_small_02") or lc.name.startswith("AS_"): lc.exclude = True
NF = 336; S.frame_start, S.frame_end = 1, NF; S.render.fps = 24
def coll(n):
    c = bpy.data.collections.new(n); S.collection.children.link(c); return c
CG, CB, CS, CP, CL, CR = coll("K_ground"), coll("K_build"), coll("K_signs"), coll("K_props"), coll("K_lights"), coll("K_rain")
rnd = random.Random(12)

# ---------------- state channels ----------------
ctrl = bpy.data.objects.new("CTRL", None); CP.objects.link(ctrl)
def chan(name, keys):
    ctrl[name] = keys[0][1]
    for f, v in keys:
        ctrl[name] = v; ctrl.keyframe_insert(f'["{name}"]', frame=f)
chan("night", [(1, 0.0), (84, 0.0), (146, 1.0), (NF, 1.0)])
chan("rain", [(1, 0.0), (214, 0.0), (240, 1.0), (NF, 1.0)])
chan("wet", [(1, 0.0), (218, 0.0), (262, 1.0), (NF, 1.0)])
chan("sun", [(1, 1.0), (84, 1.0), (128, 0.0), (NF, 0.0)])
def drive(owner, path, expr, props, index=-1):
    fc = owner.driver_add(path, index) if index >= 0 else owner.driver_add(path)
    d = fc.driver; d.type = 'SCRIPTED'
    for p in props:
        v = d.variables.new(); v.name = p; v.type = 'SINGLE_PROP'; v.targets[0].id = ctrl; v.targets[0].data_path = f'["{p}"]'
    d.expression = expr
def val(nt, name, expr, props):
    n = nt.nodes.new("ShaderNodeValue"); n.name = name; drive(n.outputs[0], "default_value", expr, props); return n.outputs[0]

# ---------------- helpers ----------------
def mesh(name, verts, faces, c, m=None, attrs=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if attrs:
        for an, arr in attrs.items():
            a = me.attributes.new(an, 'FLOAT', 'FACE'); a.data.foreach_set("value", np.array(arr, np.float32))
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    if m: o.data.materials.append(m)
    return o
def box(name, x0, x1, y0, y1, z0, z1, m, c):
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    return mesh(name, v, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], c, m)
def img_nodes(nt, mname, size, colorspace_nc=("Rough", "gl", "Displacement")):
    src = bpy.data.materials[mname].node_tree
    ims = {n.image.name: n.image for n in src.nodes if n.type == 'TEX_IMAGE'}
    geo = nt.nodes.new("ShaderNodeNewGeometry"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1/size,)*3
    nt.links.new(geo.outputs["Position"], mp.inputs[0])
    out = {}
    for key in ("Diffuse", "Rough", "gl"):
        im = [v for k, v in ims.items() if key in k]
        if not im: continue
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = im[0]; t.projection = 'BOX'; t.projection_blend = 0.2
        if key != "Diffuse": t.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs[0], t.inputs[0]); out[key] = t
    return out
def surface(name, mname, size, tint=(1, 1, 1), wet_k=1.0, base_rough=None):
    """PBR scan + wetness (darken, gloss, puddles with rain ripples)"""
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); pb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    T = img_nodes(nt, mname, size)
    tn = nt.nodes.new("ShaderNodeMix"); tn.data_type = 'RGBA'; tn.blend_type = 'MULTIPLY'; tn.inputs[0].default_value = 1.0
    nt.links.new(T["Diffuse"].outputs[0], tn.inputs[6]); tn.inputs[7].default_value = (*tint, 1)
    wet = val(nt, "wet", f"wet*{wet_k}", ["wet"]); rain = val(nt, "rain", "rain", ["rain"])
    # puddles
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    pn = nt.nodes.new("ShaderNodeTexNoise"); pn.inputs["Scale"].default_value = 0.22; pn.inputs["Detail"].default_value = 4
    nt.links.new(geo.outputs["Position"], pn.inputs["Vector"])
    pm = nt.nodes.new("ShaderNodeMapRange"); pm.inputs["From Min"].default_value = 0.48; pm.inputs["From Max"].default_value = 0.56
    nt.links.new(pn.outputs["Fac"], pm.inputs["Value"])
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = 'MULTIPLY'; nt.links.new(pm.outputs[0], pw.inputs[0]); nt.links.new(wet, pw.inputs[1])
    dk = nt.nodes.new("ShaderNodeMix"); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; nt.links.new(wet, dk.inputs[0])
    nt.links.new(tn.outputs[2], dk.inputs[6]); dk.inputs[7].default_value = (0.42, 0.42, 0.44, 1)
    nt.links.new(dk.outputs[2], pb.inputs["Base Color"])
    r0 = T["Rough"].outputs[0] if "Rough" in T else None
    rw = nt.nodes.new("ShaderNodeMix"); rw.data_type = 'FLOAT'; nt.links.new(wet, rw.inputs[0])
    if r0: nt.links.new(r0, rw.inputs[2])
    else: rw.inputs[2].default_value = base_rough or 0.7
    rw.inputs[3].default_value = 0.16
    rp = nt.nodes.new("ShaderNodeMix"); rp.data_type = 'FLOAT'; nt.links.new(pw.outputs[0], rp.inputs[0]); nt.links.new(rw.outputs[0], rp.inputs[2]); rp.inputs[3].default_value = 0.015
    nt.links.new(rp.outputs[0], pb.inputs["Roughness"])
    # ripples: animated 4D noise -> bump, scaled by rain*puddle
    rn = nt.nodes.new("ShaderNodeTexNoise"); rn.noise_dimensions = '4D'; rn.inputs["Scale"].default_value = 9.0; rn.inputs["Detail"].default_value = 2
    nt.links.new(geo.outputs["Position"], rn.inputs["Vector"])
    tval = nt.nodes.new("ShaderNodeValue"); tval.name = "time"; drive(tval.outputs[0], "default_value", "frame/6.0", [])
    nt.links.new(tval.outputs[0], rn.inputs["W"])
    bs = nt.nodes.new("ShaderNodeMath"); bs.operation = 'MULTIPLY'; nt.links.new(pw.outputs[0], bs.inputs[0]); nt.links.new(rain, bs.inputs[1])
    bsk = nt.nodes.new("ShaderNodeMath"); bsk.operation = 'MULTIPLY'; bsk.inputs[1].default_value = 0.35; nt.links.new(bs.outputs[0], bsk.inputs[0])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    if "gl" in T: nt.links.new(T["gl"].outputs[0], nm.inputs["Color"])
    nms = nt.nodes.new("ShaderNodeMath"); nms.operation = 'SUBTRACT'; nms.inputs[0].default_value = 1.0; nt.links.new(pw.outputs[0], nms.inputs[1])
    nt.links.new(nms.outputs[0], nm.inputs["Strength"])
    bp = nt.nodes.new("ShaderNodeBump"); nt.links.new(bsk.outputs[0], bp.inputs["Strength"]); bp.inputs["Distance"].default_value = 0.02
    nt.links.new(rn.outputs["Fac"], bp.inputs["Height"]); nt.links.new(nm.outputs[0], bp.inputs["Normal"])
    nt.links.new(bp.outputs[0], pb.inputs["Normal"])
    nt.links.new(pb.outputs[0], o.inputs[0])
    return m

M_road = surface("K_road", "asphalt_02", 5.0, (0.72, 0.72, 0.74))
M_walk = surface("K_walk", "concrete_pavement_02", 2.4, (0.95, 0.93, 0.9), 0.8)
M_paint = tlib.mat("K_paint", base=(0.86, 0.86, 0.84), rough=0.55)
pnt = M_paint.node_tree; wv = val(pnt, "wet", "wet", ["wet"]); pr = pnt.nodes.new("ShaderNodeMapRange"); pr.inputs["To Min"].default_value = 0.55; pr.inputs["To Max"].default_value = 0.12
pnt.links.new(wv, pr.inputs["Value"]); pnt.links.new(pr.outputs[0], pnt.nodes["Principled BSDF"].inputs["Roughness"])
M_yellow = M_paint.copy(); M_yellow.name = "K_paint_y"; M_yellow.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.6, 0.05, 1)
M_curb = surface("K_curb", "concrete_wall_008", 2.0, (0.8, 0.8, 0.78), 0.8)
M_brick = surface("K_brick", "red_brick_03", 2.2, (1, 1, 1), 0.6)
M_plast = surface("K_plaster", "white_plaster_02", 3.0, (0.92, 0.9, 0.86), 0.5)
M_tile = surface("K_tile", "rectangular_facade_tiles", 2.4, (1.0, 0.95, 0.86), 0.5)
M_conc = surface("K_conc", "concrete_wall_008", 3.0, (0.75, 0.74, 0.72), 0.5)
M_metal = tlib.mat("K_metal", base=(0.55, 0.56, 0.57), metal=1.0, rough=0.35)
M_dark = tlib.mat("K_dark", base=(0.04, 0.04, 0.045), metal=0.6, rough=0.4)
M_pole = tlib.mat("K_pole", base=(0.55, 0.55, 0.53), rough=0.6)
M_wire = tlib.mat("K_wire", base=(0.01, 0.01, 0.01), rough=0.4)

# window glass: dark reflective + night interior glow per window (random face attribute)
def window_mat(name):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); pb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    pb.inputs["Base Color"].default_value = (0.02, 0.025, 0.03, 1); pb.inputs["Roughness"].default_value = 0.05; pb.inputs["Specular IOR Level"].default_value = 0.8
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "wr"; at.attribute_type = 'GEOMETRY'
    th = nt.nodes.new("ShaderNodeMath"); th.operation = 'GREATER_THAN'; th.inputs[1].default_value = 0.42; nt.links.new(at.outputs["Fac"], th.inputs[0])
    cr = nt.nodes.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.4; e[0].color = (1.0, 0.62, 0.32, 1); e[1].position = 0.85; e[1].color = (0.75, 0.86, 1.0, 1)
    nt.links.new(at.outputs["Fac"], cr.inputs[0]); nt.links.new(cr.outputs[0], pb.inputs["Emission Color"])
    nv = val(nt, "night", "night", ["night"])
    # windows switch on staggered: on when night > attr-based threshold
    st = nt.nodes.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 0.8; nt.links.new(at.outputs["Fac"], st.inputs[0])
    on = nt.nodes.new("ShaderNodeMath"); on.operation = 'GREATER_THAN'; nt.links.new(nv, on.inputs[0]); nt.links.new(st.outputs[0], on.inputs[1])
    a = nt.nodes.new("ShaderNodeMath"); a.operation = 'MULTIPLY'; nt.links.new(th.outputs[0], a.inputs[0]); nt.links.new(on.outputs[0], a.inputs[1])
    b = nt.nodes.new("ShaderNodeMath"); b.operation = 'MULTIPLY'; b.inputs[1].default_value = 2.2; nt.links.new(a.outputs[0], b.inputs[0])
    nt.links.new(b.outputs[0], pb.inputs["Emission Strength"])
    nt.links.new(pb.outputs[0], o.inputs[0]); return m
M_win = window_mat("K_window")
def sign_mat(name, img, day=0.25, nightk=5.0, flick=0.0):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); pb = nt.nodes.new("ShaderNodeBsdfPrincipled")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(f"{W}/assets/signs/{img}.png", check_existing=True)
    nt.links.new(t.outputs[0], pb.inputs["Base Color"]); nt.links.new(t.outputs[0], pb.inputs["Emission Color"])
    pb.inputs["Roughness"].default_value = 0.25; pb.inputs["Coat Weight"].default_value = 0.5
    # each sign switches on at its own moment during dusk
    nv = val(nt, "glow", f"{day} + {nightk}*min(1, max(0, (night-{flick})*6))", ["night"])
    nt.links.new(nv, pb.inputs["Emission Strength"])
    nt.links.new(pb.outputs[0], o.inputs[0]); return m

# ---------------- ground: roads, sidewalks, curbs, markings ----------------
RA, RB = 6.0, 5.0          # half widths: road A (along x), road B (along y)
SW = 3.4                   # sidewalk width
EXT = 90
box("K_road", -EXT, EXT, -EXT, EXT, -0.05, 0.0, M_road, CG)
for sx in (-1, 1):
    for sy in (-1, 1):
        x0, x1 = sorted((sx*RB, sx*EXT)); y0, y1 = sorted((sy*RA, sy*EXT))
        box(f"K_walk_{sx}{sy}", x0, x1, y0, y1, 0.0, 0.15, M_walk, CG)
        box(f"K_curbA_{sx}{sy}", x0, x1, sy*RA - 0.12 if sy > 0 else sy*RA, sy*RA if sy > 0 else sy*RA + 0.12, 0.0, 0.16, M_curb, CG)
        box(f"K_curbB_{sx}{sy}", sx*RB - 0.12 if sx > 0 else sx*RB, sx*RB if sx > 0 else sx*RB + 0.12, y0, y1, 0.0, 0.16, M_curb, CG)
# crosswalk zebra bars + stop lines + centre lines
def bar(name, x0, x1, y0, y1, m=M_paint):
    return box(name, x0, x1, y0, y1, 0.0, 0.006, m, CG)
for side in (-1, 1):
    for i in range(int(2*RB/0.9)):          # across road A? (crosswalks on road A at x = side*(RB+1.5 .. RB+5))
        pass
for side in (-1, 1):
    xc0, xc1 = side*(RB + 1.2), side*(RB + 4.6)
    for i in range(12):
        y = -RA + 0.3 + i*1.0
        bar(f"K_zA_{side}_{i}", min(xc0, xc1), max(xc0, xc1), y, y + 0.5)
    yc0, yc1 = side*(RA + 1.2), side*(RA + 4.6)
    for i in range(10):
        x = -RB + 0.25 + i*1.0
        bar(f"K_zB_{side}_{i}", x, x + 0.5, min(yc0, yc1), max(yc0, yc1))
    # stop lines
    bar(f"K_stopA_{side}", side*(RB + 5.4) - 0.2, side*(RB + 5.4) + 0.2, (0 if side > 0 else -RA) + 0.0, (RA if side > 0 else 0))
for x0 in (-EXT, RB + 6):
    x1 = -(RB + 6) if x0 < 0 else EXT
    bar(f"K_ylA1_{x0}", x0, x1, -0.16, -0.04, M_yellow); bar(f"K_ylA2_{x0}", x0, x1, 0.04, 0.16, M_yellow)
for y0 in (-EXT, RA + 6):
    y1 = -(RA + 6) if y0 < 0 else EXT
    bar(f"K_ylB1_{y0}", -0.16, -0.04, y0, y1, M_yellow); bar(f"K_ylB2_{y0}", 0.04, 0.16, y0, y1, M_yellow)

# ---------------- buildings ----------------
GF = 0.15
def windows_mesh(name, faces_spec, c):
    """faces_spec: list of (origin, u_dir, n_dir, width, z0, cols, rows, fh, ww, wh) -> window quads + frames"""
    V, F, R = [], [], []
    FV, FF = [], []
    for (o, u, n, width, z0, cols, rows, fh, ww, wh) in faces_spec:
        o, u, n = Vector(o), Vector(u), Vector(n)
        step = width/cols
        for r in range(rows):
            for k in range(cols):
                cx = (k + 0.5)*step; zb = z0 + r*fh + (fh - wh)*0.45
                p = o + u*(cx - ww/2) + n*0.03
                q = [p + Vector((0, 0, zb)), p + u*ww + Vector((0, 0, zb)), p + u*ww + Vector((0, 0, zb + wh)), p + Vector((0, 0, zb + wh))]
                i0 = len(V); V += [tuple(x) for x in q]; F.append((i0, i0 + 1, i0 + 2, i0 + 3)); R.append(rnd.random())
                # frame: 4 thin boxes approximated as an outer quad ring slightly proud
                fw = 0.07; pf = o + u*(cx - ww/2 - fw) + n*0.045
                outer = [pf + Vector((0, 0, zb - fw)), pf + u*(ww + 2*fw) + Vector((0, 0, zb - fw)), pf + u*(ww + 2*fw) + Vector((0, 0, zb + wh + fw)), pf + Vector((0, 0, zb + wh + fw))]
                inner = [p + n*0.015 + Vector((0, 0, zb)), p + n*0.015 + u*ww + Vector((0, 0, zb)), p + n*0.015 + u*ww + Vector((0, 0, zb + wh)), p + n*0.015 + Vector((0, 0, zb + wh))]
                j0 = len(FV); FV += [tuple(x) for x in outer + inner]
                FF += [(j0, j0 + 1, j0 + 5, j0 + 4), (j0 + 1, j0 + 2, j0 + 6, j0 + 5), (j0 + 2, j0 + 3, j0 + 7, j0 + 6), (j0 + 3, j0, j0 + 4, j0 + 7)]
    w = mesh(name + "_win", V, F, c, M_win, attrs={"wr": R})
    mesh(name + "_frames", FV, FF, c, M_metal)
    return w
def building(name, x0, x1, y0, y1, floors, fh, wall, faces, shop=None):
    H = GF + 4.2 + (floors - 1)*fh
    box(name, x0, x1, y0, y1, GF, H, wall, CB)
    box(name + "_parapet", x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, H, H + 0.6, M_conc, CB)
    specs = []
    for fdir in faces:
        if fdir == 'S': o, u, n, w_ = (x0, y0, 0), (1, 0, 0), (0, -1, 0), x1 - x0
        if fdir == 'W': o, u, n, w_ = (x0, y1, 0), (0, -1, 0), (-1, 0, 0), y1 - y0
        if fdir == 'N': o, u, n, w_ = (x1, y1, 0), (-1, 0, 0), (0, 1, 0), x1 - x0
        if fdir == 'E': o, u, n, w_ = (x1, y0, 0), (0, 1, 0), (1, 0, 0), y1 - y0
        cols = max(2, int(w_/3.0))
        specs.append((o, u, n, w_, GF + 4.2, cols, floors - 1, fh, min(2.1, w_/cols*0.62), 1.5))
    windows_mesh(name, specs, CB)
    # ground-floor storefront (glass + warm interior)
    for fdir in faces:
        if fdir == 'S': a, b = (x0 + 0.3, y0 - 0.02), (x1 - 0.3, y0 - 0.02)
        elif fdir == 'W': a, b = (x0 - 0.02, y0 + 0.3), (x0 - 0.02, y1 - 0.3)
        elif fdir == 'E': a, b = (x1 + 0.02, y0 + 0.3), (x1 + 0.02, y1 - 0.3)
        else: continue
        v = [(a[0], a[1], GF + 0.25), (b[0], b[1], GF + 0.25), (b[0], b[1], GF + 3.1), (a[0], a[1], GF + 3.1)]
        mesh(f"{name}_store_{fdir}", v, [(0, 1, 2, 3)], CB, M_store)
    return H
M_store = bpy.data.materials.get("K_store") or bpy.data.materials.new("K_store"); M_store.use_nodes = True
nt = M_store.node_tree; pbs = nt.nodes["Principled BSDF"]
pbs.inputs["Base Color"].default_value = (0.12, 0.1, 0.08, 1); pbs.inputs["Roughness"].default_value = 0.06
pbs.inputs["Emission Color"].default_value = (1.0, 0.78, 0.55, 1)
sv = val(nt, "store", "0.35 + 2.4*night", ["night"]); nt.links.new(sv, pbs.inputs["Emission Strength"])
# brick/plaster/tile variety; hero = tile corner building NE
hero_H = building("K_hero", 8.6, 21.5, 9.6, 21.0, 5, 3.1, M_tile, ['S', 'W'])
building("K_n1", 8.6, 20.0, 21.4, 33.0, 4, 3.0, M_brick, ['W'])
building("K_n2", 8.6, 21.0, 33.4, 46.0, 6, 3.0, M_plast, ['W'])
building("K_e1", 21.9, 33.5, 9.6, 21.0, 6, 3.0, M_plast, ['S'])
building("K_e2", 33.9, 46.0, 9.6, 20.0, 4, 3.0, M_brick, ['S'])
building("K_e3", 46.4, 60.0, 9.6, 22.0, 8, 3.0, M_conc, ['S'])
building("K_nw1", -21.0, -8.6, 9.6, 21.0, 4, 3.0, M_brick, ['S', 'E'])
building("K_nw2", -34.0, -21.4, 9.6, 20.0, 5, 3.0, M_tile, ['S'])
building("K_nw3", -21.0, -8.6, 21.4, 34.0, 7, 3.0, M_plast, ['E'])
building("K_se1", 8.6, 21.0, -21.0, -9.6, 3, 3.0, M_brick, ['W', 'N'])
building("K_se2", 21.4, 34.0, -20.0, -9.6, 5, 3.0, M_plast, ['N'])
building("K_far1", 22.0, 34.0, 46.0, 60.0, 12, 2.9, M_conc, ['W', 'S'])   # background apartment block
building("K_far2", -36.0, -22.0, 40.0, 54.0, 15, 2.9, M_plast, ['E', 'S'])
print("ground+buildings ok", hero_H)
