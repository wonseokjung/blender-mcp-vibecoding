# loop_01: "소리가 만든 세계": obsidian ferrofluid eye over a real-spectrogram canyon, every motion from audio analysis.
import bpy, bmesh, math, json, sys
import numpy as np
from mathutils import Vector
sys.path.insert(0, 'scripts')
import importlib, tlib; importlib.reload(tlib)
W = '../_workB'
J = json.load(open(W + '/audio/an/analysis.json')); SP = np.load(W + '/audio/an/spec.npy')
N = J["n"]; FB, FD = J["fbreak"], J["fdrop"]
S = tlib.reset(); S.frame_start, S.frame_end = 1, N; S.render.fps = 24
for ng in list(bpy.data.node_groups): bpy.data.node_groups.remove(ng)
GREEN = (0.0, 1.0, 0.255)

# ---------------- controller: per-frame channels baked as custom props ----------------
kick = np.array(J["kick"]); bass = np.array(J["bass"]); hat = np.array(J["hat"]); drop = np.array(J["drop"]); spd = np.array(J["speed"])
tape = np.concatenate([[0], np.cumsum(spd)[:-1]]) / spd.sum()            # tape[0]=0, tape[N]=1 -> seamless
amp = 0.05 + 0.30*bass + 0.26*kick
amp[FB:FD] = amp[FB]*np.linspace(1, 0.92, FD - FB)                         # bullet time: spikes freeze mid-pulse
amp[FD:] += 0.55*drop[FD:]
pupil = 0.065 + 0.06*kick
pupil[FB:FD] = np.linspace(pupil[FB], 0.045, FD - FB)                       # contracts in the silence
pupil[FD:] += 0.11*drop[FD:]
lights = np.clip(0.15 + 1.6*kick + 0.5*hat, 0, 3); lights[FB:FD] *= np.linspace(1, 0.05, FD - FB); lights[FD:] += 4*drop[FD:]
crack = np.clip(0.25 + 0.9*hat + 0.6*kick, 0, 3); crack[FB:FD] *= 0.1; crack[FD:] += 3*drop[FD:]
ring = 0.0 + 6.0*drop                                                      # wordmark glow (drop only, 0 at the seam)
morph = tape*4.0                                                           # ferrofluid lattice drift (stops in bullet time)
CH = dict(amp=amp, pupil=pupil, lights=lights, crack=crack, ring=ring, morph=morph, tape=tape, kick=kick)
ctrl = bpy.data.objects.new("CTRL", None); S.collection.objects.link(ctrl)
for k, arr in CH.items():
    ctrl[k] = float(arr[0])
    for i, v in enumerate(arr):
        ctrl[k] = float(v); ctrl.keyframe_insert(f'["{k}"]', frame=i + 1)
    ctrl[k] = float(arr[0]); ctrl.keyframe_insert(f'["{k}"]', frame=N + 1)   # seam key = frame 1
for fc in tlib._fcurves(ctrl.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

def drive(owner, path, prop, expr="v", index=-1):
    fc = owner.driver_add(path, index) if index >= 0 else owner.driver_add(path)
    d = fc.driver; d.type = 'SCRIPTED'
    v = d.variables.new(); v.name = "v"; v.type = 'SINGLE_PROP'
    v.targets[0].id = ctrl; v.targets[0].data_path = f'["{prop}"]'
    d.expression = expr
    return fc

# ---------------- render / world ----------------
S.render.engine = 'CYCLES'; S.cycles.device = 'GPU'
S.cycles.samples = 48; S.cycles.use_adaptive_sampling = True; S.cycles.adaptive_threshold = 0.02; S.cycles.use_denoising = True
S.cycles.max_bounces = 8; S.cycles.glossy_bounces = 4; S.cycles.transmission_bounces = 6; S.cycles.diffuse_bounces = 2
S.render.resolution_x, S.render.resolution_y = 1920, 1080
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'
S.render.use_motion_blur = True; S.render.motion_blur_shutter = 0.35
wd = bpy.data.worlds.new("W_loop"); wd.use_nodes = True; S.world = wd
wd.node_tree.nodes["Background"].inputs[0].default_value = (0.0012, 0.0014, 0.0018, 1); wd.node_tree.nodes["Background"].inputs[1].default_value = 1.0

# ---------------- hero: obsidian ferrofluid sphere with an eye ----------------
CEN = Vector((0, 0, 2.3))
me = bpy.data.meshes.new("Hero"); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=7, radius=1.0); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
hero = bpy.data.objects.new("Hero", me); S.collection.objects.link(hero); hero.location = CEN

