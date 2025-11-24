T4A_3DFilesQtCheck
===================

Addon Blender (stub) pour contrôle qualité d'assets 3D.

Structure créée :
- `__init__.py` : manifest + hook vers autoload
- `PROD_autoload.py` : import dynamique des modules `PROD_*`
- `PROD_panel_*.py` : panels séparés pour la UI
- `PROD_mesh_analysis.py`, `PROD_image_analysis.py` : stubs pour analyses

Installation rapide :
- Copier le dossier `T4A_3DFilesQtCheck` dans `scripts/addons/` de Blender
- Activer l'addon depuis la preferences > Add-ons

Notes :
- Les fichiers Python de modules et d'options utilisent le préfixe `PROD_`.
- Les panels sont vides pour l'instant comme demandé.

Contact : Tech4Art Conseil <tech4artconseil@gmail.com>
