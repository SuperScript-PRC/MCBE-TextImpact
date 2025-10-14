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


def get_last_style(line: str):
    style_color = ""
    style_bold = False
    style_italic = False
    prev_is_fmt = False
    for char in line:
        if prev_is_fmt:
            if char == "r":
                style_color = ""
                style_bold = False
                style_italic = False
            elif char == "o":
                style_italic = True
            elif char == "l":
                style_bold = True
            else:
                style_color = char
            prev_is_fmt = False
        elif char == "§":
            prev_is_fmt = True
    return style_color, style_bold, style_italic


def cut_by_length(line: str, _spaces: int, keep_last_style=True) -> list[str]:
    """
    根据给定长度切分文本。

    Args:
        line (str): 文本
        _spaces (int): 最大长度
        keep_last_style (bool): 是否保持行最后的格式

    Returns:
        list[str]: 切分后的文本
    """
    if _spaces <= 0:
        raise ValueError("Length must be positive")
    width = 0
    spaces = _spaces * SPACE_WIDTH + max(0, _spaces - 1) * CHAR_HORIZON_PADDING
    _lcolor = ""
    _bold = False
    _italic = False  # Sorry that this is useless now
    _fmt = False
    outputs: list[str] = []
    cached = ""
    line_chars = list(line)
    while line_chars:
        char = line_chars.pop(0)
        need_continue = False
        if width >= spaces or char == "\n":
            if keep_last_style:
                inserted = ""
                if _lcolor:
                    inserted += "§" + _lcolor
                if _bold:
                    inserted += "§l"
                if _italic:
                    inserted += "§o"
                if char != "\n":
                    line_chars = [*inserted, char, *line_chars]
                    need_continue=True   
            outputs.append(cached)
            cached = ""
            width = 0
            if char == "\n" or need_continue:
                continue
        if char == "§":
            _fmt = True
        elif _fmt:
            _fmt = False
            if char == "l":
                _bold = True
            elif char == "o":
                _italic = True
            elif char == "r":
                _bold = False
                _italic = False
                _lcolor = ""
            else:
                _lcolor = char
        else:
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


def align_center(text: str, spaces: int):
    textlen = get_line_width(text)
    rest = spaces * SPACE_WIDTH - textlen
    return (
        get_specific_length_spaces(int(rest / 2))
        + text
        + get_specific_length_spaces(round(rest / 2))
    )


def align_simple(*text_or_spaces: tuple[str, int] | tuple[int, str] | str):
    string = ""
    dif = 0
    for arg_tp in text_or_spaces:
        if isinstance(arg_tp, str):
            string += arg_tp
        else:
            arg1, arg2 = arg_tp
            if isinstance(arg1, str) and isinstance(arg2, int):
                s, dif = align_left_and_get_diff(arg1, arg2, prev_diff=-dif)
                string += s
            elif isinstance(arg1, int) and isinstance(arg2, str):
                s, dif = align_right_and_get_diff(arg2, arg1, prev_diff=-dif)
                string += s
            else:
                raise ValueError("Invalid param type")
    return string


def yield_chars_and_length(line: str):
    """
    根据给定长度切分文本。

    Args:
        line (str): 文本
        _spaces (int): 最大长度

    Returns:
        list[str]: 切分后的文本
    """
    width = 0
    _bold = False
    _italic = False  # Sorry that this is useless now
    _fmt = False
    for char in line:
        if char == "§":
            _fmt = True
        elif _fmt:
            _fmt = False
            if char == "l":
                _bold = True
            elif char == "o":
                _italic = True
            elif char == "r":
                _bold = False
                _italic = False
        else:
            width += get_char_width(char, _bold) + ITALIC_CHAR_HORIZON_PADDING
        yield char, width
