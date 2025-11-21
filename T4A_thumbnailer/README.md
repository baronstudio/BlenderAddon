T4A Thumbnailer
================

Add-on Blender pour générer des miniatures (thumbnails) JPEG à partir de la caméra active.

Fonctionnalités
- Interface dans le panneau `T4A Thumbnailer` (Sidebar N panel) du `3D View`.
- Choix du dossier d'enregistrement.
- Réglage de la résolution (par défaut 64x64) et qualité JPEG.
- Bouton pour rendre une vignette à partir du matériau actif de l'objet sélectionné.
- Bouton batch : applique chaque matériau assigné à l'objet et enregistre un JPEG par matériau (nom du fichier = nom du matériau).

Installation
1. Copier le dossier `T4A_thumbnailer` dans le dossier des add-ons Blender (ou installer depuis fichier ZIP).
2. Dans Blender : `Edit > Preferences > Add-ons > Install...` (ou activer l'add-on si copié dans le dossier des add-ons).
3. Dans la vue 3D, ouvrir la Sidebar (`N`) et sélectionner l'onglet `T4A Thumbnailer`.

Utilisation rapide
- Sélectionner un objet.
- Choisir un dossier de sortie.
- Régler la résolution et la qualité.
- Cliquer sur `Rendre vignette active` ou `Batch materials`.

Notes
- L'add-on utilise la caméra active de la scène. Assurez‑vous qu'une caméra est définie.
- L'add-on affecte temporairement les matériaux de l'objet et restaure les assignations initiales après batch.
