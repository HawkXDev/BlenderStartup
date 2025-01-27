bl_info = {
    "name": "Geometry Nodes Generator",
    "author": "Your Name",
    "version": (1, 1),
    "blender": (4, 3, 0),
    "location": "Hotkey (Alt+Shift+N)",
    "description": "Generate Geometry Nodes for different object types using a Pie Menu.",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}

import bpy
import bmesh
from mathutils import Vector, Euler


def save_reset_and_apply_transforms(ob):
    """Save current transforms, reset and apply them."""
    saved_loc = Vector(ob.location)
    saved_rot = Euler(ob.rotation_euler)
    ob.location = (0, 0, 0)
    ob.rotation_euler = (0, 0, 0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return saved_loc, saved_rot


def calculate_sphere_segments(ob):
    """Calculate the number of segments in a sphere by analyzing its vertices."""
    saved_loc, saved_rot = save_reset_and_apply_transforms(ob)

    bm = bmesh.new()
    bm.from_mesh(ob.data)

    bm.verts.ensure_lookup_table()
    tempZ = round(bm.verts[4].co[2], 4)
    i = 0
    for v in bm.verts:
        if round(v.co[2], 4) == tempZ:
            i += 1

    bm.free()
    ob.location = saved_loc
    ob.rotation_euler = saved_rot
    return i


def calculate_geometry_parameters(obj):
    """Determine the sphere's parameters: segments, rings, and radius."""
    radius = max(obj.dimensions) / 2
    segments = calculate_sphere_segments(obj)
    rings = len(obj.data.polygons) // segments
    return segments, rings, radius


def calculate_cylinder_parameters(obj):
    """Determine the cylinder's parameters: vertices, height, and radius."""
    # Создаём bmesh из объекта
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    bm.verts.ensure_lookup_table()

    # Определяем векторы нормалей граней основания
    # Находим две плоские грани, принадлежащие основаниям цилиндра
    face_normals = [face.normal for face in bm.faces if len(face.verts) > 3]  # Считаем основания
    if len(face_normals) < 2:
        bm.free()
        raise ValueError("Object does not have clear cylindrical bases.")

    # Выбираем две нормали, соответствующие основаниям
    normal_1 = face_normals[0]
    normal_2 = face_normals[1]

    # Находим высоту цилиндра как расстояние между плоскостями
    vertices_positions = [v.co for v in bm.verts]
    projection = [v.dot(normal_1) for v in vertices_positions]
    min_proj = min(projection)
    max_proj = max(projection)
    height = max_proj - min_proj

    # Находим радиус как среднее расстояние от центра основания до вершин
    base_center = sum((v.co for v in bm.verts if round(v.co.dot(normal_1), 4) == round(min_proj, 4)), Vector()) / len(
        [v for v in bm.verts if round(v.co.dot(normal_1), 4) == round(min_proj, 4)]
    )
    base_vertices = [v for v in bm.verts if round(v.co.dot(normal_1), 4) == round(min_proj, 4)]
    radius = sum((v.co - base_center).length for v in base_vertices) / len(base_vertices)

    # Количество вершин в основании
    vertices_count = len(base_vertices)

    # Освобождаем bmesh
    bm.free()

    return vertices_count, height, radius


class OBJECT_OT_GenerateSphereGeometryNodes(bpy.types.Operator):
    """Generate Geometry Nodes for Sphere"""
    bl_idname = "object.generate_sphere_geometry_nodes"
    bl_label = "Generate Sphere Geometry Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object

        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Please select a Mesh object.")
            return {'CANCELLED'}

        # Additional check if object is a sphere-like mesh
        if len(obj.data.polygons) == 0 or len(obj.data.vertices) == 0:
            self.report({'WARNING'}, "The selected object does not appear to be a sphere.")
            return {'CANCELLED'}

        segments, rings, radius = calculate_geometry_parameters(obj)

        # Add Geometry Nodes modifier
        geo_nodes = obj.modifiers.new(name="GeometryNodes", type='NODES')
        node_tree = bpy.data.node_groups.new(name=f"{obj.name}_Geometry", type='GeometryNodeTree')
        geo_nodes.node_group = node_tree

        # Create interface
        interface = node_tree.interface
        interface.new_socket(name="Segments", in_out='INPUT', socket_type='NodeSocketInt')
        interface.new_socket(name="Rings", in_out='INPUT', socket_type='NodeSocketInt')
        interface.new_socket(name="Radius", in_out='INPUT', socket_type='NodeSocketFloat')
        interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

        # Create nodes
        nodes = node_tree.nodes
        links = node_tree.links

        group_output = nodes.new(type="NodeGroupOutput")
        group_output.location = (400, 0)

        sphere_node = nodes.new(type="GeometryNodeMeshUVSphere")
        sphere_node.location = (0, 0)

        # Connect UV Sphere to output
        links.new(sphere_node.outputs["Mesh"], group_output.inputs[0])

        # Set default values
        sphere_node.inputs["Segments"].default_value = segments
        sphere_node.inputs["Rings"].default_value = rings
        sphere_node.inputs["Radius"].default_value = radius

        self.report({'INFO'},
                    f"Generated Geometry Nodes for '{obj.name}' (Segments={segments}, Rings={rings}, Radius={radius})")
        return {'FINISHED'}


class OBJECT_OT_GenerateCylinderGeometryNodes(bpy.types.Operator):
    """Generate Geometry Nodes for Cylinder"""
    bl_idname = "object.generate_cylinder_geometry_nodes"
    bl_label = "Generate Cylinder Geometry Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object

        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Please select a Mesh object.")
            return {'CANCELLED'}

        # Additional check if object is a cylinder-like mesh
        if len(obj.data.polygons) == 0 or len(obj.data.vertices) == 0:
            self.report({'WARNING'}, "The selected object does not appear to be a cylinder.")
            return {'CANCELLED'}

        vertices, height, radius = calculate_cylinder_parameters(obj)

        # Add Geometry Nodes modifier
        geo_nodes = obj.modifiers.new(name="GeometryNodes", type='NODES')
        node_tree = bpy.data.node_groups.new(name=f"{obj.name}_Geometry", type='GeometryNodeTree')
        geo_nodes.node_group = node_tree

        # Create interface
        interface = node_tree.interface
        interface.new_socket(name="Vertices", in_out='INPUT', socket_type='NodeSocketInt')
        interface.new_socket(name="Height", in_out='INPUT', socket_type='NodeSocketFloat')
        interface.new_socket(name="Radius", in_out='INPUT', socket_type='NodeSocketFloat')
        interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

        # Create nodes
        nodes = node_tree.nodes
        links = node_tree.links

        group_output = nodes.new(type="NodeGroupOutput")
        group_output.location = (400, 0)

        cylinder_node = nodes.new(type="GeometryNodeMeshCylinder")
        cylinder_node.location = (0, 0)

        # Connect Cylinder to output
        links.new(cylinder_node.outputs["Mesh"], group_output.inputs[0])

        # Set default values
        cylinder_node.inputs["Vertices"].default_value = vertices
        cylinder_node.inputs["Depth"].default_value = height
        cylinder_node.inputs["Radius"].default_value = radius

        self.report({'INFO'},
                    f"Generated Geometry Nodes for '{obj.name}' (Vertices={vertices}, Height={height}, Radius={radius})")
        return {'FINISHED'}


class VIEW3D_MT_GenerateGeometryNodesSubMenu(bpy.types.Menu):
    """Submenu for Generating Geometry Nodes"""
    bl_label = "Generate Geometry Nodes"
    bl_idname = "VIEW3D_MT_generate_geometry_nodes_submenu"

    def draw(self, _context):
        layout = self.layout
        layout.operator(
            OBJECT_OT_GenerateSphereGeometryNodes.bl_idname,
            text="Generate for Sphere",
            icon='MESH_UVSPHERE',
        )
        layout.operator(
            OBJECT_OT_GenerateCylinderGeometryNodes.bl_idname,
            text="Generate for Cylinder",
            icon='MESH_CYLINDER',
        )


class VIEW3D_MT_GeometryNodesPie(bpy.types.Menu):
    """Pie Menu for Geometry Nodes"""
    bl_label = "Geometry Nodes Pie"
    bl_idname = "VIEW3D_MT_geometry_nodes_pie"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()
        pie.menu(VIEW3D_MT_GenerateGeometryNodesSubMenu.bl_idname, text="Generate Nodes", icon='NODETREE')


addon_keymaps = []


def register():
    bpy.utils.register_class(OBJECT_OT_GenerateSphereGeometryNodes)
    bpy.utils.register_class(OBJECT_OT_GenerateCylinderGeometryNodes)
    bpy.utils.register_class(VIEW3D_MT_GenerateGeometryNodesSubMenu)
    bpy.utils.register_class(VIEW3D_MT_GeometryNodesPie)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("wm.call_menu_pie", type='N', value='PRESS', alt=True, shift=True)
    kmi.properties.name = VIEW3D_MT_GeometryNodesPie.bl_idname
    addon_keymaps.append((km, kmi))

    print("Pie menu 'Geometry Nodes' registered with hotkey Alt+Shift+N.")


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(OBJECT_OT_GenerateSphereGeometryNodes)
    bpy.utils.unregister_class(OBJECT_OT_GenerateCylinderGeometryNodes)
    bpy.utils.unregister_class(VIEW3D_MT_GenerateGeometryNodesSubMenu)
    bpy.utils.unregister_class(VIEW3D_MT_GeometryNodesPie)

    print("Pie menu 'Geometry Nodes' unregistered.")


if __name__ == "__main__":
    register()
