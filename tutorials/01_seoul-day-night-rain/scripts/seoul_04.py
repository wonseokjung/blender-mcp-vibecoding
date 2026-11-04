# seoul_04: storefronts = dark reflective glass with warm interior depth; windows = soft interior light with blinds/curtain variety
import bpy
ms = bpy.data.materials["K_store"]; nt = ms.node_tree; pb = nt.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = (0.015, 0.014, 0.013, 1); pb.inputs["Roughness"].default_value = 0.04; pb.inputs["Specular IOR Level"].default_value = 0.9
wv = nt.nodes.get("shelf")
if wv:
    wv.inputs["Scale"].default_value = 0.9; wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 6
for n in nt.nodes:
    if n.type == 'MAP_RANGE': n.inputs["To Min"].default_value = 0.05; n.inputs["To Max"].default_value = 0.9
for d in nt.animation_data.drivers:
    if "night" in d.driver.expression: d.driver.expression = "0.08 + 0.55*night"
pb.inputs["Emission Color"].default_value = (1.0, 0.70, 0.42, 1)
# windows
mw = bpy.data.materials["K_window"]; nt = mw.node_tree; pbw = nt.nodes["Principled BSDF"]
if "vgrad" not in nt.nodes:
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sx.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath"); fr.operation = 'FRACT'; fr.name = "vgrad"
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = 1/3.0
    nt.links.new(sx.outputs["Z"], sc.inputs[0]); nt.links.new(sc.outputs[0], fr.inputs[0])
    gr = nt.nodes.new("ShaderNodeMapRange"); gr.inputs["From Min"].default_value = 0.1; gr.inputs["From Max"].default_value = 0.75
    gr.inputs["To Min"].default_value = 0.35; gr.inputs["To Max"].default_value = 1.0; nt.links.new(fr.outputs[0], gr.inputs["Value"])
    bl = nt.nodes.new("ShaderNodeTexWave"); bl.wave_type = 'BANDS'; bl.bands_direction = 'Z'; bl.inputs["Scale"].default_value = 9.0
    nt.links.new(geo.outputs["Position"], bl.inputs["Vector"])
    blm = nt.nodes.new("ShaderNodeMapRange"); blm.inputs["To Min"].default_value = 0.45; blm.inputs["To Max"].default_value = 1.0; nt.links.new(bl.outputs["Fac"], blm.inputs["Value"])
    at = [n for n in nt.nodes if n.type == 'ATTRIBUTE'][0]
    isb = nt.nodes.new("ShaderNodeMath"); isb.operation = 'LESS_THAN'; isb.inputs[1].default_value = 0.6; nt.links.new(at.outputs["Fac"], isb.inputs[0])
    mixb = nt.nodes.new("ShaderNodeMix"); mixb.data_type = 'FLOAT'; nt.links.new(isb.outputs[0], mixb.inputs[0]); mixb.inputs[2].default_value = 1.0; nt.links.new(blm.outputs[0], mixb.inputs[3])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.4; nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    nzm = nt.nodes.new("ShaderNodeMapRange"); nzm.inputs["To Min"].default_value = 0.55; nzm.inputs["To Max"].default_value = 1.15; nt.links.new(nz.outputs["Fac"], nzm.inputs["Value"])
    old = [l for l in nt.links if l.to_socket == pbw.inputs["Emission Strength"]][0].from_socket
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; nt.links.new(old, m1.inputs[0]); nt.links.new(gr.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(mixb.outputs[0], m2.inputs[1])
    m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = 'MULTIPLY'; nt.links.new(m2.outputs[0], m3.inputs[0]); nt.links.new(nzm.outputs[0], m3.inputs[1])
    nt.links.new(m3.outputs[0], pbw.inputs["Emission Strength"])
for n in nt.nodes:
    if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 0.85) < 1e-6: n.inputs[1].default_value = 0.7
print("seoul_04 ok")
