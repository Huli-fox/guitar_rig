"""Language-neutral messages. This module deliberately has no Blender dependency."""

import json
import numbers
import unicodedata

CONTEXT = "GuitarRig"
PREFIX = "GTR_MESSAGES_V1\n"


class Message(str):
    """An English string with its template and arguments retained for later translation."""

    def __new__(cls, template, **values):
        obj = super().__new__(cls, template.format(**values) if values else template)
        obj.template = template
        obj.values = values
        return obj

    def __add__(self, other):
        return join((self, other), "")

    def __radd__(self, other):
        return join((other, self), "")


class Joined(Message):
    def __new__(cls, parts, separator):
        obj = str.__new__(cls, separator.join(str(part) for part in parts))
        obj.parts = parts
        obj.separator = separator
        return obj


def msg(template, **values):
    """Mark a complete English template; interpolate only when rendering it."""
    return Message(template, **values)


def mark(text):
    """Mark metadata for catalog extraction without translating it at import time."""
    return text


def join(parts, separator=", "):
    """Join independently meaningful messages, retaining their translation metadata."""
    return Joined(tuple(parts), separator)


def render(value, lookup):
    """Render using a preference-aware lookup; ordinary arguments are always literal."""
    if isinstance(value, BaseException):
        value = value.args[0] if len(value.args) == 1 else str(value)
    if isinstance(value, Joined):
        return value.separator.join(render(part, lookup) if isinstance(part, Message) else str(part)
                                    for part in value.parts)
    if isinstance(value, Message):
        template = lookup(value.template, CONTEXT)
        values = {key: render(item, lookup) if isinstance(item, (Message, BaseException)) else item
                  for key, item in value.values.items()}
        try:
            return template.format(**values) if values else template
        except (KeyError, ValueError, IndexError, AttributeError, TypeError):
            # A broken community translation must not break drawing or a completed bake.
            return str(value)
    return lookup(str(value), CONTEXT)


def _encode(value):
    if isinstance(value, Joined):
        return {"join": [_encode(part) for part in value.parts], "separator": value.separator}
    if isinstance(value, Message):
        return {"message": value.template, "values": {key: _encode(item) for key, item in value.values.items()}}
    if isinstance(value, BaseException):
        return _encode(value.args[0]) if len(value.args) == 1 else str(value)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, numbers.Real):
        return float(value)
    # Reports snapshot display values, never Blender objects or mutable scene data.
    return str(value)


def _decode(value):
    if isinstance(value, dict):
        if "join" in value:
            return join((_decode(part) for part in value["join"]), value["separator"])
        return msg(value["message"], **{key: _decode(item) for key, item in value["values"].items()})
    return value


def dumps(messages):
    return PREFIX + json.dumps([(level, _encode(text)) for level, text in messages], ensure_ascii=False)


def loads(text):
    if text.startswith(PREFIX):
        try:
            return [(level, _decode(value)) for level, value in json.loads(text[len(PREFIX):])]
        except (ValueError, TypeError, KeyError):
            return []
    # Files saved before i18n contain tab-separated, already formatted English.
    return [(level, value) for line in text.splitlines()
            for level, _, value in [line.partition("\t")] if value]


def wrap(text, width):
    """Wrap by approximate display columns, including wide CJK glyphs and combining marks."""
    lines = []
    for paragraph in text.splitlines() or [""]:
        remaining = paragraph.strip()
        while remaining:
            columns, end, space = 0, 0, -1
            for index, char in enumerate(remaining):
                size = 0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in "WF" else 1
                if columns + size > width and index:
                    break
                columns += size
                end = index + 1
                if char.isspace():
                    space = index
            if end < len(remaining) and space > 0:
                end = space
            lines.append(remaining[:end].rstrip())
            remaining = remaining[end:].lstrip()
        if not paragraph.strip():
            lines.append("")
    return lines
