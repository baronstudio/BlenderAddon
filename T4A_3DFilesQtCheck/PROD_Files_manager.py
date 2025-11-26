import os
import bpy
import threading
import time
import json
import logging

from typing import List


logger = logging.getLogger('T4A.FilesManager')
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG)


def _gather_files(path: str, exts: List[str]) -> List[str]:
    found = []
    if not path:
        return found
    for root, dirs, files in os.walk(path):
        for f in files:
            fn = f.lower()
            for e in exts:
                if fn.endswith(e):
                    found.append(os.path.join(root, f))
                    break
    return found


def _import_file(filepath: str) -> bool:
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.fbx':
            bpy.ops.import_scene.fbx(filepath=filepath)
        elif ext in ('.glb', '.gltf'):
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif ext == '.obj':
            bpy.ops.import_scene.obj(filepath=filepath)
        elif ext == '.stl':
            bpy.ops.import_mesh.stl(filepath=filepath)
        elif ext == '.abc':
            bpy.ops.wm.alembic_import(filepath=filepath)
        elif ext == '.usd':
            try:
                bpy.ops.wm.usd_import(filepath=filepath)
            except Exception:
                # try generic import if different operator
                bpy.ops.import_scene.usd(filepath=filepath)
        elif ext == '.blend':
            # Append all objects from the .blend file (non-destructive)
            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                data_to.objects = data_from.objects
            for obj in data_to.objects:
                if obj is not None:
                    bpy.context.collection.objects.link(obj)
        else:
            # unknown extension
            return False
        return True
    except Exception as e:
        logger.error("[T4A] Erreur d'import pour %s: %s", filepath, e)
        return False


class T4A_OT_ScanAndImport(bpy.types.Operator):
    bl_idname = "t4a.scan_directory"
    bl_label = "Scan et importer"
    bl_description = "Scanner le répertoire défini et proposer l'import des fichiers 3D trouvés"

    files_count: bpy.props.IntProperty(name="Files Count", default=0)

    def invoke(self, context, event):
        addon_name = __package__ or "T4A_3DFilesQtCheck"
        prefs = None
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        path = getattr(prefs, 'scan_path', '') if prefs is not None else ''
        exts = ['.fbx', '.glb', '.gltf', '.obj', '.blend', '.abc', '.usd', '.stl']
        files = _gather_files(path, exts)
        self.files_count = len(files)
        self._files_list = files

        if self.files_count == 0:
            self.report({'INFO'}, "Aucun fichier trouvé dans le chemin configuré.")
            return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Nombre de fichiers trouvés: {self.files_count}")
        layout.label(text="Souhaitez-vous importer tous ces fichiers dans la scène actuelle ?")

    def execute(self, context):
        # Run scene setup before importing files
        try:
            result = bpy.ops.t4a.setup_scene(targetVolumCube=1.0)
            # operator returns a set-like value; check for FINISHED
            if result != {'FINISHED'}:
                self.report({'WARNING'}, "SetupScene cancelled or failed — import aborted.")
                return {'CANCELLED'}
        except Exception:
            self.report({'WARNING'}, "SetupScene call failed — import aborted.")
            return {'CANCELLED'}

        imported = 0
        failed = 0
        for f in getattr(self, '_files_list', []):
            # Use the operator that imports the file and places contents into a collection
            try:
                res = bpy.ops.t4a.import_file_to_collection(filepath=f)
                ok = (res == {'FINISHED'})
            except Exception:
                ok = False
            if ok:
                imported += 1
            else:
                failed += 1

        # store results into scene props for UI reporting
        try:
            scene = context.scene
            scene.t4a_last_imported_count = imported
            scene.t4a_last_import_failed = failed
        except Exception:
            pass

        self.report({'INFO'}, f"Importés: {imported}, Échecs: {failed}")
        return {'FINISHED'}


classes = (
    T4A_OT_ScanAndImport,
)


def _find_layer_collection(layer_coll, coll_name):
    """Recursively find LayerCollection matching coll_name."""
    if layer_coll.collection.name == coll_name:
        return layer_coll
    for child in layer_coll.children:
        found = _find_layer_collection(child, coll_name)
        if found:
            return found
    return None


