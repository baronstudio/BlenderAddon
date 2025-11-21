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
from ..utils.addon import package
from ..utils.export_uv import ExportUVLayout
from ..utils.material_bake_v4 import Bake


class BakePanel:
    wait = 0
    cancel_baking = False


class QBAKER_OT_material_bake(Operator, Bake, ExportUVLayout):
    bl_label = "Bake"
    bl_idname = "qbaker.material_bake"
    bl_options = {"REGISTER", "INTERNAL"}

    debug: BoolProperty(name="Debug", default=False)

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global and not material_baker.maps:
            return False
        elif not material_baker.use_map_global and any((not item.maps) for item in material_baker.materials):
            return False

        return True

    @classmethod
    def description(cls, context, properties):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global and not material_baker.maps:
            return "Add map"
        elif not material_baker.use_map_global and any((not item.maps) for item in material_baker.materials):
            return "Add map"

        return "Bake all the materials\n\nShift  •  Bake the active material\nAlt      •  Debug in the console"

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
        "BASE_COLOR": ("Base Color", None),
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
    }

    def get_map_count(self, maps):
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

    def schedule_maps(self, maps, active_material_index):
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

        self.add_to_bake(map_table, privileged_maps, active_material_index, baked_maps)
        self.add_to_bake(map_table, normal_maps, active_material_index, baked_maps)

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

            self.to_bake.put_nowait(json.dumps((active_material_index, map.name, channels)))

    def add_to_bake(self, map_table: dict, maps: list, active_material_index: int, bake_maps: dict):
        for type, map_id in maps:
            maps_same_type: set = map_table.get(type)
            if maps_same_type is None:
                continue
            bake_maps[type] = map_id
            self.to_bake.put_nowait(
                json.dumps((active_material_index, map_id, list(maps_same_type.difference([map_id]))))
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
        "Create temp blend file to bake materials."
        filepath = os.path.join(bpy.app.tempdir, "qbaker.blend")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=True, copy=True)

        expression = """
import bpy
from bpy import context

material_baker = context.scene.qbaker.material_baker
materials = [item.material for item in material_baker.materials]

for material in bpy.data.materials:
    if material in materials:
        material.use_fake_user = True
    else:
        bpy.data.materials.remove(material)

# remove all data except materials
bpy.data.batch_remove(bpy.data.objects)

bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.ops.wm.save_mainfile()
"""
        env = os.environ.copy()
        env["BLENDER_USER_SCRIPTS"] = os.path.join(os.path.dirname(__file__), "../../../../")
        env["BLENDER_USER_EXTENSIONS"] = os.path.join(os.path.dirname(__file__), "../../../../")
        env["TBB_MALLOC_DISABLE_REPLACEMENT"] = "1"

        command = [
            bpy.app.binary_path,
            "--factory-startup",
            "-b",
            filepath,
            "--addons",
            package,
            "--python-expr",
            expression,
        ]
        process = subprocess.Popen(
            command,
            env=env,
        )
        process.wait()

        return os.path.join(bpy.app.tempdir, "qbaker.blend")

    def invoke(self, context, event):
        self.debug = event.alt
        if self.debug and sys.platform != "darwin":  # Skip console toggle on macOS
            bpy.ops.wm.console_toggle()

        self.temp_blend_path = self.create_temp_blend_file(context)
        self.start_time = time.time()
        self.remove_unused_images(self.old_image_filepaths)
        self.clear(context)
        self.total_maps = 0
        self.baked_maps = 0
        self.node_offset = 0
        self.bake_path = os.path.join(bpy.app.tempdir, f"qb_baked_maps_{uuid.uuid4().hex[:8]}", "")
        os.makedirs(self.bake_path, exist_ok=True)

        material_baker = context.scene.qbaker.material_baker
        material_baker.progress = -1
        active_material = material_baker.materials[material_baker.active_material_index]
        self.bake_settings = material_baker.bake if material_baker.use_bake_global else active_material.bake

        if event.shift:
            self.bake_active_material(context, material_baker)
        else:
            for i, active_material in enumerate(material_baker.materials):
                # if not active_material.use_include:
                #     continue

                maps = active_material.maps

                if material_baker.use_map_global:
                    maps = material_baker.maps

                self.schedule_maps(maps, i)
                self.total_maps += self.get_map_count(maps)

        if self.total_maps <= 0:
            self.cancel(context)
            self.report({"WARNING"}, "Add Map")
            return {"CANCELLED"}

        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(0.1, window=context.window)
        return {"RUNNING_MODAL"}

    def bake_active_material(self, context, material_baker):
        active_material = material_baker.materials[material_baker.active_material_index]
        maps = active_material.maps

        if material_baker.use_map_global:
            maps = material_baker.maps

        self.schedule_maps(maps, material_baker.active_material_index)
        self.total_maps = self.get_map_count(maps)

    def add_image_texture(
        self,
        image: bpy.types.Image,
        active_material: bpy.types.PropertyGroup,
        map: bpy.types.PropertyGroup,
        node_offset: float,
    ):
        material = Material.get_material(name=f"{active_material.material.name}_BAKED")
        node_tree = material.node_tree
        # principled_node = node_tree.nodes['Principled BSDF']
        principled_node = next((node for node in node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        image_node = ShaderNode.image_texture(node_tree, name=image.name, image=image)
        image_node.hide = True
        image_node_pos = (
            principled_node.location.x - image_node.width - 270,
            principled_node.location.y - node_offset,
        )
        image_node.location = image_node_pos
        uvmap_node = ShaderNode.uvmap(node_tree, name="QBAKER_UVMAP", uv_map="")
        uvmap_node_pos = (
            image_node.location.x - uvmap_node.width - 270,
            principled_node.location.y,
        )
        uvmap_node.location = uvmap_node_pos
        node_tree.links.new(image_node.inputs["Vector"], uvmap_node.outputs["UV"])
        self.connect_to_principled_BSDF(node_tree, principled_node=principled_node, node=image_node, map=map)

    def connect_to_principled_BSDF(
        self,
        node_tree: bpy.types.NodeTree,
        principled_node: bpy.types.ShaderNodeBsdfPrincipled,
        node: bpy.types.Node,
        map,
    ):
        if map.type == "CHANNEL_PACK":
            if map.channel_pack.mode == "RGBA":
                self.link_channel_pack_image(node_tree, principled_node=principled_node, node=node, map=map)
            elif map.channel_pack.rgb_channel != "NONE":
                self.link_to_principled(
                    node_tree,
                    principled_node=principled_node,
                    map_type=map.channel_pack.rgb_channel,
                    output_socket=node.outputs["Color"],
                )
            if map.channel_pack.a_channel != "NONE":
                self.link_to_principled(
                    node_tree,
                    principled_node=principled_node,
                    map_type=map.channel_pack.a_channel,
                    output_socket=node.outputs["Alpha"],
                )
            return

        self.link_to_principled(
            node_tree,
            principled_node=principled_node,
            map_type=map.type,
            output_socket=node.outputs["Color"],
        )

    def link_channel_pack_image(self, node_tree, principled_node, node, map):
        separate_color_node = ShaderNode.separate_color(
            node_tree,
            name="Separate Color",
            position=(node.location.x + node.width + 80, node.location.y),
        )
        separate_color_node.hide = True
        node_tree.links.new(separate_color_node.inputs["Color"], node.outputs["Color"])

        if map.channel_pack.r_channel != "NONE":
            self.link_to_principled(
                node_tree,
                principled_node=principled_node,
                map_type=map.channel_pack.r_channel,
                output_socket=separate_color_node.outputs["Red"],
            )
        if map.channel_pack.g_channel != "NONE":
            self.link_to_principled(
                node_tree,
                principled_node=principled_node,
                map_type=map.channel_pack.g_channel,
                output_socket=separate_color_node.outputs["Green"],
            )
        if map.channel_pack.b_channel != "NONE":
            self.link_to_principled(
                node_tree,
                principled_node=principled_node,
                map_type=map.channel_pack.b_channel,
                output_socket=separate_color_node.outputs["Blue"],
            )

    def link_to_principled(self, node_tree, principled_node, map_type, output_socket):
        output_socket = self.add_converting_node(node_tree, output_socket, map_type)

        try:
            color, alpha = self.MAP_TO_PRINCIPLED_BSDF.get(map_type)
        except TypeError:
            color, alpha = None, None

        if color is None or principled_node is None:
            return

        if color and (input_socket := principled_node.inputs.get(color)):
            node_tree.links.new(input_socket, output_socket)
        if alpha is not None and (input_socket := principled_node.inputs.get(alpha)):
            node_tree.links.new(input_socket, output_socket.node.outputs["Alpha"])

    def add_converting_node(self, node_tree: bpy.types.NodeTree, output_socket, map_type):
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
        env["BLENDER_USER_SCRIPTS"] = os.path.join(os.path.dirname(__file__), "../../../../")
        env["BLENDER_USER_EXTENSIONS"] = os.path.join(os.path.dirname(__file__), "../../../../")
        env["TBB_MALLOC_DISABLE_REPLACEMENT"] = "1"

        while len(self.processes) < self.bake_settings.processes and not self.to_bake.empty():
            bakeable = self.to_bake.get()
            expression = (
                "import bpy;bpy.ops.qbaker.background_material_bake('INVOKE_DEFAULT', first_bakeable='%s', bake_path='%s')"
                % (
                    bakeable,
                    self.bake_path.replace("\\", "\\\\"),
                )
            )
            process = subprocess.Popen(
                [
                    bpy.app.binary_path,
                    "--factory-startup",
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
                #     image.filepath = ""

                material_baker = context.scene.qbaker.material_baker
                active_material = material_baker.materials[image_data["active_bake_group_index"]]

                if material_baker.use_map_global:
                    maps = material_baker.maps
                else:
                    maps = active_material.maps

                *_, map_name = image_data["map_name"].split("_")
                self.add_image_texture(
                    image=image,
                    active_material=active_material,
                    map=maps[map_name],
                    node_offset=self.node_offset,
                )
                self.node_offset += 40

            except queue.Empty as err:
                print(err)
                continue

        material_baker = context.scene.qbaker.material_baker
        if not len(self.processes) and self.to_bake.empty() and self.images.empty():
            return self.finish(context)
        material_baker.progress = int(self.baked_maps / self.total_maps * 100)
        if context.area:
            context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def finish(self, context):
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
        material_baker = context.scene.qbaker.material_baker
        material_baker.progress = -1

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


class QBAKER_OT_material_bake_cancel(Operator):
    """Cancel baking"""

    bl_label = "Cancel"
    bl_idname = "qbaker.material_bake_cancel"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        material_baker = context.scene.qbaker.material_baker
        BakePanel.cancel_baking = True
        material_baker.progress = -1
        return {"FINISHED"}


class QBAKER_OT_background_material_bake(Operator, Bake):
    """Bake the bake group"""

    bl_label = "Background Bake"
    bl_idname = "qbaker.background_material_bake"
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
        material_baker = context.scene.qbaker.material_baker
        bakeable = json.loads(self.first_bakeable)

        while bakeable:
            active_material_index, map_id, duplicate_maps = bakeable
            self.index = active_material_index
            active_material = material_baker.materials[active_material_index]
            maps = material_baker.maps if material_baker.use_map_global else active_material.maps
            map_id, channel = self.get_map_tuple(map_id)
            main_map = maps[map_id]
            maps_to_bake = [(main_map, channel)]

            if main_map.type == "CHANNEL_PACK" and channel is None:
                print(f"QB: Wait Map:{[f'{active_material_index}_{map_name}' for map_name in duplicate_maps]}")
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

            main_map.name = f"{active_material_index}_{map_id}"

            self.bake_materials(context, active_material, maps_to_bake, self.bake_path)

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
    QBAKER_OT_background_material_bake,
    QBAKER_OT_material_bake_cancel,
    QBAKER_OT_material_bake,
)


register, unregister = bpy.utils.register_classes_factory(classes)
