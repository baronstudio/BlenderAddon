"""
T4A Assets Configuration Baker - General Baking Utilities
Prépare la scène pour le baking avec Cycles
"""

import bpy
from bpy.types import Operator
import re


def clean_blender_name(name):
    """
    Remove Blender's automatic suffixes (.001, .002, etc.) from names
    for file export while keeping the original scene objects untouched.
    
    Examples:
        "Material.001" -> "Material"
        "Cube.003" -> "Cube"
        "Collection.012" -> "Collection"
        "MyMaterial" -> "MyMaterial" (unchanged)
    
    Args:
        name: The name to clean
        
    Returns:
        Cleaned name without numeric suffix
    """
    # Pattern: matches .001, .002, .999, etc. at the end of string
    return re.sub(r'\.\d{3}$', '', name)


def generate_baking_summary(props):
    """
    Generate a detailed summary of what will be baked based on enabled items.
    
    Args:
        props: T4A_BakerProperties from scene
        
    Returns:
        String with formatted summary or None if nothing to bake
    """
    try:
        summary_lines = []
        summary_lines.append("=" * 60)
        summary_lines.append("BAKING CONFIGURATION SUMMARY")
        summary_lines.append("=" * 60)
        
        total_collections = 0
        total_objects = 0
        total_materials = 0
        total_maps = 0
        
        # Loop through collections
        for coll_item in props.collections:
            if not coll_item.enabled:
                continue
            
            total_collections += 1
            coll_objects = []
            
            # Loop through objects in collection
            for obj_item in coll_item.objects:
                if not obj_item.enabled:
                    continue
                
                total_objects += 1
                obj_materials = []
                
                # Loop through materials in object
                for mat_item in obj_item.materials:
                    if not mat_item.enabled:
                        continue
                    
                    total_materials += 1
                    mat_maps = []
                    
                    # Loop through maps in material
                    for map_item in mat_item.maps:
                        if not map_item.enabled:
                            continue
                        
                        total_maps += 1
                        mat_maps.append(f"        - {map_item.map_type} ({map_item.output_format}, {map_item.resolution}px)")
                    
                    if mat_maps:
                        obj_materials.append(f"    📦 Material: {mat_item.name} ({len(mat_maps)} maps)")
                        obj_materials.extend(mat_maps)
                
                if obj_materials:
                    coll_objects.append(f"  🎲 Object: {obj_item.name} ({len([m for m in obj_item.materials if m.enabled])} materials)")
                    coll_objects.extend(obj_materials)
            
            if coll_objects:
                summary_lines.append(f"\n📁 Collection: {coll_item.name}")
                summary_lines.extend(coll_objects)
        
        # Add totals
        summary_lines.append("\n" + "-" * 60)
        summary_lines.append("TOTALS:")
        summary_lines.append(f"  Collections: {total_collections}")
        summary_lines.append(f"  Objects:     {total_objects}")
        summary_lines.append(f"  Materials:   {total_materials}")
        summary_lines.append(f"  Maps:        {total_maps}")
        summary_lines.append("=" * 60)
        
        # Check if there's anything to bake
        if total_maps == 0:
            return None
        
        return "\n".join(summary_lines)
    
    except Exception as e:
        print(f"[T4A] Error generating baking summary: {e}")
        return None


def find_layer_collection(layer_collection, collection_name):
    """
    Recherche récursive d'une layer collection par son nom
    
    Args:
        layer_collection: Le layer_collection parent où chercher
        collection_name: Le nom de la collection à trouver
        
    Returns:
        Le LayerCollection trouvé ou None si non trouvé
    """
    if layer_collection.name == collection_name:
        return layer_collection
    
    for child in layer_collection.children:
        result = find_layer_collection(child, collection_name)
        if result:
            return result
    
    return None


