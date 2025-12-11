"""
T4A Assets Configuration Baker - General Baking Utilities
Prépare la scène pour le baking avec Cycles
"""

import bpy
from bpy.types import Operator


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
        
        ##### DEBUG TEMP
        for i in props.collections: 
            print(f"|| {i.name}")
            for j in i.objects: 
                print(f"--|| {j.name}")
                for k in j.materials:
                    print(f"----|| {k.name}")


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