camd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", camd); S.collection.objects.link(cam); S.camera = cam
camd.sensor_width = 36; camd.lens = 50; camd.clip_start = 0.05; camd.clip_end = 400
tgt = bpy.data.objects.new("CamTarget", None); S.collection.objects.link(tgt); tgt.location = CEN
c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
camd.dof.use_dof = True; camd.dof.focus_object = tgt; camd.dof.aperture_fstop = 2.2

ng = bpy.data.node_groups.new("GN_ferro", 'GeometryNodeTree')
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
Nn, L = ng.nodes, ng.links
gi = Nn.new("NodeGroupInput"); go = Nn.new("NodeGroupOutput")
pos = Nn.new("GeometryNodeInputPosition"); nor = Nn.new("GeometryNodeInputNormal")
vor = Nn.new("ShaderNodeTexVoronoi"); vor.voronoi_dimensions = '4D'; vor.feature = 'F1'
vor.inputs["Scale"].default_value = 6.5; vor.inputs["Randomness"].default_value = 0.75
L.new(pos.outputs[0], vor.inputs["Vector"])
vmorph = Nn.new("ShaderNodeValue"); vmorph.name = "morph"; L.new(vmorph.outputs[0], vor.inputs["W"])
mr = Nn.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.30
mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0
L.new(vor.outputs["Distance"], mr.inputs["Value"])
pw = Nn.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.6; L.new(mr.outputs[0], pw.inputs[0])
oi = Nn.new("GeometryNodeObjectInfo"); oi.transform_space = 'RELATIVE'; oi.inputs["Object"].default_value = cam
cd = Nn.new("ShaderNodeVectorMath"); cd.operation = 'NORMALIZE'; L.new(oi.outputs["Location"], cd.inputs[0])
dt = Nn.new("ShaderNodeVectorMath"); dt.operation = 'DOT_PRODUCT'; L.new(nor.outputs[0], dt.inputs[0]); L.new(cd.outputs[0], dt.inputs[1])
em = Nn.new("ShaderNodeMapRange"); em.inputs["From Min"].default_value = 0.875; em.inputs["From Max"].default_value = 0.935
em.interpolation_type = 'SMOOTHSTEP'; L.new(dt.outputs["Value"], em.inputs["Value"])
inv = Nn.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(em.outputs[0], inv.inputs[1])
vamp = Nn.new("ShaderNodeValue"); vamp.name = "amp"
m1 = Nn.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; L.new(pw.outputs[0], m1.inputs[0]); L.new(vamp.outputs[0], m1.inputs[1])
m2 = Nn.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(inv.outputs[0], m2.inputs[1])
# eye area sinks slightly (socket for the iris)
sink = Nn.new("ShaderNodeMath"); sink.operation = 'MULTIPLY_ADD'; L.new(em.outputs[0], sink.inputs[0]); sink.inputs[1].default_value = -0.045; L.new(m2.outputs[0], sink.inputs[2])
off = Nn.new("ShaderNodeVectorMath"); off.operation = 'SCALE'; L.new(nor.outputs[0], off.inputs[0]); L.new(sink.outputs[0], off.inputs["Scale"])
sp = Nn.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], sp.inputs["Geometry"]); L.new(off.outputs[0], sp.inputs["Offset"])
st = Nn.new("GeometryNodeStoreNamedAttribute"); st.data_type = 'FLOAT'; st.inputs["Name"].default_value = "eyemask"
L.new(sp.outputs[0], st.inputs["Geometry"]); L.new(em.outputs[0], st.inputs["Value"])
st2 = Nn.new("GeometryNodeStoreNamedAttribute"); st2.data_type = 'FLOAT'; st2.inputs["Name"].default_value = "spike"
L.new(st.outputs[0], st2.inputs["Geometry"]); L.new(pw.outputs[0], st2.inputs["Value"])
L.new(st2.outputs[0], go.inputs[0])
md = hero.modifiers.new("ferro", 'NODES'); md.node_group = ng
drive(vamp.outputs[0], "default_value", "amp"); drive(vmorph.outputs[0], "default_value", "morph")

