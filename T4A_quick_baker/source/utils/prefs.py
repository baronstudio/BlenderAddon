import bpy
from bpy.props import BoolProperty, FloatVectorProperty, PointerProperty, StringProperty
from bpy.types import AddonPreferences, PropertyGroup

from .addon import package


class QBAKER_AP_bake(PropertyGroup):
    batch_name: StringProperty(
        name="Batch Name",
        description="Name the maps with additional info\n\n$name - Name of the Bakegroup\n$size    - Size of the map\n$type   - Type of the map\n\ne.g. (Bakegroup_1K_Color)",
        default="$name_$size_$type",
    )

    use_auto_udim: BoolProperty(
        name="Auto UDIM",
        description="Automatically create UDIM textures based on UV layout",
        default=True,
    )

    use_remove_disabled_maps: BoolProperty(
        name="Remove Disabled Maps",
        description="Remove disabled maps from the baked material",
        default=False,
    )


class QBAKER_AP_cage(PropertyGroup):
    color: FloatVectorProperty(
        name="Cage Color",
        description="Color for cage objects",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.7, 0.6, 0.5, 0.5),
    )

    show_wireframe: BoolProperty(
        name="Wireframe",
        description="Display the object's wireframe over solid shading",
        default=True,
    )


class QBAKER_AP_qbaker(PropertyGroup):
    bake: PointerProperty(type=QBAKER_AP_bake)
    cage: PointerProperty(type=QBAKER_AP_cage)

    use_vertex_color_object_mode: BoolProperty(
        name="Object Mode",
        description="Enable vertex color in object mode",
        default=False,
    )


class QBAKER_AP_preferences(AddonPreferences):
    bl_idname = package

    qbaker: PointerProperty(type=QBAKER_AP_qbaker)

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        col = layout.column()
        col.prop(self.qbaker.bake, "batch_name")
        col.prop(self.qbaker.bake, "use_auto_udim")
        col.prop(self.qbaker.bake, "use_remove_disabled_maps")

        col = layout.column(heading="Cage")
        col.prop(self.qbaker.cage, "color")
        col.prop(self.qbaker.cage, "show_wireframe")

        col = layout.column(heading="Vertex Color")
        col.prop(self.qbaker, "use_vertex_color_object_mode")


classes = (
    QBAKER_AP_bake,
    QBAKER_AP_cage,
    QBAKER_AP_qbaker,
    QBAKER_AP_preferences,
)


register, unregister = bpy.utils.register_classes_factory(classes)
