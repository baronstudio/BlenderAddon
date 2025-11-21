import os

import bpy

from .scene import Scene


class Image:
    @staticmethod
    def new_image(
        name: str = "Untitled",
        width: int = 1024,
        height: int = 1024,
        color: tuple = (0.0, 0.0, 0.0, 1.0),
        non_color: bool = False,
        alpha: bool = False,
        tiled: bool = False,
        float_buffer: bool = False,
        generated_type: str = "BLANK",
        check: bool = True,
    ) -> bpy.types.Image:
        """Create a new image.

        Args:
            name (str, optional): Name of the image. Defaults to "Untitled".
            width (int, optional): Width of the image. Defaults to 1024.
            height (int, optional): Height of the image. Defaults to 1024.
            color (tuple, optional): Color of the image. Defaults to (0.0, 0.0, 0.0, 1.0).
            non_color (bool, optional): Non-color data color space. Defaults to False.
            alpha (bool, optional): Alpha channel of the image. Defaults to False.
            tiled (bool, optional): Tiled image. Defaults to False.
            float_buffer (bool, optional): Float buffer. Defaults to False.
            generated_type (enum in ['BLANK', 'UV_GRID', 'COLOR_GRID'], optional): Fill the image with a grid for UV map testing. Defaults to "BLANK".
            check (bool, optional): Check for existing image. Defaults to True.

        Returns:
            bpy.types.Image: New image.
        """
        image = bpy.data.images.get(name) if check else None
        if not image:
            image = bpy.data.images.new(
                name=name,
                width=width,
                height=height,
                is_data=non_color,
                alpha=alpha,
                tiled=tiled,
                float_buffer=float_buffer,
            )
            image.generated_width = width
            image.generated_height = height

        image.generated_color = color
        image.generated_type = generated_type
        return image

    @staticmethod
    def save_image(
        image: bpy.types.Image, path: str = bpy.app.tempdir, name: str = "", file_format: str = "PNG"
    ) -> str:
        """Save the image to the filepath.

        Args:
            image (bpy.types.Image): The image to save.
            path (str): The path to save the image to.
            name (str): The name of the image.
            file_format (enum in ['BMP', 'IRIS', 'PNG', 'JPEG', 'JPEG2000', 'TARGA', 'TARGA_RAW', 'CINEON', 'DPX', 'OPEN_EXR_MULTILAYER', 'OPEN_EXR', 'HDR', 'TIFF', 'WEBP', 'AVI_JPEG', 'AVI_RAW', 'FFMPEG'], optional): The file format to save the image as. Defaults to "PNG".

        Returns:
            str: The filepath of the image.
        """
        if not name:
            name = image.name

        if file_format == "OPEN_EXR":
            image.filepath_raw = os.path.join(path, f"{name}.exr")
        else:
            image.filepath_raw = os.path.join(path, f"{name}.{file_format.lower()}")

        image.save()
        return image.filepath_raw

    @staticmethod
    def save_image_as(
        image: bpy.types.Image,
        path: str = bpy.app.tempdir,
        name: str = "",
        file_format: str = "PNG",
        color_mode: str = "RGB",
        color_depth: str = "8",
        compression: int = 15,
        quality: int = 100,
        exr_codec="ZIP",
        tiff_codec="DEFLATE",
        view_transform: str = "Standard",
    ) -> str:
        """Save the image to the filepath.

        Args:
            image (bpy.types.Image): The image to save.
            path (str): The path to save the image to.
            name (str, optional): The name of the image.
            file_format (enum in ['BMP', 'IRIS', 'PNG', 'JPEG', 'JPEG2000', 'TARGA', 'TARGA_RAW', 'CINEON', 'DPX', 'OPEN_EXR_MULTILAYER', 'OPEN_EXR', 'HDR', 'TIFF', 'WEBP', 'AVI_JPEG', 'AVI_RAW', 'FFMPEG'], optional): The file format to save the image as. Defaults to "PNG".
            color_mode (enum in ['BW', 'RGB', 'RGBA'], optional): The color mode of the image. Defaults to "RGBA".
            color_depth (enum in ['8', '16'], optional): The color depth of the image. Defaults to "8".
            compression (int, optional): The compression level of the image. Defaults to 15.
            quality (int, optional): The quality of the image. Defaults to 100.
            exr_codec (str, optional): The EXR codec. Defaults to "ZIP".
            tiff_codec (str, optional): The TIFF codec. Defaults to "DEFLATE".
            view_transform (str, optional): The view transform. Defaults to "Standard".

        Returns:
            str: The filepath of the image.
        """
        scene = Scene.new_scene(name="save_image")
        image_name = image.name

        if not name:
            name = image.name

        settings = scene.render.image_settings
        settings.file_format = file_format
        settings.color_mode = "RGB" if file_format == "JPEG" else color_mode
        settings.color_depth = "32" if file_format == "HDR" else color_depth
        settings.compression = compression
        settings.quality = quality
        settings.exr_codec = exr_codec
        settings.tiff_codec = tiff_codec
        scene.view_settings.view_transform = view_transform
        filepath = os.path.join(path, f"{name}{scene.render.file_extension}")
        image.save_render(filepath=filepath, scene=scene)
        bpy.data.scenes.remove(scene)
        image.name = image_name

        return filepath


    # Queue for expected renames performed at the end of the bake
    # Stored at module level to survive during the bake lifetime
    _expected_renames = []

    @staticmethod
    def enqueue_expected_rename(filepath: str, expected_base: str) -> None:
        """Enqueue an expected rename to be flushed later.

        Stores the tuple (filepath, expected_base) for later processing by
        `flush_expected_renames`.
        """
        try:
            Image._expected_renames.append((filepath, expected_base))
            print(f"QB_DEBUG enqueue_expected_rename: queued '{filepath}' -> '{expected_base}'")
        except Exception as e:
            print(f"QB_DEBUG enqueue_expected_rename: failed to enqueue '{filepath}' -> '{expected_base}': {e}")

    @staticmethod
    def flush_expected_renames() -> None:
        """Flush all enqueued expected renames.

        This attempts to rename files on disk to match the expected base names.
        Entries containing the `<UDIM>` placeholder are skipped because they
        correspond to multiple files.
        """
        try:
            import os
            import glob

            if not Image._expected_renames:
                return

            queue = list(Image._expected_renames)
            Image._expected_renames.clear()

            for filepath, expected_base in queue:
                try:
                    directory, filename = os.path.split(filepath)
                    base, ext = os.path.splitext(filename)

                    exp_base = os.path.splitext(expected_base)[0]

                    if "<UDIM>" in exp_base:
                        print(f"QB_DEBUG flush_expected_renames: skipping UDIM entry for '{filepath}' expected='{expected_base}'")
                        continue

                    target = os.path.join(directory, f"{exp_base}{ext}")

                    if base == exp_base:
                        # already correct
                        continue

                    # If target exists, remove it to allow overwrite
                    if os.path.exists(target):
                        try:
                            os.remove(target)
                        except Exception:
                            print(f"QB_DEBUG flush_expected_renames: cannot remove existing target '{target}'")

                    # If original file missing, try to find a close match
                    if not os.path.exists(filepath):
                        pattern = os.path.join(directory, f"{base}*{ext}")
                        matches = glob.glob(pattern)
                        if matches:
                            filepath = matches[0]
                        else:
                            print(f"QB_DEBUG flush_expected_renames: source file not found '{filepath}'")
                            continue

                    os.rename(filepath, target)
                    print(f"QB_DEBUG flush_expected_renames: renamed '{filepath}' -> '{target}'")
                except Exception as e:
                    print(f"QB_DEBUG flush_expected_renames: failed for '{filepath}' expected='{expected_base}': {e}")
        except Exception as e:
            print(f"QB_DEBUG flush_expected_renames: fatal error: {e}")

    @staticmethod
    def get_image(name: str) -> bpy.types.Image:
        """Get image by name.

        Args:
            name (str): The name of the image to get.

        Returns:
            bpy.types.Image: The image.
        """
        return bpy.data.images.get(name)

    @staticmethod
    def load_image(filepath: str = bpy.app.tempdir, check_existing: bool = True) -> bpy.types.Image:
        """Load the image.

        Args:
            filepath (str, optional): The path to the image. Defaults to bpy.app.tempdir.
            check_existing (bool, optional): If True, check if the image exists. Defaults to True.

        Returns:
            bpy.types.Image: The image.
        """
        return bpy.data.images.load(filepath=bpy.path.abspath(filepath), check_existing=check_existing)
