"""
T4A Assets Configuration Baker - Preset Loader
Loads and manages JSON preset files
"""

import bpy
import json
from pathlib import Path

# Global cache for presets (loaded once per Blender session)
_PRESETS_CACHE = {}
_CACHE_LOADED = False


def get_presets_directory():
    """Get the presets directory path from preferences or use default"""
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        custom_path = prefs.presets_path
        
        if custom_path and Path(custom_path).exists():
            return Path(custom_path)
    except:
        pass
    
    # Default: Presets folder in addon directory
    addon_dir = Path(__file__).parent
    return addon_dir / "Presets"


def load_preset_from_file(filepath):
    """Load a single preset JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        if 'id' not in data or 'name' not in data or 'maps' not in data:
            print(f"[T4A] Invalid preset file: {filepath.name}")
            return None
        
        return data
    except Exception as e:
        print(f"[T4A] Error loading preset {filepath.name}: {e}")
        return None


def load_all_presets(force_reload=False):
    """Load all preset JSON files from the presets directory"""
    global _PRESETS_CACHE, _CACHE_LOADED
    
    # Return cached presets if already loaded
    if _CACHE_LOADED and not force_reload:
        return _PRESETS_CACHE
    
    _PRESETS_CACHE = {}
    presets_dir = get_presets_directory()
    
    if not presets_dir.exists():
        print(f"[T4A] Presets directory not found: {presets_dir}")
        return _PRESETS_CACHE
    
    # Load all JSON files
    for json_file in presets_dir.glob("*.json"):
        preset_data = load_preset_from_file(json_file)
        if preset_data:
            preset_id = preset_data['id']
            _PRESETS_CACHE[preset_id] = preset_data
            print(f"[T4A] Loaded preset: {preset_data['name']} ({preset_id})")
    
    _CACHE_LOADED = True
    print(f"[T4A] Loaded {len(_PRESETS_CACHE)} preset(s)")
    
    return _PRESETS_CACHE


def get_preset(preset_id):
    """Get a specific preset by ID"""
    if not _CACHE_LOADED:
        load_all_presets()
    
    return _PRESETS_CACHE.get(preset_id)


def get_all_preset_items():
    """Get all presets as enum items for Blender UI"""
    if not _CACHE_LOADED:
        load_all_presets()
    
    items = []
    
    # Built-in presets from JSON files
    for preset_id, preset_data in _PRESETS_CACHE.items():
        items.append((
            preset_id,
            preset_data['name'],
            preset_data.get('description', '')
        ))
    
    # Sort alphabetically
    items.sort(key=lambda x: x[1])
    
    return items if items else [('NONE', "No Presets", "No presets available")]


def apply_preset_to_material(preset_id, mat_item):
    """Apply a preset configuration to a material item"""
    preset = get_preset(preset_id)
    
    if not preset:
        return False
    
    # Clear existing maps
    mat_item.maps.clear()
    
    # Add maps from preset
    for map_config in preset['maps']:
        map_item = mat_item.maps.add()
        map_item.map_type = map_config['map_type']
        map_item.file_suffix = map_config.get('file_suffix', '')
        map_item.enabled = map_config.get('enabled', True)
        map_item.output_format = map_config.get('output_format', 'PNG')
        map_item.resolution = map_config.get('resolution', 1024)
    
    return True


def save_custom_preset(preset_name, materials_data):
    """Save a custom preset to JSON file"""
    presets_dir = get_presets_directory()
    presets_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate ID from name
    preset_id = preset_name.lower().replace(' ', '_')
    
    preset_data = {
        'id': preset_id,
        'name': preset_name,
        'description': f"Custom preset with {len(materials_data)} material(s)",
        'version': '1.0',
        'is_custom': True,
        'maps': []
    }
    
    # Extract maps from first material (assuming all materials use same config)
    if materials_data:
        first_mat = materials_data[0]
        for map_item in first_mat.maps:
            preset_data['maps'].append({
                'map_type': map_item.map_type,
                'file_suffix': map_item.file_suffix,
                'enabled': map_item.enabled,
                'output_format': map_item.output_format,
                'resolution': map_item.resolution
            })
    
    # Save to file
    filepath = presets_dir / f"{preset_id}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(preset_data, f, indent=2, ensure_ascii=False)
    
    # Reload cache
    load_all_presets(force_reload=True)
    
    return preset_id


def delete_preset(preset_id):
    """Delete a preset JSON file"""
    presets_dir = get_presets_directory()
    filepath = presets_dir / f"{preset_id}.json"
    
    if filepath.exists():
        filepath.unlink()
        load_all_presets(force_reload=True)
        return True
    
    return False
