# T4A Dev Tools

Small sidebar panel for Blender add-on developers.

**Location:** 3D View → Sidebar (`N`) → **T4A Dev**
**Blender:** 4.2+

## Features

- **Reload Add-on**: pick any enabled add-on, then disable it, purge it and all its sub-modules from memory, and re-enable it. Code changes are picked up without restarting Blender.
- **Open add-on folder** of the selected add-on, or the user add-ons/extensions folder.
- **Reload All Scripts** (`script.reload`).
- **System console**: toggle (Windows) and clear.
- **Interface**: quick toggles for *Developer Extras* and *Python Tooltips*.

The selected add-on is saved in the add-on preferences.

## Notes

- T4A Dev Tools can't reload itself. Use *Reload All Scripts* for that.
- Add-ons that keep state elsewhere (handlers, timers, `bpy.app.driver_namespace`) must clean it up in their own `unregister()`.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
