bl_info = {
    "name": "B42D",
    "author": "Shreya Punjabi",
    "version": (1, 1, 0),
    "blender": (4, 4, 3),
    "location": "3D Viewport > Sidebar > B42D",
    "description": "Set up a scene for 2D editing and frame a plane for rendering",
    "doc_url": "https://github.com/shreya6064/b42d",
    "category": "3D View",
}

import bpy
from mathutils import Matrix, Vector


SHORT_SIDE_PIXELS = 1080


def set_black_background(scene):
    if scene.world is None:
        scene.world = bpy.data.worlds.new("B42D World")
    world = scene.world

    if bpy.app.version < (5, 0, 0):
        world.use_nodes = True

    tree = world.node_tree
    background = next((node for node in tree.nodes if node.type == 'BACKGROUND'), None)
    if background is None:
        output = next((node for node in tree.nodes if node.type == 'OUTPUT_WORLD'), None)
        if output is None:
            output = tree.nodes.new('ShaderNodeOutputWorld')
        surface = output.inputs["Surface"]
        if surface.is_linked:
            return
        background = tree.nodes.new('ShaderNodeBackground')
        tree.links.new(background.outputs["Background"], surface)

    background.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)


def get_image_size(obj):
    for slot in obj.material_slots:
        material = slot.material
        if material is None or material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image is not None:
                width, height = node.image.size
                if width > 0 and height > 0:
                    return width, height
    return None


class B42D_OT_start(bpy.types.Operator):
    """Set up the current scene for 2D editing"""

    bl_idname = "b42d.start"
    bl_label = "Set Up"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.render.engine = (
            'BLENDER_EEVEE' if bpy.app.version >= (5, 0, 0) else 'BLENDER_EEVEE_NEXT'
        )
        scene.render.film_transparent = True
        scene.view_settings.view_transform = 'Standard'
        set_black_background(scene)

        camera = scene.camera
        if camera is None:
            camera = bpy.data.objects.new("2D Cam", bpy.data.cameras.new("2D Cam Settings"))
            scene.collection.objects.link(camera)
            scene.camera = camera

        camera.name = "2D Cam"
        camera.matrix_world = Matrix.Translation((0.0, 0.0, 5.0))
        camera.data.name = "2D Cam Settings"
        camera.data.type = 'ORTHO'
        camera.data.shift_x = 0.0
        camera.data.shift_y = 0.0
        return {'FINISHED'}


class B42D_OT_align(bpy.types.Operator):
    """Frame a plane in the top-down camera and set the render size"""

    bl_idname = "b42d.align"
    bl_label = "Align to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'MESH'

    def execute(self, context):
        scene = context.scene
        camera = scene.camera
        if camera is None or camera.data.type != 'ORTHO':
            self.report({'WARNING'}, "Click Set Up to prepare the 2D camera first")
            return {'CANCELLED'}

        obj = context.active_object
        evaluated = obj.evaluated_get(context.evaluated_depsgraph_get())
        corners = [evaluated.matrix_world @ Vector(corner) for corner in evaluated.bound_box]
        x, y, z = zip(*corners)
        width = max(x) - min(x)
        height = max(y) - min(y)
        if min(width, height) <= 0 or max(z) - min(z) > 1e-5 * max(width, height):
            self.report({'WARNING'}, "Select a plane that lies parallel to the XY plane")
            return {'CANCELLED'}

        image_size = get_image_size(obj)
        if image_size is None:
            pixels_per_unit = SHORT_SIDE_PIXELS / min(width, height)
            resolution_x = round(width * pixels_per_unit)
            resolution_y = round(height * pixels_per_unit)
        else:
            resolution_x, resolution_y = image_size

        render = scene.render
        for setting, value in (("resolution_x", resolution_x), ("resolution_y", resolution_y)):
            limits = render.bl_rna.properties[setting]
            if not limits.hard_min <= value <= limits.hard_max:
                self.report({'WARNING'}, "The target resolution is outside Blender's supported range")
                return {'CANCELLED'}

        camera_matrix = camera.matrix_world.copy()
        camera_matrix.translation.x = (min(x) + max(x)) / 2
        camera_matrix.translation.y = (min(y) + max(y)) / 2
        camera_matrix.translation.z = max(
            camera_matrix.translation.z, max(z) + camera.data.clip_start + 0.1
        )
        camera.matrix_world = camera_matrix

        # Orthographic scale measures the longer side of the camera frame.
        aspect = resolution_x / resolution_y
        camera.data.ortho_scale = max(width, height * aspect) if aspect >= 1 else max(
            height, width / aspect
        )
        render.resolution_x = resolution_x
        render.resolution_y = resolution_y
        render.resolution_percentage = 100
        render.pixel_aspect_x = 1.0
        render.pixel_aspect_y = 1.0
        return {'FINISHED'}


class B42D_PT_main(bpy.types.Panel):
    bl_label = "B42D"
    bl_idname = "B42D_PT_ADD_MAIN"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "B42D"

    def draw(self, context):
        column = self.layout.column(align=True)
        column.operator("b42d.start", icon='FILE_IMAGE')
        column.operator("b42d.align", icon='ALIGN_MIDDLE')


classes = (B42D_OT_start, B42D_OT_align, B42D_PT_main)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
