# channel-intro iter 6: word spaces read too tight ("CONNECT AI LAB" ran together) -> +0.16 per space, recentred,
# underline/cursor refit; left letters dull -> stronger left soft light; then re-run the iter-4 animation build
import bpy, os
names = sorted([o.name for o in bpy.data.objects if o.name.startswith("L") and o.type == 'FONT'])
for o in (bpy.data.objects[n] for n in names): o.animation_data_clear()
home = {n: list(bpy.data.objects[n]["home"]) for n in names}
for n in names:
    i = int(n[1:3]); home[n][0] += 0.16 * ((i >= 8) + (i >= 11))
xs = [home[n][0] for n in names]; right = home[names[-1]][0] + bpy.data.objects[names[-1]].dimensions.x
mid = (min(xs) + right) / 2
for n in names:
    home[n][0] -= mid; o = bpy.data.objects[n]; o["home"] = tuple(home[n]); o.location = home[n]
left, right = min(xs) - mid, right - mid
ul = bpy.data.objects["Underline"]; ul.animation_data_clear(); ul["W"] = right - left; ul.scale.x = right - left; ul.location.x = (left + right) / 2
cu = bpy.data.objects["Cursor"]; cu.animation_data_clear(); cu.location.x = right + 0.38
bpy.data.objects["Soft1"].data.energy = 1100
exec(open(os.path.expanduser("scripts/intro_04.py")).read())
PREVIEW_FRAME = 130; PREVIEW_OUT = os.path.expanduser("iters/channel-intro/preview_06.png")
exec(open(os.path.expanduser("scripts/preview.py")).read())
