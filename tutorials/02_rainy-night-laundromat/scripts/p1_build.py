# #1 비 오는 심야의 우리 가게: 'CONNECT AI LAB 24H' coin laundry on a rainy Korean street, photoreal, slow push-in.
# STAGE 1 blockout, 2 models, 3 materials+wear+prints, 4 lights+rain+fog, 9 animation. Globals: LOOKDEV, SHOW_FRAME, PARAMS.
import sys, importlib, bpy, bmesh, math, random, os
from mathutils import Vector, Euler, Matrix
sys.path.insert(0, "scripts")
import tlib
importlib.reload(tlib)
from tlib import *

STAGE = globals().get('STAGE', 9)
P = dict(int_light=70.0, street=260.0, sign=5.0, fog=0.0, rain_n=2600, exposure=0.0, spp=96)
P.update(globals().get('PARAMS', {}))
NF = 228
AS = os.path.expanduser('assets')
TX = os.path.expanduser('tex1')
reset()
s = sc(); s.frame_start, s.frame_end = 1, NF
rng = random.Random(11)

C_EXT = coll('EXT_street'); C_FAC = coll('FAC_facade'); C_INT = coll('INT_room'); C_MAC = coll('MAC_machines'); C_PROP = coll('PRP_props')
C_LGT = coll('LGT_lights'); C_FX = coll('FX_rain_fog')


# ---------------- helpers ----------------
def boxm(name, c, size, m=None, col=None, bev=0.0, seg=2):
    me = bpy.data.meshes.new(name); b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0)
    for v in b.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    b.to_mesh(me); b.free()
    o = bpy.data.objects.new(name, me); (col or C_INT).objects.link(o); o.location = c
    if m:
        setmat(o, m)
    if bev:
        md = o.modifiers.new('Bevel', 'BEVEL'); md.width = bev; md.segments = seg; md.limit_method = 'ANGLE'
    return o


def cylm(name, c, r, h, m=None, col=None, seg=48, rot=(0, 0, 0), bev=0.0, r2=None, caps=True):
    me = bpy.data.meshes.new(name); b = bmesh.new()
    bmesh.ops.create_cone(b, cap_ends=caps, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    b.to_mesh(me); b.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    o = bpy.data.objects.new(name, me); (col or C_INT).objects.link(o); o.location = c; o.rotation_euler = rot
    if m:
        setmat(o, m)
    if bev:
        md = o.modifiers.new('Bevel', 'BEVEL'); md.width = bev; md.segments = 2; md.limit_method = 'ANGLE'
    return o


def torusm(name, c, R, r, m, col, rot=(0, 0, 0), U=64, V=12):
    me = bpy.data.meshes.new(name); b = bmesh.new()
    vs = [[b.verts.new(((R + r * math.cos(2 * math.pi * j / V)) * math.cos(2 * math.pi * i / U),
                        (R + r * math.cos(2 * math.pi * j / V)) * math.sin(2 * math.pi * i / U),
                        r * math.sin(2 * math.pi * j / V))) for j in range(V)] for i in range(U)]
    for i in range(U):
        for j in range(V):
            b.faces.new((vs[i][j], vs[(i + 1) % U][j], vs[(i + 1) % U][(j + 1) % V], vs[i][(j + 1) % V]))
    b.to_mesh(me); b.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = c; o.rotation_euler = rot
    setmat(o, m)
    return o


def plane(name, c, w, h, m, col, rot=(math.radians(90), 0, 0)):
    me = bpy.data.meshes.new(name); b = bmesh.new()
    bmesh.ops.create_grid(b, x_segments=1, y_segments=1, size=0.5)
    for v in b.verts:
        v.co = Vector((v.co.x * w, v.co.y * h, 0))
    uvl = b.loops.layers.uv.new('UVMap')
    for f in b.faces:
        for l in f.loops:
            l[uvl].uv = (l.vert.co.x / w + 0.5, l.vert.co.y / h + 0.5)
    b.to_mesh(me); b.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = c; o.rotation_euler = rot
    setmat(o, m)
    return o


def boolean_cut(o, cutter):
    md = o.modifiers.new('Cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cutter; md.solver = 'EXACT'
    cutter.hide_render = True; cutter.hide_viewport = True
    cutter.display_type = 'WIRE'


# ---------------- materials ----------------
def node(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n


def wear_group():
    """One wear node group for every material: edge chips, crevice grime, top dust, bottom dirt, drips, fingerprints.
    In: Color, Rough, Strength, EdgeColor, Scale -> Out: Color, Rough"""
    g = bpy.data.node_groups.get('NG_wear')
    if g:
        return g
    g = bpy.data.node_groups.new('NG_wear', 'ShaderNodeTree')
    for n_, t_ in (('Color', 'NodeSocketColor'), ('Rough', 'NodeSocketFloat'), ('Strength', 'NodeSocketFloat'), ('EdgeColor', 'NodeSocketColor'), ('Scale', 'NodeSocketFloat')):
        g.interface.new_socket(n_, in_out='INPUT', socket_type=t_)
    g.interface.new_socket('Color', in_out='OUTPUT', socket_type='NodeSocketColor')
    g.interface.new_socket('Rough', in_out='OUTPUT', socket_type='NodeSocketFloat')
    nt = g; gi = nt.nodes.new('NodeGroupInput'); go = nt.nodes.new('NodeGroupOutput')
    tc = node(nt, 'ShaderNodeTexCoord'); geo = node(nt, 'ShaderNodeNewGeometry')
    # edge chips: pointiness mapped + noise breakup
    pr = node(nt, 'ShaderNodeMapRange', **{'From Min': 0.52, 'From Max': 0.60}); nt.links.new(geo.outputs['Pointiness'], pr.inputs['Value'])
    nz = node(nt, 'ShaderNodeTexNoise', Scale=60.0, Detail=6.0); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    em = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(pr.outputs[0], em.inputs[0]); nt.links.new(nz.outputs['Fac'], em.inputs[1])
    emr = node(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.5}); nt.links.new(em.outputs[0], emr.inputs['Value'])
    # crevice grime: AO
    ao = node(nt, 'ShaderNodeAmbientOcclusion', Distance=0.12); ao.only_local = True
    aor = node(nt, 'ShaderNodeMapRange', **{'From Min': 1.0, 'From Max': 0.4}); nt.links.new(ao.outputs['AO'], aor.inputs['Value'])
    # bottom dirt: world Z
    sep = node(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sep.inputs[0])
    bz = node(nt, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.0}); nt.links.new(sep.outputs['Z'], bz.inputs['Value'])
    nz2 = node(nt, 'ShaderNodeTexNoise', Scale=8.0, Detail=8.0); nt.links.new(tc.outputs['Object'], nz2.inputs['Vector'])
    bzm = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(bz.outputs[0], bzm.inputs[0]); nt.links.new(nz2.outputs['Fac'], bzm.inputs[1])
    # top dust: normal.z
    sn = node(nt, 'ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], sn.inputs[0])
    tz = node(nt, 'ShaderNodeMapRange', **{'From Min': 0.7, 'From Max': 1.0}); nt.links.new(sn.outputs['Z'], tz.inputs['Value'])
    # drips: noise stretched in Z
    mp = node(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (14, 14, 1.2); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz3 = node(nt, 'ShaderNodeTexNoise', Scale=6.0, Detail=4.0); nt.links.new(mp.outputs[0], nz3.inputs['Vector'])
    dr = node(nt, 'ShaderNodeMapRange', **{'From Min': 0.58, 'From Max': 0.75}); nt.links.new(nz3.outputs['Fac'], dr.inputs['Value'])
    # combine grime amount
    a1 = node(nt, 'ShaderNodeMath', operation='ADD'); nt.links.new(aor.outputs[0], a1.inputs[0]); nt.links.new(bzm.outputs[0], a1.inputs[1])
    a2 = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); nt.links.new(dr.outputs[0], a2.inputs[0]); a2.inputs[1].default_value = 0.45; nt.links.new(a1.outputs[0], a2.inputs[2])
    gs = node(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True); nt.links.new(a2.outputs[0], gs.inputs[0]); nt.links.new(gi.outputs['Strength'], gs.inputs[1])
    grime_col = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); grime_col.inputs[7].default_value = (0.42, 0.37, 0.30, 1)
    nt.links.new(gs.outputs[0], grime_col.inputs[0]); nt.links.new(gi.outputs['Color'], grime_col.inputs[6])
    dust = node(nt, 'ShaderNodeMix', data_type='RGBA'); dust.inputs[7].default_value = (0.55, 0.53, 0.50, 1)
    dm = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(tz.outputs[0], dm.inputs[0]); dm.inputs[1].default_value = 0.25
    dm2 = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(dm.outputs[0], dm2.inputs[0]); nt.links.new(gi.outputs['Strength'], dm2.inputs[1])
    nt.links.new(dm2.outputs[0], dust.inputs[0]); nt.links.new(grime_col.outputs[2], dust.inputs[6])
    chip = node(nt, 'ShaderNodeMix', data_type='RGBA')
    cm = node(nt, 'ShaderNodeMath', operation='MULTIPLY', use_clamp=True); nt.links.new(emr.outputs[0], cm.inputs[0]); nt.links.new(gi.outputs['Strength'], cm.inputs[1])
    nt.links.new(cm.outputs[0], chip.inputs[0]); nt.links.new(dust.outputs[2], chip.inputs[6]); nt.links.new(gi.outputs['EdgeColor'], chip.inputs[7])
    nt.links.new(chip.outputs[2], go.inputs['Color'])
    # roughness: grime + dust rougher; fingerprints (voronoi smudges) slightly rougher on smooth surfaces
    vor = node(nt, 'ShaderNodeTexVoronoi', Scale=22.0); nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
    fp = node(nt, 'ShaderNodeMapRange', **{'From Min': 0.25, 'From Max': 0.0, 'To Max': 0.18}); nt.links.new(vor.outputs['Distance'], fp.inputs['Value'])
    r1 = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); nt.links.new(gs.outputs[0], r1.inputs[0]); r1.inputs[1].default_value = 0.35; nt.links.new(gi.outputs['Rough'], r1.inputs[2])
    r2_ = node(nt, 'ShaderNodeMath', operation='ADD', use_clamp=True); nt.links.new(r1.outputs[0], r2_.inputs[0]); nt.links.new(fp.outputs[0], r2_.inputs[1])
    r3 = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD', use_clamp=True); nt.links.new(dm2.outputs[0], r3.inputs[0]); r3.inputs[1].default_value = 0.6; nt.links.new(r2_.outputs[0], r3.inputs[2])
    nt.links.new(r3.outputs[0], go.inputs['Rough'])
    return g


