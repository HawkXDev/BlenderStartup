bl_info = {
    "name": "Manipulator Pie Menu",
    "author": "Your Name",
    "version": (1, 6),
    "blender": (3, 6, 0),
    "location": "Hotkey (Alt+Space)",
    "description": "Pie Menu for toggling manipulators (location, rotation, scale, gizmo)",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import bpy


class WM_OT_ToggleExclusiveGizmo(bpy.types.Operator):
    """Toggle a single gizmo and disable others"""
    bl_idname = "wm.toggle_exclusive_gizmo"
    bl_label = "Toggle Exclusive Gizmo"
    bl_options = {'UNDO'}

    gizmo: bpy.props.StringProperty()

    def execute(self, context):
        space = context.space_data

        # Переключаем целевой гизмо
        if self.gizmo == "translate":
            space.show_gizmo_object_translate = True
            space.show_gizmo_object_rotate = False
            space.show_gizmo_object_scale = False
        elif self.gizmo == "rotate":
            space.show_gizmo_object_translate = False
            space.show_gizmo_object_rotate = True
            space.show_gizmo_object_scale = False
        elif self.gizmo == "scale":
            space.show_gizmo_object_translate = False
            space.show_gizmo_object_rotate = False
            space.show_gizmo_object_scale = True
        elif self.gizmo == "none":
            space.show_gizmo_object_translate = False
            space.show_gizmo_object_rotate = False
            space.show_gizmo_object_scale = False

        return {'FINISHED'}


class VIEW3D_MT_ManipulatorPieMenu(bpy.types.Menu):
    """Pie Menu for Manipulators"""
    bl_label = "Manipulator Pie"
    bl_idname = "VIEW3D_MT_manipulator_pie_menu"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # Location Gizmo toggle (слева)
        pie.operator(
            "wm.toggle_exclusive_gizmo",
            text="Location Gizmo",
            icon='ORIENTATION_GLOBAL',
        ).gizmo = "translate"

        # Rotation Gizmo toggle (справа)
        pie.operator(
            "wm.toggle_exclusive_gizmo",
            text="Rotation Gizmo",
            icon='FILE_REFRESH',
        ).gizmo = "rotate"

        # Disable all Gizmos (вверху)
        pie.operator(
            "wm.toggle_exclusive_gizmo",
            text="Disable All Gizmos",
            icon='CANCEL',
        ).gizmo = "none"

        # Scale Gizmo toggle (внизу)
        pie.operator(
            "wm.toggle_exclusive_gizmo",
            text="Scale Gizmo",
            icon='FULLSCREEN_ENTER',
        ).gizmo = "scale"


addon_keymaps = []


def register():
    bpy.utils.register_class(WM_OT_ToggleExclusiveGizmo)
    bpy.utils.register_class(VIEW3D_MT_ManipulatorPieMenu)

    # Добавляем горячую клавишу Alt+Space
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("wm.call_menu_pie", type='SPACE', value='PRESS', alt=True)
    kmi.properties.name = "VIEW3D_MT_manipulator_pie_menu"
    addon_keymaps.append((km, kmi))

    print("Pie menu 'Manipulator Pie' registered with hotkey Alt+Space.")


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(WM_OT_ToggleExclusiveGizmo)
    bpy.utils.unregister_class(VIEW3D_MT_ManipulatorPieMenu)


if __name__ == "__main__":
    register()
