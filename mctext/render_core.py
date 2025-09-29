import os
from dataclasses import dataclass, field
from typing import Dict, Tuple, Union
from PIL import Image
from PIL.Image import Image as PILImage
from abc import ABC, abstractmethod
import numpy as np

from .define import CHAR_HORIZON_PADDING, SPACE_WIDTH

GRAY_NP_MATRIX = np.ndarray[tuple[int], np.dtype[np.uint8]]
RGB_NP_MATRIX = np.ndarray[tuple[int, int, int], np.dtype[np.uint8]]
RGBA_NP_MATRIX = np.ndarray[tuple[int, int, int, int], np.dtype[np.uint8]]

FMT_Obfuscated = 1 << 8
FMT_Bold = 1 << 9
FMT_Italic = 1 << 10


@dataclass
class Font:
    mat: Union[GRAY_NP_MATRIX, RGBA_NP_MATRIX]
    colored: bool = False

    @property
    def width(self) -> int:
        return self.mat.shape[1]

    @property
    def height(self) -> int:
        return self.mat.shape[0]

    def clone(self):
        return Font(self.mat.copy(), self.colored)


class FontMaker(ABC):
    @abstractmethod
    def __call__(self, rune: str, fmt: int) -> Font:
        raise NotImplementedError

    @staticmethod
    def rune_to_idx(rune: str):
        code = rune.encode(encoding="utf-16")[-2:]
        inx = int.from_bytes(code, byteorder="little")
        return inx >> 8, ((inx & 0xF0) >> 4), inx & 0xF

    @staticmethod
    def rune_to_raw_idx(rune: str) -> int:
        code = rune.encode(encoding="utf-16")[-2:]
        return int.from_bytes(code, byteorder="little")

    @staticmethod
    def idx_to_rune(group: int, row: int, col: int) -> str:
        idx = group * (16 * 16) + row * 16 + col
        code = idx.to_bytes(2, byteorder="little")
        rune = code.decode(encoding="utf-16")
        return rune


class RuneFont(FontMaker):
    SPACE_WIDTH = SPACE_WIDTH

    def __init__(self, root_dir: str) -> None:
        self.root_dir = root_dir

        self.cached_group: Dict[int, Tuple[PILImage, bool]] = {}  # 16*32,16*32
        self.cached_rune: Dict[Tuple[str, int], Font] = {}  # 32*31

    def _get_group(self, group_idx: int) -> Tuple[PILImage, bool] | None:
        if group_idx in self.cached_group:
            return self.cached_group[group_idx]
        else:
            file_path = os.path.join(self.root_dir, f"glyph_{group_idx:02X}.png")
            if not os.path.exists(file_path):
                return None
            png = Image.open(file_path)
            if png.mode != "RGBA":
                png = png.convert("RGBA")
            png = png.resize((512, 512), resample=Image.Resampling.NEAREST)
            mat = np.array(png, dtype=np.uint8)
            colored = not (
                np.all(mat[:, :, 0] == mat[:, :, 1])
                and np.all(mat[:, :, 1] == mat[:, :, 2])
            )
            if not colored:
                png = png.convert("1")
            self.cached_group[group_idx] = (png, colored)
            return png, colored

    @staticmethod
    def _tight_font(square: PILImage) -> PILImage:
        bbox = square.getbbox()
        if bbox is None:
            x1, x2 = 0, RuneFont.SPACE_WIDTH
        else:
            x1, y1, x2, y2 = bbox
        return square.crop((x1, 0, x2, 31))

    def __call__(self, rune: str, fmt: int) -> Font:
        if (rune, fmt) in self.cached_rune:
            return self.cached_rune[(rune, fmt)]
        g, r, c = self.rune_to_idx(rune)
        page = self._get_group(g)
        if page is None:
            assert rune != " "
            return self.__call__(" ", fmt)
        png, colored = page
        posx = c * 32
        posy = r * 32
        cropped = png.crop((posx, posy, posx + 32, posy + 31))
        tighted = self._tight_font(cropped)
        # H,W
        np_matrix = np.array(tighted, dtype=np.uint8)
        font = Font(np_matrix, colored)
        if fmt != 0 and not font.colored:
            font = font.clone()
            if fmt & FMT_Obfuscated:
                font.mat.fill(1)
            # if fmt & FMT_Italic:
            #     mat=font.mat
            #     h,w=mat.shape
            #     offset=2
            #     start=20
            #     nm=np.zeros((h,w+offset),dtype=np.uint8)
            #     nm[:start,offset:32+offset]=mat[:start,:32]
            #     nm[start:,:-offset]=mat[start:,:]
            #     font.mat=nm
            if fmt & FMT_Bold:
                mat = font.mat
                h, w = mat.shape
                pad = 2
                nm = np.zeros((h, w + pad), dtype=np.uint8)
                for off in range(pad):
                    nm[:, off : off - pad] |= mat[:, :]
                font.mat = nm
        self.cached_rune[(rune, fmt)] = font
        return font


@dataclass
class SimulateOptions:
    font_horizon_padding: int = CHAR_HORIZON_PADDING
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
            "h": (222, 214, 5, 255),
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
