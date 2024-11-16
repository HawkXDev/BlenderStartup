bl_info = {
    "name": "Align View to Active with Orthographic",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "Hotkey (Shift+Q)",
    "description": "Pie Menu for Aligning View to Active with Orthographic View",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import bpy


class VIEW3D_OT_AlignViewToActive(bpy.types.Operator):
    """Align view to active direction"""
    bl_idname = "view3d.align_view_to_active_geometry"
    bl_label = "Align View to Active"
    bl_description = "Align view to active direction"
    axis: bpy.props.StringProperty()

    def execute(self, context):
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

        context.space_data.region_3d.view_perspective = 'ORTHO'
        return {'FINISHED'}


class VIEW3D_MT_AlignViewToActivePie(bpy.types.Menu):
    bl_label = "Align View to Active"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator("view3d.align_view_to_active_geometry", text="Top", icon='TRIA_UP').axis = 'TOP'
        pie.operator("view3d.align_view_to_active_geometry", text="Bottom", icon='TRIA_DOWN').axis = 'BOTTOM'
        pie.operator("view3d.align_view_to_active_geometry", text="Front", icon='FORWARD').axis = 'FRONT'
        pie.operator("view3d.align_view_to_active_geometry", text="Back", icon='BACK').axis = 'BACK'
        pie.operator("view3d.align_view_to_active_geometry", text="Right", icon='TRIA_RIGHT').axis = 'RIGHT'
        pie.operator("view3d.align_view_to_active_geometry", text="Left", icon='TRIA_LEFT').axis = 'LEFT'


addon_keymaps = []


def register():
    bpy.utils.register_class(VIEW3D_OT_AlignViewToActive)
    bpy.utils.register_class(VIEW3D_MT_AlignViewToActivePie)
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("wm.call_menu_pie", type='Q', value='PRESS', shift=True)
    kmi.properties.name = "VIEW3D_MT_AlignViewToActivePie"
    addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(VIEW3D_OT_AlignViewToActive)
    bpy.utils.unregister_class(VIEW3D_MT_AlignViewToActivePie)


if __name__ == "__main__":
    register()
