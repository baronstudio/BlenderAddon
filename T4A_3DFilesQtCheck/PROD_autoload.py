"""
Autoload dynamique des modules de l'addon : importe et enregistre tous les modules
du package qui commencent par le préfixe "PROD_".
"""

import importlib
import pkgutil
import sys
import traceback
from types import ModuleType

PACKAGE_NAME = __package__
PREFIX = "PROD_"

_loaded_modules = []


def _iter_package_modules():
    if PACKAGE_NAME is None:
        return
    package = importlib.import_module(PACKAGE_NAME)
    for finder, name, ispkg in pkgutil.iter_modules(package.__path__):
        if name.startswith(PREFIX):
            yield f"{PACKAGE_NAME}.{name}", name


def register():
    """Importe et appelle register() de chaque module PROD_*."""
    global _loaded_modules
    _loaded_modules = []
    for fullname, shortname in _iter_package_modules():
        try:
            module = importlib.import_module(fullname)
            _loaded_modules.append(module)
            if hasattr(module, "register"):
                module.register()
        except Exception:
            print(f"[T4A Autoload] Erreur lors de l'import de {fullname}")
            traceback.print_exc()


def unregister():
    """Appelle unregister() sur les modules importés (ordre inverse)."""
    global _loaded_modules
    for module in reversed(_loaded_modules):
        try:
            if hasattr(module, "unregister"):
                module.unregister()
            # attempt to remove from sys.modules
            if isinstance(module, ModuleType) and module.__name__ in sys.modules:
                del sys.modules[module.__name__]
        except Exception:
            print(f"[T4A Autoload] Erreur lors de l'unregister de {getattr(module, '__name__', str(module))}")
            traceback.print_exc()
    _loaded_modules = []
