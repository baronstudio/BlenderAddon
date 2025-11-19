from math import cos, radians, sin
from typing import List, Tuple

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from ..blender import ui_line_width, ui_scale


class Draw2D:
    OPTION_INNER = bpy.context.preferences.themes["Default"].user_interface.wcol_option.inner
    TOOL_INNER_SEL = bpy.context.preferences.themes["Default"].user_interface.wcol_tool.inner_sel
    LINE_WIDTH = bpy.context.preferences.system.ui_line_width
    if bpy.app.version >= (4, 0, 0):
        TOOL_OUTLINE = bpy.context.preferences.themes["Default"].user_interface.wcol_tool.outline
    else:
        TOOL_OUTLINE = (
            *bpy.context.preferences.themes["Default"].user_interface.wcol_tool.outline[:3],
            1.0,
        )

    def _box(
        self,
        position: Vector,
        dimension: Vector,
        padding: Vector = Vector((0, 0)),
        corner: Tuple[bool, bool, bool, bool] = False,
    ) -> List:
        """Create a box with rounded corners.

        Args:
            position (Vector): Position where the box will be drawn.
            dimension (Vector): Dimension of the box.
            padding (Vector): Padding of the box.
            corner (Tuple[bool, bool, bool, bool], optional): Corner to draw. Defaults to False.

        Returns:
            List: List of coords, indices, line_indices, tex_coord.
        """
        if corner is True:
            corner = [True, True, True, True]
        elif corner is False:
            corner = [False, False, False, False]
        x, y = position
        width, height = dimension
        p = padding * ui_scale()
        radius = bpy.context.preferences.themes["Default"].user_interface.wcol_regular.roundness * 10
        smooth = 5

        def create_corner(start_angle, end_angle, center_x, center_y):
            return [
                (center_x + radius * cos(radians(i)), center_y + radius * sin(radians(i)))
                for i in range(start_angle, end_angle, smooth)
            ]

        bl_corner = create_corner(180, 270, x - p.x + radius, y - p.y + radius) if corner[0] else [(x - p.x, y - p.y)]
        br_corner = (
            create_corner(270, 360, x + p.x + width - radius, y - p.y + radius)
            if corner[1]
            else [(x + width + p.x, y - p.y)]
        )
        tr_corner = (
            create_corner(0, 90, x + p.x + width - radius, y + p.y + height - radius)
            if corner[2]
            else [(x + width + p.x, y + height + p.y)]
        )
        tl_corner = (
            create_corner(90, 180, x - p.x + radius, y + p.y + height - radius)
            if corner[3]
            else [(x - p.x, y + height + p.y)]
        )

        coords = bl_corner + br_corner + tr_corner + tl_corner
        indices = [(0, x + 1, x + 2) for x in range(len(coords) - 2)]
        line_indices = [(x, (x + 1) % len(coords)) for x in range(len(coords))]
        tex_coord = [((coord[0] - x) / width, (coord[1] - y) / height) for coord in coords]

        return coords, indices, line_indices, tex_coord

    def shader(
        self,
        coords: List[Vector],
        indices: tuple = None,
        type="POINTS",
        color: tuple = (1, 1, 1, 1),
        line_width: float = 1,
    ):
        """Shader for drawing.

        Args:
            coords (List[Vector]): List of coordinates.
            indices (tuple, optional): Indices of the coords. Defaults to None.
            type (str, optional): Type of the shader. Defaults to "POINTS".
            color (tuple, optional): Color of the shader. Defaults to (1, 1, 1, 1).
            line_width (float, optional): Line width. Defaults to 1.
        """
        if type in {"LINES", "LINE_STRIP", "LINE_LOOP"}:
            gpu.state.line_width_set(line_width)

        gpu.state.blend_set("ALPHA")

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        batch = batch_for_shader(shader, type, {"pos": coords}, indices=indices)
        shader.bind()
        shader.uniform_float("color", color)
        batch.draw(shader)

    def image_shader(
        self,
        coords: List[Vector],
        indices: tuple = None,
        texture: gpu.types.GPUTexture = None,
        color: tuple = (0, 0, 0, 0),
    ):
        """Shader for drawing images.

        Args:
            coords (List[Vector]): List of coordinates.
            indices (tuple, optional): Indices of the coords. Defaults to None.
            texture (gpu.types.GPUTexture, optional): GPUTexture to draw. Defaults to None.
            color (tuple, optional): Color of the texture. Defaults to (0, 0, 0, 0).
        """
        gpu.state.blend_set("ALPHA")

        shader = gpu.shader.from_builtin("IMAGE_COLOR")
        batch = batch_for_shader(
            shader,
            "TRI_FAN",
            {"pos": coords, "texCoord": indices},  #'texCoord': ((0, 0), (1, 0), (1, 1), (0, 1))
        )
        shader.bind()
        shader.uniform_sampler("image", texture)
        shader.uniform_sampler("color", color)
        batch.draw(shader)

    def draw_2d_box(
        self,
        position: Vector,
        dimension: Vector,
        padding: Vector = Vector((4, 4)),
        background: tuple = None,
        corner: Tuple[bool, bool, bool, bool] = False,
        outline: bool = False,
    ):
        """Draw a box with rounded corners.

        Args:
            position (Vector): Position where the box will be drawn.
            dimension (Vector): Dimension of the box.
            padding (Vector, optional): Padding of the box. Defaults to Vector((4, 4)).
            background (tuple, optional): Background color of the box. Defaults to None.
            corner (Tuple[bool, bool, bool, bool], optional): Corner to draw. Defaults to False.
            outline (bool, optional): Box outline. Defaults to False.
        """
        coords, indices, line_indices, tex_coord = self._box(position, dimension, padding, corner)
        self.shader(
            coords,
            indices=indices,
            type="TRIS",
            color=(
                bpy.context.preferences.themes["Default"].user_interface.wcol_tool.inner
                if background is None
                else background
            ),
        )
        if outline:
            self.shader(coords, indices=line_indices, type="LINES", color=self.TOOL_OUTLINE, line_width=self.LINE_WIDTH)

    def draw_2d_box_selected(
        self,
        position: Vector,
        dimension: Vector,
        padding: Vector,
        corner: Tuple[bool, bool, bool, bool] = False,
        pause_modal: bool = False,
    ):
        """Draw a selected box with rounded corners.

        Args:
            position (Vector): Position where the box will be drawn.
            dimension (Vector): Dimension of the box.
            padding (Vector): Padding of the box.
            corner (Tuple[bool, bool, bool, bool], optional): Corner to draw. Defaults to False.
            pause_modal (bool, optional): Pause the modal. Defaults to False.
        """
        coords, indices, line_indices, tex_coord = self._box(position, dimension, padding, corner)

        if pause_modal:
            background = (*self.TOOL_INNER_SEL[:3], 0.5)
            self.shader(coords, indices=indices, type="TRIS", color=background)
            self.shader(coords, indices=line_indices, type="LINES", color=background, line_width=self.LINE_WIDTH)
        else:
            self.shader(coords, indices=indices, type="TRIS", color=self.TOOL_INNER_SEL)
            self.shader(
                coords, indices=line_indices, type="LINES", color=self.TOOL_INNER_SEL, line_width=self.LINE_WIDTH
            )

    def draw_2d_checkbox(self, position: Vector, default: bool = False, pause_modal: bool = False):
        """Draw a checkbox.

        Args:
            position (Vector): Position where the checkbox will be drawn.
            default (bool, optional): Default checkbox value. Defaults to False.
            pause_modal (bool, optional): Pause the modal. Defaults to False.
        """
        dimension = Vector((14 * ui_scale(), 14 * ui_scale()))
        padding = Vector((0, 0))

        background = self.OPTION_INNER
        if default:
            background = self.TOOL_INNER_SEL
        if pause_modal:
            background = (*background[:3], 0.5)

        self.draw_2d_box(position, dimension, padding, background)

        if default:
            x, y = position
            width, height = dimension
            l = (x + (width / 4), y + (height / 2.3))
            b = (x + (width / 2.3), y + (height / 2) / 2)
            r = (x + (width / 2) + (width / 3.5), y + (height / 2) + (height / 4.5))

            check_color = bpy.context.preferences.themes["Default"].user_interface.wcol_option.item
            if pause_modal:
                check_color = (*check_color[:3], 0.5)

            self.shader((l, b, r), type="LINE_STRIP", color=check_color, line_width=self.LINE_WIDTH + 0.5)

    def draw_2d_image(
        self,
        image: bpy.types.Image,
        position: Vector,
        dimension: Vector = Vector((16, 16)),
        border: bool = False,
        corner: Tuple[bool, bool, bool, bool] = False,
    ):
        """Draw an image.

        Args:
            image (bpy.types.Image): The Image datablock.
            position (Vector): Position where the image will be drawn.
            dimension (Vector, optional): Dimension of the image. Defaults to Vector((16, 16)).
            border (bool, optional): Draw border/outline. Defaults to False.
            corner (Tuple[bool, bool, bool, bool], optional): Corner to draw. Defaults to False.
        """
        texture = gpu.texture.from_image(image)

        coords, indices, line_indices, tex_coord = self._box(position, dimension, corner=corner)
        self.image_shader(coords, indices=tex_coord, texture=texture)

        if border:
            self.shader(coords, indices=line_indices, type="LINES", color=self.TOOL_OUTLINE, line_width=self.LINE_WIDTH)

    def draw_2d_preview(
        self,
        texture: gpu.types.GPUTexture,
        position: Vector,
        dimension: Vector = Vector((16, 16)),
        border: bool = False,
        corner: Tuple[bool, bool, bool, bool] = False,
    ):
        """Draw a preview image.

        Args:
            texture (gpu.types.GPUTexture): GPUTexture to draw.
            position (Vector): Position where the image will be drawn.
            dimension (Vector, optional): Dimension of the image preview. Defaults to Vector((16, 16)).
            border (bool, optional): Border to draw. Defaults to False.
            corner (Tuple[bool, bool, bool, bool], optional): Corner to draw. Defaults to False.
        """
        coords, indices, line_indices, tex_coord = self._box(position, dimension, corner=corner)
        self.image_shader(coords, indices=tex_coord, texture=texture)

        if border:
            self.shader(coords, indices=line_indices, type="LINES", color=self.TOOL_OUTLINE, line_width=self.LINE_WIDTH)

    def draw_2d_line(
        self,
        coords: List[Vector],
        indices: tuple = None,
        color: tuple = (1, 1, 1, 1),
    ):
        """Draw a line.

        Args:
            coords (List[Vector]): List of coordinates.
            indices (tuple, optional): Indices of the coords. Defaults to None.
            color (tuple, optional): Color of the line. Defaults to (1, 1, 1, 1).
        """
        gpu.state.blend_set("ALPHA")
        # gpu.state.line_width_set(ui_line_width())
        shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")

        if indices:
            batch = batch_for_shader(shader, "LINES", {"pos": coords}, indices=indices)
        else:
            batch = batch_for_shader(shader, "LINES", {"pos": coords})

        shader.bind()
        shader.uniform_float("viewportSize", (bpy.context.region.width, bpy.context.region.height))
        shader.uniform_float("lineWidth", ui_line_width())
        shader.uniform_float("color", color)
        batch.draw(shader)

        # restore opengl defaults
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set("NONE")

    def draw_2d_controller(
        self,
        pos: Vector,
        size: float = 6,
        angle: float = 45,
        color: tuple = (0, 0, 0, 1),
        active_color: tuple = (1, 1, 1, 1),
        active: bool = False,
    ):
        """Draw a controller.

        Args:
            pos (Vector): Position where the controller will be drawn.
            size (float, optional): Size of the controller. Defaults to 6.
            angle (float, optional): Angle of the controller. Defaults to 45.
            color (tuple, optional): Color of the controller. Defaults to (0, 0, 0, 1).
            active_color (tuple, optional): Active color of the controller. Defaults to (1, 1, 1, 1).
            active (bool, optional): Is the controller active. Defaults to False.
        """
        x, y = pos
        size = size * ui_scale()
        angle_rad = radians(angle)
        cos_angle = cos(angle_rad)
        sin_angle = sin(angle_rad)

        def rotate_point(px, py, ox, oy):
            qx = ox + cos_angle * (px - ox) - sin_angle * (py - oy)
            qy = oy + sin_angle * (px - ox) + cos_angle * (py - oy)
            return qx, qy

        coords = [
            rotate_point(x - size, y, x, y),  # l
            rotate_point(x + size, y, x, y),  # r
            rotate_point(x, y + size, x, y),  # t
            rotate_point(x, y - size, x, y),  # b
        ]
        indices = [(0, 1), (2, 3)]
        self.draw_2d_line(coords, indices, color=color)

        if active:
            active_coords = [
                rotate_point(x - size, y - ui_line_width(), x, y),
                rotate_point(x - ui_line_width(), y - ui_line_width(), x, y),
                rotate_point(x - ui_line_width(), y - size, x, y),
                rotate_point(x + ui_line_width(), y - size, x, y),
                rotate_point(x + ui_line_width(), y - ui_line_width(), x, y),
                rotate_point(x + size, y - ui_line_width(), x, y),
                rotate_point(x + size, y + ui_line_width(), x, y),
                rotate_point(x + ui_line_width(), y + ui_line_width(), x, y),
                rotate_point(x + ui_line_width(), y + size, x, y),
                rotate_point(x - ui_line_width(), y + size, x, y),
                rotate_point(x - ui_line_width(), y + ui_line_width(), x, y),
                rotate_point(x - size, y + ui_line_width(), x, y),
            ]
            active_indices = [(0, 1), (1, 2), (3, 4), (4, 5), (6, 7), (7, 8), (9, 10), (10, 11)]
            self.draw_2d_line(active_coords, active_indices, color=active_color)

    def draw_2d_endpoints(
        self,
        points: List[Vector],
        size: float = 4,
        color: tuple = (0, 0, 0, 1),
    ):
        """Draw tangent lines at start and end points.

        Args:
            points (List[2D Vector]): List of start and end points.
            size (float, optional): Size of the point line. Defaults to 4.
            color (tuple, optional): Color of the point line. Defaults to (0, 0, 0, 1).
        """
        fixed_length = size * ui_scale()  # Fixed length in pixels
        start, end = points[0], points[-1]

        for point in (start, end):
            if len(points) == 2:
                ref_point = end if point == start else start
            else:
                ref_point = points[1]

            ref_line = ref_point - point
            ref_direction = ref_line.normalized()
            perp_direction = Vector((-ref_direction.y, ref_direction.x)).normalized()
            coords = (
                point - perp_direction * fixed_length,
                point + perp_direction * fixed_length,
            )
            self.draw_2d_line(coords, color=color)

    # WIP

    # def round_box(self, position=(500, 500), dimension=(200, 200), corner=None):
    #     '''Draw round box

    #     position (2D Vector) - Position where the box will be drawn.
    #     dimension (tuple) - Size of the box.
    #     corner ([BOTTOM_LEFT, BOTTOM_RIGHT, TOP_RIGHT, TOP_LEFT], booleans) - Draw corners.
    #     '''
    #     vertices = (
    #         (position[0], position[1]), # bl
    #         (position[0] + dimension[0], position[1]), # br
    #         (position[0], position[1] + dimension[1]), # tl
    #         (position[0] + dimension[0], position[1] + dimension[1])) # tr

    #     indices = (
    #         (0, 1, 2), (2, 1, 3))

    #     vertex_shader = '''
    #         uniform mat4 ModelViewProjectionMatrix;
    #         in vec2 pos;

    #         void main()
    #         {
    #             gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0, 1.0);
    #         }
    #     '''

    #     fragment_shader = '''
    #         uniform vec3 color;
    #         uniform float alpha;

    #         out vec4 FragColor;

    #         void main() {
    #             FragColor = vec4(color, alpha);
    #             FragColor = blender_srgb_to_framebuffer_space(FragColor);
    #         }
    #     '''

    #     shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
    #     batch = batch_for_shader(shader, 'TRIS', {'pos': vertices}, indices=indices)

    #     shader.bind()
    #     shader.uniform_float('color', (0, 1, 1))
    #     shader.uniform_float('alpha', 1)
    #     # shader.uniform_float('outline', 1)
    #     # shader.uniform_float('outline_color', (0.8, 0.8, 0.8))
    #     # shader.uniform_float('radius', 4)
    #     batch.draw(shader)

    # def round_box(self, position=(500, 500), dimension=(200, 200), corner=None):
    #     '''Draw round box

    #     position (2D Vector) - Position where the box will be drawn.
    #     dimension (tuple) - Size of the box.
    #     corner ([BOTTOM_LEFT, BOTTOM_RIGHT, TOP_RIGHT, TOP_LEFT], booleans) - Draw corners.
    #     '''
    #     vertices = (
    #         (position[0], position[1]), # bl
    #         (position[0] + dimension[0], position[1]), # br
    #         (position[0], position[1] + dimension[1]), # tl
    #         (position[0] + dimension[0], position[1] + dimension[1])) # tr

    #     indices = (
    #         (0, 1, 2), (2, 1, 3))

    #     vertex_shader = '''
    #         uniform mat4 ModelViewProjectionMatrix;
    #         in vec2 pos;

    #         void main() {
    #             gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0, 1.0);
    #         }
    #     '''

    #     fragment_shader = '''

    #         float rounded_box_SDF(vec2 center_position, vec2 size, float radius) {
    #             return length(max(abs(center_position) - size + radius, 0.0)) - radius;
    #         }

    #         void main() {
    #             out vec4 FragColor;

    #             vec2 size = vec2(300.0, 50.0);

    #             vec2 location = vec2(100, 100);

    #             float edgeSoftness  = 1.0;

    #             float radius = 4.0;

    #             float distance = rounded_box_SDF(gl_FragCoord.xy - location - size, size, radius);

    #             float smoothedAlpha = 1.0 - smoothstep(0.0, edgeSoftness * 2.0, distance);

    #             vec4 quadColor = mix(vec4(0.5, 0.5, 0.5, 1.0), vec4(vec3(0.239216), smoothedAlpha), smoothedAlpha);

    #             float shadowSoftness = 4.0;
    #             vec2 shadowOffset = vec2(0, 2);
    #             float shadowDistance = rounded_box_SDF(gl_FragCoord.xy - location + shadowOffset - size, size, radius);
    #             float shadowAlpha = 1.0 - smoothstep(-shadowSoftness, shadowSoftness, shadowDistance);
    #             vec4 shadowColor = vec4(vec3(0.239216), 1.0);
    #             vec3 fragColor = vec3(mix(quadColor, shadowColor, shadowAlpha - smoothedAlpha));

    #             FragColor = vec4(fragColor, 1.0);
    #             FragColor = blender_srgb_to_framebuffer_space(FragColor);
    #         }
    #     '''

    #     shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
    #     batch = batch_for_shader(shader, 'TRIS', {'pos': vertices}, indices=indices)

    #     shader.bind()
    #     batch.draw(shader)


