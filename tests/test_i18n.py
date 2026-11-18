"""Localization at display boundaries, persistence, and contributor catalog validation."""

import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bpy
import numpy as np

import guitar_rig
from guitar_rig import i18n
from guitar_rig.i18n import messages
from guitar_rig.core import bonemap, calibrate, diagnostics, presets
from guitar_rig.ui import panels

ROOT = Path(guitar_rig.__file__).parent
spec = importlib.util.spec_from_file_location("catalog_tool", ROOT / "tools" / "i18n.py")
catalog_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog_tool)


class MessageTest(unittest.TestCase):
    def test_translate_template_before_interpolating_literal_name(self):
        text = i18n.msg("Frame {frame}: {name}", frame=12, name="Bake")
        table = {"Frame {frame}: {name}": "{name} — image {frame}", "Bake": "Cuire"}
        with patch("guitar_rig.i18n.pgettext_iface", side_effect=lambda s, c: table.get(s, s)) as lookup:
            self.assertEqual(i18n.iface(text), "Bake — image 12")
            lookup.assert_called_once_with("Frame {frame}: {name}", i18n.CONTEXT)
        self.assertEqual(str(text), "Frame 12: Bake")

    def test_saved_messages_follow_language_and_keep_numeric_specs(self):
        text = i18n.msg("{side}: {value:.1f} cm at {frame}", side=i18n.msg("Left"),
                       value=np.float64(2.25), frame=np.int64(8))
        original = [('WARNING', text + i18n.msg(" Check the map."))]
        restored = calibrate.parse_messages(calibrate.format_messages(original))
        self.assertEqual(restored, original)
        table = {"Left": "Gauche", " Check the map.": " Vérifiez la carte."}
        lookup = lambda s, c: table.get(s, s)
        self.assertEqual(messages.render(restored[0][1], lookup), "Gauche: 2.2 cm at 8 Vérifiez la carte.")
        table["Left"] = "左"
        self.assertTrue(messages.render(restored[0][1], lookup).startswith("左:"))
        self.assertNotIn("Gauche", calibrate.format_messages(restored))

    def test_legacy_reports_and_corrupt_new_reports(self):
        self.assertEqual(calibrate.parse_messages("WARNING\tOld text\nINFO\tMore text"),
                         [('WARNING', "Old text"), ('INFO', "More text")])
        self.assertEqual(calibrate.parse_messages(""), [])
        self.assertEqual(calibrate.parse_messages(messages.PREFIX + "broken"), [])
        for value in ({"join": ["a"], "separator": 5}, {"message": "{0}", "values": {"a": 1}},
                      {"message": "{a.b}", "values": {"a": 1}}, {"message": 5, "values": {"a": 1}}):
            self.assertEqual(calibrate.parse_messages(messages.PREFIX + json.dumps([["INFO", value]])), [], value)

    def test_exception_metadata_and_broken_translation_fallback(self):
        value = i18n.msg("Bone {name} is missing.", name="MyBone")
        with patch("guitar_rig.i18n.pgettext_rpt", return_value="Os {name} absent."):
            self.assertEqual(i18n.report(ValueError(value)), "Os MyBone absent.")
        with patch("guitar_rig.i18n.pgettext_iface", return_value="{wrong}"):
            self.assertEqual(i18n.iface(value), "Bone MyBone is missing.")

    def test_exception_values_read_as_in_english(self):
        lookup = lambda s, c: s
        for exc in (KeyError('scale'), OSError(2, "No such file"), ValueError("plain"), ValueError()):
            text = i18n.msg("Failed: {error}", error=exc)
            self.assertEqual(messages.render(text, lookup), str(text))
            self.assertEqual(messages.render(exc, lookup), str(exc))
            restored = calibrate.parse_messages(calibrate.format_messages([('ERROR', text)]))[0][1]
            self.assertEqual(messages.render(restored, lookup), str(text))
        nested = i18n.msg("Failed: {error}", error=ValueError(i18n.msg("format {format} is too new", format=9)))
        table = {"Failed: {error}": "Échec : {error}", "format {format} is too new": "format {format} trop récent"}
        self.assertEqual(messages.render(nested, lambda s, c: table.get(s, s)), "Échec : format 9 trop récent")

    def test_malformed_preset_names_the_fault(self):
        directory = ROOT / '.tmp' / 'test_presets'
        directory.mkdir(parents=True, exist_ok=True)
        for name, data, english in (
                ('missing.json', {"format": presets.FORMAT}, "KeyError('sao_placement_scale')"),
                ('newer.json', {"format": presets.FORMAT + 1}, f"format {presets.FORMAT + 1} is newer")):
            path = directory / name
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(presets.PresetError) as caught:
                presets.load(str(path))
            self.assertIn(english, str(caught.exception))
            self.assertEqual(messages.render(caught.exception, lambda s, c: s), str(caught.exception))

    def test_preference_specific_lookup(self):
        for helper, name in ((i18n.iface, 'iface'), (i18n.tip, 'tip'), (i18n.report, 'rpt')):
            with patch("guitar_rig.i18n.pgettext_" + name, return_value="Translated") as lookup:
                self.assertEqual(helper(i18n.msg("Original")), "Translated")
                lookup.assert_called_once_with("Original", i18n.CONTEXT)

    def test_translate_before_wrapping_cjk(self):
        output = []
        class Layout:
            def column(self, **kwargs):
                return self

            def label(self, **kwargs):
                output.append(kwargs)

        context = SimpleNamespace(region=SimpleNamespace(width=168), preferences=SimpleNamespace(
            system=SimpleNamespace(ui_scale=1.0)))
        translation = "校准角色之后检查手腕的位置并重新烘焙动画以获得正确结果。"
        with patch("guitar_rig.i18n.pgettext_iface", return_value=translation) as lookup:
            panels.draw_messages(Layout(), context, [('INFO', i18n.msg("Calibrate the character first."))])
        lookup.assert_called_once()
        self.assertEqual("".join(row['text'] for row in output), translation)
        self.assertTrue(all(len(row['text']) <= 12 and row['translate'] is False for row in output))
        self.assertEqual(output[0]['icon'], 'INFO')
        self.assertTrue(all(row['icon'] == 'BLANK1' for row in output[1:]))

    def test_wrap_combining_marks_and_explicit_lines(self):
        self.assertEqual(messages.wrap("e\u0301e\u0301e\u0301", 2), ["e\u0301e\u0301", "e\u0301"])
        self.assertEqual(messages.wrap("One two\nThree", 7), ["One two", "Three"])
        self.assertEqual(messages.wrap("One\n\nTwo", 7), ["One", "", "Two"])

    def test_wrap_fills_lines(self):
        self.assertEqual(messages.wrap("One two three", 7), ["One two", "three"])
        self.assertEqual(messages.wrap("One two   three", 8), ["One two", "three"])
        self.assertEqual(messages.wrap("Abcdefghij kl", 4), ["Abcd", "efgh", "ij", "kl"])
        self.assertEqual(messages.wrap("frame-to-frame", 9), ["frame-to-", "frame"])
        self.assertEqual(messages.wrap("-5 to -15", 6), ["-5 to", "-15"])
        self.assertEqual(messages.wrap("on T-pose", 6), ["on", "T-pose"])
        text = ("The fretting hand's reach (see presets/guitar_collection_v9.1/acoustic.json) acts frame-to-frame "
                "on a T-pose, re-clamped within 99.5% of the arm.")
        for width in range(8, 60):
            self.assertEqual(messages.wrap(text, width), textwrap.wrap(text, width), width)
        # Wide text breaks between glyphs, not back at a space far to the left, and keeps punctuation attached.
        self.assertEqual(messages.wrap("将 GTR_ROOT的缩放改为正值。然后", 24), ["将 GTR_ROOT的缩放改为正", "值。然后"])
        self.assertEqual(messages.wrap("缩放改为（正值）然后", 10), ["缩放改为", "（正值）然", "后"])
        self.assertEqual(messages.wrap("前臂 (手捩) 骨", 7), ["前臂", "(手捩)", "骨"])
        self.assertEqual(messages.wrap("GTR_ROOT的缩放", 9), ["GTR_ROOT", "的缩放"])


