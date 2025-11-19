import bpy
from bpy.props import FloatVectorProperty
from bpy.types import Operator


class QBAKER_OT_vertex_color(Operator):
    bl_label = "Apply"
    bl_idname = "qbaker.vertex_color"
    bl_description = "Set Vertex Color"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        if hasattr(context.space_data, "shading"):
            return context.space_data.shading.type != "WIREFRAME"

    def _ensure_color_attribute(self, mesh, attribute_name, data_type="BYTE_COLOR", domain="CORNER"):
        """Ensure color attribute exists with version compatibility."""
        # Try modern color_attributes API first (Blender 3.2+)
        if hasattr(mesh, "color_attributes"):
            color_attribute = mesh.color_attributes.get(attribute_name)
            if not color_attribute:
                color_attribute = mesh.color_attributes.new(name=attribute_name, type=data_type, domain=domain)
            mesh.color_attributes.active_color = color_attribute
            return color_attribute

        # Fallback for older versions using vertex_colors (deprecated)
        elif hasattr(mesh, "vertex_colors"):
            color_layer = mesh.vertex_colors.get(attribute_name)
            if not color_layer:
                color_layer = mesh.vertex_colors.new(name=attribute_name)
            mesh.vertex_colors.active = color_layer
            return color_layer

        return None

    def _has_selected_faces(self, mesh):
        """Check if any faces are selected in edit mode."""
        return any(face.select for face in mesh.polygons)

    def _ensure_vertex_paint_brush(self, context):
        """Ensure we have a proper vertex paint brush that supports color operations."""
        vertex_paint = context.tool_settings.vertex_paint

        # Check if current brush exists and has color capability
        if vertex_paint.brush and hasattr(vertex_paint.brush, "vertex_paint_capabilities"):
            capabilities = vertex_paint.brush.vertex_paint_capabilities
            if hasattr(capabilities, "has_color") and capabilities.has_color:
                return vertex_paint.brush

        # Try to find a suitable brush or create one
        for brush in bpy.data.brushes:
            if (
                hasattr(brush, "vertex_paint_capabilities")
                and hasattr(brush.vertex_paint_capabilities, "has_color")
                and brush.vertex_paint_capabilities.has_color
            ):
                vertex_paint.brush = brush
                return brush

        # Fallback: create or use default vertex paint brush
        if not vertex_paint.brush or not hasattr(vertex_paint.brush, "color"):
            # Try to get the default Draw brush
            draw_brush = bpy.data.brushes.get("Draw")
            if draw_brush:
                vertex_paint.brush = draw_brush
            else:
                # Create a new brush if needed
                new_brush = bpy.data.brushes.new(name="VertexPaint", mode="VERTEX_PAINT")
                vertex_paint.brush = new_brush

        return vertex_paint.brush

    def _setup_paint_settings(self, context, mesh, color):
        """Configure vertex paint settings for the mesh."""
        # Configure paint mask
        if hasattr(mesh, "use_paint_mask"):
            mesh.use_paint_mask = True
        elif hasattr(mesh, "use_paint_mask_vertex"):
            mesh.use_paint_mask_vertex = True

        # Ensure we have a proper brush
        brush = self._ensure_vertex_paint_brush(context)

        # Set paint colors
        context.tool_settings.unified_paint_settings.color = color
        if brush and hasattr(brush, "color"):
            brush.color = color

    def _apply_color_to_object(self, context, obj, color, select_all_faces=False):
        """Apply vertex color to a single object."""
        mesh = obj.data

        # Ensure color attribute exists
        color_attribute = self._ensure_color_attribute(mesh, context.scene.qbaker.vertex_color_name or "VertexColor")
        if not color_attribute:
            return False

        # Set as active object and enter vertex paint mode
        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="VERTEX_PAINT")

        # Configure paint settings
        self._setup_paint_settings(context, mesh, color)

        # Select all faces if requested (for object mode)
        if select_all_faces:
            bpy.ops.paint.face_select_all(action="SELECT")

        # Apply color
        bpy.ops.paint.vertex_color_set()
        return True

    def _apply_vertex_color_object_mode(self, context, obj, color):
        """Apply vertex color to all faces in object mode."""
        self._apply_color_to_object(context, obj, color, select_all_faces=True)
        bpy.ops.object.mode_set(mode="OBJECT")

    def _apply_vertex_color_edit_mode(self, context, color):
        """Apply vertex color to selected faces in edit mode only."""
        # Store original state
        original_active = context.view_layer.objects.active
        selected_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]

        if not selected_objects:
            return

        # Switch to object mode to process all objects
        bpy.ops.object.mode_set(mode="OBJECT")

        # Process each selected mesh object
        for obj in selected_objects:
            # Check if object has selected faces in edit mode
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")

            if not self._has_selected_faces(obj.data):
                continue

            # Apply color to selected faces only
            bpy.ops.object.mode_set(mode="OBJECT")
            self._apply_color_to_object(context, obj, color, select_all_faces=False)

        # Restore original state
        context.view_layer.objects.active = original_active
        bpy.ops.object.mode_set(mode="EDIT")

    def execute(self, context):
        baker = context.scene.qbaker

        if context.mode == "OBJECT":
            for obj in context.selected_objects:
                if obj.type != "MESH":
                    continue
                self._apply_vertex_color_object_mode(context, obj, baker.vertex_color)
        elif context.mode == "EDIT_MESH":
            self._apply_vertex_color_edit_mode(context, baker.vertex_color)

        # Set viewport shading to show vertex colors
        if hasattr(context.space_data, "shading") and hasattr(context.space_data.shading, "color_type"):
            context.space_data.shading.color_type = "VERTEX"

        return {"FINISHED"}


class QBAKER_OT_vertex_color_preset(Operator):
    """Vertex color preset"""

    bl_label = ""
    bl_idname = "qbaker.vertex_color_preset"
    bl_options = {"REGISTER", "INTERNAL"}

    preset: FloatVectorProperty(
        name="",
        subtype="COLOR_GAMMA",
        size=3,
        min=0.0,
        max=1.0,
        default=(1, 1, 1),
    )

    @classmethod
    def poll(cls, context):
        if hasattr(context.space_data, "shading"):
            return context.space_data.shading.type != "WIREFRAME"

    def execute(self, context):
        baker = context.scene.qbaker
        baker.vertex_color = self.preset
        bpy.ops.qbaker.vertex_color()

        return {"FINISHED"}


classes = (
    QBAKER_OT_vertex_color,
    QBAKER_OT_vertex_color_preset,
)


register, unregister = bpy.utils.register_classes_factory(classes)
