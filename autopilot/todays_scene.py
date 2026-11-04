"""Today's scene: open the prebuilt golden-hour villa, vary time of day, weather and camera, render a short vertical clip.

Run inside Blender (no window):

  blender -b golden-hour-villa.blend -P autopilot/todays_scene.py -- --out out
  blender -b golden-hour-villa.blend -P autopilot/todays_scene.py -- --out out --time night --weather mist --shot pool_reveal
  blender -b golden-hour-villa.blend -P autopilot/todays_scene.py -- --out out --dry-run

The choice is seeded by the date, so each day gets a different combination and the same day
always gives the same result. Everything it changed is written to <out>/<date>/params.json.

This is a template. The fun part is asking your AI (through Blender MCP) to add new looks,
new shots or new weather to the tables below.

CONNECT AI LAB
"""
import bpy
import datetime
import json
import math
import os
import random
import sys

# ---------------------------------------------------------------- variation tables
TIMES = {
    # sun elevation (deg), sun rotation offset (deg), sky strength, aerosol, practical lights x, exposure offset
    "golden_hour": dict(elev=4.5, rot=0, sky=1.0, aerosol=3.0, lights=1.0, exposure=0.0),
    "blue_hour":   dict(elev=-3.0, rot=0, sky=2.2, aerosol=1.5, lights=1.6, exposure=0.6),
    "night":       dict(elev=-14.0, rot=0, sky=6.0, aerosol=1.0, lights=2.2, exposure=0.9),
    "dawn":        dict(elev=7.0, rot=150, sky=0.9, aerosol=1.2, lights=0.5, exposure=0.1),
}
WEATHER = {
    "clear":      dict(mist=0.0, rain=False),
    "mist":       dict(mist=0.012, rain=False),
    "light_rain": dict(mist=0.006, rain=True),
}
SHOTS = {
    # frame ranges on the scene's own 312-frame drone camera
    "drone_open":  (1, 72),
    "orbit":       (73, 144),
    "pool_reveal": (145, 216),
    "arrival":     (241, 312),
}
PRACTICAL_LIGHTS = ("V_ff_area", "V_in_area", "V_up_", "V_slat_wash", "V_pool_light")
GLOW_MATERIALS = ("V_cove", "V_lampglow")


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--time", choices=list(TIMES))
    ap.add_argument("--weather", choices=list(WEATHER))
    ap.add_argument("--shot", choices=list(SHOTS))
    ap.add_argument("--seconds", type=float, default=3.0, help="clip length")
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--percent", type=int, default=100)
    ap.add_argument("--horizontal", action="store_true", help="keep 1920x1080 instead of vertical 1080x1920")
    ap.add_argument("--dry-run", action="store_true", help="apply everything, write params.json, do not render")
    return ap.parse_args(argv)


def sky_node(world):
    return next((n for n in world.node_tree.nodes if n.type == "TEX_SKY"), None)


