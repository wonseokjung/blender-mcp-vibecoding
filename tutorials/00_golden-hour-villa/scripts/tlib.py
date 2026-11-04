# Shared helpers for the "블렌더 MCP로 만들 수 있는 것" examples. Imported inside Blender via execute_code.
import bpy, math, os
from mathutils import Vector

EX = os.path.expanduser("../_workB")
PRET = os.path.expanduser("~/Library/Fonts/Pretendard-%s.otf")


def sc():
    return bpy.context.scene


def reset():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.curves,
                 bpy.data.actions, bpy.data.node_groups, bpy.data.textures, bpy.data.images):
        for d in list(coll):
            if getattr(d, "users", 0) == 0 or coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                                                        bpy.data.cameras, bpy.data.curves, bpy.data.actions):
                try:
                    coll.remove(d)
                except Exception:
                    pass
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    s = sc()
    s.frame_start, s.frame_end, s.frame_current = 1, 168, 1
    s.render.fps = 24
    return s


def render_setup(slug, frames=168, w=1920, h=1080, samples=48, bloom=None, exposure=0.0, look='AgX - Medium High Contrast'):
    s = sc()
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = w, h, 100
    s.frame_start, s.frame_end = 1, frames
    s.render.fps = 24
    s.eevee.taa_render_samples = samples
    s.eevee.taa_samples = 16
    try:
        s.eevee.use_raytracing = True
        s.eevee.use_shadows = True
    except Exception:
        pass
    s.view_settings.view_transform = 'AgX'
    try:
        s.view_settings.look = look
    except Exception:
        pass
    s.view_settings.exposure = exposure
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGB'
    s.render.image_settings.color_depth = '8'
    s.render.filepath = os.path.join(EX, "frames", slug, "f_")
    s.render.use_overwrite = True
    if bloom:
        ng = bpy.data.node_groups.get("FinalComp") or bpy.data.node_groups.new("FinalComp", "CompositorNodeTree")
        ng.nodes.clear()
        if not ng.interface.items_tree:
            ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = ng.nodes.new("CompositorNodeRLayers"); gl = ng.nodes.new("CompositorNodeGlare"); go = ng.nodes.new("NodeGroupOutput")
        gl.name = "Glare"
        ng.links.new(rl.outputs["Image"], gl.inputs["Image"]); ng.links.new(gl.outputs["Image"], go.inputs[0])
        gl.inputs["Type"].default_value = 'Bloom'
        gl.inputs["Threshold"].default_value = bloom[0]
        gl.inputs["Strength"].default_value = bloom[1]
        gl.inputs["Size"].default_value = bloom[2]
        s.compositing_node_group = ng; s.render.use_compositing = True
    else:
        s.render.use_compositing = False
    return s


def world(color=(0.02, 0.02, 0.025), strength=1.0):
    s = sc()
    w = s.world or bpy.data.worlds.new("World"); s.world = w; w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*color, 1); bg.inputs[1].default_value = strength
    return w


def link(o, coll=None):
    (coll or sc().collection).objects.link(o)
    return o


