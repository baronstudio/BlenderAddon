"""Opérateur pour installer des dépendances Python dans l'environnement de Blender.

Ce module fournit `T4A_OT_InstallDependencies` qui exécute `python -m pip install ...`
en utilisant l'exécutable Python courant (`sys.executable`). Il est pensé pour être
appelé depuis les préférences de l'addon (bouton "Installer dépendances").
"""
import sys
import subprocess
import traceback
import logging
import bpy

logger = logging.getLogger('T4A.DependencyInstaller')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


class T4A_OT_InstallDependencies(bpy.types.Operator):
    bl_idname = "t4a.install_dependencies"
    bl_label = "Installer dépendances Python"
    bl_description = "Installe les paquets Python nécessaires (ex: PyPDF2) dans l'environnement Python de Blender"

    # Comma-separated list of packages (simple UI)
    packages: bpy.props.StringProperty(
        name="Packages",
        description="Liste séparée par des virgules des paquets à installer (ex: PyPDF2)",
        default="PyPDF2, requests, google-generativeai",
    )

    upgrade: bpy.props.BoolProperty(
        name="Forcer la mise à jour",
        description="Ajouter --upgrade lors de l'installation",
        default=True,
    )

    timeout: bpy.props.IntProperty(
        name="Timeout (s)",
        description="Timeout en secondes pour l'appel pip",
        default=300,
        min=10,
    )

    def execute(self, context):
        py = sys.executable or 'python'
        pkgs = [p.strip() for p in self.packages.split(',') if p.strip()]
        if not pkgs:
            self.report({'ERROR'}, 'Aucun paquet spécifié')
            return {'CANCELLED'}

        # Prepare pip command
        cmd = [py, '-m', 'pip', 'install']
        if self.upgrade:
            cmd.append('--upgrade')
        cmd.extend(pkgs)

        logger.info('Lancement installation pip: %s', ' '.join(cmd))
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            out = proc.stdout or ''
            err = proc.stderr or ''
            logger.debug('pip stdout:\n%s', out)
            if err:
                logger.debug('pip stderr:\n%s', err)

            if proc.returncode == 0:
                self.report({'INFO'}, f"Packages installés: {', '.join(pkgs)}")
                print(f"[T4A Installer] OK: {', '.join(pkgs)}\n{out}")
                return {'FINISHED'}
            else:
                tb = f"pip failed (rc={proc.returncode})\n{out}\n{err}"
                logger.error(tb)
                self.report({'ERROR'}, f"Échec installation: voir console (rc={proc.returncode})")
                print('[T4A Installer] ERREUR:', tb)
                return {'CANCELLED'}
        except Exception:
            tb = traceback.format_exc()
            logger.error('Installation exception: %s', tb)
            print('[T4A Installer] Exception:', tb)
            self.report({'ERROR'}, 'Exception lors de l\'installation — voir console')
            return {'CANCELLED'}


def register():
    try:
        bpy.utils.register_class(T4A_OT_InstallDependencies)
        print('[T4A Register] Registered T4A_OT_InstallDependencies')
    except ValueError as ve:
        msg = str(ve)
        if 'already registered' in msg:
            print('[T4A Register] Installer already registered - skipping')
        else:
            print('[T4A Register] ValueError registering installer:', msg)
    except Exception as e:
        print('[T4A Register] Failed to register T4A_OT_InstallDependencies:', e)


def unregister():
    try:
        bpy.utils.unregister_class(T4A_OT_InstallDependencies)
        print('[T4A Unregister] Unregistered T4A_OT_InstallDependencies')
    except ValueError as ve:
        msg = str(ve)
        if 'not registered' in msg or 'is not registered' in msg:
            print('[T4A Unregister] Installer not registered - skipping')
        else:
            print('[T4A Unregister] ValueError unregistering installer:', msg)
    except Exception as e:
        print('[T4A Unregister] Failed to unregister T4A_OT_InstallDependencies:', e)


__all__ = ('T4A_OT_InstallDependencies',)