# obsidian + thin-film; clear cornea where eyemask=1
mh = bpy.data.materials.new("M_obsidian"); mh.use_nodes = True; nt = mh.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
pb = nt.nodes.new("ShaderNodeBsdfPrincipled")
pb.inputs["Base Color"].default_value = (0.004, 0.0045, 0.005, 1); pb.inputs["Roughness"].default_value = 0.06
pb.inputs["Coat Weight"].default_value = 1.0; pb.inputs["Coat Roughness"].default_value = 0.02
try:
    pb.inputs["Thin Film Thickness"].default_value = 380; pb.inputs["Thin Film IOR"].default_value = 1.4
except Exception: pass
at_sp = nt.nodes.new("ShaderNodeAttribute"); at_sp.attribute_name = "spike"
rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.05; rr.inputs["To Max"].default_value = 0.16
nt.links.new(at_sp.outputs["Fac"], rr.inputs["Value"]); nt.links.new(rr.outputs[0], pb.inputs["Roughness"])
glass = nt.nodes.new("ShaderNodeBsdfPrincipled"); glass.inputs["Transmission Weight"].default_value = 1.0
glass.inputs["Roughness"].default_value = 0.0; glass.inputs["IOR"].default_value = 1.376; glass.inputs["Base Color"].default_value = (1, 1, 1, 1)
at_e = nt.nodes.new("ShaderNodeAttribute"); at_e.attribute_name = "eyemask"
gm = nt.nodes.new("ShaderNodeMapRange"); gm.inputs["From Min"].default_value = 0.55; gm.inputs["From Max"].default_value = 0.95
nt.links.new(at_e.outputs["Fac"], gm.inputs["Value"])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(gm.outputs[0], mx.inputs[0]); nt.links.new(pb.outputs[0], mx.inputs[1]); nt.links.new(glass.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], out.inputs[0])
hero.data.materials.append(mh)

# eye assembly: aim empty at the centre tracks the camera; iris disc just under the clear cornea
aim = bpy.data.objects.new("EyeAim", None); S.collection.objects.link(aim); aim.location = CEN
dc = aim.constraints.new('DAMPED_TRACK'); dc.target = cam; dc.track_axis = 'TRACK_Z'
me = bpy.data.meshes.new("Iris"); bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=True, segments=128, radius=0.43)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
bm.to_mesh(me); bm.free()
for v in me.vertices:                                     # shallow cone: pupil deeper
    r = math.hypot(v.co.x, v.co.y); v.co.z = -0.04*(1 - r/0.43)
iris = bpy.data.objects.new("Iris", me); S.collection.objects.link(iris); iris.parent = aim; iris.location = (0, 0, 0.885)
mi = bpy.data.materials.new("M_iris"); mi.use_nodes = True; nt = mi.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
tc = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
def M(op, a=None, b=None, v1=None):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op
    if a is not None: nt.links.new(a, n.inputs[0])
    if b is not None: nt.links.new(b, n.inputs[1])
    if v1 is not None: n.inputs[1].default_value = v1
    return n.outputs[0]
