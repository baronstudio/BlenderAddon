import bpy

from . import icon, manual, prefs

if bpy.app.version >= (4, 0, 0):
    from . import props_v4 as props
else:
    from . import props_v3 as props


def register():
    icon.register()
    props.register()
    manual.register()
    prefs.register()


def unregister():
    icon.unregister()
    props.unregister()
    manual.unregister()
    prefs.unregister()
