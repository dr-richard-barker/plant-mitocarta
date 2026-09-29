"""
SVG renderer for Plant MitoCarta maps.

Enforces:
- Okabe-Ito colorblind-safe palette.
- Evidence tiers as explicit border styles (T1 solid heavy, T2 solid light, T3 dashed, T4 dotted, T5 hairline).
- Compartment fills with light/dark adaptive CSS variables.
- Rich edge styling for electron transfer, metabolic shuttles, and retrograde signals.
"""
from __future__ import annotations

import html
import textwrap
from typing import Any, Sequence

from .layout import (
    Box,
    LaidOutNode,
    SVG_FONT_STACK,
    edge_anchors,
)

OKABE_ITO = {
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "black": "#000000",
}

COMPARTMENT_HEX = {
    "mitochondrion": "#7a4a12",
    "mitochondrial_inner_membrane": "#8c5618",
    "cristae": "#6b3f0d",
    "mitochondrial_matrix": "#5c3407",
    "mitochondrial_intermembrane_space": "#9e6522",
    "chloroplast": "#0b5c46",
    "chloroplast_inner_envelope": "#106e54",
    "chloroplast_stroma": "#084736",
    "thylakoid_membrane": "#063d2e",
    "thylakoid_lumen": "#053024",
    "stromule": "#0d684f",
    "nucleus": "#4a2a55",
    "nuclear_inner_membrane": "#5c3569",
    "nucleoplasm": "#3b2044",
    "nucleolus": "#2b1433",
    "plasma_membrane": "#1d4e6b",
    "apoplast": "#3d3d3d",
    "cytosol": "#264b63",
    "peroxisome": "#6b5a06",
    "membrane_contact_site": "#855c1b",
    "mitochondria_er_contact_site_MEAM": "#855c1b",
}


def esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


def get_stylesheet() -> str:
    return textwrap.dedent(
        f"""
        :root {{
          --pmc-bg: #ffffff;
          --pmc-ink: #111827;
          --pmc-ink-soft: #4b5563;
          --pmc-node-fill: #f9fafb;
          --pmc-node-stroke: #111827;
          --pmc-hairline: #9ca3af;
          --pmc-edge: #4b5563;
          --pmc-card-bg: #ffffff;
          --pmc-compartment-fill: rgba(0, 0, 0, 0.03);
        }}
        :root[data-theme="dark"], body.dark-mode {{
          --pmc-bg: #0b0f19;
          --pmc-ink: #f3f4f6;
          --pmc-ink-soft: #9ca3af;
          --pmc-node-fill: #151d2e;
          --pmc-node-stroke: #f3f4f6;
          --pmc-hairline: #4b5563;
          --pmc-edge: #9ca3af;
          --pmc-card-bg: #111827;
          --pmc-compartment-fill: rgba(255, 255, 255, 0.04);
        }}

        .pmc-canvas {{ fill: var(--pmc-bg); }}
        text {{ font-family: {SVG_FONT_STACK}; fill: var(--pmc-ink); }}
        .pmc-title {{ font-size: 20px; font-weight: 700; }}
        .pmc-subtitle {{ font-size: 13px; fill: var(--pmc-ink-soft); }}
        .pmc-caption {{ font-size: 11.5px; fill: var(--pmc-ink-soft); }}
        .pmc-label {{ font-size: 12.5px; font-weight: 600; text-anchor: middle; }}
        .pmc-sub {{ font-size: 10px; fill: var(--pmc-ink-soft); text-anchor: middle; }}

        .pmc-node {{ fill: var(--pmc-node-fill); stroke: var(--pmc-node-stroke); rx: 6px; ry: 6px; }}
        
        /* Evidence Tiers as Border Channels */
        .tier-T1 {{ stroke-width: 3.0px; stroke: var(--pmc-node-stroke); }}
        .tier-T2 {{ stroke-width: 1.8px; stroke: var(--pmc-node-stroke); }}
        .tier-T3 {{ stroke-width: 1.8px; stroke-dasharray: 6 4; stroke: var(--pmc-node-stroke); }}
        .tier-T4 {{ stroke-width: 1.5px; stroke-dasharray: 2 3; stroke: var(--pmc-ink-soft); }}
        .tier-T5 {{ stroke-width: 0.8px; stroke: var(--pmc-hairline); }}

        .pmc-compartment {{ fill: var(--pmc-compartment-fill); stroke-width: 1.5px; stroke-dasharray: 4 4; rx: 12px; }}
        .pmc-compartment-label {{ font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; fill: var(--pmc-ink-soft); }}

        .pmc-edge {{ fill: none; stroke: var(--pmc-edge); stroke-width: 1.6px; }}
        .pmc-edge-electron_transfer {{ stroke: {OKABE_ITO['blue']}; stroke-width: 2.2px; }}
        .pmc-edge-metabolite_flux {{ stroke: {OKABE_ITO['green']}; stroke-width: 1.8px; stroke-dasharray: 4 3; }}
        .pmc-edge-activates {{ stroke: {OKABE_ITO['orange']}; stroke-width: 1.8px; }}
        .pmc-edge-inhibits {{ stroke: {OKABE_ITO['vermillion']}; stroke-width: 2.0px; }}
        .pmc-edge-cleaved_by {{ stroke: {OKABE_ITO['purple']}; stroke-dasharray: 5 3; }}
        .pmc-edge-label {{ font-size: 9.5px; fill: var(--pmc-ink-soft); font-weight: 500; text-anchor: middle; }}
        """
    ).strip()