def pmat(name, rgb=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, wear=0.0, edge=(0.5, 0.5, 0.5), spec=0.5, coat=0.0, img=None, uv_scale=1.0, nrm=None, rough_img=None, tint=None, emission=None, alpha=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    p.inputs['Metallic'].default_value = metal; p.inputs['Specular IOR Level'].default_value = spec; p.inputs['Coat Weight'].default_value = coat
    col_out, rough_out = None, None
    if img:
        tc = node(nt, 'ShaderNodeTexCoord'); mp = node(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (uv_scale, uv_scale, uv_scale)
        nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
        it = node(nt, 'ShaderNodeTexImage'); it.image = bpy.data.images.load(img, check_existing=True); nt.links.new(mp.outputs[0], it.inputs['Vector'])
        col_out = it.outputs['Color']
        if tint:
            mt = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); mt.inputs[0].default_value = 1.0; mt.inputs[7].default_value = (*tint, 1)
            nt.links.new(col_out, mt.inputs[6]); col_out = mt.outputs[2]
        if rough_img:
            ri = node(nt, 'ShaderNodeTexImage'); ri.image = bpy.data.images.load(rough_img, check_existing=True); ri.image.colorspace_settings.name = 'Non-Color'
            nt.links.new(mp.outputs[0], ri.inputs['Vector']); rough_out = ri.outputs['Color']
        if nrm:
            ni = node(nt, 'ShaderNodeTexImage'); ni.image = bpy.data.images.load(nrm, check_existing=True); ni.image.colorspace_settings.name = 'Non-Color'
            nt.links.new(mp.outputs[0], ni.inputs['Vector'])
            nm = node(nt, 'ShaderNodeNormalMap', Strength=0.8); nt.links.new(ni.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs[0], p.inputs['Normal'])
    if wear > 0:
        g = node(nt, 'ShaderNodeGroup'); g.node_tree = wear_group()
        if col_out is not None:
            nt.links.new(col_out, g.inputs['Color'])
        else:
            g.inputs['Color'].default_value = (*rgb, 1)
        if rough_out is not None:
            nt.links.new(rough_out, g.inputs['Rough'])
        else:
            g.inputs['Rough'].default_value = rough
        g.inputs['Strength'].default_value = wear; g.inputs['EdgeColor'].default_value = (*edge, 1)
        nt.links.new(g.outputs['Color'], p.inputs['Base Color']); nt.links.new(g.outputs['Rough'], p.inputs['Roughness'])
    else:
        if col_out is not None:
            nt.links.new(col_out, p.inputs['Base Color'])
        else:
            p.inputs['Base Color'].default_value = (*rgb, 1)
        if rough_out is not None:
            nt.links.new(rough_out, p.inputs['Roughness'])
        else:
            p.inputs['Roughness'].default_value = rough
    if emission:
        p.inputs['Emission Color'].default_value = (*emission[0], 1); p.inputs['Emission Strength'].default_value = emission[1]
    if alpha is not None:
        p.inputs['Alpha'].default_value = alpha
    return m


def print_mat(name, path, rough=0.35, coat=0.25, emit=0.0, alpha_img=False, wear=0.0):
    """printed sticker / sign: image colour, satin coat; optional emission (backlit light box)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes['Principled BSDF']
    it = node(nt, 'ShaderNodeTexImage'); it.image = bpy.data.images.load(path, check_existing=True); it.interpolation = 'Cubic'
    uv = node(nt, 'ShaderNodeUVMap'); nt.links.new(uv.outputs[0], it.inputs['Vector'])
    nt.links.new(it.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough; p.inputs['Coat Weight'].default_value = coat; p.inputs['Coat Roughness'].default_value = 0.25
    if emit:
        nt.links.new(it.outputs['Color'], p.inputs['Emission Color']); p.inputs['Emission Strength'].default_value = emit
    if alpha_img:
        nt.links.new(it.outputs['Alpha'], p.inputs['Alpha'])
    # peeling corners / scuffs: noise lowers coat + adds roughness
    nz = node(nt, 'ShaderNodeTexNoise', Scale=30.0, Detail=8.0); nt.links.new(uv.outputs[0], nz.inputs['Vector'])
    mr = node(nt, 'ShaderNodeMapRange', **{'From Min': 0.45, 'From Max': 0.75, 'To Min': rough, 'To Max': min(1.0, rough + 0.35)}); nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs[0], p.inputs['Roughness'])
    return m


A = lambda n: os.path.join(AS, 'tex', n)
m_asph = pmat('M_asphalt', img=A('asphalt_02_Diffuse_2k.jpg'), rough_img=A('asphalt_02_Rough_2k.jpg'), nrm=A('asphalt_02_nor_gl_2k.jpg'), uv_scale=0.33, tint=(0.33, 0.33, 0.35))
m_pave = pmat('M_pavement', img=A('pavement_01_Diffuse_2k.jpg'), rough_img=A('pavement_01_Rough_2k.jpg'), nrm=A('pavement_01_nor_gl_2k.jpg'), uv_scale=0.5, tint=(0.45, 0.45, 0.47))
m_tile = pmat('M_floor_tile', img=A('worn_tile_floor_Diffuse_2k.jpg'), rough_img=A('worn_tile_floor_Rough_2k.jpg'), nrm=A('worn_tile_floor_nor_gl_2k.jpg'), uv_scale=0.6, tint=(0.95, 0.95, 0.93))
m_wall_in = pmat('M_wall_inside', img=A('painted_plaster_wall_Diffuse_2k.jpg'), rough_img=A('painted_plaster_wall_Rough_2k.jpg'), nrm=A('painted_plaster_wall_nor_gl_2k.jpg'), uv_scale=0.5, tint=(0.95, 0.96, 0.95), wear=0.5, edge=(0.6, 0.58, 0.55))
m_wall_ex = pmat('M_wall_outside', img=A('concrete_wall_003_Diffuse_2k.jpg'), rough_img=A('concrete_wall_003_Rough_2k.jpg'), nrm=A('concrete_wall_003_nor_gl_2k.jpg'), uv_scale=0.4, tint=(0.55, 0.55, 0.58), wear=0.7, edge=(0.3, 0.3, 0.3))
m_shutter = pmat('M_shutter', img=A('painted_metal_shutter_Diffuse_2k.jpg'), rough_img=A('painted_metal_shutter_Rough_2k.jpg'), nrm=A('painted_metal_shutter_nor_gl_2k.jpg'), uv_scale=0.5, tint=(0.6, 0.62, 0.66), wear=0.6)
m_white = pmat('M_enamel_white', (0.86, 0.87, 0.86), rough=0.28, wear=0.9, edge=(0.25, 0.25, 0.27), coat=0.3)
m_grey = pmat('M_enamel_grey', (0.42, 0.44, 0.46), rough=0.32, wear=0.8, edge=(0.6, 0.6, 0.6), coat=0.2)
m_chrome = pmat('M_chrome', (0.9, 0.9, 0.9), rough=0.12, metal=1.0, wear=0.3)
m_steel = pmat('M_steel_drum', (0.7, 0.7, 0.72), rough=0.25, metal=1.0)
m_alu = pmat('M_alu_frame', (0.36, 0.37, 0.38), rough=0.35, metal=0.9, wear=0.6, edge=(0.7, 0.7, 0.7))
m_black = pmat('M_plastic_black', (0.02, 0.02, 0.022), rough=0.35, wear=0.5, edge=(0.25, 0.25, 0.25))
m_ceil = pmat('M_ceiling', (0.80, 0.80, 0.79), rough=0.7, wear=0.4)
m_glass = bpy.data.materials.new('M_glass_storefront'); m_glass.use_nodes = True
gp = m_glass.node_tree.nodes['Principled BSDF']; gp.inputs['Base Color'].default_value = (0.95, 0.98, 0.97, 1)
gp.inputs['Transmission Weight'].default_value = 1.0; gp.inputs['Roughness'].default_value = 0.02; gp.inputs['IOR'].default_value = 1.5
m_door_glass = bpy.data.materials.new('M_glass_machine'); m_door_glass.use_nodes = True
dg = m_door_glass.node_tree.nodes['Principled BSDF']; dg.inputs['Base Color'].default_value = (0.55, 0.62, 0.62, 1)
dg.inputs['Transmission Weight'].default_value = 1.0; dg.inputs['Roughness'].default_value = 0.06; dg.inputs['IOR'].default_value = 1.45


# ---------------- EXTERIOR: street, curb, sidewalk ----------------
plane('EXT_street', (0, -9.0, 0.0), 30, 18, m_asph, C_EXT, rot=(0, 0, 0))
boxm('EXT_curb', (0, -1.85, 0.06), (30, 0.18, 0.12), pmat('M_curb', (0.42, 0.42, 0.42), rough=0.6, wear=0.9), C_EXT, bev=0.02)
sw = plane('EXT_sidewalk', (0, -0.9, 0.12), 30, 1.8, m_pave, C_EXT, rot=(0, 0, 0))
# street paint: a worn white stop line
plane('EXT_stopline', (0, -4.6, 0.003), 9.0, 0.35, pmat('M_paint', (0.62, 0.62, 0.6), rough=0.5, wear=1.0), C_EXT, rot=(0, 0, 0))
# drain grate at the curb
boxm('EXT_drain', (2.2, -2.15, 0.004), (0.9, 0.35, 0.01), pmat('M_drain', (0.08, 0.08, 0.08), rough=0.4, metal=0.8, wear=0.8), C_EXT)

# ---------------- FACADE ----------------
X0, X1, ZF, ZT = -2.7, 2.7, 0.16, 2.62
boxm('FAC_wall_L', (-5.5, 0.15, 2.4), (5.6, 0.3, 4.8), m_wall_ex, C_FAC)
boxm('FAC_wall_R', (5.5, 0.15, 2.4), (5.6, 0.3, 4.8), m_wall_ex, C_FAC)
boxm('FAC_wall_top', (0, 0.15, 3.9), (5.4, 0.3, 2.6), m_wall_ex, C_FAC)
boxm('FAC_step', (0, -0.1, 0.14), (5.4, 0.2, 0.04), pmat('M_step', (0.30, 0.30, 0.31), rough=0.5, wear=1.0), C_FAC, bev=0.005)
# left neighbour: closed metal shutter
plane('FAC_shutter', (-5.6, -0.02, 1.35), 3.4, 2.5, m_shutter, C_FAC)
boxm('FAC_shutter_box', (-5.6, -0.12, 2.75), (3.6, 0.25, 0.32), m_alu, C_FAC, bev=0.01)
# right neighbour: dark door + small lit window upstairs
boxm('FAC_door_R', (5.1, -0.02, 1.15), (1.0, 0.05, 2.1), pmat('M_door_R', (0.12, 0.13, 0.14), rough=0.35, wear=0.8), C_FAC, bev=0.01)
for i, x in enumerate((-4.6, -1.2, 1.6, 4.9)):
    lit = i == 2
    wmat = pmat('M_win2F_%d' % i, (0.02, 0.02, 0.025), rough=0.06)
    if lit:   # warm light behind venetian blinds
        nt_ = wmat.node_tree; p_ = nt_.nodes['Principled BSDF']; tc_ = node(nt_, 'ShaderNodeTexCoord')
        wv = node(nt_, 'ShaderNodeTexWave', Scale=9.0, Distortion=0.0); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
        nt_.links.new(tc_.outputs['Object'], wv.inputs['Vector'])
        mr_ = node(nt_, 'ShaderNodeMapRange', **{'From Min': 0.3, 'From Max': 0.7, 'To Min': 0.0, 'To Max': 0.35}); nt_.links.new(wv.outputs['Fac'], mr_.inputs['Value'])
        p_.inputs['Emission Color'].default_value = (1.0, 0.66, 0.36, 1); nt_.links.new(mr_.outputs[0], p_.inputs['Emission Strength'])
    boxm('FAC_win2F_%d' % i, (x, -0.01, 4.1), (1.3, 0.04, 1.0), wmat, C_FAC)
    boxm('FAC_win2F_frame_%d' % i, (x, 0.0, 4.1), (1.4, 0.06, 1.1), m_alu, C_FAC, bev=0.005)
# storefront frame + glass
for i, x in enumerate((X0, -0.9, 0.9, X1)):
    boxm('FAC_mullion_%d' % i, (x, -0.02, (ZF + ZT) / 2), (0.07, 0.1, ZT - ZF), m_alu, C_FAC, bev=0.004)
boxm('FAC_rail_top', (0, -0.02, ZT), (X1 - X0 + 0.07, 0.1, 0.07), m_alu, C_FAC, bev=0.004)
boxm('FAC_rail_bot', (0, -0.02, ZF + 0.05), (X1 - X0 + 0.07, 0.1, 0.1), m_alu, C_FAC, bev=0.004)
glass = []
for nm, (xa, xb) in (('L', (X0, -0.9)), ('R', (0.9, X1))):
    g = boxm('FAC_glass_%s' % nm, ((xa + xb) / 2, -0.02, (ZF + ZT) / 2 + 0.03), (xb - xa - 0.06, 0.008, ZT - ZF - 0.14), m_glass, C_FAC)
    glass.append(g)
# sliding door: frame + glass, slightly open
door = bpy.data.objects.new('FAC_door', None); C_FAC.objects.link(door); door.location = (0, -0.07, 0)
dfr = [boxm('FAC_door_stile_%d' % i, (x, -0.07, 1.36), (0.05, 0.05, 2.36), m_alu, C_FAC, bev=0.003) for i, x in enumerate((-0.86, 0.86))]
dfr += [boxm('FAC_door_rail_%d' % i, (0, -0.07, z), (1.77, 0.05, 0.05), m_alu, C_FAC, bev=0.003) for i, z in enumerate((0.2, 2.53))]
dgl = boxm('FAC_door_glass', (0, -0.07, 1.36), (1.68, 0.008, 2.3), m_glass, C_FAC); glass.append(dgl)
vin = plane('FAC_door_vinyl', (0, -0.076, 1.55), 1.25, 0.70, print_mat('M_door_vinyl', os.path.join(TX, 'door_vinyl.png'), rough=0.45, coat=0.0, alpha_img=True), C_FAC)
handle = boxm('FAC_door_handle', (0.72, -0.11, 1.1), (0.03, 0.04, 0.45), m_chrome, C_FAC, bev=0.008)
for o in dfr + [dgl, vin, handle]:
    o.parent = door; o.location = o.location - door.location
door.location.x = -0.18
# light-box sign (printed face, backlit)
sgn = boxm('FAC_signbox', (0, -0.17, 3.05), (5.75, 0.3, 0.72), pmat('M_signbox', (0.10, 0.11, 0.12), rough=0.4, metal=0.6, wear=0.9, edge=(0.5, 0.5, 0.5)), C_FAC, bev=0.012)
face = plane('FAC_signface', (0, -0.325, 3.05), 5.55, 0.62, print_mat('M_signface', os.path.join(TX, 'sign_face.png'), rough=0.18, coat=0.5, emit=P['sign']), C_FAC)
# little hanging OPEN plate on the door (sways in the wind)
hang = bpy.data.objects.new('FAC_hanger_pivot', None); C_FAC.objects.link(hang); hang.location = (0.35, -0.11, 2.1); hang.parent = door; hang.location = hang.location - door.location
hp = plane('FAC_hanger', (0.35, -0.115, 1.93), 0.36, 0.16, print_mat('M_hanger', os.path.join(TX, 'hanger.png'), rough=0.5), C_FAC)
hp.parent = hang; hp.location = Vector((0.35, -0.115, 1.93)) - Vector((0.35, -0.11, 2.1))
for dx in (-0.12, 0.12):
    s_ = boxm('FAC_hanger_string_%d' % int(dx * 100), (0.35 + dx * 0.5, -0.113, 2.03), (0.003, 0.003, 0.15), m_black, C_FAC)
    s_.rotation_euler = (0, -dx * 1.4, 0); s_.parent = hang; s_.location = s_.location - Vector((0.35, -0.11, 2.1))

# ---------------- INTERIOR shell ----------------
IY = 6.4
plane('INT_floor', (0, IY / 2, ZF), 5.6, IY, m_tile, C_INT, rot=(0, 0, 0))
plane('INT_ceiling', (0, IY / 2, 2.82), 5.6, IY, m_ceil, C_INT, rot=(math.radians(180), 0, 0))
plane('INT_wall_back', (0, IY, 1.5), 5.6, 2.8, m_wall_in, C_INT, rot=(math.radians(90), 0, math.radians(180)))
plane('INT_wall_L', (-2.8, IY / 2, 1.5), IY, 2.8, m_wall_in, C_INT, rot=(math.radians(90), 0, math.radians(-90)))
plane('INT_wall_R', (2.8, IY / 2, 1.5), IY, 2.8, m_wall_in, C_INT, rot=(math.radians(90), 0, math.radians(90)))
boxm('INT_skirting_L', (-2.78, IY / 2, ZF + 0.05), (0.03, IY, 0.1), m_grey, C_INT)
boxm('INT_skirting_R', (2.78, IY / 2, ZF + 0.05), (0.03, IY, 0.1), m_grey, C_INT)
boxm('INT_skirting_B', (0, IY - 0.02, ZF + 0.05), (5.6, 0.03, 0.1), m_grey, C_INT)

# ---------------- MACHINES ----------------
DRUMS = []


def machine(name, base, face_dir, w, d, h, door_r, kind, sticker):
    """front-load machine. base=(x,y,z) of the bottom centre of the FRONT face; face_dir=+1 faces +X, -1 faces -X"""
    bx, by, bz = base
    cx = bx - face_dir * d / 2
    body = boxm(name + '_body', (cx, by, bz + h / 2), (d, w, h), m_white, C_MAC, bev=0.018, seg=3)
    dz = bz + h * (0.46 if kind == 'wash' else 0.5)
    cut = cylm(name + '_cut', (bx, by, dz), door_r * 0.92, 0.5, None, C_MAC, rot=(0, math.radians(90), 0), seg=64)
    boolean_cut(body, cut)
    # drum: open steel tube + back plate with perforation look
    drum = bpy.data.objects.new(name + '_drum', None); C_MAC.objects.link(drum); drum.location = (bx - face_dir * 0.02, by, dz)
    drum.rotation_euler = (0, math.radians(90) * face_dir, 0)
    bpy.context.view_layer.update()
    tube = cylm(name + '_drum_tube', (bx - face_dir * 0.22, by, dz), door_r * 0.9, 0.4, m_steel, C_MAC, rot=(0, math.radians(90), 0), seg=48, caps=False)
    back = cylm(name + '_drum_back', (bx - face_dir * 0.42, by, dz), door_r * 0.9, 0.01, m_steel, C_MAC, rot=(0, math.radians(90), 0), seg=48)
    for i in range(3):  # baffles (rotate with the drum)
        a = i * 2 * math.pi / 3
        bf = boxm(name + '_baffle_%d' % i, (bx - face_dir * 0.22, by + math.cos(a) * door_r * 0.8, dz + math.sin(a) * door_r * 0.8), (0.36, 0.05, 0.05), m_steel, C_MAC, bev=0.01)
        bf.rotation_euler = (a, 0, 0)
        bf.parent = drum; bf.matrix_parent_inverse = drum.matrix_world.inverted()
    for o in (tube, back):
        o.parent = drum; o.matrix_parent_inverse = drum.matrix_world.inverted()
    # door: chrome ring + domed tinted glass, hinge on the left side
    ring = torusm(name + '_door_ring', (bx + face_dir * 0.025, by, dz), door_r, 0.03, m_grey if kind == 'dry' else m_chrome, C_MAC, rot=(0, math.radians(90), 0))
    gl_ = cylm(name + '_door_glass', (bx + face_dir * 0.02, by, dz), door_r * 0.93, 0.03, m_door_glass, C_MAC, rot=(0, math.radians(90), 0), seg=48, r2=door_r * 0.85)
    # control strip + display
    cs = boxm(name + '_console', (bx + face_dir * 0.004, by, bz + h - 0.09), (0.01, w - 0.06, 0.12), m_black, C_MAC, bev=0.003)
    disp = boxm(name + '_display', (bx + face_dir * 0.011, by - 0.12, bz + h - 0.09), (0.004, 0.14, 0.05), pmat(name + '_disp_mat', (0.02, 0.02, 0.02), rough=0.2, emission=((1.0, 0.18, 0.08), 3.0 if rng.random() < 0.6 else 0.0)), C_MAC)
    knob = cylm(name + '_knob', (bx + face_dir * 0.02, by + 0.16, bz + h - 0.09), 0.03, 0.03, m_chrome, C_MAC, rot=(0, math.radians(90), 0), seg=24)
    st = plane(name + '_sticker', (bx + face_dir * 0.0012, by, bz + h - 0.26), 0.24, 0.12, print_mat(name + '_stk', os.path.join(TX, sticker)), C_MAC, rot=(math.radians(90), 0, math.radians(90) * face_dir))
    return body, drum, dz


# left wall: 4 columns of stacked dryers facing +X
for i, y in enumerate((1.35, 2.15, 2.95, 3.75)):
    for lv, z0 in enumerate((ZF, ZF + 0.86)):
        b_, dr_, dz_ = machine('MAC_dryer_%d%d' % (i, lv), (-2.05, y, z0), 1, 0.78, 0.74, 0.85, 0.27, 'dry', 'sticker_dry.png')
        DRUMS.append((dr_, 'dry', i, lv, dz_))
# right wall: 4 washers facing -X + shelf above
for i, y in enumerate((1.4, 2.2, 3.0, 3.8)):
    b_, dr_, dz_ = machine('MAC_washer_%d' % i, (2.08, y, ZF), -1, 0.78, 0.72, 0.98, 0.24, 'wash', 'sticker_wash.png')
    DRUMS.append((dr_, 'wash', i, 0, dz_))
boxm('MAC_shelf_R', (2.45, 2.6, 1.62), (0.7, 3.4, 0.04), m_grey, C_MAC, bev=0.005)

# ---------------- PROPS ----------------
poster = plane('PRP_poster', (-0.9, IY - 0.015, 1.55), 0.60, 0.85, print_mat('M_poster', os.path.join(TX, 'poster.png'), rough=0.4, coat=0.4), C_PROP, rot=(math.radians(90), 0, math.radians(180)))
kiosk = boxm('PRP_kiosk', (0.9, IY - 0.3, 0.86), (0.6, 0.5, 1.4), pmat('M_kiosk', (0.12, 0.30, 0.62), rough=0.3, wear=0.8, coat=0.4, edge=(0.7, 0.7, 0.7)), C_PROP, bev=0.02)
boxm('PRP_kiosk_screen', (0.9, IY - 0.56, 1.25), (0.42, 0.02, 0.3), pmat('M_kiosk_screen', (0.02, 0.02, 0.02), rough=0.1, emission=((0.55, 0.78, 1.0), 2.5)), C_PROP)
boxm('PRP_kiosk_slot', (0.9, IY - 0.56, 0.9), (0.22, 0.02, 0.08), m_black, C_PROP)
boxm('PRP_vend_detergent', (2.2, IY - 0.38, 1.0), (0.85, 0.65, 1.7), pmat('M_vend', (0.85, 0.20, 0.18), rough=0.3, wear=0.8, coat=0.4), C_PROP, bev=0.02)
boxm('PRP_vend_window', (2.2, IY - 0.71, 1.25), (0.62, 0.02, 0.85), pmat('M_vend_win', (0.9, 0.95, 1.0), rough=0.15, emission=((0.95, 0.97, 1.0), 2.2)), C_PROP)
for k in range(12):
    boxm('PRP_vend_item_%d' % k, (1.98 + (k % 4) * 0.15, IY - 0.70, 0.95 + (k // 4) * 0.25), (0.09, 0.01, 0.16), pmat('M_item_%d' % k, [(0.2, 0.5, 0.9), (0.95, 0.75, 0.2), (0.3, 0.75, 0.45), (0.9, 0.35, 0.55)][k % 4], rough=0.4), C_PROP)
clock = cylm('PRP_clock', (-1.9, IY - 0.03, 2.3), 0.16, 0.04, m_white, C_PROP, rot=(math.radians(90), 0, 0))
# folding table + baskets + chairs + wet-floor sign + extinguisher (Poly Haven models)
boxm('PRP_table_top', (0.2, 4.7, 0.9), (1.4, 0.7, 0.04), pmat('M_table', (0.80, 0.80, 0.78), rough=0.45, wear=0.7), C_PROP, bev=0.008)
for dx in (-0.62, 0.62):
    for dy in (-0.28, 0.28):
        cylm('PRP_table_leg_%d_%d' % (int(dx * 10), int(dy * 10)), (0.2 + dx, 4.7 + dy, 0.52), 0.015, 0.72, m_chrome, C_PROP, seg=12)
with bpy.data.libraries.load(os.path.join(AS, 'ph_models.blend'), link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
PH = {o.name: o for o in dst.objects if o is not None}


def place(name, loc, rotz=0, scale=1.0, newname=None):
    src = PH[name]
    o = src.copy(); o.data = src.data
    C_PROP.objects.link(o); o.location = loc; o.rotation_euler = (0, 0, math.radians(rotz)); o.scale = (scale,) * 3
    if newname:
        o.name = newname
    return o


place('plastic_crate_01', (0.0, 4.65, 0.92 + 0.0), 12, newname='PRP_basket_a')
place('plastic_crate_01', (0.55, 4.75, 0.92), -20, newname='PRP_basket_b')
place('plastic_monobloc_chair_01', (-1.0, 5.4, ZF), 160, newname='PRP_chair_a')
place('plastic_monobloc_chair_01', (1.3, 5.2, ZF), -150, newname='PRP_chair_b')
place('WetFloorSign_01', (0.7, 2.4, ZF), 25, newname='PRP_wetfloor')
place('korean_fire_extinguisher_01', (-2.55, 5.6, ZF), 70, newname='PRP_extinguisher')
place('cardboard_box_01', (2.4, 5.3, ZF), 10, 0.8, newname='PRP_box')
place('potted_plant_02_pot', (-2.35, 0.45, ZF), 0, newname='PRP_plant_pot')
place('potted_plant_02_dirt', (-2.35, 0.45, ZF), 0, newname='PRP_plant_dirt')
place('potted_plant_02_leaves', (-2.35, 0.45, ZF), 0, newname='PRP_plant_leaves')
place('utility_box_01_box_low', (3.4, -0.32, 0.12), 180, newname='PRP_utility_box')
plane('PRP_floor_sticker', (0.0, 0.7, ZF + 0.002), 0.5, 0.5, print_mat('M_floor_sticker', os.path.join(TX, 'floor_sticker.png'), rough=0.5), C_PROP, rot=(0, 0, 0))
# detergent bottles on the shelf
for k in range(7):
    cylm('PRP_bottle_%d' % k, (2.45, 1.2 + k * 0.42, 1.76), 0.06, 0.24, pmat('M_bottle_%d' % k, [(0.15, 0.45, 0.85), (0.95, 0.95, 0.95), (0.95, 0.55, 0.2)][k % 3], rough=0.3, coat=0.5), C_PROP, seg=24, r2=0.05)
# clothes in the folding baskets / one hanging on chair
CLOTH_COLS = [(0.75, 0.15, 0.15), (0.12, 0.25, 0.55), (0.9, 0.85, 0.7), (0.2, 0.45, 0.3), (0.85, 0.55, 0.65), (0.35, 0.35, 0.38)]


def clothblob(name, c, r, col, seed, coll_=C_PROP):
    me = bpy.data.meshes.new(name); b = bmesh.new(); bmesh.ops.create_icosphere(b, subdivisions=3, radius=r)
    rr = random.Random(seed)
    ph = [rr.uniform(0, 6.28) for _ in range(6)]
    for v in b.verts:
        n_ = v.co.normalized()
        k = 1 + 0.22 * math.sin(7 * n_.x + ph[0]) * math.cos(6 * n_.y + ph[1]) + 0.12 * math.sin(13 * n_.z + ph[2]) + 0.06 * math.sin(23 * n_.x + 17 * n_.y + ph[3])
        v.co = Vector((v.co.x * k * 1.25, v.co.y * k, v.co.z * k * 0.7))
    b.to_mesh(me); b.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    o = bpy.data.objects.new(name, me); coll_.objects.link(o); o.location = c
    m_ = bpy.data.materials.get('M_cloth_%d' % CLOTH_COLS.index(col))
    if not m_:
        m_ = bpy.data.materials.new('M_cloth_%d' % CLOTH_COLS.index(col)); m_.use_nodes = True; nt = m_.node_tree; p_ = nt.nodes['Principled BSDF']
        p_.inputs['Base Color'].default_value = (*col, 1); p_.inputs['Roughness'].default_value = 0.85
        p_.inputs['Sheen Weight'].default_value = 0.6; p_.inputs['Sheen Tint'].default_value = (1, 1, 1, 1)
        wv = node(nt, 'ShaderNodeTexWave', Scale=180.0, Distortion=2.0); bp = node(nt, 'ShaderNodeBump', Strength=0.15)
        nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs[0], p_.inputs['Normal'])
    setmat(o, m_)
    md = o.modifiers.new('Sub', 'SUBSURF'); md.levels = 1; md.render_levels = 2
    return o


for k in range(5):
    clothblob('PRP_basket_cloth_%d' % k, (0.0 + (k % 3 - 1) * 0.08, 4.65 + (k // 3 - 0.5) * 0.12, 1.12 + 0.05 * (k % 2)), 0.11, CLOTH_COLS[k % 6], 70 + k)
# bench with a laundry bag, trash bin, price board on the right wall, CCTV dome
boxm('PRP_bench_seat', (-1.25, 2.6, 0.58), (0.42, 1.8, 0.05), pmat('M_bench_wood', (0.45, 0.30, 0.18), rough=0.5, wear=0.9, edge=(0.7, 0.6, 0.5)), C_PROP, bev=0.01)
for dy in (-0.75, 0.75):
    boxm('PRP_bench_leg_%d' % int(dy * 10), (-1.25, 2.6 + dy, 0.37), (0.38, 0.05, 0.42), m_alu, C_PROP, bev=0.005)
clothblob('PRP_laundry_bag', (-1.25, 2.2, 0.78), 0.2, CLOTH_COLS[1], 900)
clothblob('PRP_laundry_bag2', (-1.22, 2.55, 0.74), 0.15, CLOTH_COLS[2], 901)
cylm('PRP_trash', (2.45, 0.55, 0.52), 0.2, 0.72, pmat('M_trash', (0.18, 0.42, 0.30), rough=0.4, wear=0.8), C_PROP, seg=32)
plane('PRP_price_board', (2.785, 2.6, 2.25), 1.6, 0.5, print_mat('M_price_board', os.path.join(TX, 'sign_face.png'), rough=0.3, coat=0.4), C_PROP, rot=(math.radians(90), 0, math.radians(90)))
cylm('PRP_cctv', (1.8, 0.5, 2.76), 0.08, 0.08, m_black, C_PROP, seg=24, r2=0.05)
# clothes tumbling inside the spinning dryer(s) + a resting load in some others
SPIN = [(DRUMS[2], 0.5), (DRUMS[5], -0.35)]   # (drum entry, revs per second)
bpy.context.view_layer.update()
for (dr_, kind, i, lv, dz_), rps in SPIN:
    for k in range(6):
        a = k * 2 * math.pi / 6 + 0.4
        rr_ = 0.12 + 0.06 * (k % 2)
        cb = clothblob('MAC_cloth_%s_%d' % (dr_.name, k), (dr_.location.x - 0.2 + 0.05 * (k % 3), dr_.location.y + math.cos(a) * rr_, dz_ + math.sin(a) * rr_), 0.09, CLOTH_COLS[(k + i) % 6], 200 + k + i * 10, C_MAC)
        cb.parent = dr_; cb.matrix_parent_inverse = dr_.matrix_world.inverted()
for (dr_, kind, i, lv, dz_) in [DRUMS[0], DRUMS[7], DRUMS[9]]:
    for k in range(3):
        clothblob('MAC_rest_%s_%d' % (dr_.name, k), (dr_.location.x - 0.25 + 0.06 * k, dr_.location.y + 0.05 * (k - 1), dz_ - 0.14 + 0.04 * k), 0.1, CLOTH_COLS[(k * 2 + i) % 6], 300 + k + i, C_MAC)

# ---------------- LIGHTS ----------------
m_tube = bpy.data.materials.new('M_fluoro_tube'); m_tube.use_nodes = True
tnt = m_tube.node_tree; tnt.nodes.clear(); te = node(tnt, 'ShaderNodeEmission'); te.inputs[0].default_value = (1.0, 0.97, 0.88, 1); te.inputs[1].default_value = 9.0
to = node(tnt, 'ShaderNodeOutputMaterial'); tnt.links.new(te.outputs[0], to.inputs[0])
m_tube_flk = m_tube.copy(); m_tube_flk.name = 'M_fluoro_tube_flicker'
FIX = []
for r_, x in enumerate((-1.05, 1.05)):
    for j, y in enumerate((1.3, 3.1, 4.9)):
        fx = boxm('LGT_fixture_%d%d' % (r_, j), (x, y, 2.79), (0.32, 1.3, 0.05), m_grey, C_LGT, bev=0.006)
        flk = (r_ == 0 and j == 1)
        tb = cylm('LGT_tube_%d%d' % (r_, j), (x, y, 2.745), 0.016, 1.22, m_tube_flk if flk else m_tube, C_LGT, rot=(math.radians(90), 0, 0), seg=16)
        tb2 = cylm('LGT_tube_%d%db' % (r_, j), (x + 0.08, y, 2.745), 0.016, 1.22, m_tube_flk if flk else m_tube, C_LGT, rot=(math.radians(90), 0, 0), seg=16)
        al = area('LGT_area_%d%d' % (r_, j), (x, y, 2.70), (x, y, 0), energy=P['int_light'], size=0.3, size_y=1.25, color=(1.0, 0.93, 0.80))
        move_to(al, C_LGT); al.visible_camera = False; al.data.spread = math.radians(150)
        FIX.append((al, flk))
fill_in = area('LGT_bounce_fill', (0, 3.2, 1.4), (0, 3.2, 0), energy=P['int_light'] * 0.6, size=4.5, size_y=5.0, color=(1.0, 0.93, 0.80))
move_to(fill_in, C_LGT); fill_in.visible_camera = False; fill_in.visible_glossy = False
street = spot('LGT_streetlamp', (-7.5, -5.5, 6.8), (-0.5, -1.5, 0), energy=P['street'], angle=75, blend=0.6, color=(0.50, 0.68, 1.0), radius=0.25)
move_to(street, C_LGT)
signL = area('LGT_sign_spill', (0, -0.6, 2.95), (0, -1.6, 0), energy=P['sign'] * 30, size=5.4, size_y=0.3, color=(0.88, 0.93, 1.0))
move_to(signL, C_LGT); signL.visible_camera = False; signL.visible_glossy = False
rimL = area('LGT_far_cold', (6, -12, 3.0), (0, 0, 1), energy=180, size=4, color=(0.45, 0.62, 1.0))
move_to(rimL, C_LGT); rimL.visible_camera = False
w = world((0.0012, 0.0020, 0.0045), 1.0)

# ---------------- WET: puddles, ripples, sheen on asphalt + pavement ----------------
def wet(m, puddle_scale, thresh, darken, ripple=True):
    nt = m.node_tree; p = nt.nodes['Principled BSDF']
    tc = node(nt, 'ShaderNodeTexCoord')
    nz = node(nt, 'ShaderNodeTexNoise', Scale=puddle_scale, Detail=6.0, Roughness=0.6); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    pm = node(nt, 'ShaderNodeMapRange', **{'From Min': thresh, 'From Max': thresh + 0.04}); nt.links.new(nz.outputs['Fac'], pm.inputs['Value'])
    # roughness: wet film everywhere (0.18 + texture*0.25), mirror in puddles
    rin = p.inputs['Roughness'].links[0].from_socket if p.inputs['Roughness'].links else None
    rm = node(nt, 'ShaderNodeMapRange', **{'To Min': 0.10, 'To Max': 0.38})
    if rin:
        nt.links.new(rin, rm.inputs['Value'])
    mixr = node(nt, 'ShaderNodeMix'); mixr.data_type = 'FLOAT'; nt.links.new(pm.outputs[0], mixr.inputs[0]); nt.links.new(rm.outputs[0], mixr.inputs[2]); mixr.inputs[3].default_value = 0.015
    nt.links.new(mixr.outputs[0], p.inputs['Roughness'])
    cin = p.inputs['Base Color'].links[0].from_socket
    dk = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY'); dk.inputs[0].default_value = 1.0; dk.inputs[7].default_value = (darken, darken, darken, 1)
    nt.links.new(cin, dk.inputs[6])
    pc = node(nt, 'ShaderNodeMix', data_type='RGBA'); nt.links.new(pm.outputs[0], pc.inputs[0]); nt.links.new(dk.outputs[2], pc.inputs[6]); pc.inputs[7].default_value = (0.01, 0.011, 0.012, 1)
    nt.links.new(pc.outputs[2], p.inputs['Base Color'])
    p.inputs['Specular IOR Level'].default_value = 0.6
    if ripple:   # rain ripples: expanding rings per Voronoi cell, phase driven by time
        tv = node(nt, 'ShaderNodeValue'); tv.name = 'TIME'
        fc = tv.outputs[0].driver_add('default_value'); fc.driver.expression = 'frame/24'
        total = None
        for scale_, spd, seed_ in ((9.0, 1.3, 0.0), (15.0, 1.7, 3.3)):
            vo = node(nt, 'ShaderNodeTexVoronoi', Scale=scale_, Randomness=1.0); vo.voronoi_dimensions = '3D'
            mpp = node(nt, 'ShaderNodeMapping'); mpp.inputs['Location'].default_value = (seed_, seed_, 0)
            nt.links.new(tc.outputs['Object'], mpp.inputs['Vector']); nt.links.new(mpp.outputs[0], vo.inputs['Vector'])
            sc_ = node(nt, 'ShaderNodeSeparateColor'); nt.links.new(vo.outputs['Color'], sc_.inputs[0])
            ph_ = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); nt.links.new(tv.outputs[0], ph_.inputs[0]); ph_.inputs[1].default_value = spd; nt.links.new(sc_.outputs[0], ph_.inputs[2])
            fr = node(nt, 'ShaderNodeMath', operation='FRACT'); nt.links.new(ph_.outputs[0], fr.inputs[0])
            rad = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(fr.outputs[0], rad.inputs[0]); rad.inputs[1].default_value = 0.42
            dif = node(nt, 'ShaderNodeMath', operation='SUBTRACT'); nt.links.new(vo.outputs['Distance'], dif.inputs[0]); nt.links.new(rad.outputs[0], dif.inputs[1])
            sq = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(dif.outputs[0], sq.inputs[0]); sq.inputs[1].default_value = 22.0
            sn_ = node(nt, 'ShaderNodeMath', operation='SINE'); nt.links.new(sq.outputs[0], sn_.inputs[0])
            ga = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(dif.outputs[0], ga.inputs[0]); nt.links.new(dif.outputs[0], ga.inputs[1])
            ge = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(ga.outputs[0], ge.inputs[0]); ge.inputs[1].default_value = -400.0
            ex = node(nt, 'ShaderNodeMath', operation='EXPONENT'); nt.links.new(ge.outputs[0], ex.inputs[0])
            fade = node(nt, 'ShaderNodeMath', operation='SUBTRACT'); fade.inputs[0].default_value = 1.0; nt.links.new(fr.outputs[0], fade.inputs[1])
            r1 = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(sn_.outputs[0], r1.inputs[0]); nt.links.new(ex.outputs[0], r1.inputs[1])
            r2 = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(r1.outputs[0], r2.inputs[0]); nt.links.new(fade.outputs[0], r2.inputs[1])
            if total is None:
                total = r2
            else:
                ad = node(nt, 'ShaderNodeMath', operation='ADD'); nt.links.new(total.outputs[0], ad.inputs[0]); nt.links.new(r2.outputs[0], ad.inputs[1]); total = ad
        wm_ = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(total.outputs[0], wm_.inputs[0]); nt.links.new(pm.outputs[0], wm_.inputs[1])
        wm2 = node(nt, 'ShaderNodeMath', operation='MULTIPLY_ADD'); nt.links.new(wm_.outputs[0], wm2.inputs[0]); wm2.inputs[1].default_value = 0.8; wm2.inputs[2].default_value = 0.0
        bpn = node(nt, 'ShaderNodeBump', Strength=0.35, Distance=0.002); nt.links.new(wm2.outputs[0], bpn.inputs['Height'])
        nin = p.inputs['Normal'].links[0].from_socket if p.inputs['Normal'].links else None
        if nin:
            nt.links.new(nin, bpn.inputs['Normal'])
        nt.links.new(bpn.outputs[0], p.inputs['Normal'])


if STAGE >= 3:
    wet(m_asph, 0.55, 0.47, 0.5)
    wet(m_pave, 0.9, 0.50, 0.55)

# ---------------- glass drops (outside of the storefront) ----------------
if STAGE >= 3:
    nt = m_glass.node_tree; p = nt.nodes['Principled BSDF']; tc = node(nt, 'ShaderNodeTexCoord')
    vo = node(nt, 'ShaderNodeTexVoronoi', Scale=55.0); vo.feature = 'SMOOTH_F1' if False else 'F1'
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    sc_ = node(nt, 'ShaderNodeSeparateColor'); nt.links.new(vo.outputs['Color'], sc_.inputs[0])
    keep = node(nt, 'ShaderNodeMath', operation='GREATER_THAN'); nt.links.new(sc_.outputs[0], keep.inputs[0]); keep.inputs[1].default_value = 0.80
    dd = node(nt, 'ShaderNodeMapRange', **{'From Min': 0.32, 'From Max': 0.0}); nt.links.new(vo.outputs['Distance'], dd.inputs['Value'])
    sq = node(nt, 'ShaderNodeMath', operation='POWER'); nt.links.new(dd.outputs[0], sq.inputs[0]); sq.inputs[1].default_value = 0.5
    hm = node(nt, 'ShaderNodeMath', operation='MULTIPLY'); nt.links.new(sq.outputs[0], hm.inputs[0]); nt.links.new(keep.outputs[0], hm.inputs[1])
    # streaks (stretched noise, sliding down slowly)
    mp = node(nt, 'ShaderNodeMapping'); mp.inputs['Scale'].default_value = (60, 60, 3); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    fcv = mp.inputs['Location'].driver_add('default_value', 2); fcv.driver.expression = 'frame*0.004'
    ns = node(nt, 'ShaderNodeTexNoise', Scale=4.0, Detail=2.0); nt.links.new(mp.outputs[0], ns.inputs['Vector'])
    st = node(nt, 'ShaderNodeMapRange', **{'From Min': 0.62, 'From Max': 0.70}); nt.links.new(ns.outputs['Fac'], st.inputs['Value'])
    ad = node(nt, 'ShaderNodeMath', operation='MAXIMUM'); nt.links.new(hm.outputs[0], ad.inputs[0]); nt.links.new(st.outputs[0], ad.inputs[1])
    bp_ = node(nt, 'ShaderNodeBump', Strength=0.25, Distance=0.0008); nt.links.new(ad.outputs[0], bp_.inputs['Height']); nt.links.new(bp_.outputs[0], p.inputs['Normal'])

# ---------------- RAIN (geometry nodes, deterministic per frame) + FOG ----------------
def rain_tree(name, n, box_min, box_max, speed=7.5, wind=(1.2, 0.4), length=0.30, radius=0.0011):
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nt = ng; out = nt.nodes.new('NodeGroupOutput')
    pts = nt.nodes.new('GeometryNodePoints'); pts.inputs['Count'].default_value = n
    rv = nt.nodes.new('FunctionNodeRandomValue'); rv.data_type = 'FLOAT_VECTOR'
    rv.inputs['Min'].default_value = (*box_min,); rv.inputs['Max'].default_value = (*box_max,)
    st = nt.nodes.new('GeometryNodeSetPosition'); nt.links.new(pts.outputs[0], st.inputs['Geometry'])
    # z = zmin + mod(z0 - t*speed, H); x += wind_x * fall time
    tm = nt.nodes.new('GeometryNodeInputSceneTime')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(rv.outputs['Value'], sep.inputs[0])
    H = box_max[2] - box_min[2]
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; nt.links.new(tm.outputs['Seconds'], m1.inputs[0]); m1.inputs[1].default_value = speed
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'SUBTRACT'; nt.links.new(sep.outputs['Z'], m2.inputs[0]); nt.links.new(m1.outputs[0], m2.inputs[1])
    m2b = nt.nodes.new('ShaderNodeMath'); m2b.operation = 'SUBTRACT'; nt.links.new(m2.outputs[0], m2b.inputs[0]); m2b.inputs[1].default_value = box_min[2]
    m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'FLOORED_MODULO'; nt.links.new(m2b.outputs[0], m3.inputs[0]); m3.inputs[1].default_value = H
    m4 = nt.nodes.new('ShaderNodeMath'); m4.operation = 'ADD'; nt.links.new(m3.outputs[0], m4.inputs[0]); m4.inputs[1].default_value = box_min[2]
    # wind drift proportional to height
    wx = nt.nodes.new('ShaderNodeMath'); wx.operation = 'MULTIPLY_ADD'; nt.links.new(m4.outputs[0], wx.inputs[0]); wx.inputs[1].default_value = -wind[0] / speed; nt.links.new(sep.outputs['X'], wx.inputs[2])
    wy = nt.nodes.new('ShaderNodeMath'); wy.operation = 'MULTIPLY_ADD'; nt.links.new(m4.outputs[0], wy.inputs[0]); wy.inputs[1].default_value = -wind[1] / speed; nt.links.new(sep.outputs['Y'], wy.inputs[2])
    cmb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(wx.outputs[0], cmb.inputs[0]); nt.links.new(wy.outputs[0], cmb.inputs[1]); nt.links.new(m4.outputs[0], cmb.inputs[2])
    nt.links.new(cmb.outputs[0], st.inputs['Position'])
    cyl_ = nt.nodes.new('GeometryNodeMeshCylinder'); cyl_.inputs['Vertices'].default_value = 5; cyl_.inputs['Radius'].default_value = radius; cyl_.inputs['Depth'].default_value = length
    inst = nt.nodes.new('GeometryNodeInstanceOnPoints'); nt.links.new(st.outputs[0], inst.inputs['Points']); nt.links.new(cyl_.outputs['Mesh'], inst.inputs['Instance'])
    ang = math.atan2(wind[0], speed); angy = math.atan2(wind[1], speed)
    inst.inputs['Rotation'].default_value = (angy, -ang, 0)
    sm = nt.nodes.new('GeometryNodeSetMaterial'); nt.links.new(inst.outputs[0], sm.inputs['Geometry'])
    nt.links.new(sm.outputs[0], out.inputs[0])
    return ng, sm


if STAGE >= 4:
    rm_ = bpy.data.materials.new('M_rain'); rm_.use_nodes = True; rnt = rm_.node_tree; rnt.nodes.clear()
    ro = node(rnt, 'ShaderNodeOutputMaterial'); tr = node(rnt, 'ShaderNodeBsdfTransparent'); gl_ = node(rnt, 'ShaderNodeBsdfGlossy', Roughness=0.05)
    em_ = node(rnt, 'ShaderNodeEmission'); em_.inputs[0].default_value = (0.85, 0.92, 1.0, 1)
    # brighter near the lit storefront (world y close to 0)
    gm = node(rnt, 'ShaderNodeNewGeometry'); sp_ = node(rnt, 'ShaderNodeSeparateXYZ'); rnt.links.new(gm.outputs['Position'], sp_.inputs[0])
    nearness = node(rnt, 'ShaderNodeMapRange', **{'From Min': -4.5, 'From Max': -0.3, 'To Min': 0.02, 'To Max': 0.35}); rnt.links.new(sp_.outputs['Y'], nearness.inputs['Value'])
    rnt.links.new(nearness.outputs[0], em_.inputs['Strength'])
    ad_ = node(rnt, 'ShaderNodeAddShader'); rnt.links.new(em_.outputs[0], ad_.inputs[0]); rnt.links.new(gl_.outputs[0], ad_.inputs[1])
    mx_ = node(rnt, 'ShaderNodeMixShader'); mx_.inputs[0].default_value = 0.78; rnt.links.new(tr.outputs[0], mx_.inputs[1]); rnt.links.new(ad_.outputs[0], mx_.inputs[2])
    rnt.links.new(mx_.outputs[0], ro.inputs['Surface'])
    for nm, n, bmin, bmax, kw in (('FX_rain_near', P['rain_n'], (-5.0, -5.0, 0.0), (5.0, -0.8, 4.2), {}),
                                  ('FX_sign_drips', 70, (-2.85, -0.37, 0.12), (2.85, -0.34, 2.68), dict(speed=5.5, wind=(0.0, 0.0), length=0.09, radius=0.0016))):
        ng, sm = rain_tree('GN_' + nm, n, bmin, bmax, **kw)
        sm.inputs['Material'].default_value = rm_
        me = bpy.data.meshes.new(nm); o = bpy.data.objects.new(nm, me); C_FX.objects.link(o)
        md = o.modifiers.new('Rain', 'NODES'); md.node_group = ng
        o.visible_shadow = False
    # fog: exterior haze volume (glow around the sign and street lamp)
    if P['fog'] > 0:
        fog = boxm('FX_fog', (0, -4.0, 2.6), (18, 8.0, 5.2), None, C_FX)
        fm = bpy.data.materials.new('M_fog'); fm.use_nodes = True; fnt = fm.node_tree; fnt.nodes.clear()
        pv = node(fnt, 'ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = P['fog']; pv.inputs['Anisotropy'].default_value = 0.35
        pv.inputs['Color'].default_value = (0.8, 0.86, 0.95, 1)
        fo = node(fnt, 'ShaderNodeOutputMaterial'); fnt.links.new(pv.outputs[0], fo.inputs['Volume'])
        setmat(fog, fm)

# ---------------- CAMERA ----------------
cam, tgt = camera(loc=(1.35, -6.9, 0.78), target=(-0.25, 3.0, 1.85), lens=24)
cam.name = 'CAM_main'; tgt.name = 'CAM_target'
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = 7.2; cam.data.dof.aperture_fstop = 4.0
cam.data.dof.focus_object = None

# ---------------- ANIMATION ----------------
if STAGE >= 9:
    # slow straight push-in (0.8 m), with a breath of handheld drift
    for f in range(1, NF + 1):
        u = (f - 1) / (NF - 1)
        e = u * u * (3 - 2 * u) * 0.35 + u * 0.65
        cam.location = (1.35 - 0.12 * e + 0.004 * math.sin(f * 0.11), -6.9 + 1.4 * e, 0.78 + 0.03 * e + 0.003 * math.sin(f * 0.07 + 1))
        cam.keyframe_insert('location', frame=f)
        cam.data.dof.focus_distance = 7.2 - 1.4 * e; cam.data.dof.keyframe_insert('focus_distance', frame=f)
    linear_all(cam)
    # dryer drums spin (+ the clothes parented inside tumble with them)
    for (dr_, kind, i, lv, dz_), rps in SPIN:
        r0 = dr_.rotation_euler.copy()
        for f in (1, NF):
            dr_.rotation_euler = (r0.x + 2 * math.pi * rps * (f - 1) / 24, r0.y, r0.z)
            dr_.keyframe_insert('rotation_euler', frame=f)
        linear_all(dr_)
    for (dr_, kind, i, lv, dz_), rps in SPIN:   # tumble: each cloth also lifts and falls inside the drum
        for o in [c for c in dr_.children if c.name.startswith('MAC_cloth')]:
            l0 = o.location.copy(); ph = random.Random(o.name).uniform(0, 6.28)
            for f in range(1, NF + 1, 2):
                o.location = l0 + Vector((0.02 * math.sin(f * 0.21 + ph), 0.03 * math.sin(f * 0.17 + ph * 2), 0.03 * math.cos(f * 0.23 + ph)))
                o.keyframe_insert('location', frame=f)
            linear_all(o)
    # flicker: one fluorescent pair stutters irregularly
    fr_ = random.Random(5)
    em_node = [n for n in m_tube_flk.node_tree.nodes if n.type == 'EMISSION'][0]
    al_flk = [a for a, flk in FIX if flk][0]
    events = []
    f = 6
    while f < NF:
        f += fr_.randint(14, 40)
        burst = fr_.randint(2, 6)
        for k in range(burst):
            events.append((f + k * 2, fr_.choice([0.05, 0.25, 0.6])))
            events.append((f + k * 2 + 1, 1.0))
        f += burst * 2
    vals = {fx: 1.0 for fx in range(1, NF + 1)}
    for fx, v in events:
        if fx <= NF:
            vals[fx] = v
    for fx, v in vals.items():
        em_node.inputs[1].default_value = 9.0 * v; em_node.inputs[1].keyframe_insert('default_value', frame=fx)
        al_flk.data.energy = P['int_light'] * v; al_flk.data.keyframe_insert('energy', frame=fx)
    for idb in (m_tube_flk.node_tree, al_flk.data):
        if idb.animation_data and idb.animation_data.action:
            for fc in tlib._fcurves(idb.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'CONSTANT'
    # the OPEN plate on the door sways in the wind
    for f in range(1, NF + 1, 2):
        hang.rotation_euler = (math.radians(9 * math.sin(f * 0.19) + 4 * math.sin(f * 0.41 + 1)), 0, math.radians(3 * math.sin(f * 0.13)))
        hang.keyframe_insert('rotation_euler', frame=f)
    linear_all(hang)

# ---------------- RENDER SETTINGS ----------------
cycles_setup(NF, spp=P['spp'], thr=0.015, look='AgX - Medium High Contrast', exposure=P['exposure'], bounces=(8, 4, 4, 8), vol=1)
s.cycles.volume_step_rate = 4.0; s.cycles.volume_preview_step_rate = 4.0
s.cycles.sample_clamp_indirect = 6.0
ng = bpy.data.node_groups.get('FinalComp') or bpy.data.node_groups.new('FinalComp', 'CompositorNodeTree')
ng.nodes.clear()
if not ng.interface.items_tree:
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
rl = ng.nodes.new('CompositorNodeRLayers'); g1 = ng.nodes.new('CompositorNodeGlare'); go = ng.nodes.new('NodeGroupOutput')
ng.links.new(rl.outputs['Image'], g1.inputs['Image']); ng.links.new(g1.outputs['Image'], go.inputs[0])
g1.inputs['Type'].default_value = 'Fog Glow'
g1.inputs['Threshold'].default_value = P.get('glow_thr', 0.9); g1.inputs['Strength'].default_value = P.get('glow', 0.35); g1.inputs['Size'].default_value = 8
s.compositing_node_group = ng; s.render.use_compositing = True
s.render.engine = 'BLENDER_EEVEE' if globals().get('LOOKDEV', True) else 'CYCLES'
if STAGE < 4:
    for o in list(C_FX.objects):
        o.hide_render = True
s.frame_set(globals().get('SHOW_FRAME', 1))
viewport_camera('RENDERED')
print('built #1 stage', STAGE, 'objects', len(bpy.data.objects))
