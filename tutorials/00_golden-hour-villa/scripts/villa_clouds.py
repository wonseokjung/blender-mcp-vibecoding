# procedural thin golden-hour cloud streaks layered over the physical sky
import bpy, math
from mathutils import Vector
S = bpy.context.scene
w = bpy.data.worlds["V_sky"]; nt = w.node_tree
for n in list(nt.nodes):
    if n.name.startswith("CL_"): nt.nodes.remove(n)
sky = [n for n in nt.nodes if n.type == 'TEX_SKY'][0]; bg = [n for n in nt.nodes if n.type == 'BACKGROUND'][0]
def N(t, name):
    n = nt.nodes.new(t); n.name = "CL_" + name; return n
tc = N("ShaderNodeTexCoord", "tc")
sep = N("ShaderNodeSeparateXYZ", "sep"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
zc = N("ShaderNodeMath", "zc"); zc.operation = 'MAXIMUM'; zc.inputs[1].default_value = 0.035; nt.links.new(sep.outputs["Z"], zc.inputs[0])
px = N("ShaderNodeMath", "px"); px.operation = 'DIVIDE'; nt.links.new(sep.outputs["X"], px.inputs[0]); nt.links.new(zc.outputs[0], px.inputs[1])
py = N("ShaderNodeMath", "py"); py.operation = 'DIVIDE'; nt.links.new(sep.outputs["Y"], py.inputs[0]); nt.links.new(zc.outputs[0], py.inputs[1])
cmb = N("ShaderNodeCombineXYZ", "cmb"); nt.links.new(px.outputs[0], cmb.inputs[0]); nt.links.new(py.outputs[0], cmb.inputs[1])
mp = N("ShaderNodeMapping", "mp"); mp.inputs["Scale"].default_value = (0.35, 1.6, 1.0); mp.inputs["Rotation"].default_value[2] = math.radians(25)
nt.links.new(cmb.outputs[0], mp.inputs[0])
nz = N("ShaderNodeTexNoise", "nz"); nz.noise_dimensions = '2D'; nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 9; nz.inputs["Roughness"].default_value = 0.62
nt.links.new(mp.outputs[0], nz.inputs["Vector"])
mr = N("ShaderNodeMapRange", "mr"); mr.inputs["From Min"].default_value = 0.56; mr.inputs["From Max"].default_value = 0.78
nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
hz = N("ShaderNodeMapRange", "hz"); hz.inputs["From Min"].default_value = 0.01; hz.inputs["From Max"].default_value = 0.06
nt.links.new(sep.outputs["Z"], hz.inputs["Value"])
hz2 = N("ShaderNodeMapRange", "hz2"); hz2.inputs["From Min"].default_value = 0.45; hz2.inputs["From Max"].default_value = 0.15
nt.links.new(sep.outputs["Z"], hz2.inputs["Value"])
m1 = N("ShaderNodeMath", "m1"); m1.operation = 'MULTIPLY'; nt.links.new(mr.outputs[0], m1.inputs[0]); nt.links.new(hz.outputs[0], m1.inputs[1])
m2 = N("ShaderNodeMath", "m2"); m2.operation = 'MULTIPLY'; nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(hz2.outputs[0], m2.inputs[1])
m3 = N("ShaderNodeMath", "m3"); m3.operation = 'MULTIPLY'; m3.inputs[1].default_value = S.get("cloud_amt", 0.85); nt.links.new(m2.outputs[0], m3.inputs[0])
# cloud colour: lit warm toward the sun, dusky mauve away
el = sky.sun_elevation; az = math.pi/2 - sky.sun_rotation
sd = Vector((math.cos(az)*math.cos(el), math.sin(az)*math.cos(el), math.sin(el)))
dp = N("ShaderNodeVectorMath", "dp"); dp.operation = 'DOT_PRODUCT'; dp.inputs[1].default_value = sd
nt.links.new(tc.outputs["Generated"], dp.inputs[0])
cr = N("ShaderNodeValToRGB", "cr"); cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0.16, 0.11, 0.13, 1)
cr.color_ramp.elements[1].position = 1.0; cr.color_ramp.elements[1].color = (2.6, 1.05, 0.38, 1)
e = cr.color_ramp.elements.new(0.75); e.color = (0.75, 0.36, 0.22, 1)
dpm = N("ShaderNodeMapRange", "dpm"); dpm.inputs["From Min"].default_value = -0.3; dpm.inputs["From Max"].default_value = 1.0
nt.links.new(dp.outputs["Value"], dpm.inputs["Value"]); nt.links.new(dpm.outputs[0], cr.inputs[0])
cs = N("ShaderNodeMix", "cs"); cs.data_type = 'RGBA'; cs.blend_type = 'MULTIPLY'; cs.inputs[0].default_value = 1.0
nt.links.new(cr.outputs[0], cs.inputs[6]); cs.inputs[7].default_value = (S.get("cloud_k", 1.0),)*3 + (1,)
# keep the sky brightness scale: clouds multiply against sky luminance
lum = N("ShaderNodeRGBToBW", "lum"); nt.links.new(sky.outputs[0], lum.inputs[0])
lk = N("ShaderNodeMath", "lk"); lk.operation = 'POWER'; lk.inputs[1].default_value = 0.6; nt.links.new(lum.outputs[0], lk.inputs[0])
cs2 = N("ShaderNodeMix", "cs2"); cs2.data_type = 'RGBA'; cs2.blend_type = 'MULTIPLY'; cs2.inputs[0].default_value = 1.0
nt.links.new(cs.outputs[2], cs2.inputs[6]); nt.links.new(lk.outputs[0], cs2.inputs[7])
mx = N("ShaderNodeMix", "mx"); mx.data_type = 'RGBA'
nt.links.new(m3.outputs[0], mx.inputs[0]); nt.links.new(sky.outputs[0], mx.inputs[6]); nt.links.new(cs2.outputs[2], mx.inputs[7])
nt.links.new(mx.outputs[2], bg.inputs[0])
print("clouds ok")
