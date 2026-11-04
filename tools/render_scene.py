#!/usr/bin/env python3
"""Headless render helper: render one frame or a frame range of a .blend without opening the Blender window.

  python tools/render_scene.py scenes/blend/channel-logo-intro.blend --frame 60 --percent 50
  python tools/render_scene.py scenes/blend/golden-hour-villa.blend --start 1 --end 72 --vertical --samples 32
  python tools/render_scene.py scene.blend --frame 1 --out renders/test_ --blender "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"

GPU: picks METAL on Apple Silicon, then OPTIX, CUDA, HIP, oneAPI; falls back to CPU.
Only one render at a time per GPU: this script refuses to start while its lock file exists
(default: <system temp>/blender_mcp_vibecoding.lock).

CONNECT AI LAB
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

INNER = r'''
import bpy, sys, json, time
a = json.loads(sys.argv[sys.argv.index("--") + 1])
sc = bpy.context.scene
r = sc.render
if r.engine == "CYCLES":
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        chosen = "NONE"
        for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
            except TypeError:
                continue
            prefs.get_devices()
            devs = [d for d in prefs.devices if d.type == kind]
            if devs:
                for d in prefs.devices:
                    d.use = d.type == kind
                chosen = kind
                break
        sc.cycles.device = "GPU" if chosen != "NONE" else "CPU"
        print("[render_scene] Cycles device:", chosen if chosen != "NONE" else "CPU")
    except Exception as e:
        print("[render_scene] GPU setup skipped:", e)
    if a.get("samples"):
        sc.cycles.samples = a["samples"]
if a.get("vertical"):
    r.resolution_x, r.resolution_y = 1080, 1920
r.resolution_percentage = a["percent"]
r.filepath = a["out"]
t = time.time()
if a.get("frame") is not None:
    sc.frame_set(a["frame"])
    bpy.ops.render.render(write_still=True)
else:
    sc.frame_start, sc.frame_end = a["start"], a["end"]
    bpy.ops.render.render(animation=True)
print("[render_scene] done in %.1f s" % (time.time() - t))
'''

CANDIDATES = [
    os.environ.get("BLENDER", ""),
    "/Applications/Blender.app/Contents/MacOS/Blender",
    os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender"),
    shutil.which("blender") or "",
]


def find_blender(explicit):
    if explicit:
        return explicit
    for c in CANDIDATES:
        if c and os.path.exists(c):
            return c
    if os.name == "nt":
        base = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Blender Foundation")
        if os.path.isdir(base):
            for d in sorted(os.listdir(base), reverse=True):
                exe = os.path.join(base, d, "blender.exe")
                if os.path.exists(exe):
                    return exe
    sys.exit("Blender not found. Pass --blender PATH or set the BLENDER environment variable.")


def main():
    ap = argparse.ArgumentParser(description="Render a .blend headless (no window).")
    ap.add_argument("blend")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--frame", type=int, help="render a single frame")
    g.add_argument("--start", type=int, help="first frame of a range")
    ap.add_argument("--end", type=int, help="last frame of a range")
    ap.add_argument("--out", default=None, help="output path prefix (default: renders/<scene>/f_)")
    ap.add_argument("--percent", type=int, default=100, help="resolution percentage, e.g. 50 for a quick test")
    ap.add_argument("--samples", type=int, default=None, help="Cycles samples override")
    ap.add_argument("--vertical", action="store_true", help="render 1080x1920 (shorts / reels)")
    ap.add_argument("--blender", default=None, help="path to the Blender executable")
    ap.add_argument("--lock", default=os.path.join(tempfile.gettempdir(), "blender_mcp_vibecoding.lock"))
    a = ap.parse_args()

    blend = os.path.abspath(a.blend)
    if not os.path.exists(blend):
        sys.exit("No such file: %s" % blend)
    if a.frame is None and a.start is None:
        a.frame = 1
    if a.start is not None and a.end is None:
        sys.exit("--start needs --end")
    name = os.path.splitext(os.path.basename(blend))[0]
    out = os.path.abspath(a.out or os.path.join("renders", name, "f_"))
    os.makedirs(os.path.dirname(out), exist_ok=True)

    if os.path.exists(a.lock):
        sys.exit("Another render holds %s. Wait for it (one render per GPU), or delete the file if it is stale." % a.lock)
    with open(a.lock, "w") as f:
        f.write("render_scene.py pid %d %s\n" % (os.getpid(), time.strftime("%Y-%m-%d %H:%M:%S")))
    try:
        import json
        args = json.dumps({"frame": a.frame, "start": a.start, "end": a.end, "out": out,
                           "percent": a.percent, "samples": a.samples, "vertical": a.vertical})
        inner = os.path.join(tempfile.gettempdir(), "bmv_render_inner.py")
        with open(inner, "w", encoding="utf-8") as f:
            f.write(INNER)
        cmd = [find_blender(a.blender), "-b", "--disable-autoexec", blend, "--python", inner, "--", args]
        print("[render_scene]", " ".join(cmd[:4]), "...")
        return subprocess.call(cmd)
    finally:
        os.remove(a.lock)


if __name__ == "__main__":
    sys.exit(main())
