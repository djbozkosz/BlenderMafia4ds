import struct

from bpy        import context
from bpy        import data
from bpy        import ops
from bpy        import path
from bpy        import props
from bpy        import types
from bpy        import utils
from bpy_extras import io_utils


class Mafia4ds_Exporter:
    def __init__(self, config):
        self.Config = config
    
    
    def GetMaterialData(self, material):
        diffuse  = ""
        emission = (0.0, 0.0, 0.0)
        alpha    = 1.0
        metallic = 0.0
        
        for node in material.node_tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            
            emission = node.inputs["Emission"].default_value
            alpha    = node.inputs["Alpha"].default_value
            metallic = node.inputs["Metallic"].default_value
            
            links = node.inputs["Base Color"].links
            if len(links) == 0:
                continue
            
            diffuse = links[0].from_node.image.name
            break
        
        return (diffuse, emission, alpha, metallic)
    
    
    def WriteString(self, writer, string):
        string = path.basename(string)
        
        writer.write(struct.pack("B", len(string)))
        
        for c in string.upper().encode():
            writer.write(struct.pack("b", c))
    
    
    def WriteMaterial(self, writer, material):
        matProps = material.MaterialProps
        (diffuse, emission, alpha, metallic) = self.GetMaterialData(material)
        
        # material flags
        matFlags = 0
        matFlags |= (0x00040000 if matProps.UseDiffuseTex   else 0)
        matFlags |= (0x08000000 if matProps.Coloring        else 0)
        
        matFlags |= (0x00800000 if matProps.MipMapping      else 0)
        matFlags |= (0x10000000 if matProps.TwoSided        else 0)
    
        matFlags |= (0x00008000 if matProps.AddEffect       else 0)
        
        if matProps.AddEffect:
            matFlags |= (0x20000000 if matProps.ColorKey        else 0)
            matFlags |= (0x80000000 if matProps.AdditiveBlend   else 0)
            matFlags |= (0x40000000 if matProps.UseAlphaTexture else 0)
    
        matFlags |= (0x00080000 if matProps.UseEnvTexture   else 0)
        matFlags |= (0x00000100 if matProps.EnvDefaultMode  else 0)
        matFlags |= (0x00000200 if matProps.EnvMultiplyMode else 0)
        matFlags |= (0x00000400 if matProps.EnvAdditiveMode else 0)
        matFlags |= (0x00001000 if matProps.EnvYAxisRefl    else 0)
        matFlags |= (0x00002000 if matProps.EnvYAxisProj    else 0)
        matFlags |= (0x00004000 if matProps.EnvZAxisProj    else 0)
    
        matFlags |= (0x04000000 if matProps.AnimatedDiffuse else 0)
        matFlags |= (0x02000000 if matProps.AnimatedAlpha   else 0)
        writer.write(struct.pack("I", matFlags))
        
        # colors
        writer.write(struct.pack("fff", matProps.AmbientColor[0], matProps.AmbientColor[1], matProps.AmbientColor[2]))
        writer.write(struct.pack("fff", matProps.DiffuseColor[0], matProps.DiffuseColor[1], matProps.DiffuseColor[2]))
        writer.write(struct.pack("fff", emission[0], emission[1], emission[2]))
        
        # alpha
        writer.write(struct.pack("f", alpha))
        
        # env mapping
        if matProps.UseEnvTexture:
            writer.write(struct.pack("f", metallic))
            self.WriteString(writer, matProps.EnvTexture)
        
        # diffuse mapping
        self.WriteString(writer, diffuse)
        
        # alpha mapping
        if matProps.AddEffect and matProps.UseAlphaTexture:
            self.WriteString(writer, matProps.AlphaTexture)
        
        # animated texture
        if matProps.AnimatedDiffuse:
            writer.write(struct.pack("I", matProps.AnimatedFrames))
            writer.write(struct.pack("H", 0))
            writer.write(struct.pack("I", matProps.AnimFrameLength))
            writer.write(struct.pack("I", 0))
            writer.write(struct.pack("I", 0))
    
    
    def WriteVisualLod(self, writer, mesh):
        writer.write(struct.pack("f", 0.0)) # lod ratio
        
        vertices = mesh.data.vertices.values()
        writer.write(struct.pack("H", len(vertices)))
        
        for vertex in vertices:
            writer.write(struct.pack("fff", vertex[0], vertex[1], vertex[2]))
        
        # face groups
    
    
    def WriteVisual(self, writer, mesh):
        writer.write(struct.pack("H", 0)) # instance idx
        writer.write(struct.pack("H", 0)) # lod count
        
        self.WriteVisualLod(writer, mesh)
    
    
    def WriteMesh(self, writer, mesh):
        meshProps = mesh.MeshProps
        writer.write(struct.pack("B", meshProps.Type))
        
        if meshProps.Type == 0x01:
            writer.write(struct.pack("B", meshProps.VisualType))
            writer.write(struct.pack("H", 0x2a)) # render flags
        
        writer.write(struct.pack("H", 0)) # parent idx
        writer.write(struct.pack("fff", mesh.location[0], mesh.location[1], mesh.location[2]))
        writer.write(struct.pack("fff", mesh.scale[0], mesh.scale[1], mesh.scale[2]))
        writer.write(struct.pack("ffff", mesh.rotation_quaternion[0], mesh.rotation_quaternion[1], mesh.rotation_quaternion[2], mesh.rotation_quaternion[3]))
        writer.write(struct.pack("B", 0x09)) # culling flags
        self.WriteString(writer, mesh.name)
        self.WriteString(writer, meshProps.Parameters)
        
        if meshProps.Type == 0x01:
            self.WriteVisual(writer, mesh)
    
    
    def WriteFile(self, writer):
        writer.write("4DS\0".encode("ascii")); # fourcc
        writer.write(struct.pack("H", 0x1d))   # mafia 4ds version
        writer.write(struct.pack("Q", 0))      # guid
        
        # write all materials
        materials = data.materials
        writer.write(struct.pack("H", len(materials)))
        
        for material in materials:
            self.WriteMaterial(writer, material)
        
        # write all meshes
        meshes = context.scene.objects
        writer.write(struct.pack("H", len(meshes)))
        
        for mesh in meshes:
            self.WriteMesh(writer, mesh)
        
        # allow 5ds animation
        writer.write(struct.pack("B", 0))
    
    
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