class T4A_OT_SetupScene(bpy.types.Operator):
    bl_idname = "t4a.setup_scene"
    bl_label = "Setup Scene"
    bl_description = "Nettoie la scène active et crée un volume de référence"

    targetVolumCube: bpy.props.FloatProperty(
        name="Target Volume Cube",
        description="Taille du cube de référence en mètres",
        default=1.0,
        min=0.001,
        unit='LENGTH'
    )

    def execute(self, context):
        try:
            # 1) Delete all objects
            for obj in list(bpy.data.objects):
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass

            # 2) Unlink and remove collections under the scene collection
            scene = context.scene
            root_coll = scene.collection
            # unlink child collections
            for child in list(root_coll.children):
                try:
                    root_coll.children.unlink(child)
                except Exception:
                    pass
                try:
                    bpy.data.collections.remove(child)
                except Exception:
                    pass

            # 3) Purge orphan data (best effort)
            try:
                bpy.ops.outliner.orphans_purge(do_recursive=True)
            except Exception:
                # fallback: try without args
                try:
                    bpy.ops.outliner.orphans_purge()
                except Exception:
                    pass

            # 4) Create support collection
            coll_name = "Check_Support_Helpers"
            coll = bpy.data.collections.get(coll_name)
            if coll is None:
                coll = bpy.data.collections.new(coll_name)
            # link to scene collection if not already
            if coll.name not in [c.name for c in root_coll.children]:
                try:
                    root_coll.children.link(coll)
                except Exception:
                    pass

            # 5) Create cube of given size and place at ground so base at Z=0
            size = float(self.targetVolumCube)
            zloc = size / 4.0
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, zloc))
            obj = context.active_object
            if obj is None:
                # try last created
                obj = bpy.context.object
            if obj is not None:
                # scale to target size
                obj.scale = (size / 2.0, size / 2.0, size / 2.0)
                obj.name = "VolumeRef"
                try:
                    obj.display_type = 'WIRE'
                except Exception:
                    try:
                        obj.show_wire = True
                    except Exception:
                        pass

                # unlink from other collections and link to support collection
                for c in list(obj.users_collection):
                    try:
                        c.objects.unlink(obj)
                    except Exception:
                        pass
                try:
                    coll.objects.link(obj)
                except Exception:
                    pass

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"SetupScene failed: {e}")
            return {'CANCELLED'}


class T4A_OT_ImportFileToCollection(bpy.types.Operator):
    bl_idname = "t4a.import_file_to_collection"
    bl_label = "Import File To Collection"
    bl_description = "Importe un fichier et place ses objets dans une collection nommée selon le fichier"

    filepath: bpy.props.StringProperty(name="Filepath", subtype='FILE_PATH')

    def execute(self, context):
        filepath = self.filepath
        before_ids = {id(o) for o in bpy.data.objects}
        ok = _import_file(filepath)
        if not ok:
            return {'CANCELLED'}

        # find newly created objects
        new_objs = [o for o in bpy.data.objects if id(o) not in before_ids]

        # build collection name: EXT_filename (ext uppercased)
        base = os.path.basename(filepath)
        ext = os.path.splitext(base)[1].lstrip('.').upper() or 'FILE'
        coll_name = f"{ext}_{base}"

        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            coll = bpy.data.collections.new(coll_name)
        # link to scene collection root
        try:
            root_coll = context.scene.collection
            if coll.name not in [c.name for c in root_coll.children]:
                root_coll.children.link(coll)
        except Exception:
            pass

        # move new objects into the collection
        for obj in new_objs:
            try:
                # unlink from other collections
                for uc in list(obj.users_collection):
                    try:
                        uc.objects.unlink(obj)
                    except Exception:
                        pass
                coll.objects.link(obj)
            except Exception:
                pass

        # Assign a color tag based on hash of name (cycle through available tags)
        try:
            tags = ['COLOR_01','COLOR_02','COLOR_03','COLOR_04','COLOR_05','COLOR_06','COLOR_07','COLOR_08','COLOR_09','COLOR_10','COLOR_11','COLOR_12']
            idx = abs(hash(coll_name)) % len(tags)
            if hasattr(coll, 'color_tag'):
                try:
                    coll.color_tag = tags[idx]
                except Exception:
                    pass
        except Exception:
            pass

        # After import, try to find a matching TXT/PDF with the same base name
        # in the configured scan path and request analysis if present.
        try:
            from . import PROD_Parameters
            addon_name = PROD_Parameters.__package__
            try:
                prefs = context.preferences.addons[addon_name].preferences
                base_path = prefs.scan_path
            except Exception:
                base_path = os.environ.get('SCAN_PATH', '')

            if base_path:
                stem = os.path.splitext(base)[0]
                for ext in ('.txt', '.pdf'):
                    candidate = os.path.join(base_path, stem + ext)
                    if os.path.exists(candidate):
                        try:
                            # call operator to analyze file; it will log/store results
                            bpy.ops.t4a.analyze_text_file(filepath=candidate)
                            logger.info("[T4A] Analyse lancée pour: %s", candidate)
                        except Exception as e:
                            logger.error("[T4A] Échec analyse pour %s: %s", candidate, e)
                        break
        except Exception as e:
            logger.error("[T4A] Recherche/analyse post-import échouée: %s", e)

        return {'FINISHED'}


