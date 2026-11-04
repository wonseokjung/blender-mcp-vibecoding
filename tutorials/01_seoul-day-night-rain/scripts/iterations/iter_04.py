# seoul_03: calmer window glow, storefront interiors with mullions, AC units + rooftop tanks for Seoul density
import bpy, bmesh, math, random
from mathutils import Vector
S = bpy.context.scene; rnd = random.Random(9)
nt = bpy.data.materials["K_window"].node_tree
for n in nt.nodes:
    if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 2.2) < 1e-6: n.inputs[1].default_value = 0.85
    if n.type == 'VALTORGB':
        n.color_ramp.elements[0].color = (1.0, 0.55, 0.26, 1); n.color_ramp.elements[1].color = (0.85, 0.9, 1.0, 1)
# storefront: interior shelves/people-free noise, mullions
ms = bpy.data.materials["K_store"]; nt = ms.node_tree; pb = nt.nodes["Principled BSDF"]
if "shelf" not in nt.nodes:
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.name = "shelf"; wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 1.6; wv.inputs["Distortion"].default_value = 2.0
    nt.links.new(geo.outputs["Position"], wv.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    mm = nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'; nt.links.new(wv.outputs["Fac"], mm.inputs[0]); nt.links.new(nz.outputs["Fac"], mm.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.25; mr.inputs["To Max"].default_value = 1.0; nt.links.new(mm.outputs[0], mr.inputs["Value"])
    old = [l for l in nt.links if l.to_socket == pb.inputs["Emission Strength"]][0].from_socket
    for n in nt.nodes:
        if n.type == 'VALUE' and n.name == "store":
            d = n.outputs[0].animation_data if hasattr(n.outputs[0], "animation_data") else None
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'; nt.links.new(old, m2.inputs[0]); nt.links.new(mr.outputs[0], m2.inputs[1])
    nt.links.new(m2.outputs[0], pb.inputs["Emission Strength"])
fc = [f for f in (S.animation_data.drivers if S.animation_data else [])]
# lower the store glow expression on the driver
for d in ms.node_tree.animation_data.drivers:
    if "night" in d.driver.expression: d.driver.expression = "0.12 + 1.05*night"
CB = bpy.data.collections["K_build"]
for o in list(CB.objects):
    if o.get("v3"): bpy.data.objects.remove(o, do_unlink=True)
M_dark = bpy.data.materials["K_dark"]; M_metal = bpy.data.materials["K_metal"]
def box(name, x0, x1, y0, y1, z0, z1, m):
    me = bpy.data.meshes.new(name)
    v = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    me.from_pydata(v, [], [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    o = bpy.data.objects.new(name, me); CB.objects.link(o); o.data.materials.append(m); o["v3"] = 1; return o
# mullions on storefronts
for o in list(CB.objects):
    if "_store_" in o.name:
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        a, b = vs[0], vs[1]; L = (b - a).length; n = max(2, int(L/1.6))
        for k in range(n + 1):
            p = a.lerp(b, k/n)
            box(f"{o.name}_mul{k}", p.x - 0.04, p.x + 0.04, p.y - 0.04, p.y + 0.04, 0.4, 3.25, M_metal)
# AC outdoor units hung under windows on street faces
mac = bpy.data.materials.get("K_ac") or bpy.data.materials.new("K_ac"); mac.use_nodes = True
mac.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.78, 0.78, 0.76, 1); mac.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5
faces = [("S", 8.6, 21.5, 9.6), ("S", 21.9, 33.5, 9.6), ("S", -21.0, -8.6, 9.6), ("S", -34.0, -21.4, 9.6), ("W", 21.4, 33.0, 8.6), ("W", 33.4, 46.0, 8.6), ("E", 9.6, 21.0, -8.6)]
for i, (fd, a0, a1, c) in enumerate(faces):
    for k in range(rnd.randint(3, 6)):
        t = rnd.uniform(a0 + 1, a1 - 1); z = 4.6 + 3.0*rnd.randint(0, 3) + 0.2
        if fd == "S": box(f"K_ac_{i}_{k}", t - 0.42, t + 0.42, c - 0.36, c, z, z + 0.62, mac)
        elif fd == "W": box(f"K_ac_{i}_{k}", c - 0.36, c, t - 0.42, t + 0.42, z, z + 0.62, mac)
        else: box(f"K_ac_{i}_{k}", c, c + 0.36, t - 0.42, t + 0.42, z, z + 0.62, mac)
# rooftop water tanks / stair boxes
for i, (x, y, h) in enumerate([(15.0, 17.0, 16.9), (27.0, 15.0, 19.0), (-15.0, 15.0, 13.0), (14.0, 27.0, 13.0), (-27.0, 14.5, 16.0)]):
    box(f"K_roofbox_{i}", x - 1.5, x + 1.5, y - 1.2, y + 1.2, h, h + 2.4, bpy.data.materials["K_conc"])
    box(f"K_tank_{i}", x + 2.0, x + 3.4, y - 0.7, y + 0.7, h, h + 1.6, M_metal)
print("seoul_03 ok")
