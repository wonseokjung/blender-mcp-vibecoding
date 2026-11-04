# room-interior v2 iter 6 (after the first GPU render): we were looking at the BACK of the scanned frame (cardboard +
# wire; its front faces -Y already, so the 180 deg turn was wrong) -> 0 deg; floor-plan labels read pale grey (the dark
# text mirrored the bright sky at grazing angles) -> specular 0, rough 1, darker ink
import bpy
o = bpy.data.objects["hanging_picture_frame_01"]; o.rotation_euler = (0, 0, 0); o.location.y = 1.975
p = bpy.data.materials["Label"].node_tree.nodes["Principled BSDF"]
p.inputs["Specular IOR Level"].default_value = 0.0; p.inputs["Roughness"].default_value = 1.0; p.inputs["Base Color"].default_value = (0.02, 0.02, 0.022, 1)
bpy.ops.wm.save_mainfile(); print("ok")