# classes tuple will be defined at file end to include all operators


class T4A_OT_TestGeminiConnection(bpy.types.Operator):
    bl_idname = "t4a.test_gemini_connection"
    bl_label = "Test Gemini Connection"
    bl_description = "Test connection to Google Gemini (logs result to console)"

    def execute(self, context):
        try:
            from . import PROD_Parameters
            api_key = ''
            try:
                prefs = context.preferences.addons[PROD_Parameters.__package__].preferences
                api_key = prefs.google_api_key
                model_name = getattr(prefs, 'model_name', None)
            except Exception:
                # fallback to environment variable
                api_key = os.environ.get('GOOGLE_API_KEY', '')
                model_name = os.environ.get('MODEL_NAME', None)

            from . import PROD_gemini

            if model_name:
                res = PROD_gemini.test_connection(api_key, model=model_name)
            else:
                res = PROD_gemini.test_connection(api_key)
            logger.info('[T4A Gemini Test] result: %s', res)
            self.report({'INFO'}, 'Gemini test logged to console')
            return {'FINISHED'}
        except Exception as e:
            logger.error('[T4A Gemini Test] error: %s', e)
            self.report({'ERROR'}, f'Gemini test failed: {e}')
            return {'CANCELLED'}


class T4A_OT_AnalyzeTextFile(bpy.types.Operator):
    bl_idname = "t4a.analyze_text_file"
    bl_label = "Analyze Text/PDF File"
    bl_description = "Extract text from a TXT or PDF and ask Gemini to extract 3D dimensions"

    filepath: bpy.props.StringProperty(name="Filepath", subtype='FILE_PATH')

    def execute(self, context):
        filepath = self.filepath
        if not filepath or not os.path.exists(filepath):
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}

        # extract text
        text = ''
        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext == '.txt':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            elif ext == '.pdf':
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(filepath)
                    pages = []
                    for p in reader.pages:
                        try:
                            pages.append(p.extract_text() or '')
                        except Exception:
                            pages.append('')
                    text = '\n'.join(pages)
                except Exception:
                    self.report({'ERROR'}, 'PyPDF2 not available or failed to read PDF')
                    return {'CANCELLED'}
            else:
                self.report({'ERROR'}, 'Unsupported file type')
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f'Failed to read file: {e}')
            return {'CANCELLED'}

        # get API key
        try:
            from . import PROD_Parameters
            api_key = ''
            model_name = None
            try:
                prefs = context.preferences.addons[PROD_Parameters.__package__].preferences
                api_key = prefs.google_api_key
                model_name = getattr(prefs, 'model_name', None)
            except Exception:
                api_key = os.environ.get('GOOGLE_API_KEY', '')
                model_name = os.environ.get('MODEL_NAME', None)

            # Ensure model list is fresh before using model_name: if cache expired, refresh synchronously
            try:
                TTL = 3600
                now = time.time()
                ts = float(getattr(prefs, 'model_list_ts', 0) or 0)
                if now - ts >= TTL:
                    # refresh synchronously using PROD_gemini.list_models
                    try:
                        from . import PROD_gemini
                        res = PROD_gemini.list_models(api_key)
                        if res.get('success'):
                            detail = res.get('detail')
                            names = []
                            try:
                                if isinstance(detail, dict):
                                    for m in detail.get('models', []) or []:
                                        n = m.get('name') if isinstance(m, dict) else str(m)
                                        if n:
                                            short = n.split('/')[-1]
                                            names.append(short)
                                if not names and isinstance(detail, list):
                                    for x in detail:
                                        names.append(str(x))
                            except Exception:
                                names = []
                            if names:
                                try:
                                    prefs.model_list_json = json.dumps(names)
                                    prefs.model_list_ts = time.time()
                                    # if no model_name, set to first
                                    try:
                                        if not getattr(prefs, 'model_name', None):
                                            prefs.model_name = names[0]
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                    except Exception:
                        # ignore refresh errors; we'll proceed with existing model_name
                        pass
                    # re-read model_name after refresh
                    try:
                        model_name = getattr(prefs, 'model_name', None)
                    except Exception:
                        pass
            except Exception:
                # ignore any unexpected errors in the freshness/refresh block
                pass

            from . import PROD_gemini

            if model_name:
                res = PROD_gemini.analyze_text_dimensions(api_key, text, model=model_name)
            else:
                res = PROD_gemini.analyze_text_dimensions(api_key, text)
            detail = res.get('detail')
            # coerce detail to string
            if isinstance(detail, dict):
                detail_str = str(detail)
            else:
                detail_str = str(detail)

            # store into scene collection
            try:
                scene = context.scene
                item = scene.t4a_dimensions.add()
                item.name = os.path.basename(filepath)
                item.dimensions = detail_str
                item.expanded = False
            except Exception:
                pass

            logger.info('[T4A Analyze] result: %s', res)
            # If server returned 404, give a helpful report to the user
            status = res.get('status_code')
            if status == 404:
                self.report({'ERROR'}, "Analyse échouée (404). Vérifiez le 'Model Name' dans les préférences et que l'API Generative Language est activée pour votre projet.")
            else:
                self.report({'INFO'}, 'Analyze request sent; result logged')
            return {'FINISHED'}
        except Exception as e:
            logger.error('[T4A Analyze] error %s', e)
            self.report({'ERROR'}, f'Analyze failed: {e}')
            return {'CANCELLED'}


