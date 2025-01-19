bl_info = {
    "name": "Align View to Active with Orthographic",
    "author": "Your Name",
    "version": (1, 1),
    "blender": (3, 6, 0),
    "location": "Hotkey (Shift+Q)",
    "description": "Pie Menu for Aligning View to Active with Orthographic View",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import bpy
import math
import mathutils

ALIGN_VIEW_OPERATOR = "view3d.align_view_to_active_geometry"


class AlignViewToActiveOperator(bpy.types.Operator):
    bl_idname = ALIGN_VIEW_OPERATOR
    bl_label = "Align View to Active"
    bl_description = "Align view to active direction"
    axis: bpy.props.StringProperty()

    def execute(self, _context):
        region_3d = bpy.context.space_data.region_3d

        if self.axis == 'TOP':
            bpy.ops.view3d.view_axis(type='TOP', align_active=True)
        elif self.axis == 'BOTTOM':
            bpy.ops.view3d.view_axis(type='BOTTOM', align_active=True)
        elif self.axis == 'FRONT':
            bpy.ops.view3d.view_axis(type='FRONT', align_active=True)
        elif self.axis == 'BACK':
            bpy.ops.view3d.view_axis(type='BACK', align_active=True)
        elif self.axis == 'RIGHT':
            bpy.ops.view3d.view_axis(type='RIGHT', align_active=True)
        elif self.axis == 'LEFT':
            bpy.ops.view3d.view_axis(type='LEFT', align_active=True)
        elif self.axis == 'TOP_FLIP':
            flip_rotation = mathutils.Matrix.Rotation(math.pi, 4, 'Z')
            region_3d.view_rotation = region_3d.view_rotation @ flip_rotation.to_quaternion()
        elif self.axis == 'FRONT_FLIP':
            flip_rotation = mathutils.Matrix.Rotation(math.pi, 4, 'Y')
            region_3d.view_rotation = region_3d.view_rotation @ flip_rotation.to_quaternion()

        bpy.context.space_data.region_3d.view_perspective = 'ORTHO'
        return {'FINISHED'}


class VIEW3D_MT_AlignViewToActivePieMenu(bpy.types.Menu):  # Имя меню изменено
    bl_label = "Align View to Active"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator(ALIGN_VIEW_OPERATOR, text="Top", icon='TRIA_UP').axis = 'TOP'
        pie.operator(ALIGN_VIEW_OPERATOR, text="Bottom", icon='TRIA_DOWN').axis = 'BOTTOM'
        pie.operator(ALIGN_VIEW_OPERATOR, text="Front", icon='FORWARD').axis = 'FRONT'
        pie.operator(ALIGN_VIEW_OPERATOR, text="Back", icon='BACK').axis = 'BACK'
        pie.operator(ALIGN_VIEW_OPERATOR, text="Right", icon='TRIA_RIGHT').axis = 'RIGHT'
        pie.operator(ALIGN_VIEW_OPERATOR, text="Left", icon='TRIA_LEFT').axis = 'LEFT'
        pie.operator(ALIGN_VIEW_OPERATOR, text="Top Flip", icon='TRIA_UP_BAR').axis = 'TOP_FLIP'
        pie.operator(ALIGN_VIEW_OPERATOR, text="Front Flip", icon='FORWARD').axis = 'FRONT_FLIP'


addon_keymaps = []


def register():
    bpy.utils.register_class(AlignViewToActiveOperator)
    bpy.utils.register_class(VIEW3D_MT_AlignViewToActivePieMenu)
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("wm.call_menu_pie", type='Q', value='PRESS', shift=True)
    kmi.properties.name = "VIEW3D_MT_AlignViewToActivePieMenu"
    addon_keymaps.append((km, kmi))

    print("Pie menu 'Align View to Active' registered with hotkey Shift+Q.")


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(AlignViewToActiveOperator)
    bpy.utils.unregister_class(VIEW3D_MT_AlignViewToActivePieMenu)  # Изменено имя


if __name__ == "__main__":
    register()
