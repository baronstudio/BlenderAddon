# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from os.path import basename
from xml.sax.saxutils import escape

import bpy


def export(filepath, tile, face_data, colors, width, height, map):
    with open(filepath, "w", encoding="utf-8") as file:
        for text in get_file_parts(tile, face_data, colors, width, height, map):
            file.write(text)


def get_file_parts(tile, face_data, colors, width, height, map):
    yield from header(width, height)
    yield from draw_polygons(tile, face_data, width, height, map)
    yield from footer()


def header(width, height):
    yield '<?xml version="1.0" standalone="no"?>\n'
    yield '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" \n'
    yield '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
    yield f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"\n'
    yield '     xmlns="http://www.w3.org/2000/svg" version="1.1">\n'
    desc = f"{basename(bpy.data.filepath)}, (Blender {bpy.app.version_string})"
    yield f"<desc>{escape(desc)}</desc>\n"


def draw_polygons(tile, face_data, width, height, map):
    for uvs, color in face_data:
        color = map.face_color[:]
        line_width = map.line_width

        fill = f'fill="{get_color_string(color)}"'

        yield f'<polygon stroke="black" stroke-width="{line_width}"'
        yield f' {fill} fill-opacity="{color[3]:.2g}"'

        yield ' points="'

        for uv in uvs:
            x, y = uv[0] - tile[0], 1.0 - uv[1] + tile[1]
            yield f"{x * width:.3f},{y * height:.3f} "
        yield '" />\n'


def get_color_string(color):
    r, g, b, a = color
    return f"rgb({round(r * 255)}, {round(g * 255)}, {round(b * 255)}, {round(a * 255)})"


def footer():
    yield "\n"
    yield "</svg>\n"
