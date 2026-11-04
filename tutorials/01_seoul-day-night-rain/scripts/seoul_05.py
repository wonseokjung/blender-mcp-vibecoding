# seoul_05: storefront interiors read as lit shops: bright ceiling band, colourful shelf products (voronoi cells), dark floor band
import bpy
ms = bpy.data.materials["K_store"]; nt = ms.node_tree; pb = nt.nodes["Principled BSDF"]
for n in list(nt.nodes):
    if n.name.startswith("SF_"): nt.nodes.remove(n)
def N(t, nm):
    n = nt.nodes.new(t); n.name = "SF_" + nm; return n
geo = N("ShaderNodeNewGeometry", "geo"); sx = N("ShaderNodeSeparateXYZ", "sx"); nt.links.new(geo.outputs["Position"], sx.inputs[0])
# height in storefront (0.4 .. 3.25)
ceil = N("ShaderNodeMapRange", "ceil"); ceil.inputs["From Min"].default_value = 2.7; ceil.inputs["From Max"].default_value = 3.0; nt.links.new(sx.outputs["Z"], ceil.inputs["Value"])
shelf = N("ShaderNodeMapRange", "shelf"); shelf.inputs["From Min"].default_value = 0.7; shelf.inputs["From Max"].default_value = 0.9; nt.links.new(sx.outputs["Z"], shelf.inputs["Value"])
vor = N("ShaderNodeTexVoronoi", "vor"); vor.inputs["Scale"].default_value = 4.0; nt.links.new(geo.outputs["Position"], vor.inputs["Vector"])
hs = N("ShaderNodeHueSaturation", "hs"); hs.inputs["Saturation"].default_value = 0.55; hs.inputs["Value"].default_value = 0.9; nt.links.new(vor.outputs["Color"], hs.inputs["Color"])
warm = N("ShaderNodeMix", "warm"); warm.data_type = 'RGBA'; warm.inputs[0].default_value = 0.55; warm.inputs[6].default_value = (1.0, 0.86, 0.68, 1); nt.links.new(hs.outputs[0], warm.inputs[7])
col = N("ShaderNodeMix", "col"); col.data_type = 'RGBA'; nt.links.new(ceil.outputs[0], col.inputs[0]); nt.links.new(warm.outputs[2], col.inputs[6]); col.inputs[7].default_value = (1.0, 0.95, 0.88, 1)
nt.links.new(col.outputs[2], pb.inputs["Emission Color"])
# intensity: floor band dim, shelves medium, ceiling strip bright
lev = N("ShaderNodeMath", "lev"); lev.operation = 'MULTIPLY_ADD'; nt.links.new(shelf.outputs[0], lev.inputs[0]); lev.inputs[1].default_value = 0.65; lev.inputs[2].default_value = 0.25
lev2 = N("ShaderNodeMath", "lev2"); lev2.operation = 'MULTIPLY_ADD'; nt.links.new(ceil.outputs[0], lev2.inputs[0]); lev2.inputs[1].default_value = 1.6; nt.links.new(lev.outputs[0], lev2.inputs[2])
drv = [n for n in nt.nodes if n.type == 'VALUE' and n.name == "store"][0]
m = N("ShaderNodeMath", "m"); m.operation = 'MULTIPLY'; nt.links.new(drv.outputs[0], m.inputs[0]); nt.links.new(lev2.outputs[0], m.inputs[1])
nt.links.new(m.outputs[0], pb.inputs["Emission Strength"])
for d in nt.animation_data.drivers:
    if "night" in d.driver.expression: d.driver.expression = "0.1 + 0.85*night"
print("seoul_05 ok")
