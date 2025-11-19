from typing import List

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector


class DrawDotLine:
    def __init__(self):
        # https://projects.blender.org/blender/blender/src/branch/main/source/blender/gpu/shaders/infos/gpu_shader_line_dashed_uniform_color_info.hh
        vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
        vert_out.no_perspective("VEC2", "stipple_start")
        vert_out.flat("VEC2", "stipple_pos")

        shader_info = gpu.types.GPUShaderCreateInfo()
        shader_info.vertex_in(0, "VEC3", "pos")

        shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
        shader_info.push_constant("VEC2", "viewport_size")
        # shader_info.push_constant("FLOAT", "dash_width")
        # shader_info.push_constant("FLOAT", "udash_factor")
        # shader_info.push_constant("INT", "colors_len")
        shader_info.push_constant("VEC4", "color")
        shader_info.push_constant("VEC4", "color2")
        shader_info.vertex_out(vert_out)
        shader_info.fragment_out(0, "VEC4", "fragColor")

        # https://projects.blender.org/blender/blender/src/branch/main/source/blender/gpu/shaders/gpu_shader_3D_line_dashed_uniform_color_vert.glsl
        shader_info.vertex_source(
            """
            void main()
            {
                vec4 pos_4d = vec4(pos, 1.0);
                gl_Position = ModelViewProjectionMatrix * pos_4d;
                stipple_start = stipple_pos = viewport_size * 0.5 * (gl_Position.xy / gl_Position.w);
            }
            """
        )

        # https://projects.blender.org/blender/blender/src/branch/main/source/blender/gpu/shaders/gpu_shader_2D_line_dashed_frag.glsl
        shader_info.fragment_source(
            """
            void main()
            {
                float distance_along_line = distance(stipple_pos, stipple_start);
                /* Solid line case, simple. */
                if (0.5f >= 1.0f) {
                    fragColor = color;
                }
                /* Actually dashed line... */
                else
                {
                    float normalized_distance = fract(distance_along_line / 6);
                    if (normalized_distance <= 0.5f) {
                        fragColor = color;
                        /* fragColor.a *= clamp((1.0 + 1.0) * 0.5 - abs(0.5), 0.0, 1.0); */
                    }
                    else if (1 > 0)
                    {
                        fragColor = color2;
                    }
                    else 
                    {
                        discard;
                    }
                }
            }
            """
        )

        self.dotted_shader = gpu.shader.create_from_info(shader_info)
        del vert_out
        del shader_info

    def draw(
        self,
        coords: List[Vector],
        color: tuple = (0.8, 0.8, 0.8, 1),
        color2: tuple = (0.1, 0.1, 0.1, 1),
        line_width: float = 1,
    ):
        """Draw a dotted line.

        Args:
            coords (List[Vector]): The coordinates of the dot.
            color (tuple, optional): Color of the white dashes. Defaults to (0.8, 0.8, 0.8, 1).
            color2 (tuple, optional): Color of the black dashes. Defaults to (0.1, 0.1, 0.1, 1).
            line_width (float, optional): Line width of dotted line. Defaults to 1.
        """
        gpu.state.blend_set("ALPHA")
        gpu.state.depth_test_set("ALWAYS")
        gpu.state.line_width_set(line_width)
        batch = batch_for_shader(self.dotted_shader, "LINES", {"pos": coords})

        region = bpy.context.region

        self.dotted_shader.bind()
        self.dotted_shader.uniform_float("viewport_size", (region.width, region.height))
        # self.dotted_shader.uniform_int("colors_len", 1)
        # self.dotted_shader.uniform_float("dash_width", 6)
        # self.dotted_shader.uniform_float("udash_factor", 0.5)
        self.dotted_shader.uniform_float("color", color)
        self.dotted_shader.uniform_float("color2", color2)
        batch.draw(self.dotted_shader)
