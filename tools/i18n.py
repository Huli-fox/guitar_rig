"""Extract, update, and validate catalogs inside Blender. See TRANSLATING.md."""

import argparse
import ast
from collections import Counter, defaultdict
import importlib
import json
from pathlib import Path
import re
import string
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = "GuitarRig"
LOCALES = ROOT / "i18n" / "locales"


def literals(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        yield node.value
    elif isinstance(node, ast.IfExp):
        yield from literals(node.body)
        yield from literals(node.orelse)


def collect(addon):
    """Combine marked source messages with Blender's actual registered RNA metadata."""
    entries = defaultdict(set)

    def add(text, reference, context=CONTEXT):
        if text:
            entries[(context, str(text))].add(reference)

    for folder in ("core", "ops", "rig", "ui", "i18n"):
        for path in sorted((ROOT / folder).glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                reference = f"{path.relative_to(ROOT).as_posix()}:{getattr(node, 'lineno', 1)}"
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if name in {"msg", "mark", "iface", "tip", "rpt"} and node.args:
                    for text in literals(node.args[0]):
                        add(text, reference)
                if name in {"label", "operator", "prop", "prop_search"}:
                    for kw in node.keywords:
                        if kw.arg == "text":
                            for text in literals(kw.value):
                                add(text, reference)

    classes = list(addon.props.CLASSES) + list(addon.ui.panels.CLASSES)
    for module in addon.ops._MODULES:
        classes.extend(module.CLASSES)
    for cls in classes:
        reference = cls.__module__.replace(addon.__name__ + ".", "").replace(".", "/") + ".py:" + cls.__name__
        rna = cls.bl_rna
        context = getattr(cls, "bl_translation_context", CONTEXT)
        add(getattr(cls, "bl_label", ""), reference, context)
        if cls.__name__.startswith("GTR_OT_"):
            import bpy
            group, name = cls.bl_idname.split(".")
            rna = getattr(getattr(bpy.ops, group), name).get_rna_type()
            add(rna.description, reference, "*")
        for prop in rna.properties:
            if prop.identifier == "rna_type" or prop.translation_context != CONTEXT:
                continue
            add(prop.name, reference, prop.translation_context)
            # Blender uses the default context for RNA tooltips, independently of names.
            add(prop.description, reference, "*")
            if prop.type == 'ENUM':
                for item in prop.enum_items:
                    add(item.name, reference, prop.translation_context)
                    add(item.description, reference, "*")

    # Metadata generated outside RNA, including complete bone titles (never translated fragments).
    from guitar_rig.core import bonemap, diagnostics, guitar_frame, landmarks, presets
    from guitar_rig.ui import panels
    for slot in bonemap.SLOTS:
        add(slot.label, "core/bonemap.py:SLOTS")
        add(slot.title, "core/bonemap.py:SLOTS")
    for role in landmarks.ROLES:
        add(role.label, "core/landmarks.py:ROLES")
        add(role.description, "core/landmarks.py:ROLES")
    for _, name, description, _ in diagnostics.METRICS:
        add(name, "core/diagnostics.py:METRICS")
        add(description, "core/diagnostics.py:METRICS")
    for _, title, _ in panels.SLOT_GROUPS:
        add(title, "ui/panels.py:SLOT_GROUPS")
    for name in ("AXIS_NAMES", "GUITAR_AXIS_NAMES", "MOUNT_TEXT", "WRIST_TEXT", "LANDMARK_TEXT"):
        values = getattr(panels, name)
        for text in values.values() if isinstance(values, dict) else values:
            add(text, "ui/panels.py:" + name)
    for text in guitar_frame.CUE_TITLES.values():
        add(text, "core/guitar_frame.py:CUE_TITLES")
    for convention in bonemap.load_presets()["conventions"]:
        add(convention["label"], "presets/bone_maps.json")
    add("Guitar", "ui/panels.py:bl_category", "*")
    for preset_id in presets.builtin_ids():
        path = Path(presets.builtin_path(preset_id))
        data = json.loads(path.read_text(encoding="utf-8"))
        for text in [data.get("name", ""), data.get("description", ""), *data.get("notes", [])]:
            add(text, "presets/" + path.name)
    return entries


def fields(text):
    result = Counter()
    for _, field, spec, conversion in string.Formatter().parse(text):
        if field is not None:
            if not field.isidentifier():
                raise ValueError("use named placeholders without attribute or index access")
            result[(field, spec, conversion)] += 1
    return result


def validate(catalog, entries):
    errors = []
    for key, translated in catalog.items():
        if not translated or key not in entries:
            continue
        try:
            if fields(key[1]) != fields(translated):
                errors.append(f"{key[1]!r}: placeholders or format specifications differ")
        except ValueError as exc:
            errors.append(f"{key[1]!r}: {exc}")
    return errors


def write_catalog(path, entries, previous):
    lines = ["# SPDX-License-Identifier: GPL-3.0-or-later",
             "# UTF-8. Edit translation values; empty values fall back to English.",
             "# Updated by tools/i18n.py. See TRANSLATING.md.", "", "translations = {"]
    for key in sorted(entries):
        lines.append("    # " + ", ".join(sorted(entries[key])))
        lines.append(f"    {key!r}: {previous.get(key, '')!r},")
    obsolete = sorted(previous.keys() - entries.keys())
    if obsolete:
        lines.extend(["", "    # Obsolete entries retained for reference; remove them when no longer useful."])
        for key in obsolete:
            lines.append(f"    {key!r}: {previous[key]!r},")
    lines.extend(["}", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def check(entries, read_catalog):
    import bpy
    errors = []
    supported = {item.identifier for item in bpy.context.preferences.view.bl_rna.properties['language'].enum_items}
    template_path = LOCALES / "_template.py"
    if not template_path.exists():
        errors.append("Missing _template.py; run update")
    for path in sorted(LOCALES.glob("*.py")):
        if path != template_path and path.stem not in supported:
            errors.append(f"{path.name}: locale is not supported by this Blender; use its language identifier")
        try:
            catalog = read_catalog(path)
        except (ValueError, SyntaxError, TypeError) as exc:
            errors.append(str(exc))
            continue
        if path == template_path and set(catalog) != set(entries):
            errors.append("_template.py is out of date; run update")
        errors.extend(f"{path.name}: {error}" for error in validate(catalog, entries))
        if path != template_path:
            count = sum(bool(value) for key, value in catalog.items() if key in entries)
            obsolete = len(catalog.keys() - entries.keys())
            print(f"{path.stem}: {count}/{len(entries)} translated; {obsolete} obsolete")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("update", "check"))
    parser.add_argument("--locale", help="Blender locale identifier, e.g. zh_HANS or fr_FR")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if args.locale and (not re.fullmatch(r"[a-z]{2,3}(?:_[A-Za-z0-9]+)*", args.locale)):
        parser.error("Invalid locale identifier")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT.parent))
    addon = importlib.import_module(ROOT.name)
    if args.locale:
        import bpy
        supported = {item.identifier for item in bpy.context.preferences.view.bl_rna.properties['language'].enum_items}
        if args.locale not in supported:
            parser.error("Locale is not supported by this Blender; use its language identifier")
    addon.register()
    try:
        entries = collect(addon)
        if args.command == "update":
            paths = [LOCALES / "_template.py"]
            paths += [LOCALES / (args.locale + ".py")] if args.locale else [
                path for path in sorted(LOCALES.glob("*.py")) if not path.name.startswith("_")]
            for path in paths:
                previous = addon.i18n.read_catalog(path) if path.exists() and path.name != "_template.py" else {}
                write_catalog(path, entries, previous)
                print(f"Updated {path.relative_to(ROOT)}")
        errors = check(entries, addon.i18n.read_catalog)
        for error in errors:
            print(error, file=sys.stderr)
        print(f"{len(entries)} source messages; {len(errors)} errors")
        if errors:
            raise SystemExit(1)
    finally:
        addon.unregister()


if __name__ == "__main__":
    main()
