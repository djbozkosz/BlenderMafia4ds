bl_info = {
    "name"        : "Mafia 4DS format",
    "description" : "Mafia 4DS import / export addon.",
    "author"      : "djbozkosz",
    "version"     : (1, 0),
    "blender"     : (2, 80, 0),
    "location"    : "File > Import, File > Export, Object Properties, Material Properties",
    "warning"     : "Experimental Version! Backup your files before export!",
    "wiki_url"    : "https://github.com/djbozkosz/BlenderMafia4ds",
    "tracker_url" : "https://github.com/djbozkosz/BlenderMafia4ds/issues",
    "support"     : "COMMUNITY",
    "category"    : "Import-Export",
}


if "bpy" in locals():
    import importlib
    
    if "mafia_4ds_material_properties" in locals():
        importlib.reload(mafia_4ds_material_properties)
    if "mafia_4ds_mesh_properties" in locals():
        importlib.reload(mafia_4ds_mesh_properties)
    if "mafia_4ds_import" in locals():
        importlib.reload(mafia_4ds_import)
    if "mafia_4ds_export" in locals():
        importlib.reload(mafia_4ds_export)


import bpy

from mafia_4ds import mafia_4ds_material_properties
from mafia_4ds import mafia_4ds_mesh_properties
from mafia_4ds import mafia_4ds_import
from mafia_4ds import mafia_4ds_export


def register():
    mafia_4ds_material_properties.register()
    mafia_4ds_mesh_properties.register()
    mafia_4ds_import.register()
    mafia_4ds_export.register()


def unregister():
    mafia_4ds_material_properties.unregister()
    mafia_4ds_mesh_properties.unregister()
    mafia_4ds_import.unregister()
    mafia_4ds_export.unregister()


if __name__ == "__main__":
    register()