class T4A_OT_ListGeminiModels(bpy.types.Operator):
    bl_idname = "t4a.list_gemini_models"
    bl_label = "Lister les modèles Gemini"
    bl_description = "Interroge l'API Generative Language pour lister les modèles disponibles (logs)"

    def execute(self, context):
        try:
            from . import PROD_Parameters
            try:
                prefs = context.preferences.addons[PROD_Parameters.__package__].preferences
                api_key = prefs.google_api_key
            except Exception:
                prefs = None
                api_key = os.environ.get('GOOGLE_API_KEY', '')

            if not api_key:
                self.report({'ERROR'}, 'No API key provided')
                return {'CANCELLED'}

            import json
            import urllib.request
            import urllib.error

            # Use the v1beta models listing endpoint; ensure we use the API key from prefs
            API_KEY = (api_key or '').strip()
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

            # Reset stored model list before fetching so UI sees a clean state
            try:
                if prefs is not None:
                    prefs.model_list_json = '[]'
                    prefs.model_list_ts = 0.0
            except Exception:
                pass

            try:
                logger.debug("Récupération de la liste des modèles...")
                with urllib.request.urlopen(url) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    logger.debug("--- MODÈLES DISPONIBLES POUR VOTRE CLÉ ---")
                    found_any = False
                    seen = set()
                    ordered = []
                    for model in data.get('models', []):
                        # Keep only models that support generateContent
                        if "generateContent" in model.get('supportedGenerationMethods', []):
                            raw_name = model.get('name', '')
                            if not raw_name:
                                continue
                            # extract the last path segment after any '/'
                            short_name = raw_name.split('/')[-1].strip()
                            if not short_name:
                                continue
                            # avoid duplicates while preserving order
                            if short_name in seen:
                                continue
                            seen.add(short_name)
                            ordered.append(short_name)
                            logger.debug("Nom à utiliser : %s", short_name)
                            found_any = True
                    logger.debug("------------------------------------------")

                    if not found_any:
                        logger.debug("Aucun modèle compatible 'generateContent' trouvé.")
                    else:
                        # store results into addon preferences so EnumProperty updates
                        try:
                            if prefs is not None:
                                import json as _json
                                prefs.model_list_json = _json.dumps(ordered)
                                prefs.model_list_ts = time.time()
                                # Optionally set model_name if not set or not in list
                                try:
                                    cur = getattr(prefs, 'model_name', None)
                                    if not cur and ordered:
                                        prefs.model_name = ordered[0]
                                except Exception:
                                    pass
                        except Exception as e:
                            logger.error('[T4A List Models] Failed to save model list to preferences: %s', e)

                self.report({'INFO'}, 'Liste modèles récupérée (voir console)')
                return {'FINISHED'}
            except urllib.error.HTTPError as e:
                body = ''
                try:
                    body = e.read().decode('utf-8')
                except Exception:
                    pass
                logger.error("Erreur HTTP : %s - %s", getattr(e, 'code', ''), getattr(e, 'reason', ''))
                if body:
                    logger.error(body)
                self.report({'ERROR'}, f"HTTP Error {getattr(e, 'code', 'unknown')}")
                return {'CANCELLED'}
            except Exception as e:
                logger.error('Erreur : %s', e)
                self.report({'ERROR'}, f"Erreur: {e}")
                return {'CANCELLED'}
        except Exception as e:
            logger.error('[T4A List Models] error: %s', e)
            self.report({'ERROR'}, f'Listing failed: {e}')
            return {'CANCELLED'}


