import bpy

def test_addon_preferences():
    """Test script to verify addon preferences registration."""
    addon_name = "T4A_3DFilesQtCheck"
    
    print(f"Testing addon preferences for: {addon_name}")
    
    # Check if addon is in the preferences
    try:
        prefs = bpy.context.preferences.addons[addon_name].preferences
        print(f"✓ Addon preferences found: {type(prefs)}")
        print(f"✓ bl_idname: {getattr(prefs, 'bl_idname', 'NOT_FOUND')}")
        
        # Check properties
        print("Properties:")
        for prop in ['scan_path', 'google_api_key', 'debug_mode', 'model_name']:
            if hasattr(prefs, prop):
                value = getattr(prefs, prop, 'NOT_SET')
                print(f"  ✓ {prop}: {value}")
            else:
                print(f"  ✗ {prop}: MISSING")
                
    except KeyError:
        print(f"✗ Addon '{addon_name}' not found in preferences")
        print("Available addons:")
        for name in bpy.context.preferences.addons.keys():
            print(f"  - {name}")
    except Exception as e:
        print(f"✗ Error accessing preferences: {e}")

if __name__ == "__main__":
    test_addon_preferences()