# import bpy
# import gpu
# from gpu_extras.batch import batch_for_shader


# vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
# vert_out.smooth("VEC2", "uv")

# shader_info = gpu.types.GPUShaderCreateInfo()
# shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
# shader_info.push_constant("VEC4", "rect")
# shader_info.push_constant("VEC4", "color")
# shader_info.push_constant("FLOAT", "scale")
# shader_info.push_constant("INT", "cornerLen")

# shader_info.vertex_in(0, "VEC2", "pos")
# shader_info.vertex_out(vert_out)
# shader_info.fragment_out(0, "VEC4", "FragColor")

# shader_info.vertex_source(
#     """
#     void main(){
#         int corner_id = (gl_VertexID / cornerLen) % 4;

#         vec2 final_pos = pos * scale;

#         if (corner_id == 0) {
#             uv = pos + vec2(1.0, 1.0);
#             final_pos += rect.yw; /* top right */
#         }
#         else if (corner_id == 1) {
#             uv = pos + vec2(-1.0, 1.0);
#             final_pos += rect.xw; /* top left */
#         }
#         else if (corner_id == 2) {
#             uv = pos + vec2(-1.0, -1.0);
#             final_pos += rect.xz; /* bottom left */
#         }
#         else {
#             uv = pos + vec2(1.0, -1.0);
#             final_pos += rect.yz; /* bottom right */
#         }

#         gl_Position = (ModelViewProjectionMatrix * vec4(final_pos, 0.0, 1.0));
#     }
#     """
# )

# shader_info.fragment_source(
#     """
#     void main(){
#         /* Should be 0.8 but minimize the AA on the edges. */
#         float dist = (length(uv) - 0.78) * scale;

#         FragColor = color;
#         FragColor.a *= smoothstep(-0.09, 1.09, dist);
#     }
#     """
# )

# shader = gpu.shader.create_from_info(shader_info)
# del vert_out
# del shader_info

# pos = (100, 100)

# batch = batch_for_shader(shader, "TRIS", {"pos": pos})


# def draw():
#     shader.uniform_float("rect", (10, 20, 100, 50))  # (x, y, width, height)
#     shader.uniform_float("color", (0.5, 0.5, 0.5, 1))
#     shader.uniform_float("scale", 1)
#     shader.uniform_int("cornerLen", 4)
#     batch.draw(shader)


# bpy.types.SpaceView3D.draw_handler_add(draw, (), "WINDOW", "POST_PIXEL")
