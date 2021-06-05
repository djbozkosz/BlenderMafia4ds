## BlenderMafia4ds

[![Version: 1.0.1](https://img.shields.io/badge/version-1.0.1-lightgrey.svg)](https://github.com/djbozkosz/BlenderMafia4ds)
[![Game: Mafia](https://img.shields.io/badge/game-mafia-red.svg)](https://mafiagame.com)
[![Blender: 2.8](https://img.shields.io/badge/blender-2.8-green.svg)](https://www.blender.org/)
[![License: GPL v3](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](https://github.com/djbozkosz/BlenderMafia4ds/blob/master/LICENSE)

### Introduction:
Addon for Blender 2.8 with import and export support of Mafia PC 4ds model files.

<img src="https://i.postimg.cc/jjGmR3q3/bolt-b2.png" alt="Bolt Model B Cabriolet">

### Installation:
1. Click to green `Code` button and `Download ZIP`.
2. Copy `mafia_4ds` outside and make zip from it again (right click to directory: `Send to` -> `Compressed (zipped) folder`.
3. Open Blender and go to `Edit` -> `Preferences...`.
4. In left panel open `Add-ons` and click to `Install...`.
5. Choose your created zip file.
6. Addon should be filtered in addons list now. Expand selection and check it to enable addon.
7. Under `Preferences` choose proper directory of `Game Data Path`.

### Features:
#### Supported:
- import and export 4ds operations
- full 4ds material support with integrated panel
- basic blender material setup after import
- full mesh management: transform, flags, params with integrated panel
- currently supported mesh types: simple mesh and dummy
- lod support
#### Unsupported:
- other mesh types like single meshes, morphs, sectors, etc.
- mesh instancing

### Known issues:
- exporter doesn't support vertices with multiple UVs - you need to split vertices by yourself before export, or UV mapping will be corrupted
