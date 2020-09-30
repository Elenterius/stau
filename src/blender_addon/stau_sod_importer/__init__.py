# noinspection PyUnresolvedReferences
import bpy

bl_info = {
    "name": "Storm3D SOD Format (.sod)",
    "author": "Elenterius",
    "version": (0, 4),
    "blender": (2, 80, 0),
    "location": "File > Import > Storm3D SOD",
    "description": "Importer/Exporter for model files from Star Trek Armada I & II",
    "category": "Import-Export",
}

from . import stau_sod_import


# Registration
def menu_func_import(self, context):
    self.layout.operator(stau_sod_import.ImportSodData.bl_idname, text="Storm3D SOD (.sod)")


def register():
    bpy.utils.register_class(stau_sod_import.ImportSodData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(stau_sod_import.ImportSodData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
