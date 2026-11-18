"""Blender translation registration and display-boundary helpers."""

import ast
from pathlib import Path

from bpy.app.translations import pgettext_iface, pgettext_rpt, pgettext_tip

from .messages import CONTEXT, Message, join, mark, msg, render, wrap

_owner = None
CATALOG_DIR = Path(__file__).with_name("locales")


def iface(value):
    return render(value, pgettext_iface)


def tip(value):
    return render(value, pgettext_tip)


def report(value):
    return render(value, pgettext_rpt)


def read_catalog(path):
    """Read data-only Python catalogs without executing contributor code."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assignments = [node for node in tree.body if isinstance(node, ast.Assign)]
    if len(assignments) != 1 or len(assignments[0].targets) != 1 or not isinstance(
            assignments[0].targets[0], ast.Name) or assignments[0].targets[0].id != "translations":
        raise ValueError(f"{path}: expected one translations dictionary")
    node = assignments[0].value
    if not isinstance(node, ast.Dict):
        raise ValueError(f"{path}: translations must be a dictionary")
    result = {}
    for key_node, value_node in zip(node.keys, node.values):
        key, value = ast.literal_eval(key_node), ast.literal_eval(value_node)
        if not isinstance(key, tuple) or len(key) != 2 or not all(isinstance(v, str) for v in key):
            raise ValueError(f"{path}: invalid translation key {key!r}")
        if key in result:
            raise ValueError(f"{path}: duplicate translation key {key!r}")
        if not isinstance(value, str):
            raise ValueError(f"{path}: translation must be text: {key!r}")
        result[key] = value
    return result


def load_catalogs():
    """{locale: {key: translation}} of the locale files that read cleanly."""
    catalogs = {}
    for path in sorted(CATALOG_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            catalog = read_catalog(path)
        except (OSError, SyntaxError, ValueError, TypeError, RecursionError) as exc:
            # A broken community translation costs that language, never the add-on.
            print(f"GuitarRig: skipped the translation {path.name}: {exc}")
            continue
        catalogs[path.stem] = {key: value for key, value in catalog.items() if value}
    return catalogs


def register():
    import bpy
    global _owner
    owner = __package__.rsplit(".", 1)[0]
    bpy.app.translations.register(owner, load_catalogs())
    _owner = owner


def unregister():
    import bpy
    global _owner
    if _owner is not None:
        bpy.app.translations.unregister(_owner)
        _owner = None
