bl_info = {
    "name": "Join and Equalize Vertices",
    "author": "Your Name",
    "version": (1, 7),
    "blender": (3, 6, 0),
    "location": "Hotkey (Shift+J)",
    "description": "Join nearest vertices, equalize distances, and manage vertex groups",
    "warning": "",
    "wiki_url": "",
    "category": "Mesh",
}

import bpy
import bmesh
from mathutils import Vector


class EqualizeDistancesOperator(bpy.types.Operator):
    """Equalize distances along edges between a saved base group and selected vertices"""
    bl_idname = "mesh.equalize_distances"
    bl_label = "Equalize Distances"
    bl_options = {'REGISTER', 'UNDO'}

    distance_factor: bpy.props.FloatProperty(
        name="Distance Factor",
        description="Position factor along the perpendicular (0: at base, 1: at original, >1: further from base)",
        default=1.0,
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
        description="If enabled, adjust edges to be orthogonal to the curve",
        default=False
    )

    def execute(self, context):
        obj = context.object
        if not obj or obj.mode != 'EDIT':
            self.report({'WARNING'}, "Please enter Edit Mode and select vertices.")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        if "base_group" not in obj or not obj["base_group"]:
            self.report({'WARNING'}, "No base group set. Please save a base group first.")
            return {'CANCELLED'}

        selected_verts = [v for v in bm.verts if v.select]
        if len(selected_verts) < 1:
            self.report({'WARNING'}, "At least one vertex must be selected for the second group.")
            return {'CANCELLED'}

        group1 = [bm.verts[i] for i in obj["base_group"] if i < len(bm.verts)]
        group2 = selected_verts

        # Calculate average edge length if equalize lengths is enabled
        average_length = None
        if self.equalize_lengths:
            total_length = sum(e.calc_length() for v2 in group2 for e in v2.link_edges if e.other_vert(v2) in group1)
            edge_count = sum(1 for v2 in group2 for e in v2.link_edges if e.other_vert(v2) in group1)
            if edge_count == 0:
                self.report({'WARNING'}, "No connecting edges found.")
                return {'CANCELLED'}
            average_length = total_length / edge_count

        for v2 in group2:
            closest_base = min(group1, key=lambda bv: (v2.co - bv.co).length)
            neighbors = [e.other_vert(closest_base) for e in closest_base.link_edges if
                         e.other_vert(closest_base) in group1]

            if not neighbors:
                continue  # Skip if no neighbors

            # Get local tangent based on one or two neighbors
            if len(neighbors) == 1:
                local_tangent = (closest_base.co - neighbors[0].co).normalized()
            else:
                neighbor1, neighbor2 = neighbors[:2]
                local_tangent = (neighbor2.co - neighbor1.co).normalized()

            perpendicular = local_tangent.cross((v2.co - closest_base.co)).normalized().cross(
                local_tangent).normalized()

            # Calculate new position
            if self.orthogonal_to_curve:
                edge_length = average_length if self.equalize_lengths else (v2.co - closest_base.co).length
                new_position = closest_base.co + perpendicular * edge_length * self.distance_factor
            else:
                direction = (v2.co - closest_base.co).normalized()
                edge_length = average_length if self.equalize_lengths else (v2.co - closest_base.co).length
                new_position = closest_base.co + direction * edge_length * self.distance_factor

            v2.co = new_position  # Apply new position

        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'}, "Equalized distances relative to base group.")
        return {'FINISHED'}


class SaveBaseGroupOperator(bpy.types.Operator):
    """Save the current selection as a base group"""
    bl_idname = "mesh.save_base_group"
    bl_label = "Save Base Group"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.mode != 'EDIT':
            self.report({'WARNING'}, "Please enter Edit Mode and select vertices.")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        selected_verts = [v.index for v in bm.verts if v.select]
        if not selected_verts:
            self.report({'WARNING'}, "No vertices selected.")
            return {'CANCELLED'}

        obj["base_group"] = selected_verts
        self.report({'INFO'}, f"Saved {len(selected_verts)} vertices as base group.")
        return {'FINISHED'}


class EqualizeDistancesSubMenu(bpy.types.Menu):
    """Submenu for Equalize Distances"""
    bl_label = "Equalize Distances Options"
    bl_idname = "VIEW3D_MT_equalize_distances_submenu"

    def draw(self, context):
        layout = self.layout
        layout.operator(SaveBaseGroupOperator.bl_idname, text="Save Base Group")
        layout.operator(EqualizeDistancesOperator.bl_idname, text="Equalize to Base Group")


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

        groups = self.find_vertex_groups(selected_verts, bm)

        if len(groups) != 2:
            self.report({'WARNING'}, "Two separate groups of connected vertices are required.")
            return {'CANCELLED'}

        group1, group2 = groups
        pairs = self.find_nearest_pairs(group1, group2)

        if not pairs:
            self.report({'WARNING'}, "No nearest pairs found.")
            return {'CANCELLED'}

        for v1, v2 in pairs:
            self.create_join_cut(bm, v1, v2)

        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'}, f"Joined {len(pairs)} vertex pairs.")
        return {'FINISHED'}

    def find_vertex_groups(self, verts, bm):
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
        return [(v1, min(group2, key=lambda v2: (v1.co - v2.co).length)) for v1 in group1]

    def create_join_cut(self, bm, v1, v2):
        """Create a join cut between two vertices"""
        bpy.ops.mesh.select_all(action='DESELECT')
        v1.select = True
        v2.select = True
        bpy.ops.mesh.vert_connect_path()


