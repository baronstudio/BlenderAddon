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
                        
                        # === DIMENSIONS SECTION ===
                        dim_box = sub.box()
                        dim_box.label(text="Dimensions:", icon='DRIVER_DISTANCE')
                        try:
                            dtext = (item.dimensions or '').strip()
                            if not dtext:
                                dim_box.label(text="(empty)")
                            else:
                                # split on semicolons or newlines and show one value per line
                                parts = [p.strip() for p in re.split(r"[;\n]+", dtext) if p.strip()]
                                if len(parts) > 1:
                                    for p in parts:
                                        dim_box.label(text=p)
                                else:
                                    # fallback single-line display
                                    dim_box.label(text=dtext)
                        except Exception:
                            dim_box.label(text=f"Dimensions: {item.dimensions}")
                        
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
                        
                        # Debug: log des propriétés pour identifier le problème
                        try:
                            has_attr = hasattr(item, 'topology_result')
                            topo_obj = getattr(item, 'topology_result', None) if has_attr else None
                            success = topo_obj.analysis_success if topo_obj else False
                            print(f"[DEBUG PANEL] Item '{item.name}': has_topology_result={has_attr}, obj_exists={topo_obj is not None}, success={success}")
                        except Exception as e:
                            print(f"[DEBUG PANEL] Erreur debug pour '{item.name}': {e}")
                        
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
