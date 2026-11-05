<div align="center">

# T4A Blender Add-ons

**Free, open-source Blender tools for preparing 3D assets for real-time and the web.**
Texture baking, quality control, thumbnails and GLB export pipelines, by [Tech4Art Conseil](https://github.com/baronstudio).

[![License: GPL v3](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](LICENSE)
[![Blender](https://img.shields.io/badge/Blender-4.2%2B-orange?logo=blender&logoColor=white)](https://www.blender.org/)
[![Python syntax check](https://github.com/baronstudio/BlenderAddon/actions/workflows/check.yml/badge.svg)](https://github.com/baronstudio/BlenderAddon/actions/workflows/check.yml)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## Add-ons in this repository

Each folder is an independent add-on. Install only the ones you need.

| Add-on | What it does | Blender | Status |
|---|---|---|---|
| [**T4A Quick Baker**](T4A_quick_baker/) | PBR texture baker for many objects and materials at once: high-to-low and low-to-low, automatic cage, Unity/Unreal map presets, UDIM. A customized fork of [Quick Baker](https://b3dhub.github.io/quick-baker-docs) by Karan (@b3dhub). | 4.2+ | Stable |
| [**T4A Assets Configuration Baker**](T4A_AssetConfigBaker/) | Automates asset preparation for web product configurators. It analyzes the scene hierarchy, materials and naming, generates bake configurations from presets (glTF, game, Three.js…) and exports clean GLB files. | 5.0+ | Beta |
| [**T4A 3D Files QC Check**](T4A_3DFilesQtCheck/) | Quality-control checks for 3D files: mesh topology, UVs, texel density, textures, dimensions and scale, with optional AI-assisted reviews (Gemini). | 4.5+ | Work in progress |
| [**T4A Thumbnailer**](T4A_thumbnailer/) | Renders JPEG thumbnails from the active camera, including one image per material in batch mode. | 4.2+ | Stable |
| [**T4A Dev Tools**](T4A_DevTools/) | Helpers for add-on developers: hot-reload any enabled add-on, reload scripts, open add-on folders, toggle the system console and developer options. | 4.2+ | Stable |

## Installation

### Option 1: installer script (quickest)

From a clone or extracted download of the repository, run:

```bash
python install_addons.py            # interactive
python install_addons.py --dry-run  # preview, changes nothing
```

The script detects your installed Blender versions, then asks in the terminal which versions and add-ons to install, whether to **copy** them or **link** them to the repository (for development), and whether to enable them in Blender's preferences. It skips add-ons that need a newer Blender. Close Blender before running it.

### Option 2: from a ZIP

1. Download the repository (**Code → Download ZIP**) or a release, then extract it.
2. Zip **the add-on folder you want** on its own, for example `T4A_thumbnailer/` → `T4A_thumbnailer.zip`.
3. In Blender, go to **Edit → Preferences → Add-ons**:
   - **Blender 4.2+**: open the **⌄** menu → **Install from Disk…** and pick the ZIP.
   - **Older versions**: click **Install…** and pick the ZIP.
4. Enable the add-on. Its panel appears in the **3D View sidebar** (press `N`).

### Option 3: manual link for developers

Clone the repo and link an add-on folder into your Blender extensions or add-ons directory:

```bash
git clone https://github.com/baronstudio/BlenderAddon.git
```

On Windows, for example:

```powershell
New-Item -ItemType Junction `
  -Path "$env:APPDATA\Blender Foundation\Blender\4.2\extensions\user_default\T4A_quick_baker" `
  -Target "C:\path\to\BlenderAddon\T4A_quick_baker"
```

Each add-on folder has its own README with detailed usage.

## Contributing

Bug reports, ideas and pull requests are welcome.

- 🐛 **Found a bug?** [Open a bug report](https://github.com/baronstudio/BlenderAddon/issues/new?template=bug_report.yml)
- 💡 **Have an idea?** [Suggest a feature](https://github.com/baronstudio/BlenderAddon/issues/new?template=feature_request.yml)
- 🔧 **Want to code?** Read [CONTRIBUTING.md](CONTRIBUTING.md)

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). To report a vulnerability, see [SECURITY.md](SECURITY.md).

## License

All add-on code is licensed under the **[GNU General Public License v3.0 or later](LICENSE)**, the same license family as Blender. Every add-on folder also contains its own `LICENSE` file.

- **T4A Quick Baker** is a modified version of *Quick Baker* and the *qbpy* library, © Karan (@b3dhub), both GPL-3.0-or-later. Changes © Tech4Art Conseil. See [T4A_quick_baker/README.md](T4A_quick_baker/README.md).
- **Assets** such as presets, example scenes and icons may be under a separate license. See [T4A_AssetConfigBaker/ASSETS_LICENSE.md](T4A_AssetConfigBaker/ASSETS_LICENSE.md) (CC BY 4.0).

## Credits

- **Jean-Baptiste Baron / [Tech4Art Conseil](https://github.com/baronstudio)**: author and maintainer.
- **Karan ([@b3dhub](https://github.com/B3dHub))**: original author of [Quick Baker](https://b3dhub.github.io/quick-baker-docs) and [qbpy](https://github.com/B3dHub/qbpy). If you find the baker useful, please support the original add-on.

⭐ If these tools save you time, **star the repo** so other Blender artists can find it.