r = M('SQRT', M('ADD', M('MULTIPLY', sx.outputs["X"], sx.outputs["X"]), M('MULTIPLY', sx.outputs["Y"], sx.outputs["Y"])))
ang = M('ARCTAN2', sx.outputs["Y"], sx.outputs["X"])
u = M('SUBTRACT', None, M('DIVIDE', ang, None, 2*math.pi)); nt.links[-1].to_node.inputs[0].default_value = 0.5 if False else 0.5
un = [n for n in nt.nodes if n.type == 'MATH' and n.operation == 'SUBTRACT'][-1]; un.inputs[0].default_value = 0.5
cv = nt.nodes.new("ShaderNodeCombineXYZ")
nt.links.new(M('MULTIPLY', ang, None, 30.0), cv.inputs["X"]); nt.links.new(M('MULTIPLY', r, None, 9.0), cv.inputs["Y"])
fib = nt.nodes.new("ShaderNodeTexNoise"); fib.inputs["Scale"].default_value = 1.0; fib.inputs["Detail"].default_value = 10; fib.inputs["Roughness"].default_value = 0.7
fib.noise_dimensions = '2D'; nt.links.new(cv.outputs[0], fib.inputs["Vector"])
cr = nt.nodes.new("ShaderNodeValToRGB"); el = cr.color_ramp.elements
el[0].position = 0.35; el[0].color = (0.008, 0.009, 0.011, 1); el[1].position = 0.8; el[1].color = (0.22, 0.26, 0.29, 1)
nt.links.new(fib.outputs["Fac"], cr.inputs[0])
vpup = nt.nodes.new("ShaderNodeValue"); vpup.name = "pupil"; drive(vpup.outputs[0], "default_value", "pupil")
pmask = nt.nodes.new("ShaderNodeMapRange"); pmask.interpolation_type = 'SMOOTHSTEP'
nt.links.new(r, pmask.inputs["Value"]); nt.links.new(vpup.outputs[0], pmask.inputs["From Min"])
nt.links.new(M('ADD', vpup.outputs[0], None, 0.012), pmask.inputs["From Max"])        # 0 inside pupil -> 1 iris
limb = nt.nodes.new("ShaderNodeMapRange"); limb.inputs["From Min"].default_value = 0.33; limb.inputs["From Max"].default_value = 0.42
limb.inputs["To Min"].default_value = 1.0; limb.inputs["To Max"].default_value = 0.0; nt.links.new(r, limb.inputs["Value"])
lum = M('MULTIPLY', pmask.outputs[0], limb.outputs[0])
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = 'RGBA'; nt.links.new(lum, mixc.inputs["Factor"])
mixc.inputs[6].default_value = (0.0, 0.0, 0.0, 1); nt.links.new(cr.outputs[0], mixc.inputs[7])
pbi = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(mixc.outputs[2], pbi.inputs["Base Color"])
pbi.inputs["Metallic"].default_value = 0.85; pbi.inputs["Roughness"].default_value = 0.32
# ring wordmark (etched; glows green on the drop)
img = bpy.data.images.load(W + '/assets/iris_ring_text.png', check_existing=True); img.colorspace_settings.name = 'Non-Color'
R0, R1 = 0.195, 0.262
vr = M('DIVIDE', M('SUBTRACT', r, None, R0), None, R1 - R0)
uvc = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(un.outputs[0], uvc.inputs["X"]); nt.links.new(vr, uvc.inputs["Y"])
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = img; ti.extension = 'CLIP'; ti.interpolation = 'Cubic'
nt.links.new(uvc.outputs[0], ti.inputs["Vector"])
etch = M('MULTIPLY', ti.outputs["Color"], pmask.outputs[0])
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6; bump.inputs["Distance"].default_value = 0.002
nt.links.new(M('ADD', M('MULTIPLY', fib.outputs["Fac"], None, 0.3), M('MULTIPLY', etch, None, -1.0)), bump.inputs["Height"]); nt.links.new(bump.outputs[0], pbi.inputs["Normal"])
vring = nt.nodes.new("ShaderNodeValue"); vring.name = "ring"; drive(vring.outputs[0], "default_value", "ring")
pbi.inputs["Emission Color"].default_value = (*GREEN, 1)
nt.links.new(M('ADD', M('MULTIPLY', etch, vring.outputs[0]), M('MULTIPLY', etch, None, 0.0)), pbi.inputs["Emission Strength"])
# etched letters slightly brighter metal even when dark
nt.links.new(pbi.outputs[0], out.inputs[0])
iris.data.materials.append(mi)

