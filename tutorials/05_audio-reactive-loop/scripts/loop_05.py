# loop_05: light linking (rim -> hero only, graze -> canyon only) + low grazing light that reveals the spectrogram ridges
import bpy, sys
sys.path.insert(0, 'scripts')
import tlib
S = bpy.context.scene
def coll(name, objs):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    for o in objs:
        if o.name not in c.objects: c.objects.link(o)
    return c
hero_c = coll("LL_hero", [bpy.data.objects["Hero"], bpy.data.objects["Iris"]])
can_c = coll("LL_canyon", [bpy.data.objects["Canyon"]])
rim = bpy.data.objects["Rim"]; rim.light_linking.receiver_collection = hero_c
if "Graze" in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects["Graze"], do_unlink=True)
g = tlib.area("Graze", (0, 60, 1.2), (0, 0, 0.5), energy=9000, size=30, color=(0.75, 0.85, 1.0)); g.data.size_y = 1.5
g.visible_camera = False; g.light_linking.receiver_collection = can_c
print("l5 ok")
