#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install the T4A add-ons of this repository into local Blender installations.

Run it with any Python 3.8+ (no Blender needed to run the script itself):

    python install_addons.py              # interactive
    python install_addons.py --dry-run    # show what would happen, change nothing

The script:
  1. auto-detects the Blender versions installed on this machine
     (installed executables + existing user configuration folders),
  2. asks which Blender version(s) to install into,
  3. asks which add-on(s) to install,
  4. asks how to install them (copy, or link for development),
  5. optionally enables them in Blender's preferences.

Where add-ons go (per Blender version, in the user configuration folder):
  - Blender 4.2+ and the add-on has a blender_manifest.toml
        -> <config>/X.Y/extensions/user_default/<id>
  - otherwise (legacy add-on, or Blender < 4.2)
        -> <config>/X.Y/scripts/addons/<folder>
"""

import argparse
import ast
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# Files and folders that are never copied into Blender.
COPY_IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo",
    ".git", ".gitignore", ".gitmodules", ".vscode", ".idea", ".tools",
    "*.code-workspace", "*.blend1", "*.blend2",
    "TestScenes", "assets-test",
    "Makefile", "build.bat", "build", "dist", "releases",
)

EXTENSIONS_MIN_VERSION = (4, 2)


# --------------------------------------------------------------------------- #
# Terminal helpers
# --------------------------------------------------------------------------- #

if os.name == "nt":
    os.system("")  # enables ANSI escape codes in the Windows console

_USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def bold(t): return _c("1", t)
def dim(t): return _c("2", t)
def green(t): return _c("32", t)
def yellow(t): return _c("33", t)
def red(t): return _c("31", t)
def cyan(t): return _c("36", t)


def title(text):
    print()
    print(bold(cyan(f"== {text} ")))


def ask(prompt, default=None):
    suffix = f" [{default}]" if default is not None else ""
    try:
        answer = input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(red("Aborted."))
    return answer if answer else (default or "")


def ask_yes_no(prompt, default=True):
    hint = "Y/n" if default else "y/N"
    while True:
        answer = ask(f"{prompt} ({hint})").lower()
        if not answer:
            return default
        if answer in ("y", "yes", "o", "oui"):
            return True
        if answer in ("n", "no", "non"):
            return False
        print(yellow("  Please answer y or n."))


def ask_multi_choice(items, label, default="all"):
    """Ask the user to pick one or more items by number. Returns the selected items."""
    while True:
        answer = ask(f"Select {label} (e.g. 1,3 or 1-2, 'all', 'q' to quit)", default).lower()
        if answer in ("q", "quit", "exit"):
            sys.exit("Aborted.")
        picked = _parse_choice(answer, items)
        if picked:
            return picked


def _parse_choice(answer, items):
    """Parse '1,3', '1-2' or 'all' against items; prints an error and returns [] if invalid."""
    answer = answer.replace(" ", "").lower()
    if answer in ("a", "all", "*"):
        return list(items)
    picked = []
    try:
        for part in filter(None, answer.split(",")):
            if "-" in part:
                start, end = (int(x) for x in part.split("-", 1))
                picked.extend(range(start, end + 1))
            else:
                picked.append(int(part))
    except ValueError:
        print(yellow("  Invalid input, use numbers separated by commas."))
        return []
    if not picked or any(i < 1 or i > len(items) for i in picked):
        print(yellow(f"  Numbers must be between 1 and {len(items)}."))
        return []
    result = []
    for i in picked:
        if items[i - 1] not in result:
            result.append(items[i - 1])
    return result


def fmt_version(v):
    return ".".join(str(x) for x in v)


def parse_version(text):
    m = re.search(r"(\d+)\.(\d+)", text or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


# --------------------------------------------------------------------------- #
# Add-on discovery
# --------------------------------------------------------------------------- #

class Addon:
    def __init__(self, folder: Path):
        self.folder = folder
        self.folder_name = folder.name
        self.manifest = self._read_manifest()
        self.bl_info = self._read_bl_info()
        self.ext_id = self.manifest.get("id") or self.folder_name
        self.name = (self.manifest.get("name")
                     or self.bl_info.get("name")
                     or self.folder_name)
        self.version = self.manifest.get("version") or fmt_version(self.bl_info.get("version", ()))
        min_v = parse_version(self.manifest.get("blender_version_min", ""))
        if min_v is None and self.bl_info.get("blender"):
            min_v = tuple(self.bl_info["blender"][:2])
        self.min_blender = min_v or (2, 80)

    @property
    def has_manifest(self):
        return bool(self.manifest)

    def _read_manifest(self):
        path = self.folder / "blender_manifest.toml"
        if not path.is_file():
            return {}
        data = {}
        # Only top-level `key = "value"` lines are needed; avoids needing tomllib (3.11+).
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("["):
                break
            m = re.match(r'^\s*([A-Za-z_]+)\s*=\s*"([^"]*)"', line)
            if m:
                data[m.group(1)] = m.group(2)
        return data

    def _read_bl_info(self):
        path = self.folder / "__init__.py"
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            return {}
        for node in tree.body:
            if (isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "bl_info" for t in node.targets)):
                try:
                    return ast.literal_eval(node.value)
                except ValueError:
                    return {}
        return {}

    def problems(self):
        """Return blocking problems with the source folder (e.g. missing submodule)."""
        issues = []
        qbpy = self.folder / "qbpy"
        if (self.folder / ".gitmodules").is_file() and qbpy.is_dir() and not any(qbpy.iterdir()):
            issues.append("the 'qbpy' git submodule is empty: run `git submodule update --init`")
        return issues


def discover_addons():
    addons = []
    for folder in sorted(REPO_ROOT.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if not (folder / "__init__.py").is_file():
            continue
        addon = Addon(folder)
        if addon.has_manifest or addon.bl_info:
            addons.append(addon)
    return addons


# --------------------------------------------------------------------------- #
# Blender discovery
# --------------------------------------------------------------------------- #

class BlenderTarget:
    """One Blender version + the user configuration folder add-ons are installed into."""

    def __init__(self, version, config_dir: Path, exe: Path = None, portable=False):
        self.version = version          # (major, minor)
        self.config_dir = config_dir    # .../Blender/X.Y  (contains config/, scripts/, extensions/)
        self.exe = exe
        self.portable = portable

    @property
    def supports_extensions(self):
        return self.version >= EXTENSIONS_MIN_VERSION

    def destination(self, addon: Addon) -> Path:
        if addon.has_manifest and self.supports_extensions:
            return self.config_dir / "extensions" / "user_default" / addon.ext_id
        return self.config_dir / "scripts" / "addons" / addon.folder_name

    def module_name(self, addon: Addon) -> str:
        if addon.has_manifest and self.supports_extensions:
            return f"bl_ext.user_default.{addon.ext_id}"
        return addon.folder_name

    def describe(self):
        parts = [bold(f"Blender {fmt_version(self.version)}")]
        if self.portable:
            parts.append(yellow("(portable)"))
        parts.append(f"\n       config : {self.config_dir}"
                     + ("" if self.config_dir.exists() else dim("  (will be created)")))
        parts.append(f"\n       exe    : {self.exe}" if self.exe else
                     "\n       exe    : " + dim("not found (add-ons can't be auto-enabled)"))
        return " ".join(parts)


def user_config_root() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "Blender Foundation" / "Blender"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Blender"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return (Path(xdg) if xdg else Path.home() / ".config") / "blender"


def candidate_executables():
    found = []

    def add(p):
        p = Path(p)
        if p.is_file() and p.resolve() not in [f.resolve() for f in found]:
            found.append(p)

    on_path = shutil.which("blender")
    if on_path:
        add(on_path)

    if sys.platform == "win32":
        roots = [os.environ.get(k) for k in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432")]
        roots += [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")]
        for root in filter(None, roots):
            for exe in Path(root).glob("Blender Foundation/*/blender.exe"):
                add(exe)
            for exe in Path(root).glob("Steam/steamapps/common/Blender/blender.exe"):
                add(exe)
            for exe in Path(root).glob("Blender*/blender.exe"):
                add(exe)
    elif sys.platform == "darwin":
        for apps in (Path("/Applications"), Path.home() / "Applications"):
            for exe in apps.glob("Blender*.app/Contents/MacOS/Blender"):
                add(exe)
    else:
        home = str(Path.home())
        for pattern in ("/opt/blender*/blender", "/usr/local/blender*/blender",
                        home + "/blender*/blender", home + "/Applications/blender*/blender",
                        "/snap/blender/current/blender"):
            for exe in glob.glob(pattern):
                add(exe)
    return found


def exe_version(exe: Path):
    """Find the Blender version of an executable, without launching it if possible."""
    # Installs ship a "X.Y" data folder next to the executable (Resources/X.Y on macOS).
    search_dirs = [exe.parent]
    if sys.platform == "darwin":
        search_dirs.append(exe.parent.parent / "Resources")
    for d in search_dirs:
        try:
            for child in d.iterdir():
                if child.is_dir() and re.fullmatch(r"\d+\.\d+", child.name):
                    return parse_version(child.name)
        except OSError:
            pass
    try:
        out = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=60)
        m = re.search(r"Blender\s+(\d+)\.(\d+)", out.stdout)
        if m:
            return int(m.group(1)), int(m.group(2))
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def portable_config_dir(exe: Path, version):
    """Return the user config dir of a portable Blender, or None if not portable."""
    base = exe.parent if sys.platform != "darwin" else exe.parent.parent / "Resources"
    if version >= EXTENSIONS_MIN_VERSION and (base / "portable").is_dir():
        return base / "portable"
    legacy = base / fmt_version(version)
    if (legacy / "config").is_dir():
        return legacy
    return None


def discover_blenders():
    targets = {}
    root = user_config_root()

    for exe in candidate_executables():
        version = exe_version(exe)
        if not version:
            continue
        portable = portable_config_dir(exe, version)
        config = portable or root / fmt_version(version)
        key = str(config).lower()
        if key not in targets or targets[key].exe is None:
            targets[key] = BlenderTarget(version, config, exe, portable=bool(portable))

    # Versions that have a user config folder but no detected executable.
    if root.is_dir():
        for child in root.iterdir():
            if child.is_dir() and re.fullmatch(r"\d+\.\d+", child.name):
                key = str(child).lower()
                if key not in targets:
                    targets[key] = BlenderTarget(parse_version(child.name), child)

    return sorted(targets.values(), key=lambda t: (t.version, t.portable), reverse=True)


def target_from_custom_path(raw: str):
    path = Path(raw.strip().strip('"')).expanduser()
    if path.is_dir() and (path / ("blender.exe" if os.name == "nt" else "blender")).is_file():
        path = path / ("blender.exe" if os.name == "nt" else "blender")
    if path.is_file():
        version = exe_version(path)
        if not version:
            print(red("  Could not determine the Blender version of this executable."))
            return None
        portable = portable_config_dir(path, version)
        return BlenderTarget(version, portable or user_config_root() / fmt_version(version),
                             path, portable=bool(portable))
    version = parse_version(path.name)
    if path.is_dir() and version and re.fullmatch(r"\d+\.\d+", path.name):
        return BlenderTarget(version, path)
    print(red("  Give either a Blender executable, its folder, or a config folder named like '4.2'."))
    return None


# --------------------------------------------------------------------------- #
# Install / enable
# --------------------------------------------------------------------------- #

def is_link(path: Path):
    """True for symlinks and Windows junctions (which must be unlinked, never rmtree'd)."""
    if path.is_symlink():
        return True
    isjunction = getattr(os.path, "isjunction", None)  # Python 3.12+
    if isjunction:
        return isjunction(path)
    if os.name == "nt":
        try:
            attrs = os.lstat(path).st_file_attributes
        except OSError:
            return False
        return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
    return False


def remove_existing(path: Path):
    """Remove an existing install. Links are unlinked, never followed."""
    if is_link(path):
        try:
            os.unlink(path)
        except OSError:
            os.rmdir(path)  # Windows junction
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def make_link(src: Path, dst: Path):
    if os.name == "nt":
        # A junction needs no admin rights or Developer Mode, unlike a symlink.
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(src)],
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise OSError(result.stderr.strip() or result.stdout.strip())
    else:
        os.symlink(src, dst, target_is_directory=True)


