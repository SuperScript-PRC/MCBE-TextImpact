from dataclasses import dataclass, field
from PIL import Image
from PIL.Image import Image as PILImage
import numpy as np

from .define import ITALIC_CHAR_HORIZON_PADDING
from .render_core import (
    FontMaker,
    Font,
    RuneFont,
    FMT_Bold,
    FMT_Italic,
    FMT_Obfuscated,
    RGBA_NP_MATRIX,
)

Tuple = tuple
List = list


@dataclass
class SimulateOptions:
    font_horizon_padding: int = 4
    line_padding: int = 6
    color_mapping: dict[str, tuple[int, int, int, int]] = field(
        default_factory=lambda: {
            "0": (0, 0, 0, 255),
            "1": (0, 0, 170, 255),
            "2": (0, 170, 0, 255),
            "3": (0, 170, 170, 255),
            "4": (170, 0, 0, 255),
            "5": (170, 0, 170, 255),
            "6": (255, 170, 0, 255),
            "7": (170, 170, 170, 255),
            "8": (85, 85, 85, 255),
            "9": (85, 85, 255, 255),
            "a": (85, 255, 85, 255),
            "b": (85, 255, 255, 255),
            "c": (255, 85, 85, 255),
            "d": (255, 85, 255, 255),
            "e": (255, 255, 85, 255),
            "f": (255, 255, 255, 255),
            "g": (221, 214, 5, 255),
            "h": (227, 212, 209, 255),
            "i": (227, 212, 209, 255),
            "j": (68, 58, 59, 255),
            "m": (151, 22, 7, 255),
            "n": (180, 104, 77, 255),
            "p": (222, 177, 45, 255),
            "q": (17, 160, 54, 255),
            "s": (44, 186, 168, 255),
            "t": (33, 73, 123, 255),
            "u": (154, 92, 198, 255),
            "v": (235, 114, 20, 255),
        }
    )


class TellRawSimulator:
    def __init__(
        self,
        font: FontMaker,
        options: SimulateOptions,
    ) -> None:
        self.font = font
        self.opt = options

    def _draw(
        self,
        canvas: RGBA_NP_MATRIX,
        patch: Font,
        pos: tuple[int, int],
        color: tuple[int, int, int, int],
    ):
        h, w = patch.height, patch.width
        start_x, start_y = pos
        if not patch.colored:
            for i, v in enumerate(color):
                canvas[start_y : start_y + h, start_x : start_x + w, i] = patch.mat * v
        else:
            canvas[start_y : start_y + h, start_x : start_x + w, :] = patch.mat

    def _get_color(self, fmt: int):
        color = (255, 255, 255, 255)
        if fmt != 0:
            color_code = chr(fmt & 0x7F)
            if fmt & 0x7F != 0:
                color = self.opt.color_mapping[color_code]
        return color

    def _split_format_and_text(
        self, mix: str
    ) -> tuple[list[list[str]], list[list[int]]]:
        current_fmt = 0
        lines = mix.split("\n")
        out_text: list[list[str]] = []
        out_fmt: list[list[int]] = []
        _is_fmt: bool = False
        for line in lines:
            _text: list[str] = []
            _fmt: list[int] = []
            for c in line:
                if c == "§":
                    if _is_fmt:
                        _text.append(c)
                        _fmt.append(current_fmt)
                        _is_fmt = False
                    else:
                        _is_fmt = True
                elif _is_fmt:
                    if c == "r":
                        current_fmt = 0
                    elif c == "l":
                        current_fmt |= FMT_Bold
                    elif c == "o":
                        current_fmt |= FMT_Italic
                    elif c == "k":
                        current_fmt |= FMT_Obfuscated
                    elif (ord(c) >= ord("0") and ord(c) <= ord("9")) or (
                        ord(c) >= ord("a") and ord(c) <= ord("u")
                    ):
                        current_fmt = (current_fmt & 0xFF80) | ord(c)
                    else:
                        _text.append(c)
                        _fmt.append(current_fmt)
                    _is_fmt = False
                else:
                    _text.append(c)
                    _fmt.append(current_fmt)
            out_text.append(_text)
            out_fmt.append(_fmt)
        return out_text, out_fmt

    def _get_line_width(self, line: list[str], fmt: list[int]):
        _last_fmt = 0
        _total_width = 0
        for w, f in zip(line, fmt):
            _total_width += self.font(w, f & 0xFF80).width
            # if f&FMT_Italic and not _last_fmt&FMT_Italic:
            #     _total_width+=8
            _last_fmt = f
        if _last_fmt & FMT_Italic:
            _total_width += ITALIC_CHAR_HORIZON_PADDING
        return _total_width + max(0, len(line) - 1) * self.opt.font_horizon_padding

    def __call__(self, text: str) -> PILImage:
        lines, fmts = self._split_format_and_text(text)
        max_width = max(
            [self._get_line_width(line, fmt) for line, fmt in zip(lines, fmts)]
        )
        height = len(lines) * 31 + max(len(lines) - 1, 0) * self.opt.line_padding
        mat = np.zeros((height, max_width, 4), dtype=np.uint8)
        for line_i, (line, fmt) in enumerate(zip(lines, fmts)):
            start_y = line_i * (31 + self.opt.line_padding)
            start_x = 0
            italic_start_x = -1
            for i, (c, f) in enumerate(zip(line, fmt)):
                pos = (start_x, start_y)
                patch = self.font(c, f & 0xFF80)
                self._draw(mat, patch, pos, self._get_color(f))
                if f & FMT_Italic and italic_start_x == -1:
                    italic_start_x = start_x

                start_x += patch.width + self.opt.font_horizon_padding
                if italic_start_x == -1:
                    continue
                if (i != len(line) - 1) and (fmt[i + 1] & FMT_Italic):
                    continue

                italic_end_x = start_x - self.opt.font_horizon_padding
                italic_mat = _italic(
                    mat[start_y : start_y + 31, italic_start_x:italic_end_x]
                )
                w = italic_mat.shape[1]
                paste_x = max(italic_start_x - 4, 0)
                mat[start_y : start_y + 31, paste_x : paste_x + w] = italic_mat
                # y_start=start_y-2
                # for shift in [4,3,2,1,0,-1,-2,-3]:
                #     y_end=y_start+4
                #     orig=mat[y_start:y_end,italic_start_x:italic_end_x].copy()
                #     mat[y_start:y_end,italic_start_x:italic_end_x]=0
                #     mat[y_start:y_end,italic_start_x+shift:italic_end_x+shift]=orig
                #     y_start=y_end
                italic_start_x = -1

        image = Image.fromarray(mat)
        return image


def _shear_image(img: RGBA_NP_MATRIX, k: float):
    h, w, c = img.shape
    new_w = int(np.ceil(w + abs(k) * h))
    offset = new_w - w + 0
    out = np.zeros((h, new_w, c), dtype=np.uint8)

    for y in range(h):
        for x_new in range(new_w):
            x = x_new + k * y - offset
            _x, _y = int(np.round(x)), y
            if 0 <= _x < img.shape[1] and 0 <= _y < img.shape[0]:
                out[y, x_new] = img[_y, _x]

    return np.clip(out, 0, 255).astype(np.uint8)


def _italic(mat: RGBA_NP_MATRIX):
    k = np.tanh(np.deg2rad(15))
    return _shear_image(mat, k)


def render(
    img_dir_path: str, text: str, opt: SimulateOptions | None = None
) -> PILImage:
    simulator = TellRawSimulator(
        RuneFont(img_dir_path), options=opt or SimulateOptions()
    )
    return simulator(text)
