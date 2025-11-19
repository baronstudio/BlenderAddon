import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector


def circle_2d(
    pos: Vector = (100, 100),
    radius: float = 16,
    color: Vector = (1.0, 1.0, 1.0, 0.1),
    outline: float = None,
    outline_color: Vector = None,
):
    # Create unique interface name based on shader_name
    vert_out = gpu.types.GPUStageInterfaceInfo("BUI_interface")
    vert_out.smooth("VEC2", "pos")

    shader_info = gpu.types.GPUShaderCreateInfo()

    # Keep only the projection matrix as a push constant
    shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")

    # Use regular uniforms instead of UBO
    shader_info.push_constant("VEC2", "center")
    shader_info.push_constant("FLOAT", "radius")
    shader_info.push_constant("FLOAT", "outlineWidth")
    shader_info.push_constant("VEC4", "fillColor")
    shader_info.push_constant("VEC4", "outlineColor")

    shader_info.vertex_in(0, "VEC2", "position")
    shader_info.vertex_out(vert_out)
    shader_info.fragment_out(0, "VEC4", "FragColor")

    shader_info.vertex_source(
        """
        void main()
        {
            pos = position;
            gl_Position = ModelViewProjectionMatrix * vec4(position, 0.0, 1.0);
        }"""
    )

    shader_info.fragment_source(
        """
        void main()
        {
            float dist = distance(pos, center);
            
            // Discard pixels outside the circle
            if (dist > radius) {
                discard;
            }
            
            // Calculate inner circle edge (where outline begins)
            float inner_radius = radius - outlineWidth;
            
            // Default to fill color
            vec4 resultColor = fillColor;
            float alpha = 1.0;
            float smoothWidth = 1.0;
            
            if (dist > inner_radius) {
                // We're in the outline region
                resultColor = outlineColor;
                
                // Smooth outer edge
                if (dist > radius - smoothWidth) {
                    alpha = 1.0 - smoothstep(radius - smoothWidth, radius, dist);
                }
            } else if (dist > inner_radius - smoothWidth) {
                // We're near the inner edge - blend between fill and outline
                float blend = smoothstep(inner_radius - smoothWidth, inner_radius, dist);
                resultColor = mix(fillColor, outlineColor, blend);
            }
            
            FragColor = resultColor;
            FragColor.a *= alpha;
        }"""
    )

    # Start with a clean state
    gpu.state.blend_set("ALPHA")

    shader = gpu.shader.create_from_info(shader_info)
    shader.bind()
    del vert_out
    del shader_info

    # Create a quad that contains the circle
    x, y = pos
    buffer = 0.0  # Add a small buffer to handle smooth edges
    vertices = [
        (x - radius - buffer, y - radius - buffer),
        (x - radius - buffer, y + radius + buffer),
        (x + radius + buffer, y + radius + buffer),
        (x + radius + buffer, y - radius - buffer),
    ]
    indices = [(0, 1, 2), (0, 2, 3)]

    batch = batch_for_shader(shader, "TRIS", {"position": vertices}, indices=indices)

    shader.uniform_float("center", (x, y))
    shader.uniform_float("radius", radius * 0.5)
    shader.uniform_float("fillColor", color)
    shader.uniform_float("outlineWidth", bpy.context.preferences.system.ui_line_width if outline is None else outline)
    shader.uniform_float("outlineColor", (*color[:3], 1.0) if outline_color is None else outline_color)
    batch.draw(shader)

    # Reset state between draws
    gpu.state.blend_set("NONE")

    return shader
