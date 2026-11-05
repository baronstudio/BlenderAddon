T4A Thumbnailer
================

Add-on Blender pour générer des miniatures (thumbnails) JPEG à partir de la caméra active.

Compatibilité : **Blender 4.2 et plus, y compris 5.x**. L'add-on est packagé comme une
extension Blender (`blender_manifest.toml`).

Fonctionnalités
- Interface dans le panneau `T4A Thumbnailer` (Sidebar N panel) du `3D View`.
- Choix du dossier d'enregistrement.
- Réglage de la résolution (par défaut 64x64) et de la qualité JPEG.
- Bouton pour rendre une vignette à partir du matériau actif de l'objet sélectionné.
- Bouton batch : applique chaque matériau assigné à l'objet et enregistre un JPEG par matériau (nom du fichier = nom du matériau + suffixe).

Installation
1. Utiliser le script `install_addons.py` à la racine du dépôt, **ou**
2. Construire le ZIP de l'extension :
   `blender --command extension build --source-dir T4A_thumbnailer`
   puis dans Blender : `Edit > Preferences > Get Extensions > ⌄ > Install from Disk...`.
3. Dans la vue 3D, ouvrir la Sidebar (`N`) et sélectionner l'onglet `T4A Thumbnailer`.

Utilisation rapide
- Sélectionner un objet.
- Choisir un dossier de sortie.
- Régler la résolution et la qualité.
- Cliquer sur `Rendre vignette active` ou `Batch matériaux`.

Notes
- L'add-on utilise la caméra active de la scène ; les boutons sont désactivés s'il n'y en a pas.
- Les réglages de rendu de la scène (résolution, format de sortie, chemin) sont modifiés le temps du rendu puis restaurés.
- En batch, les matériaux de l'objet sont affectés temporairement puis les assignations initiales sont restaurées.
- Les caractères interdits dans les noms de fichiers (`/ \ : * ? " < > |`) sont remplacés par `_`.

Licence
-------

- **Licence de cet add-on**: Ce projet est distribué sous la licence GNU General Public License version 3 ou ultérieure (GPL-3.0-or-later). Voir le fichier `LICENSE` pour le texte complet.
- **Remarque sur Blender**: Blender lui-même est publié sous la licence GNU General Public License (généralement "GPL v2 or later"). En utilisant ou en distribuant cet add-on avec Blender, respectez les termes de la licence GPL applicables.

Copyright: 2026 Tech4Art Conseil
