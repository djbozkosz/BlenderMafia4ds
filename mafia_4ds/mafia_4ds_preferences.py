import bpy

from bpy import props
from bpy import types


class Mafia4ds_PreferencesGUI(types.AddonPreferences):
    bl_idname = __package__
    
    DataPath : props.StringProperty(
        name    = "Game Data Path",
        subtype = 'DIR_PATH',
        maxlen  = 255
    )
    
    
    def draw(self, context):
        layout = self.layout
        
        if len(self.DataPath) == 0:
            layout.alert = True
            layout.label(text = "Please specify game installation directory!")
            layout.alert = False
        
        layout.prop(self, "DataPath")


class Mafia4ds_Preferences(types.Operator):
    "Mafia 4ds Preferences"
    bl_idname  = "mafia4ds.preferences"
    bl_label   = "Mafia 4ds Preferences"
    bl_options = {'REGISTER', 'UNDO'}
    
    
    def execute(self, context):
        return {'FINISHED'}


def register():
    bpy.utils.register_class(Mafia4ds_Preferences)
    bpy.utils.register_class(Mafia4ds_PreferencesGUI)


def unregister():
    bpy.utils.unregister_class(Mafia4ds_Preferences)
    bpy.utils.unregister_class(Mafia4ds_PreferencesGUI)
