import numpy as np
def shore_y(x):
    x = np.asarray(x, float)
    return -34 + 5*np.sin(x/23.0) + np.maximum(0, -x-22)*1.25 + np.maximum(0, x-60)*0.5

def fbm(x, y, oct=5, base=0.012):
    v = np.zeros_like(x, float); a = 1.0; f = base
    for i in range(oct):
        v += a*np.sin(x*f*6.283 + i*1.7 + np.cos(y*f*4.1 + i)) * np.cos(y*f*6.283*0.83 + i*2.3 + np.sin(x*f*3.3))
        a *= 0.5; f *= 2.03
    return v

SEA = -14.0
def height(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    d = y - shore_y(x)                                  # >0 land
    cliff = SEA - 1.5 + (13.5 + 1.2)*np.clip((d + 1.5)/9.0, 0, 1)**0.7   # rises from sea to plateau (~-0.3)
    behind = np.maximum(0, y - 14)
    hills = 0.16*behind + 0.0009*behind**2 + 9*np.clip(behind/80, 0, 1)*(fbm(x, y)*0.6 + 0.4)
    side = np.clip((x - 22)/40, 0, 1) * 6 * (fbm(x*1.3, y*1.3) * 0.5 + 0.5)
    z = np.where(d < 0, SEA - 2.0 + d*0.08, cliff) + hills + side*np.clip(d/10, 0, 1)
    # villa pad
    pad = np.clip(1 - (np.maximum(np.abs(x) - 18, 0)/6.0), 0, 1) * np.clip(1 - np.maximum(np.abs(y + 2) - 13, 0)/6.0, 0, 1)
    z = z*(1-pad) + (-0.35)*pad
    z += 0.25*fbm(x, y, 3, 0.06)*np.clip(d/6, 0, 1)*(1-pad)
    return z