def get_defs() -> str:
    heads = {
        "pmc-arrow": "var(--pmc-edge)",
        "pmc-arrow-blue": OKABE_ITO["blue"],
        "pmc-arrow-green": OKABE_ITO["green"],
        "pmc-arrow-orange": OKABE_ITO["orange"],
        "pmc-arrow-red": OKABE_ITO["vermillion"],
    }
    out = ["<defs>"]
    for name, color in heads.items():
        out.append(
            f'<marker id="{name}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" '
            f'markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M 0 1 L 9 5 L 0 9 z" fill="{color}" />'
            f"</marker>"
        )
    # T-bar for inhibition
    out.append(
        f'<marker id="pmc-inhibit" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto">'
        f'<line x1="5" y1="1" x2="5" y2="9" stroke="{OKABE_ITO["vermillion"]}" stroke-width="2.5" />'
        f"</marker>"
    )
    out.append("</defs>")
    return "\n".join(out)


def render_map_svg(
    map_model: Any,
    theme: str = "light",
) -> str:
    """Render a compiled map to standalone SVG."""
    w = max(map_model.canvas_box.w, 900)
    h = max(map_model.canvas_box.h, 600)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" '
        f'width="{w:.1f}" height="{h:.1f}" class="pmc-svg" data-theme="{theme}">',
        f"<style>\n{get_stylesheet()}\n</style>",
        get_defs(),
        f'<rect class="pmc-canvas" width="{w:.1f}" height="{h:.1f}" />',
    ]

    # Map Header
    out.append(f'<text class="pmc-title" x="32" y="44">{esc(map_model.title)}</text>')
    if map_model.subtitle:
        out.append(
            f'<text class="pmc-subtitle" x="32" y="66">{esc(map_model.subtitle)}</text>'
        )

    # Compartments
    for comp in map_model.compartments:
        border_color = COMPARTMENT_HEX.get(comp.id, "#666666")
        out.append(
            f'<rect class="pmc-compartment" x="{comp.box.x:.1f}" y="{comp.box.y:.1f}" '
            f'width="{comp.box.w:.1f}" height="{comp.box.h:.1f}" stroke="{border_color}" />'
        )
        out.append(
            f'<text class="pmc-compartment-label" x="{comp.box.x + 12:.1f}" y="{comp.box.y + 18:.1f}">'
            f"{esc(comp.label)}</text>"
        )

    # Edges
    for edge in map_model.edges:
        src_box = map_model.node_boxes[edge.src]
        dst_box = map_model.node_boxes[edge.dst]
        p1, p2 = edge_anchors(src_box, dst_box)

        edge_class = f"pmc-edge pmc-edge-{edge.kind}"
        marker = "url(#pmc-arrow)"
        if edge.kind == "electron_transfer":
            marker = "url(#pmc-arrow-blue)"
        elif edge.kind == "metabolite_flux":
            marker = "url(#pmc-arrow-green)"
        elif edge.kind == "activates":
            marker = "url(#pmc-arrow-orange)"
        elif edge.kind == "inhibits":
            marker = "url(#pmc-inhibit)"

        out.append(
            f'<line class="{edge_class}" x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" '
            f'x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" marker-end="{marker}" />'
        )
        if edge.label:
            mx = (p1[0] + p2[0]) / 2.0
            my = (p1[1] + p2[1]) / 2.0 - 4.0
            out.append(f'<text class="pmc-edge-label" x="{mx:.1f}" y="{my:.1f}">{esc(edge.label)}</text>')

    # Nodes
    for node in map_model.nodes:
        b = node.box
        tier_class = f"tier-{node.evidence_tier}"
        out.append(
            f'<g class="pmc-node-group" id="node-{esc(node.id)}">'
            f'<rect class="pmc-node {tier_class}" x="{b.x:.1f}" y="{b.y:.1f}" '
            f'width="{b.w:.1f}" height="{b.h:.1f}" />'
        )

        # Label lines
        text_y = b.cy - (len(node.lines) - 1) * 7.5
        if node.sublines:
            text_y -= len(node.sublines) * 6.0

        for line in node.lines:
            out.append(
                f'<text class="pmc-label" x="{b.cx:.1f}" y="{text_y:.1f}">{esc(line)}</text>'
            )
            text_y += 15.0

        for sub in node.sublines:
            out.append(
                f'<text class="pmc-sub" x="{b.cx:.1f}" y="{text_y:.1f}">{esc(sub)}</text>'
            )
            text_y += 12.0

        out.append("</g>")

    out.append("</svg>")
    return "\n".join(out)