class CatalogTest(unittest.TestCase):
    def test_real_catalog_language_switch_and_blender_preferences(self):
        view = bpy.context.preferences.view
        locales = {item.identifier for item in view.bl_rna.properties['language'].enum_items}
        if 'fr_FR' not in locales or 'en_US' not in locales:
            self.skipTest('French and English locales are needed for the integration test')
        names = ['language', 'use_translate_interface', 'use_translate_tooltips', 'use_translate_reports']
        old = {name: getattr(view, name) for name in names}
        directory = ROOT / '.tmp' / 'test_locales'
        directory.mkdir(parents=True, exist_ok=True)
        template = 'GTR test frame {frame}: {name}'
        catalog = {(i18n.CONTEXT, template): 'GTR test image {frame}: {name}',
                   (i18n.CONTEXT, 'GTR untranslated test'): '',
                   (i18n.CONTEXT, 'Mode'): 'Mode traduit'}
        catalog_tool.write_catalog(directory / 'fr_FR.py', {key: {'test'} for key in catalog}, catalog)
        text = i18n.msg(template, frame=3, name='GTR_ROOT')
        saved = calibrate.format_messages([('INFO', text)])
        i18n.unregister()
        try:
            with patch.object(i18n, 'CATALOG_DIR', directory):
                i18n.register()
            view.language = 'fr_FR'
            for name in names[1:]:
                setattr(view, name, True)
            for helper in (i18n.iface, i18n.tip, i18n.report):
                self.assertEqual(helper(text), 'GTR test image 3: GTR_ROOT')
            self.assertEqual(i18n.iface('GTR untranslated test'), 'GTR untranslated test')
            prop = guitar_rig.props.GTR_Settings.bl_rna.properties['mode']
            self.assertEqual(bpy.app.translations.pgettext_iface(prop.name, prop.translation_context), 'Mode traduit')
            for helper, preference in ((i18n.iface, 'use_translate_interface'),
                                       (i18n.tip, 'use_translate_tooltips'),
                                       (i18n.report, 'use_translate_reports')):
                setattr(view, preference, False)
                self.assertEqual(helper(text), str(text))
                setattr(view, preference, True)
            view.language = 'en_US'
            self.assertEqual(i18n.iface(calibrate.parse_messages(saved)[0][1]), str(text))
            view.language = 'fr_FR'
            self.assertEqual(i18n.iface(calibrate.parse_messages(saved)[0][1]), 'GTR test image 3: GTR_ROOT')
            i18n.unregister()
            self.assertEqual(i18n.iface(text), str(text))
        finally:
            i18n.unregister()
            for name, value in old.items():
                setattr(view, name, value)
            i18n.register()

    def test_extraction_includes_generated_metadata(self):
        entries = catalog_tool.collect(guitar_rig)
        for text in ("Left Index Proximal", "Left IK Upper Arm", "Left IK Chain", "Acoustic Guitar",
                     "Pick the retargeted character", "Barrier — Left", "{count:.0f} passes",
                     "Smoothed {smoothed} guitar curves at {cutoff:g} Hz", "clamp"):
            self.assertIn((i18n.CONTEXT, text), entries)
        # No row label or state is translated only because an RNA name happens to read the same.
        for text in ("Confidence", "Fit", "Mount", "Rotation", "Solve", "Mode", "Fingertips", "High", "Follow"):
            references = entries[(i18n.CONTEXT, text)]
            self.assertTrue(any(r.rpartition(":")[2].isdigit() for r in references), (text, references))
        self.assertIn(("*", bpy.ops.gtr.bake.get_rna_type().description), entries)
        self.assertIn(("*", "Guitar"), entries)

    def test_unextracted_messages_are_rejected(self):
        def found(rel, source):
            return [(rel, ast.parse(source).body[0].value, "msg")]

        self.assertEqual(catalog_tool.unlisted(), [])
        self.assertEqual(catalog_tool.unlisted(found("core/baker.py", "msg('a' if x else 'b', n=1)")), [])
        self.assertEqual(catalog_tool.unlisted(found("ops/guitar.py", "msg(role.label)")), [])
        for source in ("msg(name)", "msg('a' if x else name)", "msg(f'{side} hand')"):
            errors = catalog_tool.unlisted(found("core/baker.py", source))
            self.assertEqual(len(errors), 1, source)
            self.assertIn("core/baker.py:1", errors[0])

    def test_catalog_is_current_and_valid(self):
        self.assertEqual(catalog_tool.check(catalog_tool.collect(guitar_rig), i18n.read_catalog), [])

    def test_placeholder_validation_allows_reordering(self):
        key = (i18n.CONTEXT, "{name}: {value:.2f}")
        self.assertEqual(catalog_tool.validate({key: "{value:.2f} pour {name}"}, {key}), [])
        for text in ("{wrong}", "{name}: {value}", "{name}: {value:.2f", "{name.__class__}"):
            self.assertTrue(catalog_tool.validate({key: text}, {key}), text)
        self.assertEqual(catalog_tool.validate({key: ""}, {key}), [])

    def test_update_preserves_translations_and_detects_duplicates(self):
        path = ROOT / ".tmp" / "test_catalog.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        key = (i18n.CONTEXT, "Bake")
        obsolete = (i18n.CONTEXT, "Old text")
        catalog_tool.write_catalog(path, {key: {'ops/bake.py'}}, {key: '烘焙', obsolete: '旧文本'})
        self.assertEqual(i18n.read_catalog(path), {key: '烘焙', obsolete: '旧文本'})
        path.write_text("translations = {('GuitarRig', 'Bake'): 'a', ('GuitarRig', 'Bake'): 'b'}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            i18n.read_catalog(path)

    def test_broken_locale_is_skipped_at_registration(self):
        directory = ROOT / '.tmp' / 'test_broken_locales'
        directory.mkdir(parents=True, exist_ok=True)
        key = (i18n.CONTEXT, 'GTR broken locale test')
        catalog_tool.write_catalog(directory / 'fr_FR.py', {key: {'test'}}, {key: 'bon'})
        (directory / 'de_DE.py').write_text(
            "translations = {('GuitarRig', 'Bake'): 'a', ('GuitarRig', 'Bake'): 'b'}", encoding="utf-8")
        (directory / 'es.py').write_text("translations = {", encoding="utf-8")
        output = io.StringIO()
        i18n.unregister()
        try:
            with patch.object(i18n, 'CATALOG_DIR', directory), contextlib.redirect_stdout(output):
                self.assertEqual(i18n.load_catalogs(), {'fr_FR': {key: 'bon'}})
                i18n.register()         # the add-on still registers, with the languages that read cleanly
                self.assertEqual(i18n._owner, guitar_rig.__name__)
        finally:
            i18n.unregister()
            i18n.register()
        self.assertIn('de_DE.py', output.getvalue())
        self.assertIn('es.py', output.getvalue())

    def test_registration_lifecycle_and_extension_namespace(self):
        i18n.unregister()
        try:
            i18n.register()
            self.assertEqual(i18n._owner, guitar_rig.__name__)
            i18n.unregister()
            i18n.unregister()
            self.assertIsNone(i18n._owner)
            with patch.object(i18n, '__package__', 'bl_ext.user_default.guitar_rig.i18n'):
                i18n.register()
                self.assertEqual(i18n._owner, 'bl_ext.user_default.guitar_rig')
                i18n.unregister()
        finally:
            i18n.register()

    def test_rna_identifiers_and_scene_data_are_english(self):
        self.assertEqual(bpy.ops.gtr.bake.get_rna_type().translation_context, i18n.CONTEXT)
        props = guitar_rig.props.GTR_Settings.bl_rna.properties
        self.assertEqual(props['mode'].translation_context, i18n.CONTEXT)
        self.assertEqual([item.identifier for item in props['mode'].enum_items], ['FOLLOW', 'ALIGN'])
        with patch('guitar_rig.i18n.pgettext_iface', return_value='翻译'):
            self.assertEqual(str(bonemap.SLOT_BY_KEY['chain_upper_arm_L'].title), 'Left IK Upper Arm')
            self.assertEqual(presets.load('acoustic').name, 'Acoustic Guitar')
            self.assertEqual(diagnostics.OBJECT_NAME, 'GTR_Diagnostics')
