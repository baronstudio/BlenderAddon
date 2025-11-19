import bpy
from bpy_extras.view3d_utils import (
    location_3d_to_region_2d,
    region_2d_to_location_3d,
    region_2d_to_origin_3d,
    region_2d_to_vector_3d,
)
from mathutils import Vector


def r2d_to_v3d(event: bpy.types.Event, coord: Vector = None) -> Vector:
    """Return a direction vector from the viewport at the specific 2D region coordinate.

    Args:
        event (bpy.types.Event): Event from the operator.
        coord (Vector, optional): 2D coordinates relative to the region: (event.mouse_region_x, event.mouse_region_y) for example. Defaults to None.

    Returns:
        Vector: Normalized 3D vector.
    """
    if coord is None:
        coord = (event.mouse_region_x, event.mouse_region_y)
    return region_2d_to_vector_3d(bpy.context.region, bpy.context.region_data, coord)


def r2d_to_o3d(event: bpy.types.Event, coord: Vector = None, clamp: bool = None) -> Vector:
    """Return the 3d view origin from the region relative 2D coords.\n
    Note:
    Orthographic views have a less obvious origin, the far clip is used to define the viewport near/far extents. Since far clip can be a very large value, the result may give with numeric precision issues.

    To avoid this problem, you can optionally clamp the far clip to a smaller value based on the data you're operating on.

    Args:
        event (bpy.types.Event): Event from the operator.
        coord (Vector, optional): 2D coordinates relative to the region; (event.mouse_region_x, event.mouse_region_y) for example. Defaults to None.
        clamp (bool, optional): Clamp the maximum far-clip value used. (negative value will move the offset away from the view_location). Defaults to None.

    Returns:
        Vector: Origin of the viewpoint in 3D space.
    """
    if coord is None:
        coord = (event.mouse_region_x, event.mouse_region_y)
    return region_2d_to_origin_3d(bpy.context.region, bpy.context.region_data, coord, clamp)


def r2d_to_l3d(event: bpy.types.Event, coord: Vector = None, depth_location: Vector = Vector((0, 0, 0))) -> Vector:
    """Return a 3D location from the region relative 2D coords, aligned with depth_location.

    Args:
        event (bpy.types.Event): Event from the operator.
        coord (Vector, optional): 2D coordinates relative to the region; (event.mouse_region_x, event.mouse_region_y) for example. Defaults to None.
        depth_location (Vector, optional): The returned vectors depth is aligned with this since there is no defined depth with a 2d region input. Defaults to Vector((0, 0, 0)).

    Returns:
        Vector: Normalized 3D vector.
    """
    if coord is None:
        coord = (event.mouse_region_x, event.mouse_region_y)
    return region_2d_to_location_3d(bpy.context.region, bpy.context.region_data, coord, depth_location)


def l3d_to_r2d(coord: Vector = Vector((0, 0, 0)), default: Vector = Vector((0, 0))) -> Vector | bpy.types.AnyType:
    """Return the region relative 2D location of a 3D position.

    Args:
        coord (Vector, optional): 3D world-space location. Defaults to Vector((0, 0, 0)).
        default (Vector, optional): Return this value if coord is behind the origin of a perspective view. Defaults to Vector((0, 0)).

    Returns:
        Vector | bpy.types.AnyType: 2D location.
    """
    return location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, coord, default=default)
