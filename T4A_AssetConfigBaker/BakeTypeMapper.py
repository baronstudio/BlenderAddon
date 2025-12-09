"""
T4A Assets Configuration Baker - Baking Type Mapper
Maps custom PBR texture types to Blender Cycles bake types
"""

# Cycles Bake Types disponibles dans Blender:
# 'COMBINED', 'AO', 'SHADOW', 'POSITION', 'NORMAL', 'UV', 
# 'ROUGHNESS', 'EMIT', 'ENVIRONMENT', 'DIFFUSE', 'GLOSSY', 'TRANSMISSION'

# Mapping: Custom Type -> (Cycles Type, Additional Settings)
BAKE_TYPE_MAPPING = {
    # PBR Core Maps
    'ALBEDO': {
        'cycles_type': 'DIFFUSE',
        'use_pass_direct': False,
        'use_pass_indirect': False,
        'use_pass_color': True,
        'description': 'Base color without lighting'
    },
    
    'NORMAL_GL': {
        'cycles_type': 'NORMAL',
        'normal_space': 'TANGENT',
        'description': 'Tangent space normal map (OpenGL)'
    },
    
    'NORMAL_DX': {
        'cycles_type': 'NORMAL',
        'normal_space': 'TANGENT',
        'flip_y': True,  # Invert Y channel for DirectX
        'description': 'Tangent space normal map (DirectX)'
    },
    
    'METALLIC': {
        'cycles_type': 'EMIT',  # Workaround: use emission to capture metallic socket
        'extract_socket': 'Metallic',  # Socket name in Principled BSDF
        'description': 'Metallic map from Principled BSDF'
    },
    
    'ROUGHNESS': {
        'cycles_type': 'ROUGHNESS',
        'description': 'Roughness map'
    },
    
    'OCCLUSION': {
        'cycles_type': 'AO',
        'description': 'Ambient Occlusion'
    },
    
    # Additional Maps
    'ALPHA': {
        'cycles_type': 'EMIT',
        'extract_socket': 'Alpha',
        'description': 'Alpha/Opacity from Principled BSDF'
    },
    
    'EMISSION': {
        'cycles_type': 'EMIT',
        'description': 'Emission map'
    },
    
    'HEIGHT': {
        'cycles_type': 'EMIT',
        'extract_socket': 'Height',
        'description': 'Height/Displacement map'
    },
    
    'GLOSSINESS': {
        'cycles_type': 'ROUGHNESS',
        'invert': True,  # Glossiness = 1 - Roughness
        'description': 'Glossiness (inverted roughness)'
    },
    
    'SPECULAR': {
        'cycles_type': 'GLOSSY',
        'use_pass_direct': True,
        'use_pass_indirect': True,
        'use_pass_color': True,
        'description': 'Specular reflectance'
    },
    
    # Legacy
    'DIFFUSE': {
        'cycles_type': 'DIFFUSE',
        'use_pass_direct': True,
        'use_pass_indirect': True,
        'use_pass_color': True,
        'description': 'Legacy diffuse with lighting'
    },
    
    'COMBINED': {
        'cycles_type': 'COMBINED',
        'description': 'Combined render output'
    },
}


def get_bake_settings(custom_type):
    """
    Get Cycles bake settings for a custom texture type
    
    Args:
        custom_type (str): Custom texture type (e.g., 'ALBEDO', 'NORMAL_GL')
    
    Returns:
        dict: Baking settings with 'cycles_type' and optional parameters
    """
    return BAKE_TYPE_MAPPING.get(custom_type, {
        'cycles_type': 'COMBINED',
        'description': 'Unknown type, using COMBINED'
    })


def setup_bake_settings(context, custom_type):
    """
    Configure Cycles bake settings based on custom type
    
    Args:
        context: Blender context
        custom_type (str): Custom texture type
    
    Returns:
        str: Cycles bake type to use with bpy.ops.object.bake()
    """
    settings = get_bake_settings(custom_type)
    bake_settings = context.scene.render.bake
    
    # Reset to defaults
    bake_settings.use_pass_direct = True
    bake_settings.use_pass_indirect = True
    bake_settings.use_pass_color = True
    
    # Apply custom settings
    if 'use_pass_direct' in settings:
        bake_settings.use_pass_direct = settings['use_pass_direct']
    
    if 'use_pass_indirect' in settings:
        bake_settings.use_pass_indirect = settings['use_pass_indirect']
    
    if 'use_pass_color' in settings:
        bake_settings.use_pass_color = settings['use_pass_color']
    
    # Normal map settings
    if 'normal_space' in settings:
        bake_settings.normal_space = settings['normal_space']
    
    return settings.get('cycles_type', 'COMBINED')


def requires_socket_extraction(custom_type):
    """
    Check if this type requires extracting a specific shader socket
    (For types like METALLIC, ALPHA that don't have direct Cycles bake types)
    
    Args:
        custom_type (str): Custom texture type
    
    Returns:
        str or None: Socket name to extract, or None if not needed
    """
    settings = get_bake_settings(custom_type)
    return settings.get('extract_socket')


def requires_post_processing(custom_type):
    """
    Check if the baked image requires post-processing
    
    Args:
        custom_type (str): Custom texture type
    
    Returns:
        dict or None: Post-processing settings
    """
    settings = get_bake_settings(custom_type)
    post_process = {}
    
    if settings.get('flip_y'):
        post_process['flip_y'] = True
    
    if settings.get('invert'):
        post_process['invert'] = True
    
    return post_process if post_process else None
