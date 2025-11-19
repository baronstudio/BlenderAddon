import bpy


def edit_node_tree(
    node_tree: bpy.types.NodeTree,
    show_region_header: bool = False,
    show_region_toolbar: bool = False,
    show_region_ui: bool = False,
    pin: bool = True,
) -> None:
    """Open a new window with the given node tree.

    Args:
        node_tree (bpy.types.NodeTree): The node tree to open.
        show_region_header (bool, optional): Show header. Defaults to False.
        show_region_toolbar (bool, optional): Show tool bar. Defaults to False.
        show_region_ui (bool, optional): Show sidebar (n-panel). Defaults to False.
        pin (bool, optional): Pin the node tree. Defaults to True.
    """
    windows = bpy.context.window_manager.windows
    ws = set(windows)

    bpy.ops.wm.window_new("INVOKE_DEFAULT")

    (new_window,) = set(windows) - ws

    area = new_window.screen.areas[0]
    area.type = "NODE_EDITOR"
    area.ui_type = node_tree.bl_idname
    space_data = area.spaces[0]

    space_data.show_region_header = show_region_header
    space_data.show_region_toolbar = show_region_toolbar
    space_data.show_region_ui = show_region_ui
    space_data.pin = pin
    space_data.node_tree = node_tree

    with bpy.context.temp_override(window=new_window, area=area, region=area.regions[-1]):
        bpy.ops.node.view_all("INVOKE_DEFAULT")
