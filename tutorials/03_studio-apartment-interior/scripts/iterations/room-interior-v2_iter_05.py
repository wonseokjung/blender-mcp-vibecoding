# room-interior v2 iter 5 (branding): the scanned frame's placeholder art ("Ray Homes" sample text) replaced by a
# CONNECT AI LAB typographic print; the art's normal map is unplugged so the old lettering can't ghost through
import bpy, os
img = bpy.data.images.get("hanging_picture_frame_01_artwork_diff.png")
img.filepath = os.path.expanduser("brand/room_print_1024.png"); img.reload()
for m in bpy.data.materials:
    if not m.use_nodes: continue
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image and n.image.name.startswith("hanging_picture_frame_01_artwork_nor"):
            for l in list(n.outputs["Color"].links): m.node_tree.links.remove(l)
            print("unplugged normal in", m.name)
bpy.ops.wm.save_mainfile(); print("ok")
