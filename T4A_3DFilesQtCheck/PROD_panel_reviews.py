import bpy
import re

class T4A_PT_PROD_FilesReviews(bpy.types.Panel):
    bl_label = "Files Reviews"
    bl_idname = "T4A_PT_PROD_files_reviews"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A_3DFilesQtCheck'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Files Reviews")
        layout.separator()

        # --- General Scene Info box ---
        box = layout.box()
        box.label(text="General Scene Info")
        try:
            scene = context.scene
            system = getattr(scene, 't4a_unit_system', None)
            scale = getattr(scene, 't4a_scale_length', None)
            if not system:
                try:
                    us = scene.unit_settings
                    system = getattr(us, 'system', 'unknown')
                except Exception:
                    system = 'unknown'
            if scale is None or (isinstance(scale, float) and scale == 0.0):
                try:
                    us = scene.unit_settings
                    scale = getattr(us, 'scale_length', 'n/a')
                except Exception:
                    scale = 'n/a'
            box.label(text=f"Unit System: {system}")
            box.label(text=f"Scale Length: {scale}")
            
            # Add warning if scale is not 1.0
            if isinstance(scale, (int, float)) and scale != 1.0:
                warning_box = box.box()
                warning_box.alert = True
                if scale > 1.0:
                    warning_box.label(text=f"⚠ Échelle > 1.0: modèles {scale}x plus grands", icon='ERROR')
                else:
                    warning_box.label(text=f"⚠ Échelle < 1.0: modèles {scale}x plus petits", icon='ERROR')
                warning_box.label(text="Les BoundingBoxes sont ajustées automatiquement")
                
        except Exception:
            box.label(text="Scene unit info unavailable")

        # --- Import Summary box ---
        ibox = layout.box()
        ibox.label(text="Import Summary")
        try:
            scene = context.scene
            imported = getattr(scene, 't4a_last_imported_count', None)
            failed = getattr(scene, 't4a_last_import_failed', None)
            if imported is None:
                imported = 0
            if failed is None:
                failed = 0
            ibox.label(text=f"Last Imported: {imported}")
            ibox.label(text=f"Last Failed: {failed}")
        except Exception:
            ibox.label(text="No import information available")

        # --- Per-file Dimension Results (collapsible boxes, closed by default) ---
        try:
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            if dims is not None and len(dims) > 0:
                for item in dims:
                    row = layout.row()
                    # draw a simple expander using the BoolProperty on the item
                    row.prop(item, 'expanded', icon='TRIA_DOWN' if item.expanded else 'TRIA_RIGHT', emboss=False, text=item.name)
                    if item.expanded:
                        sub = layout.box()
                        
                        # === DIMENSIONS SECTION AMÉLIORÉE ===
                        dim_box = sub.box()
                        dim_box.label(text="Dimensions:", icon='DRIVER_DISTANCE')
                        
                        try:
                            # Récupérer l'unité de la scène (déjà calculée en haut du panel)
                            scene = context.scene
                            unit_system = getattr(scene, 't4a_unit_system', None)
                            if not unit_system:
                                try:
                                    us = scene.unit_settings
                                    unit_system = getattr(us, 'system', 'METRIC')
                                except Exception:
                                    unit_system = 'METRIC'
                            
                            # Déterminer l'unité d'affichage et la précision
                            if unit_system == 'IMPERIAL':
                                unit_display = "in"
                                precision = 3  # 3 décimales pour l'impérial
                                volume_unit_cubic = "in³"
                            else:  # METRIC ou autre
                                # Récupérer l'unité de longueur réelle
                                try:
                                    us = scene.unit_settings
                                    length_unit = getattr(us, 'length_unit', 'CENTIMETERS')
                                    # Mapper les unités Blender vers l'affichage
                                    unit_mapping = {
                                        'KILOMETERS': 'km',
                                        'METERS': 'm',
                                        'CENTIMETERS': 'cm',
                                        'MILLIMETERS': 'mm',
                                        'MICROMETERS': 'µm'
                                    }
                                    unit_display = unit_mapping.get(length_unit, 'cm')
                                    # Unité de volume correspondante
                                    volume_mapping = {
                                        'km': 'km³',
                                        'm': 'm³', 
                                        'cm': 'cm³',
                                        'mm': 'mm³',
                                        'µm': 'µm³'
                                    }
                                    volume_unit_cubic = volume_mapping.get(unit_display, 'cm³')
                                except Exception:
                                    unit_display = "cm"
                                    volume_unit_cubic = "cm³"
                                precision = 2  # 2 décimales pour le métrique
                            
                            # Gestion du statut de tolérance (couleur de fond)
                            tolerance_status = getattr(item, 'tolerance_status', 'NO_AI_DATA')
                            
                            # Créer une ligne avec deux colonnes
                            dim_row = dim_box.row()
                            
                            # === COLONNE GAUCHE: DIMENSIONS MODÈLE 3D RÉELLES ===
                            left_col = dim_row.column()
                            left_col.scale_x = 0.5
                            
                            left_header = left_col.box()
                            left_header.label(text="Modèle 3D (BBox)", icon='MESH_CUBE')
                            
                            # Récupérer les dimensions réelles de la collection
                            file_name = item.name
                            collection_name = ""
                            actual_dimensions = None
                            
                            # Trouver la collection correspondante
                            for coll in bpy.data.collections:
                                if file_name in coll.name or coll.name in file_name:
                                    collection_name = coll.name
                                    break
                            
                            if collection_name:
                                # Calculer les dimensions de la bounding box
                                try:
                                    collection = bpy.data.collections.get(collection_name)
                                    if collection and collection.objects:
                                        # Récupérer les objets mesh de la collection
                                        mesh_objects = [obj for obj in collection.objects if obj.type == 'MESH' and obj.data]
                                        
                                        if mesh_objects:
                                            from mathutils import Vector
                                            
                                            # Calculer la bounding box globale
                                            min_coords = Vector((float('inf'), float('inf'), float('inf')))
                                            max_coords = Vector((float('-inf'), float('-inf'), float('-inf')))
                                            
                                            for obj in mesh_objects:
                                                bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
                                                for corner in bbox_corners:
                                                    for i in range(3):
                                                        min_coords[i] = min(min_coords[i], corner[i])
                                                        max_coords[i] = max(max_coords[i], corner[i])
                                            
                                            # Calculer les dimensions
                                            dimensions = max_coords - min_coords
                                            
                                            # Appliquer l'échelle de la scène si nécessaire
                                            scene = context.scene
                                            scale_factor = getattr(scene, 't4a_scale_length', 1.0)
                                            if isinstance(scale_factor, (int, float)) and scale_factor != 1.0:
                                                dimensions *= scale_factor
                                            
                                            actual_dimensions = (dimensions.x, dimensions.y, dimensions.z)
                                except Exception as calc_error:
                                    print(f"Erreur calcul dimensions: {calc_error}")
                            
                            # Affichage des dimensions réelles
                            if actual_dimensions:
                                left_col.label(text=f"L: {actual_dimensions[0]:.{precision}f} {unit_display}")
                                left_col.label(text=f"H: {actual_dimensions[1]:.{precision}f} {unit_display}")
                                left_col.label(text=f"P: {actual_dimensions[2]:.{precision}f} {unit_display}")
                                # Afficher le volume avec unité appropriée
                                volume = actual_dimensions[0] * actual_dimensions[1] * actual_dimensions[2]
                                if unit_system == 'IMPERIAL':
                                    # Volume en cubic inches
                                    if volume > 61.024:  # 1 litre = 61.024 cubic inches
                                        left_col.label(text=f"Vol: {volume/61.024:.1f} L", icon='INFO')
                                    else:
                                        left_col.label(text=f"Vol: {volume:.1f} {volume_unit_cubic}", icon='INFO')
                                else:
                                    # Volume métrique - adapter selon l'unité
                                    if unit_display == 'cm' and volume > 1000:
                                        left_col.label(text=f"Vol: {volume/1000:.1f} L", icon='INFO')
                                    elif unit_display == 'm' and volume > 0.001:
                                        left_col.label(text=f"Vol: {volume*1000:.1f} L", icon='INFO')
                                    else:
                                        left_col.label(text=f"Vol: {volume:.1f} {volume_unit_cubic}", icon='INFO')
                            else:
                                # Fallback: essayer d'utiliser les valeurs stockées
                                scene_width = getattr(item, 'scene_width', 0.0)
                                scene_height = getattr(item, 'scene_height', 0.0)
                                scene_depth = getattr(item, 'scene_depth', 0.0)
                                
                                if scene_width > 0 or scene_height > 0 or scene_depth > 0:
                                    left_col.label(text=f"L: {scene_width:.{precision}f} {unit_display}")
                                    left_col.label(text=f"H: {scene_height:.{precision}f} {unit_display}")
                                    left_col.label(text=f"P: {scene_depth:.{precision}f} {unit_display}")
                                else:
                                    na_box = left_col.box()
                                    na_box.enabled = False
                                    na_box.label(text="Modèle introuvable", icon='ERROR')
                                    if collection_name:
                                        na_box.label(text=f"Collection: {collection_name[:15]}")
                                    else:
                                        na_box.label(text="Aucune collection")
                            
                            # === COLONNE DROITE: DIMENSIONS IA ===
                            right_col = dim_row.column()
                            right_col.scale_x = 0.5
                            
                            right_header = right_col.box()
                            right_header.label(text="Dimensions IA", icon='FILE_TEXT')
                            
                            # Contenu IA dimensions
                            ai_success = getattr(item, 'ai_analysis_success', False)
                            ai_dimensions = getattr(item, 'ai_dimensions', '').strip()
                            ai_error = getattr(item, 'ai_analysis_error', '').strip()
                            
                            if ai_success and ai_dimensions:
                                # Affichage des dimensions IA trouvées
                                parts = [p.strip() for p in re.split(r"[;\n]+", ai_dimensions) if p.strip()]
                                if len(parts) > 1:
                                    for p in parts:
                                        right_col.label(text=p)
                                else:
                                    right_col.label(text=ai_dimensions)
                            elif ai_error:
                                # Erreur d'analyse IA
                                error_box = right_col.box()
                                error_box.alert = True
                                error_box.label(text="Erreur IA:", icon='ERROR')
                                # Limiter le texte d'erreur
                                error_text = ai_error[:30] + "..." if len(ai_error) > 30 else ai_error
                                error_box.label(text=error_text)
                            else:
                                # Fallback: utiliser l'ancienne propriété dimensions
                                dtext = (item.dimensions or '').strip()
                                if dtext:
                                    parts = [p.strip() for p in re.split(r"[;\n]+", dtext) if p.strip()]
                                    if len(parts) > 1:
                                        for p in parts:
                                            right_col.label(text=p)
                                    else:
                                        right_col.label(text=dtext)
                                else:
                                    # Pas de données IA du tout
                                    na_box = right_col.box()
                                    na_box.enabled = False
                                    na_box.label(text="Non disponible", icon='QUESTION')
                            
                            # === LIGNE DE STATUT DE COMPARAISON ===
                            # Calculer la comparaison en temps réel si on a les deux dimensions
                            if actual_dimensions and ai_success and ai_dimensions:
                                # Essayer de parser les dimensions IA pour la comparaison
                                try:
                                    from . import PROD_dimension_analyzer
                                    ai_parsed = PROD_dimension_analyzer.parse_ai_dimensions(ai_dimensions)
                                    
                                    if ai_parsed:
                                        # Calculer la différence en temps réel
                                        diff_percent = PROD_dimension_analyzer.calculate_dimension_difference(ai_parsed, actual_dimensions)
                                        real_status = PROD_dimension_analyzer.determine_tolerance_status(diff_percent)
                                        
                                        status_row = dim_box.row()
                                        
                                        if real_status == 'OK':
                                            status_row.label(text=f"✓ Tolérance OK ({diff_percent:.1f}%)", icon='CHECKMARK')
                                        elif real_status == 'WARNING':
                                            warn_box = status_row.box()
                                            warn_box.alert = True
                                            warn_box.label(text=f"⚠ Écart {diff_percent:.1f}%", icon='ERROR')
                                        elif real_status == 'ERROR':
                                            error_box = status_row.box()
                                            error_box.alert = True
                                            error_box.label(text=f"✗ Écart critique {diff_percent:.1f}%", icon='CANCEL')
                                        
                                        # Affichage des informations de permutation si disponibles
                                        permutation_applied = getattr(item, 'permutation_applied', False)
                                        if permutation_applied:
                                            mapping_method = getattr(item, 'mapping_method', 'auto_permutation')
                                            confidence = getattr(item, 'confidence_level', 'LOW')
                                            original_diff = getattr(item, 'original_difference', 0.0)
                                            
                                            perm_row = dim_box.row()
                                            perm_row.scale_y = 0.8
                                            
                                            # Icône selon le niveau de confiance
                                            confidence_icon = {'HIGH': 'CHECKMARK', 'MEDIUM': 'ERROR', 'LOW': 'CANCEL'}.get(confidence, 'QUESTION')
                                            confidence_color = confidence == 'HIGH'
                                            
                                            if confidence_color:
                                                perm_row.label(text=f"🔄 Permutation appliquée ({original_diff:.1f}% → {diff_percent:.1f}%)", icon=confidence_icon)
                                            else:
                                                warn_perm = perm_row.box()
                                                warn_perm.alert = confidence == 'LOW'
                                                warn_perm.label(text=f"🔄 Permutation ({original_diff:.1f}% → {diff_percent:.1f}%) - Confiance: {confidence}", icon=confidence_icon)
                                                
                                except Exception:
                                    # Fallback vers les valeurs stockées si le calcul échoue
                                    if tolerance_status in ['OK', 'WARNING', 'ERROR']:
                                        status_row = dim_box.row()
                                        diff_percentage = getattr(item, 'difference_percentage', 0.0)
                                        
                                        if tolerance_status == 'OK':
                                            status_row.label(text=f"✓ Tolérance OK ({diff_percentage:.1f}%)", icon='CHECKMARK')
                                        elif tolerance_status == 'WARNING':
                                            warn_box = status_row.box()
                                            warn_box.alert = True
                                            warn_box.label(text=f"⚠ Écart {diff_percentage:.1f}%", icon='ERROR')
                                        elif tolerance_status == 'ERROR':
                                            error_box = status_row.box()
                                            error_box.alert = True
                                            error_box.label(text=f"✗ Écart critique {diff_percentage:.1f}%", icon='CANCEL')
                                        
                                        # Affichage des informations de permutation depuis les données stockées
                                        permutation_applied = getattr(item, 'permutation_applied', False)
                                        if permutation_applied:
                                            perm_row = dim_box.row()
                                            perm_row.scale_y = 0.8
                                            original_diff = getattr(item, 'original_difference', 0.0)
                                            confidence = getattr(item, 'confidence_level', 'LOW')
                                            perm_row.label(text=f"🔄 Permutation: {original_diff:.1f}% → {diff_percentage:.1f}% (Confiance: {confidence})")
                                            
                            elif tolerance_status in ['OK', 'WARNING', 'ERROR'] and ai_success:
                                # Utiliser les valeurs stockées comme fallback
                                status_row = dim_box.row()
                                diff_percentage = getattr(item, 'difference_percentage', 0.0)
                                
                                if tolerance_status == 'OK':
                                    status_row.label(text=f"✓ Tolérance OK ({diff_percentage:.1f}%)", icon='CHECKMARK')
                                elif tolerance_status == 'WARNING':
                                    warn_box = status_row.box()
                                    warn_box.alert = True
                                    warn_box.label(text=f"⚠ Écart {diff_percentage:.1f}%", icon='ERROR')
                                elif tolerance_status == 'ERROR':
                                    error_box = status_row.box()
                                    error_box.alert = True
                                    error_box.label(text=f"✗ Écart critique {diff_percentage:.1f}%", icon='CANCEL')
                                
                                # Affichage des informations de permutation stockées
                                permutation_applied = getattr(item, 'permutation_applied', False)
                                if permutation_applied:
                                    perm_row = dim_box.row()
                                    perm_row.scale_y = 0.8
                                    original_diff = getattr(item, 'original_difference', 0.0)
                                    confidence = getattr(item, 'confidence_level', 'LOW')
                                    perm_row.label(text=f"🔄 Permutation appliquée: {original_diff:.1f}% → {diff_percentage:.1f}% (Confiance: {confidence})")
                            
                            # === BOUTON DE RECALCUL INTELLIGENT ===
                            recalc_row = dim_box.row()
                            recalc_row.scale_y = 1.2
                            
                            # Déterminer l'icône et le texte selon la situation
                            has_permutation = getattr(item, 'permutation_applied', False)
                            confidence = getattr(item, 'confidence_level', 'LOW')
                            
                            if has_permutation and confidence == 'HIGH':
                                btn_icon = 'CHECKMARK'
                                btn_text = "Optimisé"
                            elif has_permutation:
                                btn_icon = 'FILE_REFRESH'
                                btn_text = "Réoptimiser"
                            else:
                                btn_icon = 'MODIFIER'
                                btn_text = "Optimiser Mapping"
                            
                            recalc_op = recalc_row.operator("t4a.recalculate_dimensions", 
                                                          text=btn_text, 
                                                          icon=btn_icon)
                            
                            # Assigner le nom de collection au bouton
                            file_name = item.name
                            collection_name = ""
                            for coll in bpy.data.collections:
                                if file_name in coll.name:
                                    collection_name = coll.name
                                    break
                            if collection_name:
                                recalc_op.collection_name = collection_name
                                    
                        except Exception as e:
                            # Fallback en cas d'erreur
                            dim_box.alert = True
                            dim_box.label(text="Erreur d'affichage des dimensions")
                            dim_box.label(text=str(e)[:50])
                        
                        # === TEXTURES SECTION (dans le même sub-panel) ===
                        tex_box = sub.box()
                        tex_box.label(text="Textures:", icon='TEXTURE')
                        
                        if hasattr(item, 'texture_result') and item.texture_result:
                            tex_res = item.texture_result
                            
                            if tex_res.analysis_success:
                                # Row 1: Count and Size
                                row1 = tex_box.row()
                                row1.label(text=f"Nombre: {tex_res.texture_count}")
                                row1.label(text=f"Taille: {tex_res.total_size_kb:.1f} KB")
                                
                                # Row 2: Resolutions
                                if tex_res.max_resolution != "N/A" or tex_res.min_resolution != "N/A":
                                    row2 = tex_box.row()
                                    row2.label(text=f"Max: {tex_res.max_resolution}")
                                    row2.label(text=f"Min: {tex_res.min_resolution}")
                                
                                # Row 3: Processing info
                                if tex_res.extracted_count > 0 or tex_res.consolidated_count > 0:
                                    row3 = tex_box.row()
                                    if tex_res.extracted_count > 0:
                                        row3.label(text=f"Extraites: {tex_res.extracted_count}")
                                    if tex_res.consolidated_count > 0:
                                        row3.label(text=f"Consolidées: {tex_res.consolidated_count}")
                                
                                # Row 4: Directory path (if exists)
                                if tex_res.texture_directory:
                                    dir_row = tex_box.row()
                                    dir_name = tex_res.texture_directory.split('\\')[-1] if '\\' in tex_res.texture_directory else tex_res.texture_directory.split('/')[-1]
                                    dir_row.label(text=f"Dossier: {dir_name}", icon='FOLDER_REDIRECT')
                                
                                # Row 5: Consolidate button
                                btn_row = tex_box.row()
                                btn_op = btn_row.operator("t4a.consolidate_textures", text="Re-analyser Textures")
                            else:
                                # Erreur d'analyse des textures
                                tex_box.alert = True
                                tex_box.label(text="Erreur d'analyse")
                                if tex_res.analysis_error:
                                    error_text = tex_res.analysis_error[:50] + "..." if len(tex_res.analysis_error) > 50 else tex_res.analysis_error
                                    tex_box.label(text=error_text)
                                
                                # Bouton pour retenter l'analyse
                                retry_row = tex_box.row()
                                retry_op = retry_row.operator("t4a.consolidate_textures", text="Retenter Analyse")
                        else:
                            # Pas d'analyse de texture effectuée
                            tex_box.label(text="Analyse non effectuée")
                            
                            # Bouton pour lancer l'analyse
                            init_row = tex_box.row()
                            init_op = init_row.operator("t4a.consolidate_textures", text="Analyser Textures")
                        
                        # Logic commune pour tous les boutons de texture
                        file_name = item.name
                        collection_name = ""
                        for coll in bpy.data.collections:
                            if file_name in coll.name:
                                collection_name = coll.name
                                break
                        
                        # Appliquer le nom de collection aux opérateurs créés
                        if collection_name:
                            # Rechercher tous les opérateurs dans tex_box et leur assigner collection_name
                            # Note: cette logique sera exécutée par Blender lors du rendu
                            try:
                                if hasattr(item, 'texture_result') and item.texture_result:
                                    if item.texture_result.analysis_success:
                                        btn_op.collection_name = collection_name
                                    else:
                                        retry_op.collection_name = collection_name
                                else:
                                    init_op.collection_name = collection_name
                            except:
                                pass
                        
                        # === UV MAPPING SECTION ===
                        uv_box = sub.box()
                        uv_box.label(text="UV Mapping:", icon='UV')
                        
                        if hasattr(item, 'uv_result') and item.uv_result:
                            uv_res = item.uv_result
                            
                            if uv_res.analysis_success:
                                # Row 1: Faces et Layers
                                row1 = uv_box.row()
                                row1.label(text=f"Faces: {uv_res.total_faces}")
                                row1.label(text=f"Couches: {uv_res.uv_layers_count}")
                                
                                # Row 2: Status avec icônes
                                row2 = uv_box.row()
                                if uv_res.has_overlaps:
                                    row2.label(text=f"Overlaps: {uv_res.overlap_percentage:.1f}%", icon='ERROR')
                                else:
                                    row2.label(text="Overlaps: OK", icon='CHECKMARK')
                                
                                if uv_res.has_outside_uvs:
                                    row2.label(text=f"Outside: {uv_res.outside_percentage:.1f}%", icon='ERROR')
                                else:
                                    row2.label(text="Outside: OK", icon='CHECKMARK')
                                
                                # Row 3: Layout et UDIM
                                row3 = uv_box.row()
                                if uv_res.is_square:
                                    row3.label(text=f"Ratio: {uv_res.aspect_ratio:.2f} (carré)", icon='CHECKMARK')
                                else:
                                    row3.label(text=f"Ratio: {uv_res.aspect_ratio:.2f}", icon='INFO')
                                
                                if uv_res.uses_udim:
                                    row3.label(text=f"UDIM: {uv_res.udim_count} tiles", icon='TEXTURE')
                                else:
                                    row3.label(text="UDIM: Non", icon='MESH_PLANE')
                                
                                # Row 4: Bouton re-analyser
                                btn_row = uv_box.row()
                                uv_btn_op = btn_row.operator("t4a.analyze_uvs", text="Re-analyser UVs")
                                if collection_name:
                                    uv_btn_op.collection_name = collection_name
                            else:
                                # Erreur d'analyse UV
                                uv_box.alert = True
                                uv_box.label(text="Erreur d'analyse UV")
                                if uv_res.analysis_error:
                                    error_text = uv_res.analysis_error[:50] + "..." if len(uv_res.analysis_error) > 50 else uv_res.analysis_error
                                    uv_box.label(text=error_text)
                                
                                # Bouton pour retenter l'analyse
                                retry_row = uv_box.row()
                                retry_uv_op = retry_row.operator("t4a.analyze_uvs", text="Retenter Analyse UV")
                                if collection_name:
                                    retry_uv_op.collection_name = collection_name
                        else:
                            # Pas d'analyse UV effectuée
                            uv_box.label(text="Analyse non effectuée")
                            
                            # Bouton pour lancer l'analyse
                            init_row = uv_box.row()
                            init_uv_op = init_row.operator("t4a.analyze_uvs", text="Analyser UVs")
                            if collection_name:
                                init_uv_op.collection_name = collection_name
                        
                        # === TOPOLOGY SECTION ===
                        topology_box = sub.box()
                        topology_box.label(text="Topologie:", icon='MESH_DATA')
                        
                        if hasattr(item, 'topology_result'):
                            topo_res = item.topology_result
                            
                            # Vérifier si l'analyse a été tentée (success=True OU error non vide)
                            analysis_attempted = topo_res.analysis_success or (topo_res.analysis_error and topo_res.analysis_error.strip())
                            
                            if analysis_attempted:
                                if topo_res.analysis_success:
                                    # Row 1: Statistiques générales
                                    row1 = topology_box.row()
                                    row1.label(text=f"Vertices: {topo_res.total_vertices}")
                                    row1.label(text=f"Polygones: {topo_res.total_polygons}")
                                    
                                    # Row 2: Problèmes manifold et normales
                                    row2 = topology_box.row()
                                    if topo_res.has_manifold_issues:
                                        row2.label(text=f"Manifold: {topo_res.manifold_error_count} erreurs", icon='ERROR')
                                    else:
                                        row2.label(text="Manifold: OK", icon='CHECKMARK')
                                    
                                    if topo_res.has_normal_issues:
                                        row2.label(text=f"Normales: {topo_res.inverted_faces_count} inversées", icon='ERROR')
                                    else:
                                        row2.label(text=f"Normales: {topo_res.normal_consistency:.0f}%", icon='CHECKMARK')
                                    
                                    # Row 3: Vertices problématiques
                                    row3 = topology_box.row()
                                    if topo_res.has_isolated_vertices:
                                        row3.label(text=f"Isolés: {topo_res.isolated_vertices_count}", icon='ERROR')
                                    else:
                                        row3.label(text="Isolés: OK", icon='CHECKMARK')
                                    
                                    if topo_res.has_duplicate_vertices:
                                        row3.label(text=f"Doublons: {topo_res.duplicate_vertices_count}", icon='ERROR')
                                    else:
                                        row3.label(text="Doublons: OK", icon='CHECKMARK')
                                    
                                    # Row 4: Vertex colors et distribution
                                    row4 = topology_box.row()
                                    if topo_res.has_vertex_colors:
                                        row4.label(text=f"Colors: {topo_res.vertex_color_layers_count} couches", icon='COLOR')
                                    else:
                                        row4.label(text="Colors: Aucune", icon='MESH_PLANE')
                                    
                                    # Afficher la distribution des polygones de façon compacte
                                    if topo_res.total_polygons > 0:
                                        quad_pct = topo_res.quads_percentage
                                        tri_pct = topo_res.triangles_percentage
                                        ngon_pct = topo_res.ngons_percentage
                                        
                                        if quad_pct >= 50:
                                            row4.label(text=f"Quads: {quad_pct:.0f}%", icon='MESH_CUBE')
                                        elif tri_pct >= 50:
                                            row4.label(text=f"Tris: {tri_pct:.0f}%", icon='MESH_ICOSPHERE')
                                        else:
                                            row4.label(text=f"Mix: Q{quad_pct:.0f}/T{tri_pct:.0f}/N{ngon_pct:.0f}", icon='MESH_DATA')
                                    
                                    # Row 5: Bouton re-analyser
                                    btn_row = topology_box.row()
                                    topo_btn_op = btn_row.operator("t4a.analyze_topology", text="Re-analyser Topologie")
                                    if collection_name:
                                        topo_btn_op.collection_name = collection_name
                                else:
                                    # Erreur d'analyse topologie
                                    topology_box.alert = True
                                    topology_box.label(text="Erreur d'analyse topologie")
                                    if topo_res.analysis_error:
                                        error_text = topo_res.analysis_error[:50] + "..." if len(topo_res.analysis_error) > 50 else topo_res.analysis_error
                                        topology_box.label(text=error_text)
                                    
                                    # Bouton pour retenter l'analyse
                                    retry_row = topology_box.row()
                                    retry_topo_op = retry_row.operator("t4a.analyze_topology", text="Retenter Analyse Topologie")
                                    if collection_name:
                                        retry_topo_op.collection_name = collection_name
                            else:
                                topology_box.label(text="Analyse attendue mais non effectuée")
                        else:
                            # Pas d'analyse topologie effectuée
                            topology_box.label(text="Analyse non effectuée")
                            
                            # Bouton pour lancer l'analyse
                            init_row = topology_box.row()
                            init_topo_op = init_row.operator("t4a.analyze_topology", text="Analyser Topologie")
                            if collection_name:
                                init_topo_op.collection_name = collection_name
                        
                        # === TEXEL DENSITY SECTION ===
                        texel_box = sub.box()
                        texel_box.label(text="Texel Density:", icon='TEXTURE')
                        
                        # Vérifier si les UVs ont été analysées (prérequis pour texel density)
                        uv_analyzed = hasattr(item, 'uv_result') and item.uv_result and item.uv_result.analysis_success
                        
                        if uv_analyzed and hasattr(item, 'uv_result') and item.uv_result.has_texel_analysis:
                            uv_res = item.uv_result
                            
                            if uv_res.has_texel_analysis:
                                # Row 1: Densité moyenne et variance - utiliser l'unité de la scène
                                row1 = texel_box.row()
                                row1.label(text=f"Moyenne: {uv_res.average_texel_density:.1f} px/{unit_display}")
                                
                                # Afficher le statut avec l'icône appropriée
                                if uv_res.texel_density_status == 'GOOD':
                                    row1.label(text=f"Variance: {uv_res.texel_density_variance:.1f}%", icon='CHECKMARK')
                                elif uv_res.texel_density_status == 'WARNING':
                                    row1.label(text=f"Variance: {uv_res.texel_density_variance:.1f}%", icon='INFO')
                                else:  # ERROR
                                    row1.label(text=f"Variance: {uv_res.texel_density_variance:.1f}%", icon='ERROR')
                                
                                # Row 2: Min/Max densités - utiliser l'unité de la scène
                                row2 = texel_box.row()
                                row2.label(text=f"Min: {uv_res.min_texel_density:.1f} px/{unit_display}")
                                row2.label(text=f"Max: {uv_res.max_texel_density:.1f} px/{unit_display}")
                                
                                # Row 3: Bouton re-analyser
                                btn_row = texel_box.row()
                                texel_btn_op = btn_row.operator("t4a.analyze_texel_density", text="Re-analyser Texel Density")
                                if collection_name:
                                    texel_btn_op.collection_name = collection_name
                        
                        elif uv_analyzed:
                            # UVs analysées mais pas de texel density
                            texel_box.label(text="Analyse non effectuée")
                            
                            # Bouton pour lancer l'analyse
                            init_row = texel_box.row()
                            init_texel_op = init_row.operator("t4a.analyze_texel_density", text="Analyser Texel Density")
                            if collection_name:
                                init_texel_op.collection_name = collection_name
                        
                        else:
                            # UVs non analysées - prérequis manquant
                            texel_box.alert = True
                            texel_box.label(text="Analyse UV requise d'abord", icon='ERROR')
                            texel_box.label(text="Analysez les UVs avant le Texel Density")
                            
            else:
                layout.label(text="No dimension results available")
        except Exception:
            layout.label(text="Dimension results unavailable")


classes = (
    T4A_PT_PROD_FilesReviews,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