def apply_time(sc, t):
    sky = sky_node(sc.world)
    if sky:
        sky.sun_elevation = math.radians(t["elev"])
        sky.sun_rotation = (sky.sun_rotation + math.radians(t["rot"])) % (2 * math.pi)
        if hasattr(sky, "aerosol_density"):
            sky.aerosol_density = t["aerosol"]
    bg = next((n for n in sc.world.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg:
        bg.inputs["Strength"].default_value *= t["sky"]
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.name.startswith(PRACTICAL_LIGHTS):
            o.data.energy *= t["lights"]
    for m in bpy.data.materials:
        if m.name.startswith(GLOW_MATERIALS) and m.node_tree:
            for n in m.node_tree.nodes:
                s = n.inputs.get("Emission Strength") or (n.inputs.get("Strength") if n.type == "EMISSION" else None)
                if s is not None:
                    s.default_value *= t["lights"]
    # the scene animates exposure (drone auto-exposure); shift the whole curve
    ad = sc.animation_data
    curves = []
    if ad and ad.action:
        try:
            curves = list(ad.action.layers[0].strips[0].channelbags[0].fcurves)
        except Exception:
            curves = list(getattr(ad.action, "fcurves", []))
    moved = False
    for fc in curves:
        if fc.data_path == "view_settings.exposure":
            for k in fc.keyframe_points:
                k.co.y += t["exposure"]
                k.handle_left.y += t["exposure"]
                k.handle_right.y += t["exposure"]
            moved = True
    if not moved:
        sc.view_settings.exposure += t["exposure"]


def apply_weather(sc, w, seed, cam):
    nt = sc.world.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    if w["mist"] > 0:
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.name = "TODAY_mist"
        vol.inputs["Density"].default_value = w["mist"]
        vol.inputs["Color"].default_value = (0.82, 0.86, 0.92, 1.0)
        nt.links.new(vol.outputs[0], out.inputs["Volume"])
    if w["rain"]:
        add_rain(sc, seed, cam)


def add_rain(sc, seed, cam):
    """Simple rain: thin streaks in a box in front of the camera, falling on a looping curve, with motion blur."""
    rnd = random.Random(seed)
    verts, faces = [], []
    base = [(rnd.uniform(-7, 7), rnd.uniform(-4, 4), -rnd.uniform(1.5, 20), rnd.uniform(0.25, 0.45)) for _ in range(900)]
    for tile in (-16, -8, 0, 8):  # the pattern repeats every 8 m, so the 8 m loop below has no visible jump
        for x, y, z, L in base:
            y += tile
            wdt = 0.004 * (-z / 6 + 0.5)
            b = len(verts)
            verts += [(x - wdt, y, z), (x + wdt, y, z), (x + wdt, y + L, z), (x - wdt, y + L, z)]
            faces.append((b, b + 1, b + 2, b + 3))
    me = bpy.data.meshes.new("TODAY_rain")
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("TODAY_rain", me)
    sc.collection.objects.link(ob)
    ob.parent = cam  # built in camera space (x right, y up, -z forward), so the rain is always in shot
    mat = bpy.data.materials.new("TODAY_rain")
    if mat.node_tree is None:  # Blender 4.x
        mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.85, 0.9, 1.0, 1.0)
    em.inputs["Strength"].default_value = 0.6
    mix.inputs["Fac"].default_value = 0.35
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs["Surface"])
    me.materials.append(mat)
    ob.visible_shadow = False
    # fall: move the block down 8 m every 12 frames, looping
    ob.location = (0, 0, 0)
    ob.keyframe_insert("location", index=1, frame=0)
    ob.location = (0, -8.0, 0)
    ob.keyframe_insert("location", index=1, frame=12)
    ad = ob.animation_data
    try:
        fcs = ad.action.layers[0].strips[0].channelbags[0].fcurves
    except Exception:
        fcs = ad.action.fcurves
    for fc in fcs:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
        fc.modifiers.new("CYCLES")
    sc.render.use_motion_blur = True


def main():
    a = args()
    sc = bpy.context.scene
    seed = int(a.date.replace("-", ""))
    rnd = random.Random(seed)
    pick = dict(
        time=a.time or rnd.choice(list(TIMES)),
        weather=a.weather or rnd.choice(list(WEATHER)),
        shot=a.shot or rnd.choice(list(SHOTS)),
    )
    cam = sc.camera
    apply_time(sc, TIMES[pick["time"]])
    apply_weather(sc, WEATHER[pick["weather"]], seed, cam)

    s0, s1 = SHOTS[pick["shot"]]
    n = max(1, int(round(a.seconds * sc.render.fps)))
    sc.frame_start, sc.frame_end = s0, min(s1, s0 + n - 1)
    if not a.horizontal:
        sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.resolution_percentage = a.percent
    if sc.render.engine == "CYCLES":
        sc.cycles.samples = a.samples
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
                try:
                    prefs.compute_device_type = kind
                except TypeError:
                    continue
                prefs.get_devices()
                if any(d.type == kind for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = d.type == kind
                    sc.cycles.device = "GPU"
                    break
        except Exception:
            pass

    day = os.path.join(os.path.abspath(a.out), a.date)
    os.makedirs(day, exist_ok=True)
    sc.render.filepath = os.path.join(day, "frames", "f_")
    info = dict(pick, date=a.date, seed=seed, frames=[sc.frame_start, sc.frame_end],
                resolution=[sc.render.resolution_x, sc.render.resolution_y, a.percent],
                samples=a.samples, engine=sc.render.engine, dry_run=a.dry_run)
    with open(os.path.join(day, "params.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    print("[todays_scene]", json.dumps(info))
    if not a.dry_run:
        bpy.ops.render.render(animation=True)
        print("[todays_scene] frames in", os.path.join(day, "frames"))


main()
