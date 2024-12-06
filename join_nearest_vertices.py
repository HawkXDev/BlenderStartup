bl_info = {
    "name": "Join and Equalize Vertices",
    "author": "Your Name",
    "version": (1, 6),
    "blender": (3, 6, 0),
    "location": "Hotkey (Shift+J)",
    "description": "Join nearest vertices and equalize distances between two groups",
    "warning": "",
    "wiki_url": "",
    "category": "Mesh",
}

import bpy
import bmesh
from mathutils import Vector


class EqualizeDistancesOperator(bpy.types.Operator):
    """Equalize distances along edges between two selected groups of vertices"""
    bl_idname = "mesh.equalize_distances"
    bl_label = "Equalize Distances"
    bl_options = {'REGISTER', 'UNDO'}

    distance_factor: bpy.props.FloatProperty(
        name="Distance Factor",
        description="Position factor along the edges (0: near first group, 1: original position, >1: further from first group)",
        default=0.5,
        min=0.0,
        max=10.0,
        step=0.1,
        precision=2
    )

    equalize_lengths: bpy.props.BoolProperty(
        name="Equalize Edge Lengths",
        description="If enabled, make all connecting edges the same length",
        default=False
    )

    orthogonal_to_curve: bpy.props.BoolProperty(
        name="Make Orthogonal to Curve",
        description="If enabled, adjust edges to be orthogonal in the plane",
        default=False
    )

    def execute(self, context):
        obj = context.object
        if not obj or obj.mode != 'EDIT':
            self.report({'WARNING'}, "Please enter Edit Mode and select vertices.")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        selected_verts = [v for v in bm.verts if v.select]

        if len(selected_verts) < 2:
            self.report({'WARNING'}, "At least two groups of vertices must be selected.")
            return {'CANCELLED'}

        group1, group2 = self.identify_groups(selected_verts)

        if not group1 or not group2:
            self.report({'WARNING'}, "Could not identify two groups of vertices.")
            return {'CANCELLED'}

        average_length = None
        if self.equalize_lengths:
            total_length = sum(e.calc_length() for v2 in group2 for e in v2.link_edges if e.other_vert(v2) in group1)
            edge_count = sum(1 for v2 in group2 for e in v2.link_edges if e.other_vert(v2) in group1)
            if edge_count == 0:
                self.report({'WARNING'}, "No connecting edges found.")
                return {'CANCELLED'}
            average_length = total_length / edge_count

        for v2 in group2:
            connected_edges = [e for e in v2.link_edges if e.other_vert(v2) in group1]
            if not connected_edges:
                continue

            avg_pos = Vector((0.0, 0.0, 0.0))
            for edge in connected_edges:
                v1 = edge.other_vert(v2)
                edge_length = edge.calc_length() if not self.equalize_lengths else average_length

                if self.orthogonal_to_curve:
                    # Calculate the tangent and normal in the plane
                    neighbors = [e.other_vert(v1) for e in v1.link_edges if e.other_vert(v1) != v2]
                    if len(neighbors) < 2:
                        continue  # Need at least two neighbors to calculate a normal

                    tangent = (neighbors[1].co - neighbors[0].co).normalized()
                    edge_vec = (v2.co - v1.co).normalized()
                    projection = edge_vec - tangent * edge_vec.dot(tangent)

                    # Correct projection length with distance_factor
                    projection_length = edge_length * self.distance_factor
                    target_pos = v1.co + projection.normalized() * projection_length

                    avg_pos += target_pos
                else:
                    # Standard behavior
                    direction = (v2.co - v1.co).normalized()
                    target_pos = v1.co + direction * edge_length
                    avg_pos += v1.co + (target_pos - v1.co) * self.distance_factor

            avg_pos /= len(connected_edges)
            v2.co = avg_pos

        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'},
                    f"Distances equalized{' with orthogonal adjustment' if self.orthogonal_to_curve else ''}.")
        return {'FINISHED'}

    def identify_groups(self, selected_verts):
        midpoint = len(selected_verts) // 2
        group1 = selected_verts[:midpoint]
        group2 = selected_verts[midpoint:]
        return group1, group2


class JoinNearestVerticesOperator(bpy.types.Operator):
    """Join nearest vertices between two groups"""
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
        self.report({'INFO'}, f"Joined {len(pairs)} vertex pairs.")
        return {'FINISHED'}

    def find_vertex_groups(self, verts, bm):
        """Find connected groups of selected vertices"""
        visited = set()
        groups = []

        def dfs(vertex, group):
            stack = [vertex]
            while stack:
                current = stack.pop()
                if current not in visited:
                    visited.add(current)
                    group.append(current)
                    for edge in current.link_edges:
                        neighbor = edge.other_vert(current)
                        if neighbor in verts and neighbor not in visited:
                            stack.append(neighbor)

        for v in verts:
            if v not in visited:
                group = []
                dfs(v, group)
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
        """Create a join cut between two vertices"""
        bpy.ops.mesh.select_all(action='DESELECT')
        v1.select = True
        v2.select = True
        bpy.ops.mesh.vert_connect_path()


class JoinNearestPieMenu(bpy.types.Menu):
    """Pie Menu for Join and Equalize Vertices"""
    bl_label = "Join and Equalize Vertices"
    bl_idname = "VIEW3D_MT_join_nearest_pie_menu"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator(JoinNearestVerticesOperator.bl_idname, text="Join Nearest Vertices")
        pie.operator(EqualizeDistancesOperator.bl_idname, text="Equalize Distances")


addon_keymaps = []


def register():
    bpy.utils.register_class(JoinNearestVerticesOperator)
    bpy.utils.register_class(EqualizeDistancesOperator)
    bpy.utils.register_class(JoinNearestPieMenu)

    # Register hotkey
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("wm.call_menu_pie", type='J', value='PRESS', shift=True)
    kmi.properties.name = JoinNearestPieMenu.bl_idname
    addon_keymaps.append((km, kmi))

    print("Pie menu 'Join and Equalize Vertices' registered with hotkey Shift+J.")


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(JoinNearestVerticesOperator)
    bpy.utils.unregister_class(EqualizeDistancesOperator)
    bpy.utils.unregister_class(JoinNearestPieMenu)


if __name__ == "__main__":
    register()
