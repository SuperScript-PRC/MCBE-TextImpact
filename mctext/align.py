import numpy
from pathlib import Path
from .define import (
    BOLD_PAD,
    SPACE_WIDTH,
    CHAR_HORIZON_PADDING,
    ITALIC_CHAR_HORIZON_PADDING,
)

from .render_core import RuneFont
from .utils import find_closest

with open(Path(__file__).parent / "font_widths.dat", "rb") as f:
    _warr = numpy.fromfile(f, dtype=numpy.uint8)


def get_char_width(char: str, bold=False) -> int:
    idx = RuneFont.rune_to_raw_idx(char)
    return int(_warr[idx] + (BOLD_PAD if bold else 0))


def get_line_width(line: str) -> int:
    if "\n" in line:
        raise ValueError("Line contains newline; use get_lines_length instead")
    width = 0
    _bold = False
    _italic = False
    _fmt = False
    length = 0
    for char in line:
        if char == "§":
            _fmt = True
            continue
        elif _fmt:
            _fmt = False
            if char == "l":
                _bold = True
            elif char == "o":
                _italic = True
            elif char == "r":
                _bold = False
                _italic = False
            continue
        length += 1
        width += get_char_width(char, _bold)
    width += max(0, length - 1) * CHAR_HORIZON_PADDING
    if _italic:
        width += ITALIC_CHAR_HORIZON_PADDING
    return width


def get_lines_width(lines: list[str]) -> int:
    return max(get_line_width(line) for line in lines)


def get_specific_length_spaces(length: int):
    return get_specific_length_spaces_and_diff(length)[0]


def get_specific_length_spaces_and_diff(length: int, *, prev_diff=0):
    solutions, min_diff = find_closest(
        SPACE_WIDTH + CHAR_HORIZON_PADDING,
        SPACE_WIDTH + BOLD_PAD + CHAR_HORIZON_PADDING,
        length + prev_diff,
    )
    a, b, _ = solutions[0]
    s = "§l" + " " * b + "§r" + " " * a
    return s, int(min_diff)


def cut_by_length(line: str, _spaces: int) -> list[str]:
    width = 0
    spaces = _spaces * SPACE_WIDTH + max(0, _spaces - 1) * CHAR_HORIZON_PADDING
    _bold = False
    _italic = False  # Sorry that this is useless now
    _fmt = False
    outputs: list[str] = []
    cached = ""
    for char in line:
        if width >= spaces or char == "\n":
            outputs.append(cached)
            cached = ""
            width = 0
        if char == "§":
            _fmt = True
            continue
        elif _fmt:
            _fmt = False
            if char == "l":
                _bold = True
            elif char == "o":
                _italic = True
            elif char == "r":
                _bold = False
                _italic = False
            continue
        width += get_char_width(char, _bold) + CHAR_HORIZON_PADDING
        cached += char
    if cached.strip():
        outputs.append(cached)
    return outputs


def align_any_and_get_diff(text: str, spaces: int, *, prev_diff=0):
    width = get_line_width(text)
    spaces_left = spaces * SPACE_WIDTH - width
    if spaces_left < 0:
        return "", spaces_left
    return get_specific_length_spaces_and_diff(spaces_left, prev_diff=prev_diff)


def align_any(text: str, spaces: int):
    return align_any_and_get_diff(text, spaces)[0]


def align_left(text: str, spaces: int):
    return text + align_any(text, spaces)


def align_left_and_get_diff(text: str, spaces: int, *, prev_diff=0):
    t, diff = align_any_and_get_diff(text, spaces, prev_diff=prev_diff)
    return text + t, diff


def align_right(text: str, spaces: int):
    return align_any(text, spaces) + text


def align_right_and_get_diff(text: str, spaces: int, *, prev_diff=0):
    t, diff = align_any_and_get_diff(text, spaces, prev_diff=prev_diff)
    return t + text, diff


def align_simple(*text_or_spaces: str | int):
    string = ""
    dif = 0
    prev_arg = None
    param_len = len(text_or_spaces)
    for i, arg in enumerate(text_or_spaces):
        if i == param_len - 1:
            if isinstance(arg, str):
                string += arg
            elif isinstance(arg, int):
                string += align_right("", arg)
            break
        if prev_arg is None:
            prev_arg = arg
            continue
        if isinstance(prev_arg, str) and isinstance(arg, int):
            s, dif = align_left_and_get_diff(prev_arg, arg, prev_diff=-dif)
            string += s
            prev_arg = None
        elif isinstance(prev_arg, int) and isinstance(arg, str):
            s, dif = align_right_and_get_diff(arg, prev_arg, prev_diff=-dif)
            string += s
            prev_arg = None
        else:
            raise ValueError("Invalid param type")
    return string
