bl_info = {
    "name": "B42D",
    "author": "Shreya Punjabi",
    "version": (1,0),
    "blender": (4, 4, 3),
    "location": "View 3D > Properties > B42D",
    "description": "Sets up scene for 2D editing",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import bpy


class B42d_UI(bpy.types.Panel):
    "Add bevel"
    bl_label = "B42D"
    bl_idname = "B42D_PT_ADD_MAIN"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "B42D"


    def draw(self, context):
        layout = self.layout
        row=layout.row()
        row = layout.row()
        row.operator("b42d.start", icon = "FILE_IMAGE")
        row = layout.row()
        row.operator("b42d.align", icon = "ALIGN_MIDDLE")


class START_B42D(bpy.types.Operator):
    "Set up scene for 2D editing"
    bl_idname = "b42d.start"
    bl_label = "Set Up" 
    bl_options = {'REGISTER', 'UNDO'} 


    def execute(self, context):
        bpy.data.scenes["Scene"].render.engine = "BLENDER_EEVEE_NEXT"
        bpy.data.scenes["Scene"].render.film_transparent = True
        bpy.data.scenes["Scene"].view_settings.view_transform = "Standard"
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = [0.000000, 0.000000, 0.000000, 1.000000]
        cam_ob = bpy.context.scene.camera
        if cam_ob.type == 'CAMERA':
            cam_ob.name = "2D Cam"
            cam_ob.location = (0.0,0.0,5.0)
            cam_ob.rotation_euler = (0.0,0.0,0.0)
        cam = cam_ob.data
        cam.name = "2D Cam Settings"
        cam.type = "ORTHO"
        return {"FINISHED"}

    @classmethod

    def poll(cls, context):
        return True


class ALIGN(bpy.types.Operator):
    "Align camera to selected plane"
    bl_idname = "b42d.align"
    bl_label = "Align to Selected" 
    bl_options = {'REGISTER', 'UNDO'} 


    def execute(self, context):
        active = bpy.context.active_object
        try:
            mat = active.material_slots[0].material
            orth_zoom = max(active.dimensions)
            cam_ob = bpy.context.scene.camera
            x_pos, y_pos = active.location[0], active.location[1]
            cam_ob.location[0], cam_ob.location[1] = x_pos, y_pos
            if cam_ob.type == 'CAMERA':
                if cam_ob.name == "2D Cam":
                    cam = cam_ob.data
            cam.ortho_scale = orth_zoom
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    img = node.image
                    bpy.data.scenes["Scene"].render.resolution_x = img.size[0]
                    bpy.data.scenes["Scene"].render.resolution_y = img.size[1]
                    return {"FINISHED"}
            return {"CANCELLED"}
        except:
            self.report({"WARNING"}, "Aligning is possible only after set up")
            return {"CANCELLED"}

    @classmethod

    def poll(cls, context):
        active = bpy.context.active_object
        if active and active.type=="MESH" and min(active.dimensions) == 0.0:
            return True
        return False


def register():
    bpy.utils.register_class(B42d_UI)  
    bpy.utils.register_class(START_B42D)
    bpy.utils.register_class(ALIGN)
    bpy.types.Scene.my_image = bpy.props.PointerProperty(name="Image", type=bpy.types.Image)


def unregister():
    bpy.utils.unregister_class(B42d_UI)  
    bpy.utils.unregister_class(START_B42D) 
    bpy.utils.unregister_class(ALIGN)
    del bpy.types.Scene.my_image

if __name__ == "__main__":
    register()
