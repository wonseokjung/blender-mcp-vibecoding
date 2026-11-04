# room-interior v2 iter 2: Poly Haven's sofas are all antique (sofa_03 = brown Chesterfield, wrong for a 원룸) ->
# modern bouclé sofa modelled with soft bevels + subsurf and the scanned wool_boucle texture; scanned plaster read
# grey/dirty -> HSV lift to a clean warm white keeping the scan's surface detail; linen/jersey scans were blue ->
# desaturated to natural off-white
import bpy, math
from mathutils import Matrix
OBJ = bpy.data.objects
o = OBJ.get("sofa_03")
if o: bpy.data.objects.remove(o, do_unlink=True)

def hsv(mat, sat, val, hue=0.5):
    nt = bpy.data.materials[mat].node_tree; p = nt.nodes["Principled BSDF"]
    l = p.inputs["Base Color"].links[0]; src = l.from_socket
    h = nt.nodes.get("Lift") or nt.nodes.new("ShaderNodeHueSaturation"); h.name = "Lift"
    nt.links.new(src, h.inputs["Color"]); nt.links.new(h.outputs["Color"], p.inputs["Base Color"])
    h.inputs["Hue"].default_value = hue; h.inputs["Saturation"].default_value = sat; h.inputs["Value"].default_value = val

hsv("white_plaster_02", 0.25, 1.55)
hsv("rough_linen", 0.12, 1.45)
hsv("jersey_melange", 0.1, 1.3)
hsv("wool_boucle", 0.35, 1.5)

# bouclé sofa (2.1 m), facing +y, in G_Sofa
boucle = bpy.data.materials["wool_boucle"]
import sys, os, importlib
sys.path.insert(0, os.path.expanduser("scripts")); import exlib; importlib.reload(exlib)
for n in [o.name for o in OBJ if o.name.startswith("SofaV2")]:
    bpy.data.objects.remove(OBJ[n], do_unlink=True)
g = OBJ["G_Sofa"]
x0, x1, y0, y1 = 0.1, 2.2, -1.9, -1.0
parts = [("Base", (x0, x1, y0, y1, 0.06, 0.40)), ("Back", (x0, x1, y0, y0 + 0.24, 0.40, 0.82)),
         ("ArmL", (x0, x0 + 0.22, y0, y1, 0.40, 0.64)), ("ArmR", (x1 - 0.22, x1, y0, y1, 0.40, 0.64)),
         ("Seat0", (x0 + 0.22, (x0 + x1) / 2, y0 + 0.24, y1 - 0.01, 0.40, 0.55)), ("Seat1", ((x0 + x1) / 2, x1 - 0.22, y0 + 0.24, y1 - 0.01, 0.40, 0.55))]
for nm, (a, b, c, d, e, f) in parts:
    o = exlib.prim('cube', f"SofaV2{nm}", loc=((a + b) / 2, (c + d) / 2, (e + f) / 2), scale=(b - a - 0.01, d - c - 0.01, f - e - 0.01), m=boucle, bevel=0.07, bseg=5)
    sd = o.modifiers.new("Sub", 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    o.parent = g; o.matrix_parent_inverse = Matrix.Identity(4)
for k, x in enumerate((0.42, 1.88)):   # dark legs
    o = exlib.prim('cylinder', f"SofaV2Leg{k}", loc=(x, -1.45, 0.03), scale=(0.05, 0.05, 0.06), m=bpy.data.materials["Charcoal"])
    o.parent = g; o.matrix_parent_inverse = Matrix.Identity(4)
print("ok")
