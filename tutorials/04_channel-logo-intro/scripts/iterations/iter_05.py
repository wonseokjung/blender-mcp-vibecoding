# channel-intro iter 5: cursor nudged off the B; F12 preview f130 to judge chrome, bloom and the green under AgX
import bpy, os
bpy.data.objects["Cursor"].location.x += 0.1
PREVIEW_FRAME = 130; PREVIEW_OUT = os.path.expanduser("iters/channel-intro/preview_05.png")
exec(open(os.path.expanduser("scripts/preview.py")).read())
