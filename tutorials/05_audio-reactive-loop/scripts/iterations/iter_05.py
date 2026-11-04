# loop_03: readable obsidian (horizon-gradient world + softbox key + amber side), cone spikes, fewer cracks, brighter iris
import bpy, math, sys
sys.path.insert(0, 'scripts')
import tlib
S = bpy.context.scene
wd = S.world; nt = wd.node_tree
for n in list(nt.nodes):
    if n.name.startswith("G_"): nt.nodes.remove(n)
bg = nt.nodes["Background"]
tc = nt.nodes.new("ShaderNodeTexCoord"); tc.name = "G_tc"
sx = nt.nodes.new("ShaderNodeSeparateXYZ"); sx.name = "G_sx"; nt.links.new(tc.outputs["Generated"], sx.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.name = "G_cr"
e = cr.color_ramp.elements
e[0].position = 0.0; e[0].color = (0.010, 0.012, 0.016, 1)
e[1].position = 0.35; e[1].color = (0.0006, 0.0007, 0.0010, 1)
x = e.new(0.06); x.color = (0.030, 0.034, 0.042, 1)
mr = nt.nodes.new("ShaderNodeMapRange"); mr.name = "G_mr"; mr.inputs["From Min"].default_value = -0.05; mr.inputs["From Max"].default_value = 1.0
nt.links.new(sx.outputs["Z"], mr.inputs["Value"]); nt.links.new(mr.outputs[0], cr.inputs[0]); nt.links.new(cr.outputs[0], bg.inputs[0])

# lights
for nm in ("Softbox", "Amber"):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
sb = tlib.area("Softbox", (1.5, -5.0, 8.5), (0, 2, 1.5), energy=650, size=5.0, color=(0.88, 0.93, 1.0)); sb.visible_camera = False
am = tlib.area("Amber", (-9, -2, 2.0), (0, 0, 2.3), energy=160, size=2.5, color=(1.0, 0.55, 0.22)); am.visible_camera = False
cat = bpy.data.objects.get("Catch") or None
if cat: bpy.data.objects.remove(cat, do_unlink=True)
cl = tlib.area("Catch", (-0.8, -3.5, 3.6), (0, 0, 2.3), energy=25, size=0.6, color=(1, 1, 1)); cl.visible_camera = False; cl.visible_diffuse = False
bpy.data.objects["Rim"].data.energy = 1400
bpy.data.objects["Key"].data.energy = 0.0

# cone spikes
ng = bpy.data.node_groups["GN_ferro"]
for n in ng.nodes:
    if n.type == 'MAP_RANGE' and abs(n.inputs["From Max"].default_value - 0.30) < 1e-6:
        n.inputs["From Max"].default_value = 0.13
    if n.type == 'MATH' and n.operation == 'POWER':
        n.inputs[1].default_value = 1.35
    if n.type == 'TEX_VORONOI':
        n.inputs["Scale"].default_value = 7.5; n.inputs["Randomness"].default_value = 0.55

# fewer, finer cracks
mc = bpy.data.materials["M_canyon"]; nt = mc.node_tree
for n in nt.nodes:
    if n.type == 'MAP_RANGE' and abs(n.inputs["From Min"].default_value - 0.52) < 1e-6:
        n.inputs["From Min"].default_value = 0.58; n.inputs["From Max"].default_value = 0.66
    if n.type == 'MAP_RANGE' and abs(n.inputs["From Max"].default_value - 0.035) < 1e-6:
        n.inputs["From Max"].default_value = 0.02
    if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 5.0) < 1e-6:
        n.inputs[1].default_value = 2.5
pc = nt.nodes["Principled BSDF"]; pc.inputs["Roughness"].default_value = 0.12; pc.inputs["Base Color"].default_value = (0.012, 0.013, 0.015, 1)

# iris a touch brighter (graphite -> brushed silver fibres)
mi = bpy.data.materials["M_iris"]
for n in mi.node_tree.nodes:
    if n.type == 'VALTORGB':
        n.color_ramp.elements[1].color = (0.42, 0.47, 0.5, 1)
print("l3 ok")
