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

## Licence

- Code source : sous licence GNU General Public License v3.0 (GPLv3).
	Le fichier `LICENSE` contient les informations de licence et le lien
	vers le texte complet de la licence.

## Assets fournis

- Le dossier `assets-test/` contient des exemples et fichiers de tests.
- Ces assets peuvent être distribués sous une licence différente ou
	être la propriété de tiers ; leur réutilisation ou redistribution
	peut nécessiter l'autorisation explicite de leurs auteurs.
- Par défaut, le dépôt source (code) est sous GPLv3, mais vérifiez
	les fichiers présents dans `assets-test/` pour connaître leur
	licence ou indication d'auteur avant toute redistribution.
