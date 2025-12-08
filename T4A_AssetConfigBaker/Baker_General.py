"""
T4A Assets Configuration Baker - General Baking Utilities
Prépare la scène pour le baking avec Cycles
"""

import bpy
from bpy.types import Operator

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
    T4A_OT_PrepareCyclesBaking,
)

def register():
    pass

def unregister():
    pass
