import bpy
import bmesh
import struct

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
        
        tree = material.node_tree
        
        if not tree:
            return (diffuse, emission, alpha, metallic)
        
        for node in tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            
            emission = node.inputs["Emission"].default_value
            alpha    = node.inputs["Alpha"].default_value
            metallic = node.inputs["Metallic"].default_value
            
            links = node.inputs["Base Color"].links
            if len(links) == 0:
                break
            
            image = links[0].from_node.image
            
            if not image:
                break
            
            diffuse = image.name
        
        return (diffuse, emission, alpha, metallic)
    
    
    def IsLod(self, mesh):
        return mesh.name.find("_lod") != -1
    
    
    def SerializeString(self, writer, string):
        string = path.basename(string)
        
        writer.write(struct.pack("B", len(string)))
        
        for c in string.encode():
            writer.write(struct.pack("b", c))
    
    
    def SerializeMaterial(self, writer, material):
        matProps = material.MaterialProps
        (diffuse, emission, alpha, metallic) = self.GetMaterialData(material)
        
        # material flags
        matFlags = 0x00000001
        
        if len(diffuse) > 0:
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
            self.SerializeString(writer, matProps.EnvTexture.upper())
        
        # diffuse mapping
        self.SerializeString(writer, diffuse.upper())
        
        # alpha mapping
        if matProps.AddEffect and matProps.UseAlphaTexture:
            self.SerializeString(writer, matProps.AlphaTexture.upper())
        
        # animated texture
        if matProps.AnimatedDiffuse:
            writer.write(struct.pack("I", matProps.AnimatedFrames))
            writer.write(struct.pack("H", 0))
            writer.write(struct.pack("I", matProps.AnimFrameLength))
            writer.write(struct.pack("I", 0))
            writer.write(struct.pack("I", 0))
    
    
    def SerializeVisualLod(self, writer, mesh, meshProps):
        writer.write(struct.pack("f", meshProps.LodRatio)) # lod ratio
        
        # apply modifiers
        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh      = mesh.evaluated_get(depsgraph)
        
        bMesh     = bmesh.new()
        bMesh.from_mesh(mesh.to_mesh())
        
        bmesh.ops.triangulate(bMesh, faces = bMesh.faces[:], quad_method = "BEAUTY", ngon_method = "BEAUTY")
        
        # vertices
        vertices = bMesh.verts
        writer.write(struct.pack("H", len(vertices)))
        
        uvLayer = bMesh.loops.layers.uv.active
        
        for vertex in vertices:
            uv = (0.0, 0.0)
            
            for loop in vertex.link_loops:
                loopUV = loop[uvLayer].uv
                uv     = (loopUV[0], loopUV[1])
                break
            
            writer.write(struct.pack("fff", vertex.co[0], vertex.co[2], vertex.co[1]))
            writer.write(struct.pack("fff", vertex.normal[0], vertex.normal[2], vertex.normal[1]))
            writer.write(struct.pack("ff", uv[0], -uv[1]))
        
        # faces
        faces = bMesh.faces
        faces.sort(key = lambda face: face.material_index)
        
        lastMatIdx = -1
        faceGroups = []
        faceGroup  = []
        
        for face in faces:
            if lastMatIdx != face.material_index:
                lastMatIdx = face.material_index
                if len(faceGroup) > 0:
                    faceGroups.append(faceGroup)
                    faceGroup = []
            
            faceGroup.append(face)
        
        if len(faceGroup) > 0:
            faceGroups.append(faceGroup)
        
        writer.write(struct.pack("B", len(faceGroups)))
        
        for faceGroup in faceGroups:
            writer.write(struct.pack("H", len(faceGroup)))
            lastMatIdx = 0
        
            for face in faceGroup:
                lastMatIdx = face.material_index
                writer.write(struct.pack("HHH", face.verts[0].index, face.verts[2].index, face.verts[1].index))
            
            materialIdx = -1
            
            if len(mesh.material_slots) > 0:
                material = mesh.material_slots[lastMatIdx].material
                
                if material:
                    materialIdx = bpy.data.materials.find(material.name)
            
            writer.write(struct.pack("H", materialIdx + 1))
        
        del bMesh
    
    
    def SerializeVisual(self, writer, mesh, meshProps, meshes):
        writer.write(struct.pack("H", meshProps.InstanceIdx)) # instance idx
        
        lods    = []
        lodName = "{}_lod".format(mesh.name)
        
        for lod in meshes:
            if lod == mesh:
                continue
            
            if lod.name.startswith(lodName) == False:
                continue
            
            lods.append(lod)
        
        lods.sort(key = lambda mesh: mesh.name)
        
        # find lods in meshes list - starts with "mesh_name_lod"
        # put in separe list and remove from original
        # write lod0 and in foreach rest of lods
        
        writer.write(struct.pack("B", len(lods) + 1)) # lod count
        
        self.SerializeVisualLod(writer, mesh, meshProps)
        
        for lod in lods:
            self.SerializeVisualLod(writer, lod, lod.MeshProps)
    
    def SerializeBillboard(self, writer, meshProps):
        writer.write(struct.pack("I", meshProps.Axis))
        writer.write(struct.pack("?", meshProps.AxisMode))

    
    def SerializeDummy(self, writer, mesh):
        aabb    = mesh.bound_box
        aabbMin = [ aabb[0][0], aabb[0][1], aabb[0][2] ]
        aabbMax = [ aabb[0][0], aabb[0][1], aabb[0][2] ]
        
        for corner in aabb:
            if aabbMin[0] > corner[0]:
                aabbMin[0] = corner[0]
            if aabbMax[0] < corner[0]:
                aabbMax[0] = corner[0]
            
            if aabbMin[1] > corner[1]:
                aabbMin[1] = corner[1]
            if aabbMax[1] < corner[1]:
                aabbMax[1] = corner[1]
            
            if aabbMin[2] > corner[2]:
                aabbMin[2] = corner[2]
            if aabbMax[2] < corner[2]:
                aabbMax[2] = corner[2]
        
        writer.write(struct.pack("fff",  aabbMin[0], aabbMin[2], aabbMin[1]))
        writer.write(struct.pack("fff",  aabbMax[0], aabbMax[2], aabbMax[1]))
    
    
    def SerializeMesh(self, writer, mesh, meshes):
        meshProps = mesh.MeshProps
        writer.write(struct.pack("B", int(meshProps.Type, 0)))
        
        if meshProps.Type == "0x01":
            writer.write(struct.pack("B", int(meshProps.VisualType, 0)))
            writer.write(struct.pack("H", meshProps.RenderFlags)) # render flags
        
        parentIdx = 0
        parent    = mesh.parent
        
        if parent:
            parentIdx = meshes.index(parent) + 1
        
        location = mesh.location
        scale    = mesh.scale
        rotation = mesh.rotation_euler.to_quaternion()
        
        writer.write(struct.pack("H",    parentIdx)) # parent idx
        writer.write(struct.pack("fff",  location[0], location[2], location[1]))
        writer.write(struct.pack("fff",  scale[0],    scale[2],    scale[1]))
        writer.write(struct.pack("ffff", rotation[0], rotation[1], rotation[3], rotation[2]))
        writer.write(struct.pack("B", meshProps.CullingFlags)) # culling flags
        self.SerializeString(writer, mesh.name)
        self.SerializeString(writer, meshProps.Parameters)
        
        type       = meshProps.Type
        visualType = meshProps.VisualType
        
        if type == "0x01":
            if visualType == "0x00":
                self.SerializeVisual(writer, mesh, meshProps, meshes)

            elif visualType == "0x04":
                self.SerializeVisual(writer, mesh, meshProps, meshes)
                self.SerializeBillboard(writer, meshProps)

            else:
                self.ShowError("Unsupported visual type {}!".format(visualType))
                return
        
        elif type == "0x06":
            self.SerializeDummy(writer, mesh)
        
        else:
            self.ShowError("Unsupported mesh type {}!".format(type))
            return
    
    
    def SerializeFile(self, writer):
        writer.write("4DS\0".encode());      # fourcc
        writer.write(struct.pack("H", 0x1d)) # mafia 4ds version
        
        scene = types.Scene
        
        guid  = getattr(scene, "guid", 0)
        writer.write(struct.pack("Q", guid)) # guid
        
        # write all materials
        materials = bpy.data.materials
        writer.write(struct.pack("H", len(materials)))
        
        for material in materials:
            self.SerializeMaterial(writer, material)
        
        # write all meshes
        includeMeshesMode = self.Config.IncludeMeshes
        allMeshes         = []
        
        if includeMeshesMode == "0":
            allMeshes = bpy.context.collection.all_objects
            
        elif includeMeshesMode == "1":
            allMeshes = bpy.context.visible_objects
        
        meshes    = []
        meshCount = 0
        
        for mesh in allMeshes:
            if mesh.type == "MESH":
                meshes.append(mesh)
                
                if self.IsLod(mesh) == False:
                    meshCount += 1
        
        writer.write(struct.pack("H", meshCount))
        
        for mesh in meshes:
            if self.IsLod(mesh) == False:
                self.SerializeMesh(writer, mesh, meshes)
        
        # allow 5ds animation
        isAnimated = getattr(scene, "isAnimated", 0)
        writer.write(struct.pack("B", isAnimated))
    
    
    def Export(self, filename):
        with open(filename, "wb") as writer:
            self.SerializeFile(writer)
        
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
            ("0", "All in Collection",  ""),
            ("1", "Visible Only", "")
        ],
        default = "0"
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
