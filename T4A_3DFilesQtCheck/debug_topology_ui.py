import bpy

def debug_topology_results():
    """Debug des résultats de topologie dans les panels."""
    print("\n=== DEBUG TOPOLOGY RESULTS ===")
    
    scene = bpy.context.scene
    dims = getattr(scene, 't4a_dimensions', None)
    
    if dims is None:
        print("❌ Pas de propriétés t4a_dimensions trouvées dans la scène")
        return
    
    print(f"✅ Propriétés t4a_dimensions trouvées: {len(dims)} entrées")
    
    for i, item in enumerate(dims):
        print(f"\n--- Entrée {i+1}: {item.name} ---")
        
        # Vérifier si topology_result existe
        if hasattr(item, 'topology_result'):
            topo_res = item.topology_result
            if topo_res:
                print(f"  ✅ topology_result existe")
                print(f"  - analysis_success: {topo_res.analysis_success}")
                print(f"  - analysis_error: '{topo_res.analysis_error}'")
                
                if topo_res.analysis_success:
                    print(f"  - total_vertices: {topo_res.total_vertices}")
                    print(f"  - total_polygons: {topo_res.total_polygons}")
                    print(f"  - has_manifold_issues: {topo_res.has_manifold_issues}")
                    print(f"  - manifold_error_count: {topo_res.manifold_error_count}")
                    print(f"  - has_normal_issues: {topo_res.has_normal_issues}")
                    print(f"  - inverted_faces_count: {topo_res.inverted_faces_count}")
                    print(f"  - normal_consistency: {topo_res.normal_consistency}")
                    print(f"  - has_isolated_vertices: {topo_res.has_isolated_vertices}")
                    print(f"  - isolated_vertices_count: {topo_res.isolated_vertices_count}")
                    print(f"  - has_duplicate_vertices: {topo_res.has_duplicate_vertices}")
                    print(f"  - duplicate_vertices_count: {topo_res.duplicate_vertices_count}")
                    print(f"  - has_vertex_colors: {topo_res.has_vertex_colors}")
                    print(f"  - vertex_color_layers_count: {topo_res.vertex_color_layers_count}")
                    print(f"  - quads_percentage: {topo_res.quads_percentage}")
                    print(f"  - triangles_percentage: {topo_res.triangles_percentage}")
                    print(f"  - ngons_percentage: {topo_res.ngons_percentage}")
                else:
                    print(f"  ❌ Analyse échouée: {topo_res.analysis_error}")
            else:
                print(f"  ❌ topology_result est None/vide")
        else:
            print(f"  ❌ topology_result n'existe pas")
        
        # Vérifier les autres propriétés pour comparaison
        if hasattr(item, 'uv_result') and item.uv_result:
            print(f"  📝 uv_result.analysis_success: {item.uv_result.analysis_success}")
        if hasattr(item, 'texture_result') and item.texture_result:
            print(f"  📝 texture_result.analysis_success: {item.texture_result.analysis_success}")

def debug_collections():
    """Debug des collections dans la scène."""
    print("\n=== DEBUG COLLECTIONS ===")
    
    # Collections de niveau racine
    root_collections = [coll for coll in bpy.data.collections if coll.name not in [c.children for c in bpy.data.collections for c in c.children]]
    print(f"Collections racine: {len(root_collections)}")
    
    for coll in bpy.data.collections:
        print(f"Collection: '{coll.name}'")
        print(f"  - Objets: {len(coll.objects)}")
        if len(coll.objects) > 0:
            print(f"  - Premier objet: {coll.objects[0].name}")

if __name__ == "__main__":
    debug_topology_results()
    debug_collections()