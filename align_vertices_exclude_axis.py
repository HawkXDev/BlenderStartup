bl_info = {
    "name": "Align Vertices with Axis Exclusion",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "Hotkey (Shift+X)",
    "description": "Pie Menu for Aligning Vertices with Axis Exclusion",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import bpy
import bmesh

ALIGN_VERTICES_OPERATOR = "mesh.align_vertices_exclude_axis"


class AlignVerticesExcludeAxisOperator(bpy.types.Operator):
    """Align vertices excluding one axis"""
    bl_idname = ALIGN_VERTICES_OPERATOR
    bl_label = "Align Vertices"
    exclude_axis: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.object
        if not obj or obj.mode != 'EDIT':
            self.report({'WARNING'}, "Please enter Edit Mode and select vertices.")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        selected_verts = [v for v in bm.verts if v.select]

        if not selected_verts:
            self.report({'WARNING'}, "No vertices selected.")
            return {'CANCELLED'}

        # Calculate average position
        avg_position = [0.0, 0.0, 0.0]
        for vert in selected_verts:
            avg_position[0] += vert.co.x
            avg_position[1] += vert.co.y
            avg_position[2] += vert.co.z
        avg_position = [coord / len(selected_verts) for coord in avg_position]

        # Align vertices
        for vert in selected_verts:
            if self.exclude_axis == 'X':
                vert.co.y = avg_position[1]
                vert.co.z = avg_position[2]
            elif self.exclude_axis == 'Y':
                vert.co.x = avg_position[0]
                vert.co.z = avg_position[2]
            elif self.exclude_axis == 'Z':
                vert.co.x = avg_position[0]
                vert.co.y = avg_position[1]

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}


class AlignVerticesPieMenu(bpy.types.Menu):
    bl_label = "Align Vertices"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator(ALIGN_VERTICES_OPERATOR, text="Exclude X").exclude_axis = 'X'
        pie.operator(ALIGN_VERTICES_OPERATOR, text="Exclude Y").exclude_axis = 'Y'
        pie.operator(ALIGN_VERTICES_OPERATOR, text="Exclude Z").exclude_axis = 'Z'


addon_keymaps = []


def register():
    bpy.utils.register_class(AlignVerticesExcludeAxisOperator)
    bpy.utils.register_class(AlignVerticesPieMenu)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("wm.call_menu_pie", type='X', value='PRESS', shift=True)
    kmi.properties.name = "AlignVerticesPieMenu"
    addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(AlignVerticesExcludeAxisOperator)
    bpy.utils.unregister_class(AlignVerticesPieMenu)


if __name__ == "__main__":
    register()
