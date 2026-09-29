"""
Deterministic layout engine with measured text for Plant MitoCarta maps.

Principles:
- Text is measured before sizing boxes (box derives from text, not the reverse).
- Font metrics support matplotlib TextPath if available, with deterministic fallback.
- Okabe-Ito friendly layout constants.
- Multi-lane, multi-compartment bounding box derivation.
"""
from __future__ import annotations

import dataclasses
import functools
import math
from typing import Iterable, Sequence

FONT_FAMILY = "DejaVu Sans"
SVG_FONT_STACK = "'DejaVu Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif"

PAD_X = 14.0
PAD_Y = 10.0
LINE_SPACING = 1.25
MIN_GUTTER_X = 36.0
MIN_GUTTER_Y = 32.0
COMPARTMENT_PAD = 28.0
CANVAS_MARGIN = 32.0

# Approximate relative glyph widths for Helvetica/DejaVu Sans fallback
AVG_CHAR_WIDTH = 0.58


@functools.lru_cache(maxsize=4096)
def measure(text: str, size: float, weight: str = "normal") -> tuple[float, float]:
    """Return (width, height) of a single text run."""
    if not text:
        return (0.0, size)
    try:
        from matplotlib.font_manager import FontProperties
        from matplotlib.textpath import TextPath
        fp = FontProperties(family=FONT_FAMILY, size=size, weight=weight)
        tp = TextPath((0, 0), text, prop=fp)
        bb = tp.get_extents()
        return (float(bb.width), float(size))
    except Exception:
        # High-fidelity deterministic character-based estimation
        width = len(text) * size * (0.62 if weight == "bold" else AVG_CHAR_WIDTH)
        return (float(width), float(size))


def wrap(text: str, size: float, max_width: float, weight: str = "normal") -> list[str]:
    """Greedy word wrap against measured width."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if measure(trial, size, weight)[0] <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def text_block(
    text: str, size: float, max_width: float, weight: str = "normal"
) -> tuple[list[str], float, float]:
    """Wrap text and return (lines, block_width, block_height)."""
    lines = wrap(text, size, max_width, weight)
    width = max((measure(ln, size, weight)[0] for ln in lines), default=0.0)
    height = len(lines) * size * LINE_SPACING
    return lines, width, height


@dataclasses.dataclass
class Box:
    """Axis-aligned bounding box in SVG coordinate space."""
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2.0

    @property
    def cy(self) -> float:
        return self.y + self.h / 2.0

    def expanded(self, pad: float) -> Box:
        return Box(self.x - pad, self.y - pad, self.w + 2 * pad, self.h + 2 * pad)

    def contains(self, other: Box, tol: float = 0.01) -> bool:
        return (
            self.x - tol <= other.x
            and self.y - tol <= other.y
            and other.x2 <= self.x2 + tol
            and other.y2 <= self.y2 + tol
        )


@dataclasses.dataclass
class LaidOutNode:
    id: str
    box: Box
    lines: list[str]
    font_size: float
    font_weight: str
    sublines: list[str] = dataclasses.field(default_factory=list)
    sub_font_size: float = 0.0
    lane: str | None = None
    row: int = 0
    col: int = 0
    reserve_bottom: float = 0.0
    payload: dict = dataclasses.field(default_factory=dict)


def size_node(
    label: str,
    font_size: float,
    *,
    sublabel: str = "",
    sub_font_size: float = 0.0,
    preferred_width: float = 200.0,
    min_width: float = 100.0,
    weight: str = "bold",
) -> tuple[Box, list[str], list[str]]:
    """Size a box strictly around its measured text."""
    lines, w, h = text_block(label, font_size, preferred_width, weight)
    sublines: list[str] = []
    if sublabel:
        sub_size = sub_font_size or font_size * 0.8
        sublines, sw, sh = text_block(sublabel, sub_size, preferred_width)
        w = max(w, sw)
        h += sh

    # Widen for any single unbroken token
    for token in label.replace("\n", " ").split():
        w = max(w, measure(token, font_size, weight)[0])

    w = max(w + 2 * PAD_X, min_width)
    h = h + 2 * PAD_Y
    return Box(0, 0, w, h), lines, sublines


def edge_anchors(src: Box, dst: Box) -> tuple[tuple[float, float], tuple[float, float]]:
    """Compute anchor points on box perimeters for an edge between src and dst."""
    # Determine primary direction
    dx = dst.cx - src.cx
    dy = dst.cy - src.cy

    if abs(dx) > abs(dy):
        # Horizontal connection
        if dx > 0:
            p1 = (src.x2, src.cy)
            p2 = (dst.x, dst.cy)
        else:
            p1 = (src.x, src.cy)
            p2 = (dst.x2, dst.cy)
    else:
        # Vertical connection
        if dy > 0:
            p1 = (src.cx, src.y2)
            p2 = (dst.cx, dst.y)
        else:
            p1 = (src.cx, src.y)
            p2 = (dst.cx, dst.y2)
    return p1, p2
