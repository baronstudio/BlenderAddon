from math import cos, radians, sin
from typing import List, Tuple

import bpy
import gpu
import numpy as np
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from ..blender import ui_line_width


class Draw3D:
    def draw_3d_line(
        self,
        coords: List[Vector],
        type: str = "LINES",
        color: Tuple[float, float, float, float] = (0, 0, 0, 1),
        depth_mode: str = "ALWAYS",
    ):
        """Draw a line in the viewport.

        Args:
            coords (List[Vector]): 3D coordinates of the line.
            type (str ['LINES' 'LINE_STRIP', 'LINES_ADJ'], optional): Type of the line. Defaults to "LINES".
            color (Tuple[float, float, float, float], optional): Color of the line. Defaults to (0, 0, 0, 1).
            depth_mode (str, optional): GPU depth test. Defaults to "ALWAYS".
        """
        gpu.state.blend_set("ALPHA")
        gpu.state.depth_test_set(depth_mode)

        shader = gpu.shader.from_builtin("POLYLINE_SMOOTH_COLOR")
        batch = batch_for_shader(shader, type, {"pos": coords, "color": [color] * len(coords)})
        shader.bind()
        shader.uniform_float("lineWidth", ui_line_width())
        # shader.uniform_float("color", color)
        batch.draw(shader)

    def draw_3d_line_blend(
        self,
        coords: List[Vector],
        type: str = "LINES",
        colors: Tuple[Tuple[float, float, float, float], ...] = ((1, 0, 0, 1), (0, 0, 1, 1)),
        depth_mode: str = "ALWAYS",
    ):
        """Draw a line with blending.

        Args:
            coords (List[Vector]): 3D coordinates of the line.
            type (str ['LINES' 'LINE_STRIP', 'LINES_ADJ'], optional): Type of the line. Defaults to "LINES".
            colors (Tuple[Tuple[float, float, float, float], ...], optional): Colors of the line. Defaults to ((1, 0, 0, 1), (0, 0, 1, 1)).
            depth_mode (str, optional): GPU depth test. Defaults to "ALWAYS".
        """
        gpu.state.blend_set("ALPHA")
        gpu.state.depth_test_set(depth_mode)

        shader = gpu.shader.from_builtin("POLYLINE_SMOOTH_COLOR")
        batch = batch_for_shader(shader, type, {"pos": coords, "color": colors})
        shader.bind()
        shader.uniform_float("lineWidth", ui_line_width())
        batch.draw(shader)

    def draw_3d_arc(
        self,
        start: Vector,
        center: Vector,
        end: Vector,
        radius: float = 1,
        color: Tuple[float, float, float, float] = (0, 0, 0, 1),
    ):
        """Draw an arc in the viewport.

        Args:
            start (Vector): Start point of the arc.
            center (Vector): Center point of the arc.
            end (Vector): End point of the arc.
            radius (float, optional): Radius of the arc. Defaults to 1.
            color (Tuple[float, float, float, float], optional): Color of the arc. Defaults to (0, 0, 0, 1).
        """
        coords = []

        start_vec, end_vec = (start - center).normalized(), (end - center).normalized()
        normal = (start - center).cross(end - center).normalized()
        matrix = Matrix.Translation(center)
        matrix.col[0].xyz = start_vec
        matrix.col[1].xyz = normal.cross(matrix.col[0].xyz).normalized()
        matrix.col[2].xyz = normal

        start_angle = np.degrees(np.arctan2(start_vec.dot(matrix.col[1].xyz), start_vec.dot(matrix.col[0].xyz)))
        end_angle = np.degrees(np.arctan2(end_vec.dot(matrix.col[1].xyz), end_vec.dot(matrix.col[0].xyz)))
        angle_range = np.linspace(start_angle, end_angle)

        for angle in angle_range:
            x = radius * cos(radians(angle))
            y = radius * sin(radians(angle))
            coord = Vector((x, y, 0))
            coords.append(matrix @ coord)

        self.draw_3d_line(coords, type="LINE_STRIP", color=color)

    def draw_3d_polygon(
        self,
        coords: List[Vector],
        indices: Tuple = None,
        shader_type: str = "SMOOTH_COLOR",
        type: str = "TRI_FAN",
        colors: Tuple[Tuple[float, float, float, float], ...] = None,
        depth_mode: str = "ALWAYS",
    ):
        """Draw a polygon in the viewport.

        Args:
            coords (List[Vector]): 3D coordinates of the polygon.
            indices (Tuple, optional): Indices of the coords. Defaults to None.
            shader_type (str ['FLAT_COLOR', 'UNIFORM_COLOR', 'SMOOTH_COLOR'], optional): Shader type. Defaults to "SMOOTH_COLOR".
            type (str ['TRIS',  'TRI_FAN' 'TRI_STRIP'], optional): Type of the polygon. Defaults to "TRI_FAN".
            colors (Tuple[Tuple[float, float, float, float], ...], optional): Colors of the coords. Defaults to None.
            depth_mode (str, optional): GPU depth test. Defaults to "ALWAYS".
        """
        gpu.state.blend_set("ALPHA")
        gpu.state.depth_test_set(depth_mode)

        if not colors:
            colors = [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)] * (len(coords) // 3 + 1)

        shader = gpu.shader.from_builtin(shader_type)
        shader.bind()
        if shader_type == "UNIFORM_COLOR":
            batch = batch_for_shader(shader, type, {"pos": coords}, indices=indices)
            shader.uniform_float("color", colors[0])
        else:
            batch = batch_for_shader(shader, type, {"pos": coords, "color": colors}, indices=indices)
        batch.draw(shader)

    def draw_3d_axis(self, point: Vector, axis: str = "Z"):
        """Draw axis from the point location.

        Args:
            point (Vector): The point to draw the axis for.
            axis (str, optional): The axis to draw the line to. Defaults to "Z".
        """
        axis_map = {
            "X": (
                bpy.context.region.width,
                point.y,
                point.z,
                bpy.context.preferences.themes["Default"].user_interface.axis_x,
            ),
            "Y": (
                point.x,
                bpy.context.region.width,
                point.z,
                bpy.context.preferences.themes["Default"].user_interface.axis_y,
            ),
            "Z": (
                point.x,
                point.y,
                bpy.context.region.height,
                bpy.context.preferences.themes["Default"].user_interface.axis_z,
            ),
        }

        if axis in axis_map:
            x, y, z, axis_color = axis_map[axis]
            coords = (
                [(-x, y, z), (x, y, z)]
                if axis == "X"
                else [(x, -y, z), (x, y, z)]
                if axis == "Y"
                else [(x, y, -z), (x, y, z)]
            )
            color = (*axis_color, 1)

            gpu.state.blend_set("ALPHA")
            shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
            batch = batch_for_shader(shader, "LINES", {"pos": coords})
            shader.bind()
            shader.uniform_float("lineWidth", ui_line_width())
            shader.uniform_float("color", color)
            batch.draw(shader)
