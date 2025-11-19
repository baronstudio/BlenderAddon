from . import node_tree_to_script, test


def register():
    node_tree_to_script.register()
    test.register()


def unregister():
    node_tree_to_script.unregister()
    test.unregister()
