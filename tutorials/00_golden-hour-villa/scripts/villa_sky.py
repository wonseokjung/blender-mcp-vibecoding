import bpy, math
S = bpy.context.scene
w = bpy.data.worlds.get("V_sky") or bpy.data.worlds.new("V_sky"); w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
sky = nt.nodes.new("ShaderNodeTexSky"); sky.sky_type = 'MULTIPLE_SCATTERING'
EL = math.radians(S.get("sun_el", 7.0)); AZ = math.radians(S.get("sun_az", 203.0))
sky.sun_elevation = EL
# blender sky: sun_rotation measured so that direction = (sin(rot), cos(rot))? solve: we want dir angle AZ from +X
sky.sun_rotation = (math.pi/2 - AZ) % (2*math.pi)
sky.sun_disc = True; sky.sun_size = math.radians(0.9); sky.sun_intensity = S.get("sun_int", 1.0)
sky.air_density = S.get("air", 1.0); sky.aerosol_density = S.get("aero", 2.0); sky.ozone_density = 1.0; sky.altitude = 10
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = S.get("sky_str", 0.25)
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(sky.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0])
S.world = w
sun = bpy.data.objects["V_sun"]; sun.hide_render = S.get("sun_lamp_off", 1) == 1
print("sky ok", [round(x, 3) for x in getattr(sky, "sun_direction", (0, 0, 0))])
