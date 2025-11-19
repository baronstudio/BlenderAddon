import bpy


class Scene:
    @staticmethod
    def new_scene(name: str) -> bpy.types.Scene:
        """Create a new scene.

        Args:
            name (str): Name of the scene.

        Returns:
            bpy.types.Scene: New scene.
        """
        return bpy.data.scenes.get(name) or bpy.data.scenes.new(name)
