# villa_14: green roof (grass tufts on the gravel half), lower NE establishing that faces the glowing back band
import bpy, math, sys
import numpy as np
S = bpy.context.scene
exec(compile(open('scripts/villa_veg.py').read().split("rng = np.random.default_rng(11)")[0], 'vv', 'exec'))
rng = np.random.default_rng(5)
xs = np.arange(-0.85, 7.5, 0.3); ys = np.arange(-7.45, 4.3, 0.3)
X, Y = np.meshgrid(xs, ys); X = X.ravel() + rng.uniform(-0.12, 0.12, X.size); Y = Y.ravel() + rng.uniform(-0.12, 0.12, Y.size)
keep = ~((X > 1.8) & (X < 5.7) & (Y > -3.2) & (Y < 1.2))
X, Y = X[keep], Y[keep]
P = np.stack([X, Y, np.full(X.size, 7.0 + 0.27)], 1)
scatter("V_roof_grass", "grass_medium_01_LOD0", P, rng.choice([0, 1, 2, 3, 4, 5], len(P)), rng.uniform(0, 6.283, len(P)), rng.uniform(1.4, 2.4, len(P)))
bpy.data.materials["V_gravel"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.08, 0.05, 1)
cam = bpy.data.objects["Cam"]; tgt = bpy.data.objects["CamTarget"]
def setkey(obj, frame, val):
    obj.location = val; obj.keyframe_insert("location", frame=frame)
setkey(cam, 1, (22, 46, 29)); setkey(tgt, 1, (-3, -6, 1.0))
print("v14 ok", len(P))
