import contextlib
import json
import os
import queue
import subprocess
import sys
import threading
import time
import uuid
from collections import defaultdict

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator

from ...qbpy import Image, Material, ShaderNode
from ..utils.addon import package, preferences
from ..utils.bake import post_bake
from ..utils.bake_v4 import Bake
from ..utils.export_uv import ExportUVLayout


class BakePanel:
    wait = 0
    cancel_baking = False


class QBAKER_OT_bake(Operator, Bake, ExportUVLayout):
    bl_label = "Bake"
    bl_idname = "qbaker.bake"
    bl_options = {"REGISTER", "INTERNAL"}

    debug: BoolProperty(name="Debug", default=False)

    @classmethod
    def poll(cls, context):
        qbaker = context.scene.qbaker

        def check_object_bake():
            for bake_group in qbaker.bake_groups:
                if bake_group.use_include and not bake_group.use_high_to_low:
                    if not bake_group.objects:
                        return False
                    if any(not item.object.data.uv_layers for item in bake_group.objects):
                        return False
                    if any(not item.object.data.materials for item in bake_group.objects):
                        return False
            return True

        def check_high_to_low_bake():
            for bake_group in qbaker.bake_groups:
                if bake_group.use_include and bake_group.use_high_to_low:
                    if not bake_group.groups:
                        return False
                    for group in bake_group.groups:
                        if not group.high_poly:
                            return False
                        if any(not item.object.data.materials for item in group.high_poly):
                            return False
                        if not group.low_poly:
                            return False
                        if any(not item.object.data.uv_layers for item in group.low_poly):
                            return False
            return True

        def check_maps():
            if qbaker.use_map_global and not qbaker.maps:
                return False
            if not qbaker.use_map_global and any(
                not bake_group.maps for bake_group in qbaker.bake_groups if bake_group.use_include
            ):
                return False
            return True

        # Check for object bake
        if not check_object_bake():
            return False

        # Check for high to low bake
        if not check_high_to_low_bake():
            return False

        # Check for global or local map
        if not check_maps():
            return False

        return True

    @classmethod
    def description(cls, context, properties):
        qbaker = context.scene.qbaker

        def check_object_bake():
            for bake_group in qbaker.bake_groups:
                if bake_group.use_include and not bake_group.use_high_to_low:
                    if not bake_group.objects:
                        return "Add object to the bake groups"
                    if any(not item.object.data.uv_layers for item in bake_group.objects):
                        return "Add uv map to the objects"
                    if any(not item.object.data.materials for item in bake_group.objects):
                        return "Add material to the objects"
            return None

        def check_high_to_low_bake():
            for bake_group in qbaker.bake_groups:
                if bake_group.use_include and bake_group.use_high_to_low:
                    if not bake_group.groups:
                        return "Add group to the bake groups"
                    for group in bake_group.groups:
                        if not group.high_poly:
                            return "Add high poly to the groups"
                        if any(not item.object.data.materials for item in group.high_poly):
                            return "Add material to the high poly"
                        if not group.low_poly:
                            return "Add low poly to the groups"
                        if any(not item.object.data.uv_layers for item in group.low_poly):
                            return "Add uv map to the low poly"
            return None

        def check_maps():
            if qbaker.use_map_global and not qbaker.maps:
                return "Add global map"
            if not qbaker.use_map_global and any(
                not bake_group.maps for bake_group in qbaker.bake_groups if bake_group.use_include
            ):
                return "Add map to the bake groups"
            return None

        # Check for object bake
        if result := check_object_bake():
            return result

        # Check for high to low bake
        if result := check_high_to_low_bake():
            return result

        # Check for global or local map
        if result := check_maps():
            return result

        return "Bake all the bake groups\n\nShift  •  Bake the active bake group\nAlt      •  Debug in the console"

    total_maps = 0
    baked_maps = 0

    # temp_blend_path = os.path.join(bpy.app.tempdir, 'qbaker.blend')
    to_bake = queue.Queue()  # contains string as tuple of (active_bake_group_index, map_id, duplicate_maps); duplicate_maps are the maps that bake the same data, for Channel_Pack this attribute contain the channel_maps_ids
    processes = []
    baked = queue.Queue()
    images = queue.Queue()
    errors = queue.Queue()
    finished_maps = set()
    baking_schedule = {}
    finished_maps_lock = threading.Lock()
    old_image_filepaths = []

    MAP_TO_PRINCIPLED_BSDF = {
        "BASE_COLOR": ("Base Color", "Alpha"),
        "METALLIC": ("Metallic", None),
        "ROUGHNESS": ("Roughness", None),
        "IOR": ("IOR", None),
        "ALPHA": ("Alpha", None),
        "NORMAL": ("Normal", None),
        "SUBSURFACE_WEIGHT": ("Subsurface Weight", None),
        "": ("Subsurface Radius", None),
        "SUBSURFACE_SCALE": ("Subsurface Scale", None),
        "SUBSURFACE_IOR": ("Subsurface IOR", None),
        "SUBSURFACE_ANISOTROPY": ("Subsurface Anisotropy", None),
        "SPECULAR": ("Specular IOR Level", None),
        "SPECULAR_TINT": ("Specular Tint", None),
        "ANISOTROPIC": ("Anisotropic", None),
        "ANISOTROPIC_ROTATION": ("Anisotropic Rotation", None),
        "TANGENT": ("Tangent", None),
        "TRANSMISSION_WEIGHT": ("Transmission Weight", None),
        "COAT_WEIGHT": ("Coat Weight", None),
        "COAT_ROUGHNESS": ("Coat Roughness", None),
        "COAT_IOR": ("Coat IOR", None),
        "COAT_TINT": ("Coat Tint", None),
        "COAT_NORMAL": ("Coat Normal", None),
        "SHEEN_WEIGHT": ("Sheen Weight", None),
        "SHEEN_ROUGHNESS": ("Sheen Roughness", None),
        "SHEEN_TINT": ("Sheen Tint", None),
        "EMISSION": ("Emission Color", None),
        "EMISSION_STRENGTH": ("Emission Strength", None),
        "COMBINED": ("Base Color", "Alpha"),
        "DIFFUSE": ("Base Color", "Alpha"),
    }

    def get_map_count(self, bake_group, maps):
        maps_count = 0
        render_count = 0

        for map in maps:
            if not map.use_include:
                continue
            if map.type == "CHANNEL_PACK":
                channel_count = (map.channel_pack.mode == "RGBA") * (
                    (map.channel_pack.r_channel != "NONE")
                    + (map.channel_pack.g_channel != "NONE")
                    + (map.channel_pack.b_channel != "NONE")
                    + (map.channel_pack.a_channel != "NONE")
                )
                channel_count += (map.channel_pack.mode == "RGB_A") * (
                    (map.channel_pack.rgb_channel != "NONE") + (map.channel_pack.a_channel != "NONE")
                )
                render_count += channel_count > 0
                maps_count += channel_count
            else:
                maps_count += 1

        return maps_count + render_count

    def cleanup_objects(self, object_collection):
        object_list = []
        offset = 0

        for i, obj in enumerate(object_collection):
            if obj.object is None or obj.object.type != "MESH" or obj.object.name in object_list:
                object_collection.remove(i - offset)
                offset += 1
            else:
                object_list.append(obj.object.name)

    def cleanup_bake_group(self, bake_group):
        if bake_group.use_high_to_low:
            for group in bake_group.groups:
                if not group.use_include:
                    continue

                self.cleanup_objects(group.high_poly)
                self.cleanup_objects(group.low_poly)
        else:
            self.cleanup_objects(bake_group.objects)

    def validate_combined(self, maps) -> bool:
        return not any(
            (
                map.type == "COMBINED"
                and not (
                    (map.combined.use_pass_direct or map.combined.use_pass_indirect)
                    and (
                        map.combined.use_pass_diffuse
                        or map.combined.use_pass_glossy
                        or map.combined.use_pass_transmission
                        or map.combined.use_pass_emit
                    )
                )
            )
            for map in maps
        )

    def schedule_maps(self, maps, active_bake_group_index):
        channel_pack_maps = []
        privileged_maps = []
        normal_maps = []
        map_table = defaultdict(set)
        baked_maps = {}

        for map in maps:
            if not map.use_include:
                continue

            if map.type != "CHANNEL_PACK":
                normal_maps.append((map.type, map.name))
                map_table[map.type].add(map.name)
                continue

            channel_pack_maps.append(map)
            if map.channel_pack.mode == "RGBA":
                if map.channel_pack.r_channel != "NONE":
                    map_name = f"{map.name}_r"
                    privileged_maps.append((map.channel_pack.r_channel, map_name))
                    map_table[map.channel_pack.r_channel].add(map_name)
                if map.channel_pack.g_channel != "NONE":
                    map_name = f"{map.name}_g"
                    privileged_maps.append((map.channel_pack.g_channel, map_name))
                    map_table[map.channel_pack.g_channel].add(map_name)
                if map.channel_pack.b_channel != "NONE":
                    map_name = f"{map.name}_b"
                    privileged_maps.append((map.channel_pack.b_channel, map_name))
                    map_table[map.channel_pack.b_channel].add(map_name)
            elif map.channel_pack.rgb_channel != "NONE":
                map_name = f"{map.name}_rgb"
                privileged_maps.append((map.channel_pack.rgb_channel, map_name))
                map_table[map.channel_pack.rgb_channel].add(map_name)

            if map.channel_pack.a_channel != "NONE":
                map_name = f"{map.name}_a"
                privileged_maps.append((map.channel_pack.a_channel, map_name))
                map_table[map.channel_pack.a_channel].add(map_name)

        self.add_to_bake(map_table, privileged_maps, active_bake_group_index, baked_maps)
        self.add_to_bake(map_table, normal_maps, active_bake_group_index, baked_maps)

        for map in channel_pack_maps:
            channels = []
            if map.channel_pack.mode == "RGBA":
                if map.channel_pack.r_channel != "NONE":
                    channels.append(baked_maps[map.channel_pack.r_channel])
                if map.channel_pack.g_channel != "NONE":
                    channels.append(baked_maps[map.channel_pack.g_channel])
                if map.channel_pack.b_channel != "NONE":
                    channels.append(baked_maps[map.channel_pack.b_channel])
            elif map.channel_pack.rgb_channel != "NONE":
                channels.append(baked_maps[map.channel_pack.rgb_channel])
            if map.channel_pack.a_channel != "NONE":
                channels.append(baked_maps[map.channel_pack.a_channel])

            self.to_bake.put_nowait(json.dumps((active_bake_group_index, map.name, channels)))

    def add_to_bake(self, map_table: dict, maps: list, active_bake_group_index: int, bake_maps: dict):
        for type, map_id in maps:
            maps_same_type: set = map_table.get(type)
            if maps_same_type is None:
                continue
            bake_maps[type] = map_id
            self.to_bake.put_nowait(
                json.dumps(
                    (
                        active_bake_group_index,
                        map_id,
                        list(maps_same_type.difference([map_id])),
                    )
                )
            )
            del map_table[type]

    def remove_unused_images(self, filepaths: list):
        for filepath in filepaths:
            bake_dir = os.path.dirname(filepath)
            if not os.path.isfile(filepath):
                continue
            os.remove(filepath)
            if os.path.isdir(bake_dir) and len(os.listdir(bake_dir)) == 0:
                os.rmdir(bake_dir)

    def create_temp_blend_file(self, context):
        temp_filepath = os.path.join(bpy.app.tempdir, "qbaker.blend")
        bpy.ops.wm.save_as_mainfile(filepath=temp_filepath, compress=True, copy=True)

        return os.path.join(bpy.app.tempdir, "qbaker.blend")

    def invoke(self, context, event):
        self.debug = event.alt
        if self.debug and sys.platform != "darwin":  # Skip console toggle on macOS
            bpy.ops.wm.console_toggle()

        self.start_time = time.time()
        self.remove_unused_images(self.old_image_filepaths)
        self.clear(context)
        self.total_maps = 0
        self.baked_maps = 0
        self.node_offset = 0
        self.bake_path = os.path.join(bpy.app.tempdir, f"qb_baked_maps_{uuid.uuid4().hex[:8]}", "")
        os.makedirs(self.bake_path, exist_ok=True)
        baker = context.scene.qbaker
        baker.bake.batch_name = preferences().qbaker.bake.batch_name
        baker.bake.use_auto_udim = preferences().qbaker.bake.use_auto_udim
        baker.progress = -1

        bake_group = baker.bake_groups[baker.active_bake_group_index]
        self.bake_settings = baker.bake if baker.use_bake_global else bake_group.bake

        if event.shift:
            self.bake_active_bakegroup(context, baker)
        else:
            for i, bake_group in enumerate(baker.bake_groups):
                if not bake_group.use_include:
                    continue

                bake_group.bake.batch_name = preferences().qbaker.bake.batch_name
                bake_group.bake.use_auto_udim = preferences().qbaker.bake.use_auto_udim

                # if material := bpy.data.materials.get(f"{bake_group.name}_BAKED"):
                #     bpy.data.materials.remove(material)

                maps = bake_group.maps
                self.cleanup_bake_group(bake_group)

                if baker.use_map_global:
                    maps = baker.maps

                self.schedule_maps(maps, i)
                self.total_maps += self.get_map_count(bake_group, maps)

                if not self.validate_combined(maps):
                    self.report(
                        {"WARNING"},
                        "Combined map requires lighting and contributions enabled",
                    )

                for map in maps:
                    if map.type == "WIREFRAME" and map.use_include:
                        if not self.bake_settings.folders:
                            self.report({"WARNING"}, "Wireframe map needs path to save")
                            continue
                        self.wireframe(context, bake_group, map)

        if self.total_maps <= 0:
            self.cancel(context)
            self.report({"WARNING"}, "Include a bake group")
            return {"CANCELLED"}

        self.temp_blend_path = self.create_temp_blend_file(context)
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(0.1, window=context.window)
        return {"RUNNING_MODAL"}

    def bake_active_bakegroup(self, context, baker):
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        bake_group.bake.batch_name = preferences().qbaker.bake.batch_name
        bake_group.bake.use_auto_udim = preferences().qbaker.bake.use_auto_udim

        # if material := bpy.data.materials.get(f"{bake_group.name}_BAKED"):
        #     bpy.data.materials.remove(material)

        maps = bake_group.maps
        self.cleanup_bake_group(bake_group)

        if baker.use_map_global:
            maps = baker.maps

        self.schedule_maps(maps, baker.active_bake_group_index)
        self.total_maps = self.get_map_count(bake_group, maps)

        if not self.validate_combined(maps):
            self.report({"WARNING"}, "Combined map requires lighting and contributions enabled")

        for map in maps:
            if map.type == "WIREFRAME" and map.use_include:
                if not self.bake_settings.folders:
                    self.report({"WARNING"}, "Wireframe map needs path to save")
                    continue
                self.wireframe(context, bake_group, map)

    def add_image_texture(
        self,
        image: bpy.types.Image,
        bake_group: bpy.types.PropertyGroup,
        map: bpy.types.PropertyGroup,
        node_offset: float,
    ):
        material = Material.get_material(name=f"{bake_group.name}_BAKED")
        material["mat_type"] = f"{bake_group.name}_BAKED"
        material.use_fake_user = False
        node_tree = material.node_tree

        principled_node = next((node for node in node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        image_node = ShaderNode.image_texture(node_tree, name=map.name, image=image)
        image_node.hide = True
        image_node_pos = (
            principled_node.location.x - image_node.width - 270,
            principled_node.location.y - node_offset,
        )
        image_node.location = image_node_pos
        uvmap_node = ShaderNode.uvmap(node_tree, name="QBAKER_UVMAP", uv_map="")
        uvmap_node_pos = (
            image_node.location.x - uvmap_node.width - 200,
            principled_node.location.y,
        )
        uvmap_node.location = uvmap_node_pos
        node_tree.links.new(image_node.inputs.get("Vector"), uvmap_node.outputs.get("UV"))
        self.connect_to_principled_BSDF(node_tree, principled_node=principled_node, node=image_node, map=map)

    def connect_to_principled_BSDF(
        self,
        node_tree: bpy.types.ShaderNodeTree,
        principled_node: bpy.types.ShaderNodeBsdfPrincipled,
        node: bpy.types.ShaderNode,
        map: bpy.types.PropertyGroup,
    ):
        if map.type == "CHANNEL_PACK":
            if map.channel_pack.mode == "RGBA":
                self.link_channel_pack_image(node_tree, principled_node=principled_node, node=node, map=map)
            elif map.channel_pack.rgb_channel != "NONE":
                self.link_to_principled(
                    node_tree,
                    principled_node=principled_node,
                    map_type=map.channel_pack.rgb_channel,
                    output_socket=node.outputs.get("Color"),
                )
            if map.channel_pack.a_channel != "NONE":
                self.link_to_principled(
                    node_tree,
                    principled_node=principled_node,
                    map_type=map.channel_pack.a_channel,
                    output_socket=node.outputs.get("Alpha"),
                )
            return

        self.link_to_principled(
            node_tree,
            principled_node=principled_node,
            map_type=map.type,
            output_socket=node.outputs.get("Color"),
        )

    def link_channel_pack_image(
        self,
        node_tree: bpy.types.ShaderNodeTree,
        principled_node: bpy.types.ShaderNodeBsdfPrincipled,
        node: bpy.types.ShaderNode,
        map: bpy.types.PropertyGroup,
    ):
        separate_color_node = ShaderNode.separate_color(
            node_tree,
            name="Separate Color",
            position=(node.location.x + node.width + 80, node.location.y),
        )
        separate_color_node.hide = True
        node_tree.links.new(separate_color_node.inputs.get("Color"), node.outputs.get("Color"))

        if map.channel_pack.r_channel != "NONE":
            self.link_to_principled(
                node_tree,
                principled_node=principled_node,
                map_type=map.channel_pack.r_channel,
                output_socket=separate_color_node.outputs.get("Red"),
            )
        if map.channel_pack.g_channel != "NONE":
            self.link_to_principled(
                node_tree,
                principled_node=principled_node,
                map_type=map.channel_pack.g_channel,
                output_socket=separate_color_node.outputs.get("Green"),
            )
        if map.channel_pack.b_channel != "NONE":
            self.link_to_principled(
                node_tree,
                principled_node=principled_node,
                map_type=map.channel_pack.b_channel,
                output_socket=separate_color_node.outputs.get("Blue"),
            )

    def link_to_principled(
        self,
        node_tree: bpy.types.ShaderNodeTree,
        principled_node: bpy.types.ShaderNodeBsdfPrincipled,
        output_socket: bpy.types.NodeSocket,
        map_type: str,
    ):
        output_socket = self.add_converting_node(node_tree, output_socket, map_type)
        color, alpha = self.MAP_TO_PRINCIPLED_BSDF.get(map_type, (None, None))

        if color and principled_node:
            input_socket = principled_node.inputs.get(color)
            if input_socket and not (map_type in {"COMBINED", "DIFFUSE"} and input_socket.is_linked):
                node_tree.links.new(input_socket, output_socket)

        if alpha and principled_node:
            input_socket = principled_node.inputs.get(alpha)
            if input_socket and not (map_type in {"COMBINED", "DIFFUSE"} and input_socket.is_linked):
                node_tree.links.new(input_socket, output_socket.node.outputs.get("Alpha"))

    def add_converting_node(
        self, node_tree: bpy.types.ShaderNodeTree, output_socket: bpy.types.NodeSocket, map_type: str
    ) -> bpy.types.NodeSocket:
        node = output_socket.node

        if map_type == "NORMAL":
            normal_node = ShaderNode.normal_map(
                node_tree,
                name="Normal",
                position=(node.location.x + node.width + 80, node.location.y),
            )
            normal_node.hide = True
            node_tree.links.new(normal_node.inputs["Color"], output_socket)
            output_socket = normal_node.outputs["Normal"]
        elif map_type == "DISPLACEMENT":
            displacement_node = ShaderNode.displacement(
                node_tree,
                name="Displacement",
                position=(node.location.x + node.width + 80, node.location.y),
            )
            displacement_node.hide = True
            node_tree.links.new(displacement_node.inputs["Height"], output_socket)
            output_socket = displacement_node.outputs["Displacement"]
            material_output = node_tree.nodes.get("Material Output")
            if material_output and material_output.bl_idname == "ShaderNodeOutputMaterial":
                node_tree.links.new(material_output.inputs["Displacement"], output_socket)
        return output_socket

    def handle_process_data(self, data, images: queue.Queue):
        data_type = data["type"]
        if data_type == self.TYPE_IMAGE:
            images.put(data)

    def schedule_next_task(
        self, process: subprocess.Popen, finished_maps: set, baking_schedule: dict, to_bake: queue.Queue
    ):
        active_bake_group_index, main_map_id, duplicate_maps_ids = json.loads(baking_schedule[process.pid])
        finished_maps.add(f"{active_bake_group_index}_{main_map_id}")
        finished_maps.update(f"{active_bake_group_index}_{id}" for id in duplicate_maps_ids)
        next_task = None if to_bake.empty() else to_bake.get()
        baking_schedule[process.pid] = next_task
        process.stdin.write("%s\n" % next_task)
        process.stdin.flush()

    def wait_for_map(self, process: subprocess.Popen, finished_maps: set, wait_maps: list):
        while True:
            if not wait_maps:
                return
            with self.finished_maps_lock:
                if any((map not in finished_maps) for map in wait_maps):
                    time.sleep(0.1)
                    continue
            process.stdin.write("QB: Continue\n")
            process.stdin.flush()
            wait_maps.clear()
            return

    def handle_background_baking(
        self,
        process: subprocess.Popen,
        baked: queue.Queue,
        images: queue.Queue,
        finished_maps: set,
        baking_schedule: dict,
        to_bake: queue.Queue,
        errors: queue.Queue,
    ):
        wait_maps = []
        wait_thread = None

        while process.poll() is None:
            for line in process.stdout:
                if "QB: Baked Map" in line:
                    baked.put(1)
                elif "QB: Next Map" in line:
                    self.schedule_next_task(process, finished_maps, baking_schedule, to_bake)
                elif "QB: Wait Map" in line:
                    wait_maps.extend(json.loads(line.rsplit(":", 1)[1].replace("'", '"')))
                    wait_thread = threading.Thread(
                        target=self.wait_for_map,
                        args=(process, finished_maps, wait_maps),
                        daemon=True,
                    )
                    wait_thread.start()
                elif "System is out of GPU memory" in line:
                    print(line)
                    print("Reduce the number of process in preference")
                    errors.put(line)
                    errors.put("Reduce the number of process in preference")

                if line.startswith("{") and line.endswith("}\n"):  # check for json format
                    self.handle_process_data(json.loads(line), images)
                elif self.debug:
                    print(line)  # DEBUG print lines without image data

        outs, errs = process.communicate()
        baked_count = 0

        for line in outs.split("\n"):
            baked_count += "QB: Baked Map" in line

            if line.startswith("{") and line.endswith("}\n"):  # check for json format
                self.handle_process_data(json.loads(line), images)
            elif self.debug:
                print(line)  # DEBUG print lines without image data

        baked.put(baked_count)

        if wait_thread is not None and wait_thread.is_alive():
            wait_maps.clear()
            wait_thread.join()

        if errs != "":
            print(errs)
            errors.put(errs)
            return

    def modal(self, context, event):
        if BakePanel.cancel_baking:
            self.cancel(context)
            return {"CANCELLED"}

        if BakePanel.wait > 0:
            BakePanel.wait -= 1
            return {"PASS_THROUGH"}

        if event.type != "TIMER":
            return {"PASS_THROUGH"}

        BakePanel.wait = 5

        cycle_device = bpy.context.preferences.addons["cycles"].preferences.compute_device_type
        if cycle_device == "NONE":
            cycle_device = "CPU"

        env = os.environ.copy()
        # env["BLENDER_USER_SCRIPTS"] = os.path.join(os.path.dirname(__file__), "../../../../")
        # env["BLENDER_USER_EXTENSIONS"] = os.path.join(os.path.dirname(__file__), "../../../../")
        env["TBB_MALLOC_DISABLE_REPLACEMENT"] = "1"

        while len(self.processes) < self.bake_settings.processes and not self.to_bake.empty():
            bakeable = self.to_bake.get()
            expression = (
                "import bpy;bpy.ops.qbaker.background_bake('INVOKE_DEFAULT', first_bakeable='%s', bake_path='%s')"
                % (
                    bakeable,
                    self.bake_path.replace("\\", "\\\\"),
                )
            )
            process = subprocess.Popen(
                [
                    bpy.app.binary_path,
                    # "--factory-startup",
                    "-b",
                    self.temp_blend_path,
                    "-E",
                    "CYCLES",
                    "--addons",
                    package,
                    "--python-expr",
                    expression,
                    "--",
                    "--cycles-device",
                    cycle_device,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                encoding="utf-8",
                env=env,
            )
            thread = threading.Thread(
                target=self.handle_background_baking,
                args=(
                    process,
                    self.baked,
                    self.images,
                    self.finished_maps,
                    self.baking_schedule,
                    self.to_bake,
                    self.errors,
                ),
                daemon=True,
            )
            self.baking_schedule[process.pid] = bakeable
            thread.start()
            self.processes.append((process.pid, process, thread))

        for index, process, thread in self.processes:
            if thread.is_alive():
                continue
            self.processes.remove((index, process, thread))

        while not self.baked.empty():
            try:
                self.baked_maps += self.baked.get()
            except queue.Empty as err:
                print(err)
                continue

        while not self.images.empty():
            try:
                image_data = self.images.get()
                image = Image.load_image(image_data["path"], check_existing=False)
                if old_image := Image.get_image(image_data["name"]):
                    basedir, file = os.path.split(old_image.filepath)
                    if "qb_baked_maps" in old_image.filepath and os.path.isdir(basedir):
                        filename = file.split(".", maxsplit=1)[0]
                        files = filter(lambda x: filename in x, os.listdir(basedir))
                        self.remove_unused_images(os.path.join(basedir, file) for file in files)
                    bpy.data.images.remove(old_image)
                image.name = image_data["name"]
                image.colorspace_settings.name = image_data["color_space"]
                image.alpha_mode = image_data["alpha_mode"]
                image.source = image_data["source"]
                if image_data["source"] == "TILED":
                    image.reload()
                # else:
                #     image.pack()
                #     self.old_image_filepaths.append(image.filepath)
                #     # image.filepath = ""
                #     image.filepath = os.path.join(
                #         os.path.dirname(image.filepath),
                #         os.path.basename(image.filepath).replace(
                #             os.path.basename(image.filepath).split(".")[0], image.name
                #         ),
                #     )
                baker = context.scene.qbaker
                bake_group = baker.bake_groups[image_data["active_bake_group_index"]]
                maps = bake_group.maps
                if baker.use_map_global:
                    maps = baker.maps
                *_, map_name = image_data["map_name"].split("_")

                if baker.bake.use_create_material if baker.use_bake_global else bake_group.bake.use_create_material:
                    self.add_image_texture(
                        image=image,
                        bake_group=bake_group,
                        map=maps[map_name],
                        node_offset=self.node_offset,
                    )
                    self.node_offset += 40

            except queue.Empty as err:
                print(err)
                continue

        baker = context.scene.qbaker
        if not len(self.processes) and self.to_bake.empty() and self.images.empty():
            return self.finish(context)
        baker.progress = int(self.baked_maps / self.total_maps * 100)
        if context.area:
            context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def finish(self, context):
        post_bake(context)
        # Flush any enqueued expected renames now that baking finished
        try:
            Image.flush_expected_renames()
        except Exception:
            pass
        self.clear(context)

        if context.area:
            context.area.tag_redraw()

        error = ""
        while not self.errors.empty():
            error += f"{self.errors.get_nowait()}\n"  # possible because no Thread is running

        if self.debug and error != "":
            self.report({"ERROR"}, error)
        else:
            baking_time = round((time.time() - self.start_time), 2)
            self.report({"INFO"}, f"Bake Time: {baking_time} sec")

        if self.debug and sys.platform != "darwin":  # Skip console toggle on macOS
            bpy.ops.wm.console_toggle()

        return {"FINISHED"}

    def execute(self, context):
        return {"FINISHED"}

    def cancel(self, context):
        for index, process, thread in self.processes:
            process.kill()
            thread.join()
            while thread.is_alive():
                thread.join()

        error = ""
        while not self.errors.empty():
            error += f"{self.errors.get_nowait()}\n"  # possible because no Thread is running

        if self.debug and error != "":
            self.report({"ERROR"}, error)
        else:
            self.report({"INFO"}, "Baking: Cancelled")

        self.clear(context)

        if self.debug and sys.platform != "darwin":  # Skip console toggle on macOS
            bpy.ops.wm.console_toggle()

        if context.area:
            context.area.tag_redraw()

    def clear(self, context):
        baker = context.scene.qbaker
        baker.progress = -1

        with contextlib.suppress(AttributeError):
            context.window_manager.event_timer_remove(self.timer)
        # with contextlib.suppress(OSError):
        #     os.remove(self.temp_blend_path)

        BakePanel.wait = 0
        BakePanel.cancel_baking = False

        self.processes.clear()
        with self.to_bake.mutex:
            self.to_bake.queue.clear()
        with self.baked.mutex:
            self.baked.queue.clear()
        with self.images.mutex:
            self.images.queue.clear()
        self.finished_maps.clear()
        self.baking_schedule.clear()


class QBAKER_OT_bake_cancel(Operator):
    """Cancel baking"""

    bl_label = "Cancel"
    bl_idname = "qbaker.bake_cancel"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        baker = context.scene.qbaker
        BakePanel.cancel_baking = True
        baker.progress = -1
        return {"FINISHED"}


class QBAKER_OT_background_bake(Operator, Bake):
    """Bake the bake group"""

    bl_label = "Background Bake"
    bl_idname = "qbaker.background_bake"
    bl_options = {"REGISTER", "INTERNAL"}

    first_bakeable: StringProperty(name="bakeable to start with before checking stdin")
    bake_path: StringProperty(name="path ot bake the maps to")

    def read_input_line(self):
        for line in sys.stdin:
            return line

    def get_map_tuple(self, map_id):
        split = map_id.split("_")
        channel = None
        if len(split) == 2:
            map_id, channel = split
        return map_id, channel

    def execute(self, context):
        baker = context.scene.qbaker
        bakeable = json.loads(self.first_bakeable)

        while bakeable:
            active_bake_group_index, map_id, duplicate_maps = bakeable
            self.index = active_bake_group_index
            bake_group = baker.bake_groups[active_bake_group_index]
            maps = baker.maps if baker.use_map_global else bake_group.maps
            map_id, channel = self.get_map_tuple(map_id)
            main_map = maps[map_id]
            maps_to_bake = [(main_map, channel)]

            if main_map.type == "CHANNEL_PACK" and channel is None:
                print(f"QB: Wait Map:{[f'{active_bake_group_index}_{map_name}' for map_name in duplicate_maps]}")
                sys.stdout.flush()

                while "QB: Continue" not in (line := self.read_input_line()):
                    print(f"Missed Input: {line}")

                channel_labels = []
                if main_map.channel_pack.mode == "RGBA":
                    if main_map.channel_pack.r_channel != "NONE":
                        channel_labels.append("r_channel")
                    if main_map.channel_pack.g_channel != "NONE":
                        channel_labels.append("g_channel")
                    if main_map.channel_pack.b_channel != "NONE":
                        channel_labels.append("b_channel")
                elif main_map.channel_pack.rgb_channel != "NONE":
                    channel_labels.append("rgb_channel")

                if main_map.channel_pack.a_channel != "NONE":
                    channel_labels.append("a_channel")

                for channel_map_id, channel_label in zip(duplicate_maps, channel_labels):
                    self.baked_maps[getattr(main_map.channel_pack, channel_label)] = channel_map_id
            else:
                for duplicate_map_id in duplicate_maps:
                    duplicate_map_id, channel = self.get_map_tuple(duplicate_map_id)
                    maps_to_bake.append((maps[duplicate_map_id], channel))

            main_map.name = f"{active_bake_group_index}_{map_id}"

            if bake_group.use_high_to_low:
                self.bake_high_to_low(context, bake_group, maps_to_bake, self.bake_path)
            elif any("_decal" in child.name.lower() for item in bake_group.objects for child in item.object.children):
                self.bake_decals(context, bake_group, maps_to_bake, self.bake_path)
            else:
                self.bake_objects(context, bake_group, maps_to_bake, self.bake_path)

            print("QB: Next Map")
            sys.stdout.flush()

            line = self.read_input_line()
            if "None" in line:
                bakeable = None
                break

            bakeable = json.loads(line)
            self.baked_maps.clear()
            main_map.name = map_id

        return {"FINISHED"}


classes = (
    QBAKER_OT_background_bake,
    QBAKER_OT_bake_cancel,
    QBAKER_OT_bake,
)


register, unregister = bpy.utils.register_classes_factory(classes)
