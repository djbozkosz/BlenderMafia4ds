import bpy


class Aaa(bpy.types.PropertyGroup):
    bbb = bpy.props.IntProperty(name="My Int")
    #aaa : bpy.props.EnumProperty(
    #    name = "aaa",
    #    items = [
    #        ("1", "Aaa", "Aaa"),
    #        ("2", "Aab", "Aab"),
    #        ("3", "Aac", "Aac")
    #    ]
    #)


class Mafia4dsMeshProperties(bpy.types.Panel):
    """Mafia 4ds Mesh Properties"""
    bl_label = "Mafia 4ds Mesh Properties"
    bl_idname = "OBJECT_PT_mafia_4ds_mesh_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    

    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        layout.prop(context.scene.aaa, "bbb")
        #layout.prop(context.scene.Aaa, "aaa")

        #obj = context.object

        #row = layout.row()
        #row.label(text="Hello world!", icon='WORLD_DATA')

        #row = layout.row()
        #row.label(text="Active object is: " + obj.name)
        #row = layout.row()
        #row.prop(obj, "name")

        #row = layout.row()
        #row.operator("mesh.primitive_cube_add")


def register():
    bpy.utils.register_class(Aaa)
    bpy.utils.register_class(Mafia4dsMeshProperties)
    
    bpy.types.Scene.aaa = bpy.props.PointerProperty(type = Aaa)


def unregister():
    bpy.utils.unregister_class(Aaa)
    bpy.utils.unregister_class(Mafia4dsMeshProperties)
    
    del bpy.types.Scene.Aaa


if __name__ == "__main__":
    register()