class LogSelectedVerticesOperator(bpy.types.Operator):
    """Log coordinates of selected vertices and saved groups"""
    bl_idname = "mesh.log_selected_vertices"
    bl_label = "Log Selected Vertices"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.mode != 'EDIT':
            self.report({'WARNING'}, "Please enter Edit Mode and select vertices.")
            return {'CANCELLED'}

        # Логирование выделенных вершин
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        selected_verts = [v for v in bm.verts if v.select]

        if selected_verts:
            print("Selected Vertices:")
            for i, v in enumerate(selected_verts):
                print(f"Vertex {i + 1}: ({v.co.x:.6f}, {v.co.y:.6f}, {v.co.z:.6f})")
        else:
            self.report({'INFO'}, "No vertices selected.")

        # Логирование сохраненных групп
        if "saved_groups" in obj:
            print("\nSaved Groups:")
            for group_name, vertex_indices in obj["saved_groups"].items():
                print(f"{group_name}:")
                for i, vert_index in enumerate(vertex_indices):
                    v = bm.verts[vert_index]  # Получаем вершину по индексу
                    print(f"  Vertex {i + 1}: ({v.co.x:.6f}, {v.co.y:.6f}, {v.co.z:.6f})")
        else:
            print("No saved groups found.")

        self.report({'INFO'}, "Logged all selected vertices and saved groups.")
        return {'FINISHED'}


class SaveSelectionOperator(bpy.types.Operator):
    """Save current selection to a group"""
    bl_idname = "mesh.save_selection"
    bl_label = "Save Selection to Group"
    bl_options = {'REGISTER'}

    group_index: bpy.props.IntProperty(name="Group Index", default=1, min=1, max=2)

    def execute(self, context):
        obj = context.object
        if not obj or obj.mode != 'EDIT':
            self.report({'WARNING'}, "Please enter Edit Mode and select vertices.")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        selected_verts = [v.index for v in bm.verts if v.select]
        if not selected_verts:
            self.report({'WARNING'}, "No vertices selected.")
            return {'CANCELLED'}

        # Инициализируем хранилище пользовательских данных, если его нет
        if "saved_groups" not in obj:
            obj["saved_groups"] = {}

        # Сохраняем выборку в указанную группу
        obj["saved_groups"][f"group_{self.group_index}"] = selected_verts

        self.report({'INFO'}, f"Saved {len(selected_verts)} vertices to group {self.group_index}.")
        return {'FINISHED'}


class LogVerticesSubMenu(bpy.types.Menu):
    """Submenu for Log Selected Vertices"""
    bl_label = "Log Vertices Options"
    bl_idname = "VIEW3D_MT_log_vertices_submenu"

    def draw(self, context):
        layout = self.layout
        layout.operator(LogSelectedVerticesOperator.bl_idname, text="Log All Selected Vertices")
        layout.operator(SaveSelectionOperator.bl_idname, text="Save to Group 1").group_index = 1
        layout.operator(SaveSelectionOperator.bl_idname, text="Save to Group 2").group_index = 2


class VertexOperationsPieMenu(bpy.types.Menu):
    """Pie Menu for Vertex Operations"""
    bl_label = "Vertex Operations"
    bl_idname = "VIEW3D_MT_vertex_operations_pie_menu"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.operator(JoinNearestVerticesOperator.bl_idname, text="Join Nearest Vertices")
        pie.menu(EqualizeDistancesSubMenu.bl_idname, text="Equalize Distances")
        pie.menu(LogVerticesSubMenu.bl_idname, text="Log Selected Vertices")


addon_keymaps = []


def register():
    bpy.utils.register_class(JoinNearestVerticesOperator)
    bpy.utils.register_class(EqualizeDistancesOperator)
    bpy.utils.register_class(SaveBaseGroupOperator)
    bpy.utils.register_class(EqualizeDistancesSubMenu)
    bpy.utils.register_class(LogSelectedVerticesOperator)
    bpy.utils.register_class(SaveSelectionOperator)
    bpy.utils.register_class(LogVerticesSubMenu)
    bpy.utils.register_class(VertexOperationsPieMenu)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("wm.call_menu_pie", type='J', value='PRESS', shift=True)
    kmi.properties.name = VertexOperationsPieMenu.bl_idname
    addon_keymaps.append((km, kmi))

    print("Pie menu 'Vertex Operations' registered with hotkey Shift+J.")


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(JoinNearestVerticesOperator)
    bpy.utils.unregister_class(EqualizeDistancesOperator)
    bpy.utils.unregister_class(SaveBaseGroupOperator)
    bpy.utils.unregister_class(EqualizeDistancesSubMenu)
    bpy.utils.unregister_class(LogSelectedVerticesOperator)
    bpy.utils.unregister_class(SaveSelectionOperator)
    bpy.utils.unregister_class(LogVerticesSubMenu)
    bpy.utils.unregister_class(VertexOperationsPieMenu)


if __name__ == "__main__":
    register()
