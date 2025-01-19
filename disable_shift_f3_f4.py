bl_info = {
    "name": "Remap Shift+F4 and Shift+F3",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "3D Viewport",
    "description": "Remaps Shift+F4 and Shift+F3 to print a message in the console",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import bpy

addon_keymaps = []


class PrintShiftF4Operator(bpy.types.Operator):
    """Print Shift+F4 Message"""
    bl_idname = "view3d.print_shift_f4"
    bl_label = "Shift+F4 Action"

    def execute(self, context):
        print("Shift+F4 was pressed in 3D Viewport!")
        return {'FINISHED'}


class PrintShiftF3Operator(bpy.types.Operator):
    """Print Shift+F3 Message"""
    bl_idname = "view3d.print_shift_f3"
    bl_label = "Shift+F3 Action"

    def execute(self, context):
        print("Shift+F3 was pressed in 3D Viewport!")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(PrintShiftF4Operator)
    bpy.utils.register_class(PrintShiftF3Operator)

    # Добавляем новые горячие клавиши
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type="VIEW_3D")

    # Переназначение Shift+F4
    kmi = km.keymap_items.new("view3d.print_shift_f4", type="F4", value="PRESS", shift=True)
    addon_keymaps.append((km, kmi))

    # Переназначение Shift+F3
    kmi = km.keymap_items.new("view3d.print_shift_f3", type="F3", value="PRESS", shift=True)
    addon_keymaps.append((km, kmi))

    print("Shift+F4 and Shift+F3 remapped in 3D Viewport!")


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(PrintShiftF4Operator)
    bpy.utils.unregister_class(PrintShiftF3Operator)

    print("Shift+F4 and Shift+F3 remappings removed.")


if __name__ == "__main__":
    register()