def install(addon: Addon, target: BlenderTarget, mode: str, dry_run: bool):
    dst = target.destination(addon)
    action = "link" if mode == "link" else "copy"
    replaced = dst.exists() or is_link(dst)
    label = f"{addon.name} -> {dst}"
    if dry_run:
        print(f"  {dim('[dry-run]')} {action}{' (replace)' if replaced else ''}: {label}")
        return True
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if replaced:
            remove_existing(dst)
        if mode == "link":
            make_link(addon.folder, dst)
        else:
            shutil.copytree(addon.folder, dst, ignore=COPY_IGNORE)
    except (OSError, shutil.Error) as exc:
        print(f"  {red('FAILED')} {label}\n         {exc}")
        return False
    print(f"  {green('OK')}     {action}{' (replaced)' if replaced else ''}: {label}")
    return True


ENABLE_SCRIPT = r"""
import sys, addon_utils, bpy
mods = sys.argv[sys.argv.index("--") + 1:]
for mod in mods:
    try:
        result = addon_utils.enable(mod, default_set=True, persistent=True, handle_error=None)
        print(("T4A_ENABLED " if result else "T4A_FAILED ") + mod, flush=True)
    except Exception as exc:
        print("T4A_FAILED " + mod + " " + repr(exc), flush=True)
bpy.ops.wm.save_userpref()
print("T4A_PREFS_SAVED", flush=True)
"""


