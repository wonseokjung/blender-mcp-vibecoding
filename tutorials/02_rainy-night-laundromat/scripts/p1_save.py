LOOKDEV = False; STAGE = 9; SHOW_FRAME = 1
exec(open("scripts/p1_build.py").read())
import bpy
bpy.context.scene.render.engine = 'CYCLES'
print(save_blend('p1_laundry'))
