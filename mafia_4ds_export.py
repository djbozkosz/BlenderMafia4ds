import struct

from bpy        import context
from bpy        import data
from bpy        import ops
from bpy        import props
from bpy        import types
from bpy        import utils
from bpy_extras import io_utils


class Mafia4ds_Exporter:
    def __init__(self, config):
        self.Config = config
    
    
    def GetTexture(self, material, name):
        for node in material.node_tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            
            links = node.inputs[name].links
            if len(links) == 0:
                continue
            
            return links[0].from_node.image.name
    
    
    def WriteMaterial(self, writer, material):
        diffuse = self.GetTexture(material, "Base Color")
        env     = self.GetTexture(material, "Subsurface Color")
        
        if diffuse:
            print(diffuse)
        else:
            print("aaa")
            
        if env:
            print(env)
        else:
            print("bbb")
        #writer.write()
    
    
    def WriteFile(self, writer):
        writer.write("4DS\0".encode("ascii")); # fourcc
        writer.write(struct.pack("H", 0x1d))   # mafia 4ds version
        writer.write(struct.pack("Q", 0))      # guid
        
        # write all materials
        materials = data.materials
        writer.write(struct.pack("H", len(materials)))
        
        for material in materials:
            self.WriteMaterial(writer, material)
    
    
    def Export(self, filename):
        writer = open(filename, "wb")
        
        self.WriteFile(writer)
        
        writer.close()
        
        return {'FINISHED'}


class Mafia4ds_ExportDialog(types.Operator, io_utils.ExportHelper):
    "Export Mafia 4ds model."
    bl_idname    = "mafia4ds.export"
    bl_text      = "Mafia (.4ds)"
    bl_label     = "Export 4DS"
    filename_ext = ".4ds"

    filter_glob : props.StringProperty(
        default = "*.4ds",
        options = {'HIDDEN'},
        maxlen  = 255
    )
    
    IncludeMeshes : props.EnumProperty(
        name  = "Include Meshes",
        items = [
            ("0", "Selected Objects",  ""),
            ("1", "Active Collection", "")
        ],
        default = "1"
    )

    def execute(self, context):
        exporter = Mafia4ds_Exporter(self)
        return exporter.Export(self.filepath)


def MenuExport(self, context):
    self.layout.operator(Mafia4ds_ExportDialog.bl_idname, text = Mafia4ds_ExportDialog.bl_text)


def register():
    utils.register_class(Mafia4ds_ExportDialog)
    types.TOPBAR_MT_file_export.append(MenuExport)


def unregister():
    utils.unregister_class(Mafia4ds_ExportDialog)
    types.TOPBAR_MT_file_export.remove(MenuExport)


if __name__ == "__main__":
    register()

    ops.mafia4ds.export('INVOKE_DEFAULT')
