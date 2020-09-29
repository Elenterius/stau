#!/usr/bin/env python3
import bpy
import bmesh


def main(context):
    # external file execution in blender
    filename = "E:\\PycharmProjects\\stau\\sod_utils\\sod_importer_blender.py"
    exec(compile(open(filename).read(), filename, 'exec'))


class RunExternalScriptOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.run_external_script"
    bl_label = "Run External Script"

    # @classmethod
    # def poll(cls, context):
    #     return context.active_object is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(RunExternalScriptOperator)


def unregister():
    bpy.utils.unregister_class(RunExternalScriptOperator)


if __name__ == "__main__":
    register()
