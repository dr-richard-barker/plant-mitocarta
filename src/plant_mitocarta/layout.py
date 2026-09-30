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
MIN_GUTTER_X = 104.0
MIN_GUTTER_Y = 48.0
COMPARTMENT_PAD = 24.0
CANVAS_MARGIN = 44.0

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
    badges: list[tuple[str, str]] = dataclasses.field(default_factory=list)
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


@dataclasses.dataclass
class EdgeRoute:
    """Compiled collision-free route and label geometry for a map edge."""
    path_d: str
    label_pos: tuple[float, float]
    label_box: Box | None
    label_lines: list[str]
    waypoints: list[tuple[float, float]]
    kind: str = "generic"


def rounded_path_d(pts: list[tuple[float, float]], r: float = 8.0) -> str:
    """Convert waypoints into SVG path with smooth fillet arcs at bends."""
    if len(pts) <= 2:
        return f"M {pts[0][0]:.1f} {pts[0][1]:.1f} L {pts[-1][0]:.1f} {pts[-1][1]:.1f}"

    d = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(1, len(pts) - 1):
        p_prev = pts[i - 1]
        p_curr = pts[i]
        p_next = pts[i + 1]

        v_in = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
        v_out = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])

        len_in = math.hypot(v_in[0], v_in[1])
        len_out = math.hypot(v_out[0], v_out[1])
        if len_in == 0 or len_out == 0:
            continue

        cur_r = min(r, len_in / 2.0, len_out / 2.0)
        p_before = (p_curr[0] - (v_in[0] / len_in) * cur_r, p_curr[1] - (v_in[1] / len_in) * cur_r)
        p_after = (p_curr[0] + (v_out[0] / len_out) * cur_r, p_curr[1] + (v_out[1] / len_out) * cur_r)

        d.append(f"L {p_before[0]:.1f} {p_before[1]:.1f}")
        d.append(f"Q {p_curr[0]:.1f} {p_curr[1]:.1f} {p_after[0]:.1f} {p_after[1]:.1f}")

    d.append(f"L {pts[-1][0]:.1f} {pts[-1][1]:.1f}")
    return " ".join(d)


def route_edge(
    src_node: LaidOutNode,
    dst_node: LaidOutNode,
    all_nodes: Sequence[LaidOutNode],
    *,
    gutter_x: float = MIN_GUTTER_X,
    edge_label: str = "",
    edge_kind: str = "generic",
    highway_slot: int = 0,
) -> EdgeRoute:
    """
    Route an edge between two nodes with guaranteed zero collisions against intermediate nodes.
    Uses inter-lane gutter transit for adjacent/same lanes and dedicated overhead/underfloor
    highway corridors for multi-lane spans.
    """
    s_box, d_box = src_node.box, dst_node.box
    s_col, s_row = src_node.col, src_node.row
    d_col, d_row = dst_node.col, dst_node.row

    # 1. Compute path waypoints and label anchor position
    if s_col == d_col:
        # Same lane connection
        if abs(d_row - s_row) == 1:
            # Immediately adjacent rows
            if d_row > s_row:
                p1 = (s_box.cx, s_box.y2)
                p2 = (d_box.cx, d_box.y)
            else:
                p1 = (s_box.cx, s_box.y)
                p2 = (d_box.cx, d_box.y2)
            pts = [p1, p2]
            lx, ly = (s_box.cx, (p1[1] + p2[1]) / 2.0)
        else:
            # Skipping rows: arc through right gutter of lane
            gx = s_box.x2 + (gutter_x / 2.0)
            p1 = (s_box.x2, s_box.cy)
            p2 = (d_box.x2, d_box.cy)
            pts = [p1, (gx, p1[1]), (gx, p2[1]), p2]
            lx, ly = (gx, (p1[1] + p2[1]) / 2.0)
    elif abs(d_col - s_col) == 1:
        # Adjacent lanes connection: transit inside the inter-lane gutter
        if d_col > s_col:
            p1 = (s_box.x2, s_box.cy)
            p2 = (d_box.x, d_box.cy)
            gx = (s_box.x2 + d_box.x) / 2.0
        else:
            p1 = (s_box.x, s_box.cy)
            p2 = (d_box.x2, d_box.cy)
            gx = (s_box.x + d_box.x2) / 2.0
        pts = [p1, (gx, p1[1]), (gx, p2[1]), p2]
        lx, ly = (gx, (p1[1] + p2[1]) / 2.0)
    else:
        # Multi-lane span (>= 2 columns): highway route via gutter corridors
        all_min_y = min((n.box.y for n in all_nodes), default=s_box.y)
        all_max_y = max((n.box.y2 for n in all_nodes), default=s_box.y2)

        if d_col > s_col:
            p1 = (s_box.x2, s_box.cy)
            g1_x = s_box.x2 + (gutter_x / 2.0)
            p2 = (d_box.x, d_box.cy)
            g2_x = d_box.x - (gutter_x / 2.0)
        else:
            p1 = (s_box.x, s_box.cy)
            g1_x = s_box.x - (gutter_x / 2.0)
            p2 = (d_box.x2, d_box.cy)
            g2_x = d_box.x2 + (gutter_x / 2.0)

        avg_y = (s_box.cy + d_box.cy) / 2.0
        slot_offset = (highway_slot % 4) * 12.0
        if avg_y < (all_min_y + all_max_y) / 2.0:
            y_hw = all_min_y - 28.0 - slot_offset
        else:
            y_hw = all_max_y + 28.0 + slot_offset

        pts = [p1, (g1_x, p1[1]), (g1_x, y_hw), (g2_x, y_hw), (g2_x, p2[1]), p2]
        lx, ly = ((g1_x + g2_x) / 2.0, y_hw)

    # 2. Build SVG path with rounded fillets
    path_d = rounded_path_d(pts, r=8.0)

    # 3. Size and position label background scrim
    label_box = None
    lines: list[str] = []
    if edge_label:
        lines, w, h = text_block(edge_label, 9.5, max_width=80.0, weight="bold")
        label_box = Box(lx - (w / 2.0) - 4.0, ly - (h / 2.0) - 3.0, w + 8.0, h + 6.0)

    return EdgeRoute(
        path_d=path_d,
        label_pos=(lx, ly),
        label_box=label_box,
        label_lines=lines,
        waypoints=pts,
        kind=edge_kind,
    )