# ---------------- canyon: the real spectrogram as terrain (3 tiles, scrolls with the tape clock) ----------------
spec = SP.copy()
for b in range(spec.shape[0]):                       # fill empty low bands (FFT bins sparser than bands)
    if spec[b].max() < 1e-6:
        nb = [k for k in range(spec.shape[0]) if spec[k].max() > 1e-6]
        j = min(nb, key=lambda k: abs(k - b)); spec[b] = spec[j]
def blur1(a, sig, axis, wrap):
    k = np.exp(-0.5*(np.arange(-4, 5)/sig)**2); k /= k.sum()
    pad = np.pad(a, [(4, 4) if ax == axis else (0, 0) for ax in range(a.ndim)], mode='wrap' if wrap else 'edge')
    return np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), axis, pad)
spec = blur1(blur1(spec, 1.2, 0, False), 1.0, 1, True)
TL = 48.0; HW = 16.0; NB = spec.shape[0]
nx = 2*NB + 1; ny = N
xs = np.linspace(-HW, HW, nx); ax = np.abs(xs)/HW
band = np.clip(((1 - ax)*(NB - 1)).round().astype(int), 0, NB - 1)    # centre = high freq, edges = sub bass
Z = np.zeros((3*ny, nx))
for t in range(3):
    for j in range(ny):
        v = spec[band, j]
        Z[t*ny + j] = 0.12*v + (v**1.7)*(0.25 + 5.2*ax**1.6)
ysv = np.arange(3*ny)*(TL/ny) - TL
X, Y = np.meshgrid(xs, ysv)
rng = np.random.default_rng(3)
verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
idx = np.arange(3*ny*nx).reshape(3*ny, nx)
f = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
me = bpy.data.meshes.new("Canyon")
me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel().astype(np.float32))
me.loops.add(f.size); me.loops.foreach_set("vertex_index", f.ravel().astype(np.int32))
me.polygons.add(len(f)); me.polygons.foreach_set("loop_start", (np.arange(len(f))*4).astype(np.int32))
me.update(); me.validate()
for p in me.polygons: p.use_smooth = True
hfrow = spec[int(NB*0.75):].mean(0); hfrow = (hfrow - hfrow.min())/(np.ptp(hfrow) + 1e-9)
at = me.attributes.new("hf", 'FLOAT', 'POINT'); at.data.foreach_set("value", np.repeat(np.tile(hfrow, 3), nx).astype(np.float32))
canyon = bpy.data.objects.new("Canyon", me); S.collection.objects.link(canyon)
sub = canyon.modifiers.new("sub", 'SUBSURF'); sub.levels = 1; sub.render_levels = 1
mc = bpy.data.materials.new("M_canyon"); mc.use_nodes = True; nt = mc.node_tree
pc = nt.nodes["Principled BSDF"]; pc.inputs["Base Color"].default_value = (0.006, 0.0065, 0.007, 1); pc.inputs["Roughness"].default_value = 0.18
pc.inputs["Coat Weight"].default_value = 0.6
tcx = nt.nodes.new("ShaderNodeTexCoord")
vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs["Scale"].default_value = 0.55
nt.links.new(tcx.outputs["Object"], vo.inputs["Vector"])
ce = nt.nodes.new("ShaderNodeMapRange"); ce.inputs["From Min"].default_value = 0.0; ce.inputs["From Max"].default_value = 0.035
ce.inputs["To Min"].default_value = 1.0; ce.inputs["To Max"].default_value = 0.0; nt.links.new(vo.outputs["Distance"], ce.inputs["Value"])
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.0; nz.inputs["Detail"].default_value = 8
nt.links.new(tcx.outputs["Object"], nz.inputs["Vector"])
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35
nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs[0], pc.inputs["Normal"])
ah = nt.nodes.new("ShaderNodeAttribute"); ah.attribute_name = "hf"
sepc = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tcx.outputs["Object"], sepc.inputs[0])
valley = nt.nodes.new("ShaderNodeMapRange"); valley.inputs["From Min"].default_value = 1.6; valley.inputs["From Max"].default_value = 0.2
nt.links.new(sepc.outputs["Z"], valley.inputs["Value"])            # cracks only low in the valley
def MM(op, a, b=None, v=None):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op; nt.links.new(a, n.inputs[0])
    if b is not None: nt.links.new(b, n.inputs[1])
    if v is not None: n.inputs[1].default_value = v
    return n.outputs[0]
