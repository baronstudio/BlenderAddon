import blf
import bpy
from mathutils import Vector

from ..blender import dpi, ui_scale


class DrawText:
    def draw_text(
        self,
        pos: Vector,
        text: str = "Hello World",
        text_color: tuple = None,
        text_size: float = None,
        font_id: int = 0,
    ):
        """Draw text.

        Args:
            pos (2D Vector): Position to draw text at.
            text (str, optional): Text to draw. Defaults to "Hello World".
            text_color (tuple containing RGB values, optional, optional): Color of the text. Defaults to None.
            text_size (float, optional): Size of the text. Defaults to None.
            font_id (int, optional): Font id. Defaults to 1.
        """
        text_color = text_color or bpy.context.preferences.themes["Default"].user_interface.wcol_tool.text
        text_size = text_size or bpy.context.preferences.ui_styles[0].widget.points

        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0, 0, 0, 0.5)
        blf.shadow_offset(font_id, 0, -1)

        if bpy.app.version >= (4, 0, 0):
            blf.size(font_id, text_size * ui_scale())
        else:
            blf.size(font_id, text_size, dpi())

        blf.color(font_id, *text_color, 1)
        blf.position(font_id, *pos, 0)
        blf.draw(font_id, text)

    def get_text_dims(self, text: str, text_size: float = None, font_id: int = 1) -> Vector:
        """Get text dimensions.

        Args:
            text (str): Text to get dimensions for.
            text_size (float, optional): Size of the text. Defaults to None.
            font_id (int, optional): Font id. Defaults to 1.

        Returns:
            Vector: Dimension of the text in pixels.
        """
        text_size = text_size or bpy.context.preferences.ui_styles[0].widget.points

        if bpy.app.version >= (4, 0, 0):
            blf.size(font_id, text_size * ui_scale())
        else:
            blf.size(font_id, text_size, dpi())

        return Vector(blf.dimensions(font_id, text))
