from typing import Callable
from .align import get_line_width

from typing import List, Tuple, Optional


# def get_line_width(text:str):
#     return simu.compute_width(text)[0]

S = get_line_width(" ") + 4
B = get_line_width("§l ") + 4
print(S, B)


def _check_same_parity(c: List[int]) -> bool:
    """检查奇偶是否相同"""
    if not c:
        return True
    p = c[0] & 1
    return all((ci & 1) == p for ci in c)


def solve_xy(c: int) -> Optional[Tuple[int, int]]:
    if c % 2 != 0:
        return None  # 无解

    m = c // 2
    # 通解: x = -m + 7t, y = m - 6t
    a, b = S // 2, B // 2
    t_min = (m + a) // b  # ceil(m/7)
    t_max = m // a  # floor(m/6)
    if t_min <= t_max:
        t = t_min
        x = -m + b * t
        y = m - a * t
        return (x, y)
    else:
        return None


def resolve(c: List[int]) -> Optional[List[Tuple[int, int]]]:
    if not c:
        return None

    if not _check_same_parity(c):
        return None
    parity = c[0] & 1
    width = max(c)
    if (width & 1) != parity:
        width += 1

    while True:
        res: List[Tuple[int, int]] = []
        ok = True
        for ci in c:
            di = width - ci
            ret = solve_xy(di)

            if ret is None:
                ok = False
                break
            x, y = ret
            assert x * S + y * B + ci == width
            res.append(ret)
        if ok:
            return res
        else:
            width += 2
    raise ValueError


def pad(texts: List[str]) -> List[str]:
    cs = [get_line_width(t) for t in texts]
    res = resolve(cs)
    assert res is not None
    pads = [
        "§r"
        + ((" " * ns) if ns > 0 else "")
        + (("§l" + " " * nb + "§r") if nb > 0 else "")
        for (ns, nb) in res
    ]
    return [t + p for t, p in zip(texts, pads)]


class Padder:
    def __init__(self, text_lines: str, pad: Callable[[List[str]], List[str]]) -> None:
        lines = text_lines.split("\n")
        self.pending_lines = lines
        self.padded = ["" for _ in lines]
        self._pad_i: int = 1
        self._pad_mark = self._pad_mark = f"(pad{self._pad_i})"
        self._pad = pad

    def _step(self):
        assert not self._all_done
        match_list: List[str] = []
        match_index: List[int] = []
        for i, (c, p) in enumerate(zip(self.padded, self.pending_lines)):
            if p.find(self._pad_mark) == -1:
                continue
            match_index.append(i)
            t, r = p.split(self._pad_mark, 1)
            self.pending_lines[i] = r
            match_list.append(c + t)
        out = self._pad(match_list)
        for i, o in zip(match_index, out):
            self.padded[i] = o
        self._pad_i += 1
        self._pad_mark = f"(pad{self._pad_i})"

    @property
    def _all_done(self):
        return all(ln.find(self._pad_mark) == -1 for ln in self.pending_lines)

    def _finish(self):
        return "\n".join([ln + t for ln, t in zip(self.padded, self.pending_lines)])

    def __call__(self) -> str:
        while not self._all_done:
            self._step()
        return self._finish()


def pad_with_format(
    text: str, pad_fn: Optional[Callable[[List[str]], List[str]]] = None
):
    return Padder(text, pad_fn or pad)()
