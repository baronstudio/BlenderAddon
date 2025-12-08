import bpy
print('=== T4A Baker Props Debug ===')
if hasattr(bpy.types.Scene, 't4a_baker_props'):
    print(' t4a_baker_props is registered on Scene')
    scene = bpy.context.scene
    if hasattr(scene, 't4a_baker_props'):
        print(' Current scene has t4a_baker_props')
        props = scene.t4a_baker_props
        print(f'  - Type: {type(props)}')
        print(f'  - Has materials: {hasattr(props, \"materials\")}')
    else:
        print(' Current scene does NOT have t4a_baker_props')
else:
    print(' t4a_baker_props is NOT registered on Scene')
    print('  Available Scene properties:')
    for attr in dir(bpy.types.Scene):
        if 't4a' in attr.lower():
            print(f'    - {attr}')
