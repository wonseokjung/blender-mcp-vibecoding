# loop_07: bullet time freezes a big spike burst (not a calm sphere), stronger groove spikes, faint always-on etched wordmark, brighter grade
import bpy, json, numpy as np, sys
sys.path.insert(0, 'scripts'); import tlib
W = '../_workB'
J = json.load(open(W + '/audio/an/analysis.json')); N = J["n"]; FB, FD = J["fbreak"], J["fdrop"]
kick = np.array(J["kick"]); bass = np.array(J["bass"]); drop = np.array(J["drop"])
amp = 1.25*(0.05 + 0.30*bass + 0.26*kick)
peak = float(amp[FB-12:FB].max())*1.15                     # the last hit before the silence, frozen
t = np.arange(FD - FB)
amp[FB:FD] = peak*(1.0 - 0.06*t/(FD - FB)) + 0.012*np.sin(t*0.35)*np.exp(-t/25)
amp[FD:] += 0.55*drop[FD:]
ring = 0.35 + 6.0*drop                                        # etched wordmark always faintly visible; flares on the drop
ctrl = bpy.data.objects["CTRL"]
for name, arr in (("amp", amp), ("ring", ring)):
    for fc in tlib._fcurves(ctrl.animation_data.action):
        if fc.data_path == f'["{name}"]':
            for i, kp in enumerate(fc.keyframe_points):
                f = int(round(kp.co[0])) - 1
                v = float(arr[f % N]); kp.co[1] = v; kp.handle_left[1] = v; kp.handle_right[1] = v
            fc.update()
S = bpy.context.scene; S.view_settings.exposure = 0.35; S.view_settings.look = 'AgX - High Contrast'
bpy.data.materials['M_haze'].node_tree.nodes['Principled Volume'].inputs['Density'].default_value = 0.0045
S.frame_set(1); bpy.ops.wm.save_mainfile(); print("l7 ok peak", round(peak, 3))
