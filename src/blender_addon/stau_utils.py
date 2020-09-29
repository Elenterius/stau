# noinspection PyUnresolvedReferences
import bpy


def set_view3d_shading(mode="SOLID", screens=[]):
    screens = screens if screens else [bpy.context.screen]
    for s in screens:
        for spc in s.areas:
            if spc.type == "VIEW_3D":
                spc.spaces[0].shading.type = mode
                break
