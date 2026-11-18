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


def _unwrap(exc):
    """The message an exception was raised with, or else its text exactly as `str()` and `{}` show it."""
    if len(exc.args) == 1 and isinstance(exc.args[0], Message):
        return exc.args[0]
    return str(exc)


def render(value, lookup):
    """Render using a preference-aware lookup; ordinary arguments are always literal."""
    if isinstance(value, BaseException):
        value = _unwrap(value)
    if isinstance(value, Joined):
        return value.separator.join(render(part, lookup) if isinstance(part, Message) else str(part)
                                    for part in value.parts)
    if isinstance(value, Message):
        template = lookup(value.template, CONTEXT)
        values = {key: _unwrap(item) if isinstance(item, BaseException) else item
                  for key, item in value.values.items()}
        values = {key: render(item, lookup) if isinstance(item, Message) else item for key, item in values.items()}
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
        return _encode(_unwrap(value))
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
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            return []   # a damaged report must not break the panel that draws it
    # Files saved before i18n contain tab-separated, already formatted English.
    return [(level, value) for line in text.splitlines()
            for level, _, value in [line.partition("\t")] if value]


NO_BREAK_BEFORE = frozenset(")]}.,:;?!%、。，．：；？！）］｝〉》」』】〕’”‰")
NO_BREAK_AFTER = frozenset("([{（［｛〈《「『【〔‘“")


def _columns(char):
    return 0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in "WF" else 1


def _can_break(text, index):
    """Whether a line may end before text[index]."""
    char, before = text[index], text[index - 1]
    if char.isspace():
        return True
    size = _columns(char)
    if size == 2 or size and _columns(before) == 2:
        # Wide text has no spaces: break between any two glyphs that punctuation does not bind.
        return char not in NO_BREAK_BEFORE and before not in NO_BREAK_AFTER
    # After the hyphen of a compound word, as textwrap does: "wrist-|rotation", but not "T-pose" or "-15".
    return (before == "-" and index >= 3 and text[index - 2].isalpha() and text[index - 3].isalnum()
            and char.isalpha() and text[index + 1:index + 2].isalpha())


def _line_end(text, width):
    """Index where the first line of `text` ends: the last place to break that keeps it within `width`."""
    columns, best = 0, 0
    for index, char in enumerate(text):
        size = _columns(char)
        if index:
            if _can_break(text, index):
                best = index
            if columns + size > width:
                if 0 < best < index:
                    # A word longer than a whole line is cut wherever it stands: start it on this line.
                    stop = next((i for i in range(index + 1, len(text)) if _can_break(text, i)), len(text))
                    if sum(_columns(c) for c in text[best:stop].lstrip()) > width:
                        return index
                return best or index
        columns += size
    return len(text)


def wrap(text, width):
    """Wrap by approximate display columns, including wide CJK glyphs and combining marks."""
    lines = []
    for paragraph in text.splitlines() or [""]:
        remaining = paragraph.strip()
        if not remaining:
            lines.append("")
        while remaining:
            end = _line_end(remaining, width)
            lines.append(remaining[:end].rstrip())
            remaining = remaining[end:].lstrip()
    return lines
