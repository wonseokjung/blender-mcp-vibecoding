# room-interior v2 iter 3: the bouclé scan's colour map is a check pattern (sofa + rug read as tartan) -> keep only its
# scanned normal/roughness under a plain oat colour + sheen; walls still read as grey concrete -> 80% mix toward a
# warm white (scan detail stays in the bump); monitor screen off (flat white emission looked CG)
import bpy
nt = bpy.data.materials["wool_boucle"].node_tree; p = nt.nodes["Principled BSDF"]
for l in list(p.inputs["Base Color"].links): nt.links.remove(l)
p.inputs["Base Color"].default_value = (0.62, 0.58, 0.52, 1); p.inputs["Sheen Weight"].default_value = 0.6
wt = bpy.data.materials["white_plaster_02"].node_tree; h = wt.nodes["Lift"]; pp = wt.nodes["Principled BSDF"]
mx = wt.nodes.get("ToWhite") or wt.nodes.new("ShaderNodeMix"); mx.name = "ToWhite"; mx.data_type = 'RGBA'
mx.inputs[0].default_value = 0.8; mx.inputs[7].default_value = (0.88, 0.85, 0.80, 1)
wt.links.new(h.outputs["Color"], mx.inputs[6]); wt.links.new(mx.outputs[2], pp.inputs["Base Color"])
scr = bpy.data.materials.get("Screen")
if scr:
    scr.node_tree.nodes["Emission"].inputs[0].default_value = (0.02, 0.025, 0.03, 1); scr.node_tree.nodes["Emission"].inputs[1].default_value = 0.4
print("ok")
