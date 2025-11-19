from math import radians

import bpy

from .object import Object


class Curve:
    @staticmethod
    def curve(
        name: str = "Curve", points=None, cuts: int = 0, axis: str = "POS_Y", check: bool = True
    ) -> bpy.types.Object:
        curve = bpy.data.curves.get(name) if check else bpy.data.curves.new(name, "CURVE")
        if not curve:
            curve = bpy.data.curves.new(name, "CURVE")
        curve.use_path = False
        curve.use_stretch = True
        curve.use_deform_bounds = True
        curve.dimensions = "3D"

        curve_object = bpy.data.objects.get(name) if check else bpy.data.objects.new(name, curve)
        if not curve_object:
            curve_object = bpy.data.objects.new(name, curve)
        curve_object.show_in_front = True

        Object.link_object(obj=curve_object, collecion=bpy.context.object.users_collection[0])
        Curve.spline(curve_object, points=Curve.subdivide(points, cuts=cuts), deform_axis=axis)

        return curve_object

    @staticmethod
    def spline(
        obj: bpy.types.Object,
        points,
        type: str = "BEZIER",
        deform_axis: str = "POS_Y",
        resolution_u: int = 36,
        order_u: str = 3,
    ):
        axis = {"POS_X": 0, "POS_Y": 90, "POS_Z": 180, "NEG_X": -90, "NEG_Y": 180, "NEG_Z": -90}

        obj.data.splines.clear()
        spline = obj.data.splines.new(type)
        spline.use_endpoint_u = True
        spline.resolution_u = resolution_u
        tilt = radians(axis[deform_axis])
        count = len(points)

        if type == "BEZIER":
            spline.bezier_points.add(count - 1)
            handle_offset = ((points[-1] - points[0]) / count) * 0.5

            for point, vec in zip(spline.bezier_points, points):
                point.co = vec
                point.radius = 1
                point.tilt = tilt
                point.handle_left_type = point.handle_right_type = "ALIGNED"
                point.handle_right = vec + handle_offset
                point.handle_left = vec - handle_offset
        else:
            spline.points.add(count - 1)
            spline.order_u = order_u

            for point, vec in zip(spline.points, points):
                point.co = (*vec, 1)
                point.radius = 1
                point.tilt = tilt

    @staticmethod
    def subdivide(point, cuts: int = 0) -> list:
        return [point[0] + (point[1] - point[0]) * (i / (cuts + 1)) for i in range(cuts + 2)]
