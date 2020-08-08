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
    
    
    def SetMaterialData(self, material, diffuse, emission, alpha, metallic):
        material.use_nodes = True
        
        node  = None
        nodes = material.node_tree.nodes
        
        for node in nodes:
            if node.type == "BSDF_PRINCIPLED":
                break
        
        if node is None:
            return
            
        node.inputs["Emission" ].default_value = [ emission[0], emission[1], emission[2], 1.0]
        node.inputs["Alpha"    ].default_value = alpha
        node.inputs["Metallic" ].default_value = metallic
        node.inputs["Specular" ].default_value = 0.0
        node.inputs["Roughness"].default_value = 0.0
            
        baseColor      = node.inputs["Base Color"]
        baseColorLinks = baseColor.links
            
        if len(baseColorLinks) > 0:
            image      = baseColorLinks[0].from_node.image
        else:
            image      = nodes.new(type="ShaderNodeTexImage")
            imageColor = image.outputs["Color"]
            
            links      = material.node_tree.links
            links.new(imageColor, baseColor)
        
        if len(diffuse) == 0:
            return
            
        file        = data.images.load(filepath = "C:/Hry/Mafia/maps/{}".format(diffuse), check_existing = True)
        image.image = file
    
    
    def ShowError(self, message):
        print(message)
        
        context.window_manager.popup_menu(lambda self, context:
            self.layout.label(text = message
        ), title = "Error", icon = "ERROR")
    
    
    def DeserializeStringFixed(self, reader, length):
        tuple  = struct.unpack("{}c".format(length), reader.read(length))
        string = ""
        
        for c in tuple:
            string += c.decode()
        
        return string
    
    
    def DeserializeString(self, reader):
        length = struct.unpack("B", reader.read(1))[0]
        return self.DeserializeStringFixed(reader, length)
    
    
    def DeserializeMaterial(self, reader):
        material = data.materials.new("material")
        matProps = material.MaterialProps
        
        # material flags
        matFlags = struct.unpack("I", reader.read(4))[0]
        
        matProps.UseDiffuseTex   = (matFlags & 0x00040000) != 0
        
        matProps.Coloring        = (matFlags & 0x08000000) != 0
        matProps.MipMapping      = (matFlags & 0x00800000) != 0
        matProps.TwoSided        = (matFlags & 0x10000000) != 0
    
        matProps.AddEffect       = (matFlags & 0x00008000) != 0
        
        matProps.ColorKey        = (matFlags & 0x20000000) != 0
        matProps.AdditiveBlend   = (matFlags & 0x80000000) != 0
        matProps.UseAlphaTexture = (matFlags & 0x40000000) != 0
    
        matProps.UseEnvTexture   = (matFlags & 0x00080000) != 0
        matProps.EnvDefaultMode  = (matFlags & 0x00000100) != 0
        matProps.EnvMultiplyMode = (matFlags & 0x00000200) != 0
        matProps.EnvAdditiveMode = (matFlags & 0x00000400) != 0
        matProps.EnvYAxisRefl    = (matFlags & 0x00001000) != 0
        matProps.EnvYAxisProj    = (matFlags & 0x00002000) != 0
        matProps.EnvZAxisProj    = (matFlags & 0x00004000) != 0
    
        matProps.AnimatedDiffuse = (matFlags & 0x04000000) != 0
        matProps.AnimatedAlpha   = (matFlags & 0x02000000) != 0
        
        # colors
        matProps.AmbientColor = struct.unpack("fff", reader.read(4 * 3))
        matProps.DiffuseColor = struct.unpack("fff", reader.read(4 * 3))
        emission              = struct.unpack("fff", reader.read(4 * 3))
        
        # alpha
        alpha = struct.unpack("f", reader.read(4))[0]
        
        # env mapping
        metallic = 0.0
        
        if matProps.UseEnvTexture:
            metallic            = struct.unpack("f", reader.read(4))[0]
            matProps.EnvTexture = self.DeserializeString(reader).lower()
        
        # diffuse mapping
        diffuse = self.DeserializeString(reader).lower()
        material.name = diffuse
        
        # alpha mapping
        if matProps.AddEffect and matProps.UseAlphaTexture:
            matProps.AlphaTexture = self.DeserializeString(reader).lower()
        
        # animated texture
        if matProps.AnimatedDiffuse:
            matProps.AnimatedFrames  = struct.unpack("I", reader.read(4))[0]
            reader.read(2)
            matProps.AnimFrameLength = struct.unpack("I", reader.read(4))[0]
            reader.read(8)
        
        self.SetMaterialData(material, diffuse, emission, alpha, metallic)
    
    
    def DeserializeVisualLod(self, reader, mesh, lodIdx):
        if lodIdx > 0:
            self.ShowError("todo lod!")
            # new mesh, reparent
        
        lodRatio          = struct.unpack("f", reader.read(4))[0]
        bMesh             = bmesh.new()
        
        # vertices
        vertices          = bMesh.verts
        vertexCount       = struct.unpack("H", reader.read(2))[0]
        
        for vertexIdx in range(vertexCount):
            position      = struct.unpack("fff", reader.read(4 * 3))
            normal        = struct.unpack("fff", reader.read(4 * 3))
            uv            = struct.unpack("ff",  reader.read(4 * 2))
            
            vertex        = vertices.new()
            vertex.co     = [ position[0], position[2], position[1] ]
            vertex.normal = [ normal[0],   normal[2],   normal[1] ]
        
        # faces
        faces             = bMesh.faces
        faceGroupCount    = struct.unpack("B", reader.read(1))[0]
        
        for faceGroupIdx in range(faceGroupCount):
            faceCount     = struct.unpack("H", reader.read(2))[0]
            
            for faceIdx in range(faceCount):
                faceIdxs  = struct.unpack("HHH", reader.read(2 * 3))
                face      = faces.new(vertices[faceIdxs[0]], vertices[faceIdxs[2]], vertices[faceIdxs[1]])
                
            materialIdx   = struct.unpack("H", reader.read(2))[0]

        
        bMesh.to_mesh(mesh)
        del bMesh
    
    
    def DeserializeVisual(self, reader, mesh):
        instanceIdx = struct.unpack("H", reader.read(2))[0]
        if instanceIdx > 0:
            return;
        
        lodCount = struct.unpack("B", reader.read(1))[0]
        
        for lodIdx in range(lodCount):
            self.DeserializeVisualLod(writer, mesh, lodIdx)
    
    
    def DeserializeMesh(self, reader, meshes):
        type = struct.unpack("B", reader.read(1))[0]
        if type != 0x01: # temporary
            self.ShowError("Unsupported mesh type {}!".format(type))
            return False
        
        visualType = 0
        
        if type == 0x01:
            visualType  = struct.unpack("B", reader.read(1))[0]
            renderFlags = struct.unpack("H", reader.read(2))[0]
        
        if visualType != 0x00: # temporary
            self.ShowError("Unsupported visual type {}!".format(visualType))
            return False
        
        parentIdx            = struct.unpack("H", reader.read(2))[0]
        location             = struct.unpack("fff", reader.read(4 * 3))
        scale                = struct.unpack("fff", reader.read(4 * 3))
        rotation             = struct.unpack("ffff", reader.read(4 * 4))
        
        cullingFlags         = struct.unpack("B", reader.read(1))[0]
        name                 = self.DeserializeString(reader)
        parameters           = self.DeserializeString(reader)
        
        mesh                 = data.meshes.new(name)
        meshObj              = data.objects.new(name, mesh)
        
        context.collection.objects.link(meshObj)
        meshes.append(mesh)
        
        meshProps            = mesh.MeshProps
        meshProps.Type       = type
        meshProps.VisualType = visualType
        meshProps.Parameters = parameters
        
        if parentIdx > 0:
            mesh.parent = meshes[parentIdx - 1]
        
        mesh.location        = [ location[0], location[2], location[1] ]
        mesh.scale           = [ scale[0],    scale[2],    scale[1] ]
        mesh.rotation        = [ rotation[0], rotation[1], rotation[3], rotation[2] ]
        
        if type == 0x01:
            self.DeserializeVisual(reader, mesh)
        
        return True
    
    
    def DeserializeFile(self, reader):
        fourcc = self.DeserializeStringFixed(reader, 4)
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
        
        for idx in range(materialCount):
            self.DeserializeMaterial(reader)
        
        # read all meshes
        meshCount = struct.unpack("H", reader.read(2))[0]
        meshes    = []
        
        for idx in range(meshCount):
             result = self.DeserializeMesh(reader, meshes)
             if result == False:
                 break
    
    
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