vcr = nt.nodes.new("ShaderNodeValue"); vcr.name = "crack"; drive(vcr.outputs[0], "default_value", "crack")
emis = MM('MULTIPLY', MM('MULTIPLY', MM('MULTIPLY', ce.outputs[0], valley.outputs[0]), MM('ADD', ah.outputs["Fac"], None, 0.25)), vcr.outputs[0])
pc.inputs["Emission Color"].default_value = (*GREEN, 1); big = nt.nodes.new("ShaderNodeTexNoise"); big.inputs["Scale"].default_value = 0.09; big.inputs["Detail"].default_value = 2
nt.links.new(tcx.outputs["Object"], big.inputs["Vector"])
bm_ = nt.nodes.new("ShaderNodeMapRange"); bm_.inputs["From Min"].default_value = 0.52; bm_.inputs["From Max"].default_value = 0.62
nt.links.new(big.outputs["Fac"], bm_.inputs["Value"])
nt.links.new(MM('MULTIPLY', MM('MULTIPLY', emis, bm_.outputs[0]), None, 5.0), pc.inputs["Emission Strength"])
canyon.data.materials.append(mc)
for i in range(N + 1):
    canyon.location = (0, -tape[i] * TL if i < N else -TL, 0); canyon.keyframe_insert("location", index=1, frame=i + 1)
for fc in tlib._fcurves(canyon.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---------------- lights: rim + reflection-only rhythm sequencer ----------------
rim = tlib.area("Rim", (0, 9, 6.5), tuple(CEN), energy=900, size=6, color=(0.85, 0.92, 1.0))
key = tlib.area("Key", (-5, -3, 7), tuple(CEN), energy=120, size=3, color=(1.0, 0.78, 0.55))
mstrip = bpy.data.materials.new("M_strip"); mstrip.use_nodes = True; nt = mstrip.node_tree; nt.nodes.clear()
eo = nt.nodes.new("ShaderNodeOutputMaterial"); ee = nt.nodes.new("ShaderNodeEmission"); ee.inputs["Color"].default_value = (0.9, 0.95, 1.0, 1)
vl = nt.nodes.new("ShaderNodeValue"); vl.name = "lights"; drive(vl.outputs[0], "default_value", "lights", "v*14")
nt.links.new(vl.outputs[0], ee.inputs["Strength"]); nt.links.new(ee.outputs[0], eo.inputs[0])
for i in range(6):
    a = i/6*2*math.pi
    st_ = tlib.prim('cube', f"Strip_{i}", loc=(4.2*math.cos(a), 4.2*math.sin(a), 6.0), scale=(0.08, 3.2, 0.04), rot=(0, 0, a), m=mstrip)
    st_.visible_camera = False; st_.visible_diffuse = False; st_.visible_shadow = False
# subtle green under-light from the cracks reflected in the hero (kept tiny)
print("loop built", N, "frames")
S.frame_set(1)