def enable_in_blender(target: BlenderTarget, addons, dry_run: bool):
    modules = [target.module_name(a) for a in addons]
    if dry_run:
        print(f"  {dim('[dry-run]')} enable in Blender {fmt_version(target.version)}: {', '.join(modules)}")
        return
    print(f"  Launching Blender {fmt_version(target.version)} in background to enable add-ons...")
    cmd = [str(target.exe), "--background", "--python-exit-code", "1",
           "--python-expr", ENABLE_SCRIPT, "--", *modules]
    env = dict(os.environ)
    if target.portable:
        env.pop("BLENDER_USER_RESOURCES", None)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env,
                             encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"  {red('FAILED')} could not run Blender: {exc}")
        return
    for line in out.stdout.splitlines():
        if line.startswith("T4A_ENABLED "):
            print(f"  {green('ENABLED')} {line.split(' ', 1)[1]}")
        elif line.startswith("T4A_FAILED "):
            print(f"  {red('NOT ENABLED')} {line.split(' ', 1)[1]}")
    if "T4A_PREFS_SAVED" not in out.stdout:
        print(f"  {yellow('Preferences may not have been saved.')} Blender output:")
        for line in (out.stdout + out.stderr).strip().splitlines()[-15:]:
            print(dim(f"    {line}"))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description="Install the T4A add-ons into local Blender installations.")
    parser.add_argument("--dry-run", action="store_true", help="show what would be done, change nothing")
    args = parser.parse_args()

    print(bold("T4A Blender add-ons installer"))
    print(dim(f"Repository: {REPO_ROOT}"))
    if args.dry_run:
        print(yellow("Dry run: nothing will be written."))

    # ---- 1. Blender versions -------------------------------------------------
    title("Step 1/4 - Blender installations")
    print("Detecting Blender...")
    targets = discover_blenders()
    while True:
        if targets:
            for i, t in enumerate(targets, 1):
                print(f"  {bold(str(i)):>3}) {t.describe()}")
        else:
            print(yellow("  No Blender installation detected."))
        print(f"  {bold('p')}) enter a custom path (portable Blender, other location)")
        if not targets:
            choice = "p"
        else:
            choice = ask("Select Blender version(s) (e.g. 1,3 or 'all', 'p' for custom path, 'q' to quit)", "1").lower()
        if choice in ("q", "quit"):
            sys.exit("Aborted.")
        if choice == "p":
            custom = target_from_custom_path(ask("Path to blender executable or config folder"))
            if custom:
                targets.insert(0, custom)
                print(green(f"  Added Blender {fmt_version(custom.version)}."))
            continue
        selected_targets = _parse_choice(choice, targets)
        if selected_targets:
            break

    # ---- 2. Add-ons ----------------------------------------------------------
    title("Step 2/4 - Add-ons")
    addons = discover_addons()
    if not addons:
        sys.exit(red("No add-ons found in the repository."))
    for i, a in enumerate(addons, 1):
        kind = "extension" if a.has_manifest else "legacy add-on"
        print(f"  {bold(str(i)):>3}) {bold(a.name)} {dim(a.version)}  "
              f"{dim(f'[{a.folder_name}, {kind}, Blender {fmt_version(a.min_blender)}+]')}")
    selected_addons = ask_multi_choice(addons, "add-on(s)", "all")

    blocked = [(a, p) for a in selected_addons for p in a.problems()]
    for a, p in blocked:
        print(red(f"  {a.name}: {p}"))
    if blocked:
        if not ask_yes_no("Continue anyway with these add-ons", default=False):
            selected_addons = [a for a in selected_addons if not a.problems()]

    # ---- 3. Mode --------------------------------------------------------------
    title("Step 3/4 - Install mode")
    print(f"  {bold('1')}) copy  - copy the files (for users; re-run the script to update)")
    link_kind = "junction" if os.name == "nt" else "symlink"
    print(f"  {bold('2')}) link  - {link_kind} to this repository (for developers; edits are live)")
    mode = "link" if ask("Mode", "1").strip() in ("2", "link", "l") else "copy"

    # ---- Plan ----------------------------------------------------------------
    plan = []
    for t in selected_targets:
        for a in selected_addons:
            if t.version < a.min_blender:
                print(yellow(f"  Skip {a.name} for Blender {fmt_version(t.version)}: "
                             f"requires Blender {fmt_version(a.min_blender)}+"))
                continue
            plan.append((t, a))
    if not plan:
        sys.exit(yellow("Nothing to install."))

    title("Summary")
    for t, a in plan:
        dst = t.destination(a)
        note = yellow(" (will replace existing)") if (dst.exists() or is_link(dst)) else ""
        print(f"  Blender {fmt_version(t.version)}  {a.name}  ->  {dst}{note}")
    print(yellow("Close the selected Blender versions before continuing."))
    if not ask_yes_no(f"Proceed with {mode}", default=True):
        sys.exit("Aborted.")

    # ---- 4. Install + enable ---------------------------------------------------
    title("Step 4/4 - Installing")
    installed = {}
    failures = 0
    for t, a in plan:
        if install(a, t, mode, args.dry_run):
            installed.setdefault(id(t), (t, []))[1].append(a)
        else:
            failures += 1

    enable_targets = [(t, al) for t, al in installed.values() if t.exe]
    if enable_targets and ask_yes_no("Enable the installed add-ons in Blender preferences now", default=True):
        for t, al in enable_targets:
            enable_in_blender(t, al, args.dry_run)
    for t, _ in installed.values():
        if not t.exe:
            print(dim(f"  Blender {fmt_version(t.version)}: no executable found, "
                      "enable the add-ons in Edit > Preferences > Add-ons."))

    print()
    if failures:
        print(red(f"Done with {failures} error(s)."))
        sys.exit(1)
    print(green("Done.") + " Start Blender; panels are in the 3D View sidebar (N).")


if __name__ == "__main__":
    main()
