# T4A Asset Config Baker - Feature Backlog

## 🚀 Features Implemented

### ✅ PBR Preset System
- **Standard PBR**: Albedo, Normal (OpenGL), Metallic, Roughness, Occlusion
- **Game Engine**: Optimized preset for game engines
- **Full PBR Suite**: Complete texture set with Alpha, Emission, Height
- **glTF 2.0**: glTF standard compliant naming
- **Custom**: Manual map configuration

### ✅ Map Types Available
- Albedo (Base Color)
- Normal (OpenGL and DirectX formats)
- Metallic
- Roughness
- Occlusion (AO)
- Alpha/Opacity
- Emission
- Height/Displacement
- Glossiness
- Specular
- Diffuse (Legacy)
- Combined

### ✅ File Naming Convention
- Lowercase suffixes: `_albedo`, `_normal_gl`, `_occlusion`, etc.
- Format: `{MaterialName}{suffix}.{ext}`
- Example: `Wood_albedo.png`, `Metal_normal_gl.png`

---

## 📋 Backlog - Future Features

### 🎨 Channel Packing
**Priority: High**

#### ORM Packing (Occlusion + Roughness + Metallic)
- Combine 3 grayscale maps into RGB channels
- R = Occlusion
- G = Roughness  
- B = Metallic
- Output format: `{MaterialName}_orm.png`

#### Custom RGBA Packing
- User-configurable channel assignment
- Support for various packing schemes (Unity, Unreal, etc.)

**Implementation Notes:**
- New operator: `T4A_OT_PackTextures`
- Post-process after individual map baking
- Option to delete source maps after packing
- Validation of source map existence

---

### 🔄 Normal Map Conversion
**Priority: Medium**

#### OpenGL ↔ DirectX Conversion
- Convert between Y-up (OpenGL) and Y-down (DirectX) formats
- Automatic detection of source format
- Batch conversion support

**Implementation Notes:**
- New operator: `T4A_OT_ConvertNormalMap`
- Option in UI to convert on export
- Pixel manipulation: invert green channel
- Preserve other channels (R, B, A)

**Code Reference:**
```python
# Pseudo-code for conversion
def convert_normal_map(image, target_format):
    pixels = list(image.pixels)
    for i in range(1, len(pixels), 4):  # Green channel
        pixels[i] = 1.0 - pixels[i]  # Invert
    image.pixels = pixels
```

---

### 📁 Export Profiles
**Priority: Medium**

#### Engine-Specific Presets
- **Unreal Engine**
  - BaseColor, Normal, ORM (packed)
  - Naming: `T_MaterialName_C`, `T_MaterialName_N`, `T_MaterialName_ORM`
  
- **Unity URP/HDRP**
  - BaseColor (Albedo), Normal, Metallic, Smoothness (1-Roughness)
  - Naming: `MaterialName_Albedo`, `MaterialName_Normal`, etc.
  
- **glTF 2.0**
  - BaseColor, Normal, MetallicRoughness (packed B=Metallic, G=Roughness)
  - Naming: `MaterialName_baseColor`, `MaterialName_normal`, etc.

- **Three.js**
  - Standard PBR with optional EmissiveMap
  - Web-optimized sizes (max 2048x2048)

**Implementation Notes:**
- Extend `pbr_preset` enum with engine profiles
- Add export path templates per profile
- Automatic texture compression options
- Batch export for multiple objects

---

### 🔧 Advanced Features

#### Smart Suffix Detection
- Auto-detect map type from shader nodes
- Suggest appropriate suffixes based on usage

#### Texture Optimization
- Automatic downsizing for web export
- Compression (JPEG quality, PNG optimization)
- Format conversion bulk operations

#### Validation & Preview
- Preview packed textures before save
- Validation warnings (missing maps, incorrect formats)
- Texture preview in UI with thumbnail

---

## 📝 Technical Debt

### Code Improvements
- [ ] Refactor baking logic into helper functions
- [ ] Add unit tests for texture packing
- [ ] Improve error handling and user feedback
- [ ] Add progress bar for batch operations

### Documentation
- [ ] User guide for PBR presets
- [ ] Video tutorials for common workflows
- [ ] API documentation for developers

---

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ PBR preset system
- ✅ File naming conventions
- ✅ Multi-map baking per material

### Phase 2 (Next)
- [ ] ORM channel packing
- [ ] Normal map conversion
- [ ] Export profiles (Unreal, Unity, glTF)

### Phase 3 (Future)
- [ ] Advanced packing configurations
- [ ] Texture optimization pipeline
- [ ] Real-time preview system

---

## 📞 Contact & Contributions

For feature requests or bug reports:
- GitHub: https://github.com/baronstudio/BlenderAddon/issues
- Maintainer: Jean-Baptiste BARON / Tech 4 Art Conseil