class T4A_OT_Bakeconfiguration(Operator):
    """Loop on all collections and objects to set bake configuration"""
    bl_idname = "t4a.bake_configuration"
    bl_label = "Configurer le baking pour les collections"
    bl_description = "Configure les collections et objets pour le baking"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        props = scene.t4a_baker_props
        
        # Generate and print baking summary
        summary = generate_baking_summary(props)
        if summary is None:
            self.report({'WARNING'}, "No items enabled for baking. Enable collections, objects, materials and maps first.")
            return {'CANCELLED'}
        
        # Print summary to console
        print(summary)
        self.report({'INFO'}, "Baking summary printed to console. Check System Console (Window > Toggle System Console)")
        
        # Initialize baking state
        props.is_baking = True
        props.bake_progress = 0.0
        
        # Count total objects to bake
        total_objects = sum(1 for coll_item in props.collections if coll_item.enabled 
                           for obj_item in coll_item.objects if obj_item.enabled)
        current_object = 0

        #memorise la collection courante
        current_collection = context.view_layer.active_layer_collection

        #memorize collection layer exclud status
        collection_exclude_status = {}
        for coll_item in props.collections:
            collection = bpy.data.collections.get(coll_item.name)
            if collection:
                ColLayer = context.view_layer.layer_collection.children.get(collection.name)
                if ColLayer:
                    collection_exclude_status[coll_item.name] = ColLayer.exclude

        #looping on collections liste in props
        for coll_item in props.collections:
            if not coll_item.enabled:
                continue

            collection = bpy.data.collections.get(coll_item.name)
            if not collection:
                self.report({'WARNING'}, f"Collection '{coll_item.name}' introuvable")
                continue
            
            

            #isolate curent collection from other in props.collections
            laycol = bpy.context.view_layer.layer_collection
            for other_coll_item in props.collections:
                if other_coll_item.name != coll_item.name:
                    other_collection = bpy.data.collections.get(other_coll_item.name)
                    coltoexclude = find_layer_collection(laycol,other_collection.name)
                    if coltoexclude is None :
                        self.report({'INFO'}, "Configuration de baking appliquée aux collections sélectionnées")
                        return {'FINISHED'}
                    else:
                        coltoexclude.exclude = True
                        
                    for i in laycol.children:
                        if i.name == other_collection.name:
                            i.exclude = True
                    #if other_collection:
                    #        laycol = bpy.context.view_layer.layer_collection
                    #        for i in laycol.children:
                    #            if i.name == other_collection.name:
                    #                i.exclude = True
                            #.children[other_collection.name].exclude = True
                else:
                    coltokip = find_layer_collection(laycol,coll_item.name)
                    if coltokip is not None:
                        coltokip.exclude = False
                    
            #looping on objects in objects in curent collection props
            for objtobake in coll_item.objects:

                if not objtobake.enabled:
                    continue

                obj = collection.objects.get(objtobake.name)
                if obj.type != 'MESH':
                    continue
                
                # Update progress
                current_object += 1
                if total_objects > 0:
                    props.bake_progress = (current_object / total_objects) * 100.0

                # Assure que l'objet est visible et sélectionnable, selectionné et actif
                obj.hide_viewport = False
                obj.hide_render = False
                bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]
                bpy.data.objects[obj.name].select_set(True)
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)


                # bake the object with configrured settings
                bpy.ops.t4a.baker_mat( target_object=obj.name)
                self.report({'INFO'}, f"===============fin du cycle de baking pour : {obj.name} ===================")
                

        
            #restore collection layer exclude status
            for coll_item in props.collections:
                collection = bpy.data.collections.get(coll_item.name)
                if collection:
                    ColLayer = context.view_layer.layer_collection.children.get(collection.name)
                    if ColLayer and coll_item.name in collection_exclude_status:
                        ColLayer.exclude = collection_exclude_status[coll_item.name]
        
        #restor current collection
        context.view_layer.active_layer_collection = current_collection
        
        # Finalize baking state
        props.is_baking = False
        props.bake_progress = 100.0

        self.report({'INFO'}, "Configuration de baking appliquée aux collections sélectionnées")
        return {'FINISHED'}

class T4A_OT_PrepareCyclesBaking(Operator):
    """Prépare la scène pour le baking avec Cycles"""
    bl_idname = "t4a.prepare_cycles_baking"
    bl_label = "Préparer la scène pour le baking Cycles"
    bl_description = "Configure le moteur de rendu, les samples et les options nécessaires pour le baking Cycles"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        render = scene.render
        cycles = scene.cycles

        # Définit Cycles comme moteur de rendu
        render.engine = 'CYCLES'
        self.report({'INFO'}, "Moteur de rendu défini sur Cycles")

        # Active le device GPU si disponible
        prefs = bpy.context.preferences.addons['cycles'].preferences if 'cycles' in bpy.context.preferences.addons else None
        if prefs and hasattr(prefs, 'compute_device_type'):
            devices = prefs.get_devices() if hasattr(prefs, 'get_devices') else None
            if devices and 'CUDA' in devices:
                prefs.compute_device_type = 'CUDA'
            else:
                prefs.compute_device_type = 'NONE'
            self.report({'INFO'}, f"Device de calcul : {prefs.compute_device_type}")

        # Paramètres de samples
        cycles.samples = 64
        cycles.use_adaptive_sampling = True
        cycles.max_bounces = 4
        cycles.use_denoising = False
        # cycles.use_progressive_refine = False  # Obsolète dans Blender 3.x/5.x
        self.report({'INFO'}, "Options Cycles configurées pour le baking")

        # Désactive le motion blur et autres options inutiles
        render.use_motion_blur = False
        render.use_persistent_data = True

        # Désactive le film transparent (utile pour baking)
        scene.render.film_transparent = False

        return {'FINISHED'}

# Système d'autoload : expose uniquement le tuple classes
classes = (
    T4A_OT_Bakeconfiguration,
    T4A_OT_PrepareCyclesBaking,
)

def register():
    pass

def unregister():
    pass
