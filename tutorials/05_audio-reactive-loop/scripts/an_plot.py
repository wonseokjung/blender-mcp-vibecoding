import json, numpy as np
from PIL import Image, ImageDraw
J = json.load(open("an/analysis.json")); S = np.load("an/spec.npy"); N = J["n"]
W, H = N*4, 96*4
img = np.zeros((H + 240, W, 3), np.uint8)
sp = (np.flipud(S) * 255).astype(np.uint8); sp = np.kron(sp, np.ones((4, 4), np.uint8))
img[:H, :, 0] = sp; img[:H, :, 1] = (sp*0.55).astype(np.uint8); img[:H, :, 2] = (sp*0.25).astype(np.uint8)
im = Image.fromarray(img); d = ImageDraw.Draw(im)
def plot(key, y0, col):
    v = J[key]; pts = [(i*4, y0 + 70 - v[i]*70) for i in range(N)]; d.line(pts, fill=col, width=2); d.text((4, y0), key, fill=col)
plot("kick", H + 5, (0, 255, 65)); plot("bass", H + 80, (200, 200, 200)); plot("speed", H + 160, (255, 170, 60))
for f, c in ((J["fbreak"], (255, 255, 255)), (J["fdrop"], (0, 255, 65))):
    d.line([(f*4, 0), (f*4, H + 240)], fill=c, width=1)
im.save("an/spectrogram.png")
