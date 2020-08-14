import bmesh
import struct
import mathutils

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
    
    
    def ShowWarning(self, message):
        print(message)
    
    
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
        
        return material
    
    
    def DeserializeVisualLod(self, reader, materials, mesh, meshData, meshProps):
        meshProps.LodRatio = struct.unpack("f", reader.read(4))[0]
        bMesh              = bmesh.new()
        
        # vertices
        vertices           = bMesh.verts
        uvs                = []
        vertexCount        = struct.unpack("H", reader.read(2))[0]
        
        for vertexIdx in range(vertexCount):
            position       = struct.unpack("fff", reader.read(4 * 3))
            normal         = struct.unpack("fff", reader.read(4 * 3))
            uv             = struct.unpack("ff",  reader.read(4 * 2))
            
            vertex         = vertices.new()
            vertex.co      = [ position[0], position[2], position[1] ]
            vertex.normal  = [ normal[0],   normal[2],   normal[1] ]
            uvs.append([ uv[0], -uv[1] ])
        
        vertices.ensure_lookup_table()
        
        # faces
        faces               = bMesh.faces
        uvLayer             = bMesh.loops.layers.uv.new()
        faceGroupCount      = struct.unpack("B", reader.read(1))[0]
        
        for faceGroupIdx in range(faceGroupCount):
            faceCount       = struct.unpack("H", reader.read(2))[0]
            
            ops.object.material_slot_add({ "object" : mesh })
            materialSlotIdx = len(mesh.material_slots) - 1
            materialSlot    = mesh.material_slots[materialSlotIdx]
            
            for faceIdx in range(faceCount):
                vertexIdxs             = struct.unpack("HHH", reader.read(2 * 3))
                vertexIdxsSwap         = [ vertexIdxs[0], vertexIdxs[2], vertexIdxs[1] ]
                
                try:
                    face               = faces.new([ vertices[vertexIdxsSwap[0]], vertices[vertexIdxsSwap[1]], vertices[vertexIdxsSwap[2]] ])
                except:
                    self.ShowWarning("Mesh {} has duplicate face [ {}, {}, {} ]!".format(mesh.name, vertexIdxsSwap[0], vertexIdxsSwap[1], vertexIdxsSwap[2]))
                
                face.material_index    = materialSlotIdx
                
                for loop, vertexIdx in zip(face.loops, vertexIdxsSwap):
                    loop[uvLayer].uv   = uvs[vertexIdx]
            
            materialIdx                = struct.unpack("H", reader.read(2))[0]
            
            if materialIdx > 0:
                materialSlot.material = materials[materialIdx - 1]
        
        ops.object.shade_smooth({ "object" : mesh })
        
        bMesh.to_mesh(meshData)
        del bMesh
    
    
    def DeserializeVisual(self, reader, materials, mesh, meshData, meshProps):
        instanceIdx           = struct.unpack("H", reader.read(2))[0]
        meshProps.InstanceIdx = instanceIdx
        
        if instanceIdx > 0:
            return;
        
        meshName = mesh.name
        lodCount = struct.unpack("B", reader.read(1))[0]
        
        for lodIdx in range(lodCount):
            if lodIdx > 0:
                name           = "{}_lod{}".format(meshName, lodIdx)
                meshData       = data.meshes.new(name)
                newMesh        = data.objects.new(name, meshData)
                newMesh.parent = mesh
                mesh           = newMesh
                meshProps      = mesh.MeshProps
                
                context.collection.objects.link(mesh)
            
            self.DeserializeVisualLod(reader, materials, mesh, meshData, meshProps)
            
            # commented out, as i was not able to enable them in editor
            #if lodIdx > 0:
            #    mesh.hide_viewport = True
    
    
    def DeserializeDummy(self, reader, meshData):
        aabbMin  = struct.unpack("fff", reader.read(4 * 3))
        aabbMax  = struct.unpack("fff", reader.read(4 * 3))
        
        vertexData = [
            [ aabbMin[0], aabbMax[2], aabbMin[1],  0,  1,  0 ],
            [ aabbMax[0], aabbMax[2], aabbMin[1],  0,  1,  0 ],
            [ aabbMin[0], aabbMax[2], aabbMax[1],  0,  1,  0 ],
            [ aabbMax[0], aabbMax[2], aabbMax[1],  0,  1,  0 ],
            [ aabbMax[0], aabbMin[2], aabbMin[1],  0, -1,  0 ],
            [ aabbMin[0], aabbMin[2], aabbMin[1],  0, -1,  0 ],
            [ aabbMax[0], aabbMin[2], aabbMax[1],  0, -1,  0 ],
            [ aabbMin[0], aabbMin[2], aabbMax[1],  0, -1,  0 ],
            [ aabbMin[0], aabbMax[2], aabbMax[1],  0,  0,  1 ],
            [ aabbMax[0], aabbMax[2], aabbMax[1],  0,  0,  1 ],
            [ aabbMin[0], aabbMin[2], aabbMax[1],  0,  0,  1 ],
            [ aabbMax[0], aabbMin[2], aabbMax[1],  0,  0,  1 ],
            [ aabbMax[0], aabbMax[2], aabbMax[1],  1,  0,  0 ],
            [ aabbMax[0], aabbMax[2], aabbMin[1],  1,  0,  0 ],
            [ aabbMax[0], aabbMin[2], aabbMax[1],  1,  0,  0 ],
            [ aabbMax[0], aabbMin[2], aabbMin[1],  1,  0,  0 ],
            [ aabbMax[0], aabbMax[2], aabbMin[1],  0,  0, -1 ],
            [ aabbMin[0], aabbMax[2], aabbMin[1],  0,  0, -1 ],
            [ aabbMax[0], aabbMin[2], aabbMin[1],  0,  0, -1 ],
            [ aabbMin[0], aabbMin[2], aabbMin[1],  0,  0, -1 ],
            [ aabbMin[0], aabbMax[2], aabbMin[1], -1,  0,  0 ],
            [ aabbMin[0], aabbMax[2], aabbMax[1], -1,  0,  0 ],
            [ aabbMin[0], aabbMin[2], aabbMin[1], -1,  0,  0 ],
            [ aabbMin[0], aabbMin[2], aabbMax[1], -1,  0,  0 ]
        ]
        
        faceData = [
            [ 0,  2,  1  ],
            [ 1,  2,  3  ],
            [ 4,  6,  5  ],
            [ 5,  6,  7  ],
            [ 8,  10, 9  ],
            [ 9,  10, 11 ],
            [ 12, 14, 13 ],
            [ 13, 14, 15 ],
            [ 16, 18, 17 ],
            [ 17, 18, 19 ],
            [ 20, 22, 21 ],
            [ 21, 22, 23 ]
        ]
        
        bMesh    = bmesh.new()
        vertices = bMesh.verts
        vx       = []
        
        for v in vertexData:
            vertex        = vertices.new()
            vertex.co     = [ v[0], v[2], v[1] ] # todo aabb
            vertex.normal = [ v[3], v[5], v[4] ]
            vx.append(vertex)
        
        vertices.ensure_lookup_table()
        
        faces = bMesh.faces
        
        for f in faceData:
            faces.new([ vx[f[0]], vx[f[1]], vx[f[2]] ])
        
        bMesh.to_mesh(meshData)
        del bMesh
    
    
    def DeserializeMesh(self, reader, materials, meshes):
        type        = struct.unpack("B", reader.read(1))[0]
        visualType  = 0
        renderFlags = 0
        
        if type == 0x01:
            visualType  = struct.unpack("B", reader.read(1))[0]
            renderFlags = struct.unpack("H", reader.read(2))[0]
        
        parentIdx            = struct.unpack("H", reader.read(2))[0]
        location             = struct.unpack("fff", reader.read(4 * 3))
        scale                = struct.unpack("fff", reader.read(4 * 3))
        rotation             = struct.unpack("ffff", reader.read(4 * 4))
        
        cullingFlags         = struct.unpack("B", reader.read(1))[0]
        name                 = self.DeserializeString(reader)
        parameters           = self.DeserializeString(reader)
        
        meshData             = data.meshes.new(name)
        mesh                 = data.objects.new(name, meshData)
        
        context.collection.objects.link(mesh)
        meshes.append(mesh)
        
        meshProps              = mesh.MeshProps
        meshProps.Type         = "0x{:02x}".format(type)
        meshProps.VisualType   = "0x{:02x}".format(visualType)
        meshProps.Parameters   = parameters
        meshProps.RenderFlags  = renderFlags
        meshProps.CullingFlags = cullingFlags
        
        if parentIdx > 0:
            mesh.parent = meshes[parentIdx - 1]
        
        mesh.location       = [ location[0], location[2], location[1] ]
        mesh.scale          = [ scale[0],    scale[2],    scale[1] ]
        mesh.rotation_euler = mathutils.Quaternion([ rotation[0], rotation[1], rotation[3], rotation[2] ]).to_euler()
        
        if type == 0x01:
            if visualType != 0x00:
                self.ShowError("Unsupported visual type {}!".format(visualType))
                return False
            
            self.DeserializeVisual(reader, materials, mesh, meshData, meshProps)
        
        elif type == 0x06:
            self.DeserializeDummy(reader, meshData)
        
        else:
            self.ShowError("Unsupported mesh type {}!".format(type))
            return False
        
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
        
        scene      = types.Scene
        
        guid       = struct.unpack("Q", reader.read(8))[0]
        scene.guid = guid
        
        # read all materials
        materialCount = struct.unpack("H", reader.read(2))[0]
        materials     = []
        
        for idx in range(materialCount):
            material = self.DeserializeMaterial(reader)
            materials.append(material)
        
        # read all meshes
        meshCount = struct.unpack("H", reader.read(2))[0]
        meshes    = []
        
        for idx in range(meshCount):
             result = self.DeserializeMesh(reader, materials, meshes)
             if result == False:
                 break
        
        # allow 5ds animation
        isAnimated       = struct.unpack("B", reader.read(1))[0]
        scene.isAnimated = isAnimated
    
    
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
