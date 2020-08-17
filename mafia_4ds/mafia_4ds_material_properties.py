from bpy import props
from bpy import types
from bpy import utils


class Mafia4ds_GlobalMaterialProperties(types.PropertyGroup):
    UseDiffuseTex   : props.BoolProperty       (name = "Use Diffuse Tex",   default = True)
    Coloring        : props.BoolProperty       (name = "Coloring",          default = False)
    AmbientColor    : props.FloatVectorProperty(name = "Ambient Color",     default = (1.0, 1.0, 1.0), subtype = "COLOR", size = 3)
    DiffuseColor    : props.FloatVectorProperty(name = "Diffuse Color",     default = (1.0, 1.0, 1.0), subtype = "COLOR", size = 3)
    
    MipMapping      : props.BoolProperty       (name = "Mip Mapping",       default = True)
    TwoSided        : props.BoolProperty       (name = "Two Sided",         default = False)
    
    AddEffect       : props.BoolProperty       (name = "Add Effect",        default = False)
    ColorKey        : props.BoolProperty       (name = "Color Key",         default = False)
    AdditiveBlend   : props.BoolProperty       (name = "Additive Blend",    default = False)
    
    UseAlphaTexture : props.BoolProperty       (name = "Use Alpha Texture", default = False)
    AlphaTexture    : props.StringProperty     (name = "Alpha Texture",     default = "", subtype = "FILE_PATH")
    
    UseEnvTexture   : props.BoolProperty       (name = "Use Env Texture",   default = False)
    EnvDefaultMode  : props.BoolProperty       (name = "Env Default Mode",  default = True)
    EnvMultiplyMode : props.BoolProperty       (name = "Env Multiply Mode", default = False)
    EnvAdditiveMode : props.BoolProperty       (name = "Env Additive Mode", default = False)
    EnvYAxisRefl    : props.BoolProperty       (name = "Env Y Axis Refl",   default = True)
    EnvYAxisProj    : props.BoolProperty       (name = "Env Y Axis Proj",   default = False)
    EnvZAxisProj    : props.BoolProperty       (name = "Env Z Axis Proj",   default = False)
    EnvTexture      : props.StringProperty     (name = "Env Texture",       default = "", subtype = "FILE_PATH")
    
    AnimatedDiffuse : props.BoolProperty       (name = "Animated Diffuse",  default = False)
    AnimatedAlpha   : props.BoolProperty       (name = "Animated Alpha",    default = False)
    AnimatedFrames  : props.IntProperty        (name = "Animated Frames",   default = 0)
    AnimFrameLength : props.IntProperty        (name = "Anim Frame Length", default = 100)


class Mafia4ds_MaterialPropertiesPanel(types.Panel):
    "Mafia 4ds Material Properties"
    bl_label       = "Mafia 4ds Material Properties"
    bl_idname      = "MATERIAL_PT_mafia_4ds_material_properties"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "material"
    
    
    def draw(self, context):
        matProps = context.material.MaterialProps
        layout   = self.layout
        
        layout.label(text = "Basic setup:")
        layout.prop(matProps, "UseDiffuseTex")
        layout.prop(matProps, "Coloring")
        layout.prop(matProps, "AmbientColor")
        layout.prop(matProps, "DiffuseColor")
        
        layout.prop(matProps, "MipMapping")
        layout.prop(matProps, "TwoSided")
        
        layout.separator()
        layout.label(text = "Effects:")
        layout.prop(matProps, "AddEffect")
        layout.prop(matProps, "ColorKey")
        layout.prop(matProps, "AdditiveBlend")
        layout.prop(matProps, "UseAlphaTexture")
        layout.prop(matProps, "AlphaTexture")
        
        layout.separator()
        layout.label(text = "Env Mapping:")
        layout.prop(matProps, "UseEnvTexture")
        layout.prop(matProps, "EnvDefaultMode")
        layout.prop(matProps, "EnvMultiplyMode")
        layout.prop(matProps, "EnvAdditiveMode")
        layout.prop(matProps, "EnvYAxisRefl")
        layout.prop(matProps, "EnvYAxisProj")
        layout.prop(matProps, "EnvZAxisProj")
        layout.prop(matProps, "EnvTexture")
        
        layout.separator()
        layout.label(text = "Animated Textures:")
        layout.prop(matProps, "AnimatedDiffuse")
        layout.prop(matProps, "AnimatedAlpha")
        layout.prop(matProps, "AnimatedFrames")
        layout.prop(matProps, "AnimFrameLength")


def register():
    utils.register_class(Mafia4ds_GlobalMaterialProperties)
    utils.register_class(Mafia4ds_MaterialPropertiesPanel)
    
    types.Material.MaterialProps = props.PointerProperty(type = Mafia4ds_GlobalMaterialProperties)


def unregister():
    utils.unregister_class(Mafia4ds_GlobalMaterialProperties)
    utils.unregister_class(Mafia4ds_MaterialPropertiesPanel)
    
    del types.Material.MaterialProps


if __name__ == "__main__":
    register()
