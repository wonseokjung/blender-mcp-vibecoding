#!/usr/bin/env python3
"""Download a practice scene (.blend) listed in scenes/manifest.json and verify its sha256.

Standard library only. Works on macOS, Windows and Linux with Python 3.8+.

  python tools/get_scene.py --list
  python tools/get_scene.py golden-hour-villa
  python tools/get_scene.py all --out scenes/blend
  python tools/get_scene.py channel-logo-intro --base-url http://localhost:8000/

The default download location is the GitHub Release named in the manifest
(base_url). Use --base-url or the BMV_BASE_URL environment variable for a mirror.

CONNECT AI LAB
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_MANIFEST = os.path.join(ROOT, "scenes", "manifest.json")
CHUNK = 1024 * 1024


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.1f %s" % (n, unit) if unit != "B" else "%d B" % n
        n /= 1024.0


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def download(url, dest, expected_bytes=None):
    part = dest + ".part"
    have = os.path.getsize(part) if os.path.exists(part) else 0
    req = urllib.request.Request(url, headers={"User-Agent": "blender-mcp-vibecoding/1.0"})
    if have:
        req.add_header("Range", "bytes=%d-" % have)
    with urllib.request.urlopen(req, timeout=60) as resp:
        if have and resp.status != 206:  # server ignored the range: start over
            have = 0
        total = resp.headers.get("Content-Length")
        total = (int(total) + have) if total else expected_bytes
        mode = "ab" if have else "wb"
        done, t0, last = have, time.time(), 0.0
        with open(part, mode) as out:
            while True:
                block = resp.read(CHUNK)
                if not block:
                    break
                out.write(block)
                done += len(block)
                now = time.time()
                if now - last > 0.5:
                    last = now
                    speed = (done - have) / max(now - t0, 1e-6)
                    pct = (" %5.1f%%" % (100.0 * done / total)) if total else ""
                    sys.stdout.write("\r  %s / %s%s  %s/s   " % (human(done), human(total) if total else "?", pct, human(speed)))
                    sys.stdout.flush()
    sys.stdout.write("\r  %s downloaded%s\n" % (human(done), " " * 30))
    os.replace(part, dest)


def main():
    ap = argparse.ArgumentParser(description="Download CONNECT AI LAB practice scenes for Blender MCP.")
    ap.add_argument("scene", nargs="?", help="scene id from the manifest, or 'all'")
    ap.add_argument("--list", action="store_true", help="list scenes and exit")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--base-url", default=os.environ.get("BMV_BASE_URL"), help="override the manifest base_url")
    ap.add_argument("--out", default=os.path.join(ROOT, "scenes", "blend"), help="output folder")
    ap.add_argument("--force", action="store_true", help="download again even if a verified file exists")
    a = ap.parse_args()

    with open(a.manifest, encoding="utf-8") as f:
        man = json.load(f)
    scenes = man["scenes"]

    if a.list or not a.scene:
        print("Scenes (%s v%s):" % (man.get("name", ""), man.get("version", "")))
        for s in scenes:
            print("  %-28s %9s  %-12s %s" % (s["id"], human(s["bytes"]), s.get("level", ""), s["title_en"]))
        if not a.scene:
            print("\nUsage: python tools/get_scene.py <scene-id|all>")
        return 0

    base = a.base_url or man["base_url"]
    if not base.endswith("/"):
        base += "/"
    todo = scenes if a.scene == "all" else [s for s in scenes if s["id"] == a.scene]
    if not todo:
        print("Unknown scene '%s'. Use --list." % a.scene)
        return 2
    os.makedirs(a.out, exist_ok=True)

    failed = 0
    for s in todo:
        dest = os.path.join(a.out, s["file"])
        print("%s  (%s)" % (s["title_en"], human(s["bytes"])))
        if os.path.exists(dest) and not a.force:
            print("  already here, checking sha256 ...")
            if sha256_of(dest) == s["sha256"]:
                print("  OK  %s" % dest)
                continue
            print("  checksum differs, downloading again")
        url = urllib.parse.urljoin(base, urllib.parse.quote(s["release_asset"]))
        print("  from %s" % url)
        try:
            download(url, dest, s["bytes"])
        except Exception as e:  # network errors, 404 ...
            print("  download failed: %s" % e)
            failed += 1
            continue
        got = sha256_of(dest)
        if got != s["sha256"]:
            print("  sha256 MISMATCH (expected %s, got %s). File kept as %s.bad" % (s["sha256"], got, dest))
            os.replace(dest, dest + ".bad")
            failed += 1
        else:
            print("  sha256 OK  %s" % dest)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
