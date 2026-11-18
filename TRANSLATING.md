# Translating GuitarRig

GuitarRig uses Blender's language and translation preferences. English is the source
language. Each other language is a UTF-8 Python dictionary in `i18n/locales/`, named
after a Blender locale, such as `fr_FR.py` or `zh_HANS.py`. Empty or missing entries
fall back to English. Partial translations are welcome.

No external Python packages, gettext compiler, or translation service are needed.
Catalogs are read as literal data; they contain no executable Python code.

## Add a language

From the `guitar_rig` directory, run:

```sh
blender -b --factory-startup --python-exit-code 1 --python tools/i18n.py -- update --locale fr_FR
```

This generates `i18n/locales/fr_FR.py` and updates `_template.py`. The template is a
reference catalog and is never registered as a language. Use a locale supported by
the Blender versions you target. Blender's Python Console can list the identifiers:

```python
[(item.identifier, item.name) for item in bpy.context.preferences.view.bl_rna.properties['language'].enum_items]
```

Edit the values on the right side of the dictionary entries:

```python
translations = {
    ('GuitarRig', 'Bake'): 'Cuire',
    ('GuitarRig', 'Captured at frame {frame}'): 'Capturé à l’image {frame}',
}
```

The first part of each key is the translation context. Keep both parts of the key
unchanged. Labels and dynamic messages use `GuitarRig`; Blender's RNA tooltips and
the sidebar category use the default `*` context. Comments show the source locations
or the Blender class using each entry.

Keep named placeholders, conversions, and numeric formats exactly as written:
`{frame}`, `{name!r}`, `{distance:.2f}`. You may reorder placeholders to suit your
language. Preserve the number of occurrences. Use `{{` and `}}` for literal braces
in a formatted message. Translate whole sentences naturally; units, directions,
and Blender terms should be consistent throughout the catalog.

Object, bone, action, and user preset names are literal data. For example,
`GTR_ROOT`, `GuitarBake`, and `GuitarRefine` in instructions refer to real scene
names and should remain recognizable. Internal property names, enum identifiers,
diagnostic curve keys, and animation paths do not change with the UI language.
Editable magnet names also remain as entered or loaded from a preset.

## Update and validate

After source changes, update all catalogs:

```sh
blender -b --factory-startup --python-exit-code 1 --python tools/i18n.py -- update
blender -b --factory-startup --python-exit-code 1 --python tools/i18n.py -- check
```

Updating preserves existing translations, adds empty entries for new messages, and
keeps obsolete entries in a separate section for reference. You can remove obsolete
entries after reviewing them. Source changes intentionally create a new entry;
review the old translation before copying it across. Source-reference comments are
generated and will be refreshed on update.

Checking reports translation coverage and rejects unsupported locale filenames, duplicate keys, malformed entries,
invalid format strings, and placeholder mismatches. It also detects an outdated
template. Addon tests include the catalog check:

```sh
blender -b --factory-startup --python-exit-code 1 --python tests/run.py -- -k test_i18n
```

For this checkout on Windows, Blender is `D:/Blender/blender.exe` (or
`/d/Blender/blender` in a compatible shell). Keep test artifacts in `guitar_rig/.tmp/`.

## Preview and submit

1. Build and install the extension, or use your normal development installation.
2. In **Preferences > Interface > Translation**, choose the language and enable
   interface, tooltip, and report translation as needed.
3. Restart Blender after editing a catalog, or disable and re-enable the addon.
   Changing the language itself does not require restarting.
4. Check the Guitar sidebar at narrow and wide widths, tooltips, operator reports,
   and viewport overlays. Try an incomplete setup to see validation messages, then
   calibrate and bake a character to see saved reports.
5. Run the validation command and submit your locale file. Include an updated
   template if you also changed source messages.

New saved reports retain their English templates and arguments, so they follow the
current language after reopening a `.blend` file. Reports created by older versions
remain readable in their original wording until you regenerate them. Help text is
translated before wrapping, with display-width estimates for Chinese, Japanese,
and combining characters. Very narrow layouts and font-dependent widths still need
visual review by a speaker of the language.

## For developers

Use English literals for RNA property names/descriptions and class labels, with
`translation_context=CONTEXT` or `bl_translation_context = CONTEXT`. Use
`text_ctxt=CONTEXT` for static layout text. Do not translate these at import time.

For dynamic text, retain the template until the display boundary:

```python
from ..i18n import CONTEXT, iface, msg, report as rpt

message = msg('Captured at frame {frame}', frame=scene.frame_current)
layout.label(text=iface(message), translate=False)
self.report({'INFO'}, rpt(message))
```

Use `tip()` for dynamic tooltips and poll explanations, `iface()` for UI and overlay
text, and `report()` for operator reports. Each respects its Blender preference.
The reports helper in `ops/common.py` handles lists of `(severity, message)` pairs.
`draw_messages()` translates and wraps those lists and prevents double translation.

Arguments are literal unless explicitly wrapped in `msg()`. This prevents an object
called `Bake` from being translated accidentally. Use nested messages for built-in
terms that need their own translations. Prefer complete templates over fragments,
English case conversion, or assembling plurals by appending `s`. Count-neutral
phrasing such as `Actions removed: {count}` avoids assuming a language's plural rules.

`msg()` values behave as English strings for existing diagnostics and tests, but
retain metadata for translation. Keep them intact: f-strings, `str()`, case changes,
and ordinary string joins discard that metadata. Use `i18n.join()` for lists of
independent messages, and pass an exception directly to `report()` to retain its
message. Store report lists through `calibrate.format_messages()` and read them
through `calibrate.parse_messages()`.

The extractor combines explicit `msg()`/`mark()` calls, layout text, registered RNA,
generated bone/landmark metadata, and bundled preset text. Mark standalone display
constants with `mark('English text')`; it is an identity function used by extraction.
For new generated metadata, extend `tools/i18n.py:collect()` and its coverage test.

The extractor reads literal text only, so `msg(name)` contributes nothing to the
catalog and `name` would stay English in every language. `check` rejects such calls
unless `DYNAMIC` in `tools/i18n.py` lists them, next to the place their texts are
extracted from. Prefer a literal, or one complete template per case:

```python
msg('Smoothed {count} arm curves' if arm else 'Smoothed {count} guitar curves', count=count)
```

Name placeholders for what they hold (`{frame}`, `{distance}`, `{side}`), since the
name is all a translator sees of the value. A placeholder name is part of the catalog
key: renaming one later orphans every existing translation of that message.

Always regenerate the template after changing messages. No application code changes
are needed to add a locale file. Extension builds include the locale catalogs but not
`_template.py`, which is only a starting point for contributors. A locale file that
cannot be read is skipped with a console message when the add-on is enabled.