def mat(name, base=(0.8, 0.8, 0.8), metal=0.0, rough=0.5, transmission=0.0, ior=1.45, emit=None, strength=0.0,
        alpha=1.0, coat=0.0, sss=0.0, spec=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    p.inputs["Transmission Weight"].default_value = transmission
    p.inputs["IOR"].default_value = ior
    p.inputs["Alpha"].default_value = alpha
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Specular IOR Level"].default_value = spec
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = strength
    if alpha < 1.0 or transmission > 0:
        try:
            m.surface_render_method = 'BLENDED' if alpha < 1.0 else 'DITHERED'
        except Exception:
            pass
    return m


def emit_mat(name, color, strength=5.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


def setmat(o, m):
    o.data.materials.clear(); o.data.materials.append(m)
    return o


def prim(kind, name, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), m=None, bevel=None, smooth=False, **kw):
    """Primitive via bmesh (no operator context needed). kind: cube, uvsphere, icosphere, cylinder, cone, torus(plane)."""
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    if kind == 'cube':
        bmesh.ops.create_cube(bm, size=1.0)
    elif kind == 'uvsphere':
        bmesh.ops.create_uvsphere(bm, u_segments=kw.get('u', 48), v_segments=kw.get('v', 24), radius=0.5)
    elif kind == 'icosphere':
        bmesh.ops.create_icosphere(bm, subdivisions=kw.get('sub', 3), radius=0.5)
    elif kind == 'cylinder':
        bmesh.ops.create_cone(bm, cap_ends=True, segments=kw.get('seg', 48), radius1=0.5, radius2=0.5, depth=1.0)
    elif kind == 'cone':
        bmesh.ops.create_cone(bm, cap_ends=True, segments=kw.get('seg', 48), radius1=0.5, radius2=kw.get('r2', 0.0), depth=1.0)
    elif kind == 'plane':
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    bm.to_mesh(me); bm.free()
    if smooth:
        for pz in me.polygons:
            pz.use_smooth = True
    o = bpy.data.objects.new(name, me); link(o, kw.get('coll'))
    o.location, o.scale, o.rotation_euler = loc, scale, rot
    if m:
        setmat(o, m)
    if bevel:
        md = o.modifiers.new("Bevel", 'BEVEL'); md.width = bevel; md.segments = kw.get('bseg', 3)
        md.limit_method = 'ANGLE'
        md.affect = 'EDGES'
    return o


def subsurf(o, lv=2):
    md = o.modifiers.new("Sub", 'SUBSURF'); md.levels = lv; md.render_levels = lv
    for pz in o.data.polygons:
        pz.use_smooth = True
    return md


def text(body, name, font, size=1.0, extrude=0.1, bevel=0.01, align='CENTER', loc=(0, 0, 0), rot=(math.radians(90), 0, 0), m=None, valign='CENTER', spacing=1.0):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size; cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 3
    cu.align_x = align; cu.align_y = valign; cu.space_character = spacing
    o = bpy.data.objects.new(name, cu); link(o)
    o.location, o.rotation_euler = loc, rot
    if m:
        cu.materials.append(m)
    return o


def area(name, loc, target=(0, 0, 0), energy=500, size=2.0, color=(1, 1, 1), shape='RECTANGLE', size_y=None):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color; l.shape = shape
    l.size = size; l.size_y = size_y or size
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    aim(o, target)
    return o


def spot(name, loc, target=(0, 0, 0), energy=500, angle=40, blend=0.5, color=(1, 1, 1), radius=0.1):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = energy; l.color = color
    l.spot_size = math.radians(angle); l.spot_blend = blend; l.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    aim(o, target)
    return o


def sun(name, rot, energy=3, color=(1, 1, 1), angle=2.0):
    l = bpy.data.lights.new(name, 'SUN'); l.energy = energy; l.color = color; l.angle = math.radians(angle)
    o = link(bpy.data.objects.new(name, l)); o.rotation_euler = [math.radians(a) for a in rot]
    return o


def aim(o, target):
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def camera(loc=(0, -10, 2), target=(0, 0, 0), lens=35, dof=None):
    s = sc()
    cd = bpy.data.cameras.new("Cam"); cd.lens = lens; cd.sensor_width = 36
    cam = link(bpy.data.objects.new("Cam", cd)); cam.location = loc
    tgt = link(bpy.data.objects.new("CamTarget", None)); tgt.location = target
    c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    s.camera = cam
    if dof:
        cd.dof.use_dof = True; cd.dof.focus_object = tgt; cd.dof.aperture_fstop = dof
    return cam, tgt


def key(o, path, frames_vals, interp='BEZIER', ease=None):
    """frames_vals: list of (frame, value). value may be tuple for vector paths."""
    for f, v in frames_vals:
        setattr(o, path, v)
        o.keyframe_insert(data_path=path, frame=f)
    ad = o.animation_data
    if ad and ad.action:
        _set_interp(ad.action, interp, ease)


def _fcurves(action):
    try:
        return list(action.fcurves)
    except Exception:
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out += list(cb.fcurves)
        return out


def _set_interp(action, interp, ease):
    for fc in _fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = interp
            if ease:
                kp.easing = ease


def linear_all(o):
    if o.animation_data and o.animation_data.action:
        _set_interp(o.animation_data.action, 'LINEAR', None)


def viewport_camera(shading='RENDERED'):
    for win in bpy.context.window_manager.windows:
        for a in win.screen.areas:
            if a.type == 'VIEW_3D':
                sp = a.spaces.active
                sp.region_3d.view_perspective = 'CAMERA'
                sp.shading.type = shading
                sp.show_region_ui = True
                try:
                    sp.overlay.show_overlays = True
                except Exception:
                    pass


def save(slug):
    p = os.path.join(EX, "blend", slug + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=p, copy=True, compress=False)
    return p


def frame(f):
    sc().frame_set(f)