class T4A_OT_FindMatchingTextAndAnalyze(bpy.types.Operator):
    bl_idname = "t4a.find_and_analyze_matching"
    bl_label = "Find matching TXT/PDF and analyze"
    bl_description = "Look for TXT/PDF files with same base name as imported 3D files and analyze them"

    def execute(self, context):
        try:
            from . import PROD_Parameters
            addon_name = PROD_Parameters.__package__
            try:
                prefs = context.preferences.addons[addon_name].preferences
                base_path = prefs.scan_path
            except Exception:
                base_path = os.environ.get('SCAN_PATH', '')

            if not base_path:
                self.report({'ERROR'}, 'No scan path configured')
                return {'CANCELLED'}

            # iterate imported collections in scene root
            scene = context.scene
            root_coll = scene.collection
            processed = 0
            for coll in list(root_coll.children):
                # if collection name has an underscore, assume format EXT_basename
                parts = coll.name.split('_', 1)
                if len(parts) != 2:
                    continue
                base = parts[1]
                stem = os.path.splitext(base)[0]
                # search for stem.txt or stem.pdf
                found = None
                for ext in ('.txt', '.pdf'):
                    candidate = os.path.join(base_path, stem + ext)
                    if os.path.exists(candidate):
                        found = candidate
                        break
                if found:
                    # call analyze operator
                    try:
                        bpy.ops.t4a.analyze_text_file(filepath=found)
                        processed += 1
                    except Exception:
                        pass

            self.report({'INFO'}, f'Processed {processed} matching text files')
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f'Find/Analyze failed: {e}')
            return {'CANCELLED'}




def register():
    import traceback
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            logger.debug("[T4A Register] Registered %s", getattr(cls, '__name__', str(cls)))
        except ValueError as ve:
            msg = str(ve)
            if 'already registered' in msg:
                logger.debug("[T4A Register] Skipping already-registered %s", getattr(cls, '__name__', str(cls)))
            else:
                logger.debug("[T4A Register] ValueError registering %s: %s", getattr(cls, '__name__', str(cls)), msg)
                traceback.print_exc()
        except Exception:
            logger.debug("[T4A Register] Failed to register %s", getattr(cls, '__name__', str(cls)))
            traceback.print_exc()


def unregister():
    import traceback
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            logger.debug("[T4A Unregister] Unregistered %s", getattr(cls, '__name__', str(cls)))
        except ValueError as ve:
            msg = str(ve)
            if 'not registered' in msg or 'is not registered' in msg:
                logger.debug("[T4A Unregister] Skipping not-registered %s", getattr(cls, '__name__', str(cls)))
            else:
                logger.debug("[T4A Unregister] ValueError unregistering %s: %s", getattr(cls, '__name__', str(cls)), msg)
                traceback.print_exc()
        except Exception:
            logger.debug("[T4A Unregister] Failed to unregister %s", getattr(cls, '__name__', str(cls)))
            traceback.print_exc()


classes = (
    T4A_OT_ScanAndImport,
    T4A_OT_SetupScene,
    T4A_OT_ImportFileToCollection,
    T4A_OT_TestGeminiConnection,
    T4A_OT_AnalyzeTextFile,
    T4A_OT_ListGeminiModels,
    T4A_OT_FindMatchingTextAndAnalyze,
)
