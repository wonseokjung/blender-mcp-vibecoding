import bpy
ng = bpy.data.node_groups["GN_ferro"]
for n in ng.nodes:
    if n.type == 'MAP_RANGE' and abs(n.inputs["From Max"].default_value - 0.13) < 1e-6:
        n.inputs["From Max"].default_value = 0.62
    if n.type == 'MATH' and n.operation == 'POWER':
        n.inputs[1].default_value = 2.2
for nm in ("Softbox", "Amber"):
    bpy.data.objects[nm].visible_glossy = False
bpy.data.objects["Softbox"].data.energy = 450
print("l4 ok")
