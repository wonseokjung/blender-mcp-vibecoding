# loop_post.py: copy frames, add a short chroma split exactly on the drop (analysis-driven), verify the loop seam numerically
import json, os, shutil, numpy as np
from PIL import Image
W = "../_workB"
J = json.load(open(W + "/audio/an/analysis.json")); FD = J["fdrop"]; N = J["n"]
src, dst = W + "/frames/loop_v2", W + "/frames/loop_v2_post"; os.makedirs(dst, exist_ok=True)
for i in range(1, N + 1):
    a = f"{src}/f_{i:04d}.png"; b = f"{dst}/f_{i:04d}.png"
    k = i - (FD + 1)                                     # frame index FD (0-based) == Blender frame FD+1
    if 0 <= k < 6:
        im = np.asarray(Image.open(a).convert("RGB")).astype(np.int16)
        s = int(round(14*np.exp(-k/1.6)*(0.5 + 0.5*J["drop"][FD + k])))
        out = im.copy()
        out[:, s:, 0] = im[:, :-s, 0] if s else im[:, :, 0]
        out[:, :-s or None, 2] = im[:, s:, 2] if s else im[:, :, 2]
        Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(b)
    else:
        shutil.copyfile(a, b)
def mad(p, q):
    x = np.asarray(Image.open(p).convert("L").resize((480, 270))).astype(np.float32)
    y = np.asarray(Image.open(q).convert("L").resize((480, 270))).astype(np.float32)
    return float(np.abs(x - y).mean())
d = [mad(f"{dst}/f_{i:04d}.png", f"{dst}/f_{i+1:04d}.png") for i in range(1, N)]
seam = mad(f"{dst}/f_{N:04d}.png", f"{dst}/f_0001.png")
rep = dict(seam_diff=round(seam, 3), median_consecutive=round(float(np.median(d)), 3), mean_consecutive=round(float(np.mean(d)), 3),
           p90_consecutive=round(float(np.percentile(d, 90)), 3), seam_percentile=round(float((np.array(d) < seam).mean()*100), 1))
json.dump(rep, open(W + "/logs/loop_v2_seam.json", "w"), indent=1); print(rep)
