bl_info = {
    "name": "Join Nearest Vertices",
    "author": "Your Name",
    "version": (1, 3),
    "blender": (3, 6, 0),
    "location": "Hotkey (Shift+Alt+J)",
    "description": "Join nearest vertices between two groups using Join (J)",
    "warning": "",
    "wiki_url": "",
    "category": "Mesh",
}

import bpy
import bmesh


class JoinNearestVerticesOperator(bpy.types.Operator):
    """Join nearest vertices between two groups using J"""
    bl_idname = "mesh.join_nearest_vertices"
    bl_label = "Join Nearest Vertices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.mode != 'EDIT':
            self.report({'WARNING'}, "Please enter Edit Mode and select vertices.")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        selected_verts = [v for v in bm.verts if v.select]

        if len(selected_verts) < 2:
            self.report({'WARNING'}, "At least two vertices must be selected.")
            return {'CANCELLED'}

        # Find groups of connected vertices among the selected ones
        groups = self.find_vertex_groups(selected_verts, bm)

        if len(groups) != 2:
            self.report({'WARNING'},
                        f"Two separate groups of connected vertices are required. Found {len(groups)} groups.")
            return {'CANCELLED'}

        group1, group2 = groups

        # Find nearest pairs between two groups
        pairs = self.find_nearest_pairs(group1, group2)

        if not pairs:
            self.report({'WARNING'}, "No nearest pairs found between groups.")
            return {'CANCELLED'}

        # Create join cuts between pairs
        for v1, v2 in pairs:
            self.create_join_cut(bm, v1, v2)

        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'}, f"Joined {len(pairs)} vertex pairs using J.")
        return {'FINISHED'}

    def find_vertex_groups(self, verts, bm):
        """Find connected groups of selected vertices"""
        groups = []
        visited = set()

        def dfs(v, group):
            stack = [v]
            while stack:
                current = stack.pop()
                if current not in visited:
                    visited.add(current)
                    group.append(current)
                    stack.extend(e.other_vert(current) for e in current.link_edges if e.other_vert(current).select)

        for vert in verts:
            if vert not in visited:
                group = []
                dfs(vert, group)
                if group:  # Ensure the group is not empty
                    groups.append(group)

        return groups

    def find_nearest_pairs(self, group1, group2):
        """Find nearest pairs of vertices between two groups"""
        pairs = []
        for v1 in group1:
            nearest_v2 = min(group2, key=lambda v2: (v1.co - v2.co).length)
            pairs.append((v1, nearest_v2))
        return pairs

    def create_join_cut(self, bm, v1, v2):
        """Create a join (J) cut between two vertices"""
        bpy.ops.mesh.select_all(action='DESELECT')  # Deselect all
        v1.select = True
        v2.select = True
        bpy.ops.mesh.vert_connect_path()  # Join vertices with J


class JoinNearestPieMenu(bpy.types.Menu):
    """Pie Menu for Join Nearest Vertices"""
    bl_label = "Join Nearest Vertices"
    bl_idname = "VIEW3D_MT_join_nearest_pie_menu"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator(JoinNearestVerticesOperator.bl_idname, text="Join Nearest Vertices")


addon_keymaps = []


def register():
    bpy.utils.register_class(JoinNearestVerticesOperator)
    bpy.utils.register_class(JoinNearestPieMenu)

    # Register hotkey
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    # kmi = km.keymap_items.new("wm.call_menu_pie", type='J', value='PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("wm.call_menu_pie", type='J', value='PRESS', shift=True)
    kmi.properties.name = JoinNearestPieMenu.bl_idname
    addon_keymaps.append((km, kmi))

    print("Pie menu 'Join Nearest Vertices' registered with hotkey Shift+J.")


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(JoinNearestVerticesOperator)
    bpy.utils.unregister_class(JoinNearestPieMenu)


if __name__ == "__main__":
    register()
