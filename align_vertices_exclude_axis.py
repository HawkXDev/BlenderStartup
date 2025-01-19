bl_info = {
    "name": "Align Vertices with Axis Exclusion and Grouping",
    "author": "Your Name",
    "version": (1, 2),
    "blender": (3, 6, 0),
    "location": "Hotkey (Shift+X)",
    "description": "Pie Menu for Aligning Vertices with Axis Exclusion and Grouping by Distance",
    "warning": "",
    "wiki_url": "",
    "category": "3D View",
}

import bpy
import bmesh
from mathutils import Vector


class AlignVerticesExcludeAxisOperator(bpy.types.Operator):
    """Align vertices excluding one axis"""
    bl_idname = "mesh.align_vertices_exclude_axis"
    bl_label = "Align Vertices"
    bl_options = {'REGISTER', 'UNDO'}

    exclude_axis: bpy.props.EnumProperty(
        name="Exclude Axis",
        description="Axis to exclude from alignment",
        items=[
            ('X', "X", "Exclude X-axis"),
            ('Y', "Y", "Exclude Y-axis"),
            ('Z', "Z", "Exclude Z-axis"),
        ],
        default='X'
    )

    merge_distance: bpy.props.FloatProperty(
        name="Merge Distance",
        description="Maximum distance for grouping vertices",
        default=0.1,
        min=0.0,
        precision=4,
    )

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

        # Group vertices based on distance
        groups = []
        for vert in selected_verts:
            found_group = None
            for group in groups:
                for other_vert in group:
                    if self.is_within_distance(vert.co, other_vert.co):
                        found_group = group
                        break
                if found_group:
                    break
            if found_group:
                found_group.append(vert)
            else:
                groups.append([vert])

        # Align each group
        for group in groups:
            avg_position = Vector((0.0, 0.0, 0.0))
            for vert in group:
                avg_position += vert.co
            avg_position /= len(group)

            for vert in group:
                if self.exclude_axis == 'X':
                    vert.co.y = avg_position.y
                    vert.co.z = avg_position.z
                elif self.exclude_axis == 'Y':
                    vert.co.x = avg_position.x
                    vert.co.z = avg_position.z
                elif self.exclude_axis == 'Z':
                    vert.co.x = avg_position.x
                    vert.co.y = avg_position.y

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}

    def is_within_distance(self, co1, co2):
        """Check if two coordinates are within the merge distance, excluding the selected axis."""
        if self.exclude_axis == 'X':
            dist = (co1.y - co2.y) ** 2 + (co1.z - co2.z) ** 2
        elif self.exclude_axis == 'Y':
            dist = (co1.x - co2.x) ** 2 + (co1.z - co2.z) ** 2
        elif self.exclude_axis == 'Z':
            dist = (co1.x - co2.x) ** 2 + (co1.y - co2.y) ** 2
        return dist <= self.merge_distance ** 2


class AlignVerticesPieMenuMT(bpy.types.Menu):  # Переименовано
    bl_label = "Align Vertices"
    bl_idname = "VIEW3D_MT_align_vertices_pie_menu"  # Исправлено имя

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator("mesh.align_vertices_exclude_axis", text="Exclude X").exclude_axis = 'X'
        pie.operator("mesh.align_vertices_exclude_axis", text="Exclude Y").exclude_axis = 'Y'
        pie.operator("mesh.align_vertices_exclude_axis", text="Exclude Z").exclude_axis = 'Z'


addon_keymaps = []


def register():
    bpy.utils.register_class(AlignVerticesExcludeAxisOperator)
    bpy.utils.register_class(AlignVerticesPieMenuMT)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("wm.call_menu_pie", type='X', value='PRESS', shift=True)
    kmi.properties.name = "VIEW3D_MT_align_vertices_pie_menu"
    addon_keymaps.append((km, kmi))

    print("Pie menu 'Align Vertices' registered with hotkey Shift+X.")


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(AlignVerticesExcludeAxisOperator)
    bpy.utils.unregister_class(AlignVerticesPieMenuMT)


if __name__ == "__main__":
    register()
