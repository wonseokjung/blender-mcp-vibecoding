import bpy, sys
sys.path.insert(0, 'scripts')
import tlib
can_c = bpy.data.collections["LL_canyon"]
for nm in ("Graze", "GrazeL", "GrazeR"):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
for nm, x in (("GrazeL", -42), ("GrazeR", 42)):
    g = tlib.area(nm, (x, 14, 5.0), (0, 14, 0.0), energy=5200, size=40, color=(0.72, 0.82, 1.0)); g.data.size_y = 2.0
    g.visible_camera = False; g.light_linking.receiver_collection = can_c
pc = bpy.data.materials["M_canyon"].node_tree.nodes["Principled BSDF"]; pc.inputs["Roughness"].default_value = 0.28
# haze: thin homogeneous volume box
if "Haze" in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects["Haze"], do_unlink=True)
hz = tlib.prim('cube', "Haze", loc=(0, 10, 6), scale=(70, 90, 12.5))
mv = bpy.data.materials.get("M_haze") or bpy.data.materials.new("M_haze"); mv.use_nodes = True; nt = mv.node_tree; nt.nodes.clear()
o = nt.nodes.new("ShaderNodeOutputMaterial"); pv = nt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 0.012; pv.inputs["Anisotropy"].default_value = 0.55; pv.inputs["Color"].default_value = (0.8, 0.85, 0.9, 1)
nt.links.new(pv.outputs[0], o.inputs["Volume"]); tlib.setmat(hz, mv)
hz.visible_shadow = False
print("l6 ok")
