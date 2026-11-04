# generic small F12 preview: set PREVIEW_FRAME / PREVIEW_OUT before exec
import bpy, os, time
s = bpy.context.scene; s.frame_set(PREVIEW_FRAME)
fp, pct, spp = s.render.filepath, s.render.resolution_percentage, s.eevee.taa_render_samples
s.render.resolution_percentage = 50; s.eevee.taa_render_samples = 32; s.render.filepath = PREVIEW_OUT
t0 = time.time(); bpy.ops.render.render(write_still=True); print("render s", round(time.time() - t0, 2))
s.render.filepath, s.render.resolution_percentage, s.eevee.taa_render_samples = fp, pct, spp
