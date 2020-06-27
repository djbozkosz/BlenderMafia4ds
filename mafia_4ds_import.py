import bmesh
import struct

from bpy        import context
from bpy        import data
from bpy        import ops
from bpy        import path
from bpy        import props
from bpy        import types
from bpy        import utils
from bpy_extras import io_utils


class Mafia4ds_Importer:
    def __init__(self, config):
        self.Config = config
    
    
    def ShowError(self, message):
        print(message)
        
        context.window_manager.popup_menu(lambda self, context:
            self.layout.label(text = message
        ), title = "Error", icon = "ERROR")
    
    
    def DeserializeString(self, reader, length):
        tuple  = struct.unpack("{}c".format(length), reader.read(length))
        string = ""
        
        for c in tuple:
            string += c.decode()
        
        return string
    
    
    def DeserializeFile(self, reader):
        fourcc = self.DeserializeString(reader, 4)
        if fourcc != "4DS\0":
            self.ShowError("Not a 4DS file!")
            return
        
        version = struct.unpack("H", reader.read(2))[0]
        if version != 0x1d:
            self.ShowError("Invalid 4DS version {}!".format(version))
            return
        
        guid = struct.unpack("Q", reader.read(8))[0]
        
        # read all materials
        materialCount = struct.unpack("H", reader.read(2))[0]
    
    
    def Import(self, filename):
        with open(filename, "rb") as reader:
            self.DeserializeFile(reader)
        
        return {'FINISHED'}


class Mafia4ds_ImportDialog(types.Operator, io_utils.ImportHelper):
    "Import Mafia 4ds model."
    bl_idname    = "mafia4ds.import_"
    bl_text      = "Mafia (.4ds)"
    bl_label     = "Import 4DS"
    filename_ext = ".4ds"

    filter_glob : props.StringProperty(
        default = "*.4ds",
        options = {'HIDDEN'},
        maxlen  = 255
    )
    
    #IncludeMeshes : props.EnumProperty(
    #    name  = "Include Meshes",
    #    items = [
    #        ("0", "Selected Objects",  ""),
    #        ("1", "Active Collection", "")
    #    ],
    #    default = "1"
    #)

    def execute(self, context):
        exporter = Mafia4ds_Importer(self)
        return exporter.Import(self.filepath)


def MenuImport(self, context):
    self.layout.operator(Mafia4ds_ImportDialog.bl_idname, text = Mafia4ds_ImportDialog.bl_text)


def register():
    utils.register_class(Mafia4ds_ImportDialog)
    types.TOPBAR_MT_file_import.append(MenuImport)


def unregister():
    utils.unregister_class(Mafia4ds_ImportDialog)
    types.TOPBAR_MT_file_import.remove(MenuImport)


if __name__ == "__main__":
    register()

    ops.mafia4ds.import_('INVOKE_DEFAULT')
