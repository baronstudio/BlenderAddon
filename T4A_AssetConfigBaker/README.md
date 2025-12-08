# T4A Assets Configuration Baker

Blender 5.0+ Extension for automating 3D asset preparation for web-based configurators.

## Structure du Code

```
T4A_AssetConfigBaker/
├── __init__.py              # Point d'entrée principal avec système auto_load
├── auto_load.py             # Système d'auto-chargement des modules
├── blender_manifest.toml    # Manifeste Blender 5.0
│
├── Panels.py                # Interface utilisateur (N-Panel 3D View)
├── Prefs.py                 # Préférences de l'addon
├── Properties.py            # Propriétés de scène et variables runtime
│
├── Baker_V1.py              # Moteur de baking 3D
└── Baker_Mat_V1.py          # Moteur de baking de matériaux
```

## Modules

### `__init__.py`
Point d'entrée principal de l'extension. Utilise le système `auto_load` pour charger automatiquement tous les modules Python.

### `auto_load.py`
Système d'auto-chargement qui :
- Découvre automatiquement tous les modules Python
- Enregistre les classes Blender (Panels, Operators, Properties, etc.)
- Gère les dépendances entre classes

### `Panels.py`
Interface utilisateur dans la 3D View (N-Panel) :
- **T4A_PT_MainPanel** (bl_order=0) : Panel principal
- **T4A_PT_BakerPanel** (bl_order=1) : Options de baking 3D
- **T4A_PT_MaterialBakerPanel** (bl_order=2) : Options de baking matériaux
- **T4A_PT_InfoPanel** (bl_order=99) : Informations de l'addon (manifest)

Utilise `bl_order` pour contrôler l'ordre d'affichage des panels.

### `Prefs.py`
Préférences utilisateur de l'addon :
- Chemins d'export par défaut
- Paramètres de performance (GPU, résolution max)
- Options de workflow (auto-save, debug)
- Conventions de nommage
- Paramètres d'export GLB

### `Properties.py`
Propriétés de scène (`context.scene.t4a_baker_props`) :
- Paramètres de baking 3D (résolution, samples, margin)
- Paramètres de baking matériaux (type, format, options)
- État de processing (is_baking, progress, temps)
- Paramètres d'export (GLB, chemin, nom)
- Options hiérarchie et métadonnées

### `Baker_V1.py`
Moteur de baking 3D avec opérateurs :
- `T4A_OT_BakerExample` : Baking 3D principal
- `T4A_OT_AnalyzeScene` : Analyse de scène
- `T4A_OT_PrepareForBake` : Préparation objets (UV, matériaux)
- `T4A_OT_BakeTextures` : Baking de textures
- `T4A_OT_ExportAsset` : Export GLB

### `Baker_Mat_V1.py`
Moteur de baking de matériaux avec opérateurs :
- `T4A_OT_BakerMatExample` : Baking matériau principal
- `T4A_OT_BakePBRMaps` : Baking set PBR complet
- `T4A_OT_BakeDiffuse` : Baking diffuse/base color
- `T4A_OT_BakeNormal` : Baking normal map
- `T4A_OT_BakeRoughness` : Baking roughness
- `T4A_OT_BakeAO` : Baking ambient occlusion
- `T4A_OT_OptimizeMaterials` : Optimisation matériaux web
- `T4A_OT_CreateBakeMaterial` : Création matériau baked
- `T4A_OT_BatchBakeMaterials` : Baking batch multiple objets

## Installation

1. Télécharger ou cloner le dépôt
2. Dans Blender 5.0+, aller dans Edit > Preferences > Extensions
3. Cliquer sur "Install from Disk"
4. Sélectionner le dossier `T4A_AssetConfigBaker`
5. Activer l'extension

## Utilisation

1. Ouvrir le N-Panel dans la 3D View
2. Naviguer vers l'onglet "T4A Baker"
3. Configurer les paramètres de baking
4. Sélectionner les objets à baker
5. Exécuter les opérations de baking

## Développement

### Ajouter un nouveau module
Le système `auto_load` détectera automatiquement tout nouveau fichier `.py` ajouté dans le dossier.

### Ajouter un panel
1. Créer une classe héritant de `bpy.types.Panel` dans `Panels.py`
2. Définir `bl_order` pour contrôler la position
3. Le système `auto_load` l'enregistrera automatiquement

### Ajouter un opérateur
1. Créer une classe héritant de `bpy.types.Operator`
2. L'ajouter dans `Baker_V1.py` (baking 3D) ou `Baker_Mat_V1.py` (matériaux)
3. Ajouter la classe au tuple `classes` pour l'enregistrement

### Ajouter une propriété
1. Définir la propriété dans `T4A_BakerProperties` (`Properties.py`)
2. Accès via `context.scene.t4a_baker_props.ma_propriete`

## Licence

GPL-3.0-or-later

## Auteur

Jean-Baptiste BARON
Tech 4 Art Conseil

## Repository

https://github.com/baronstudio/BlenderAddon/tree/master/T4A_AssetConfigBaker
