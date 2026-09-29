"""
SBGN-ML Process Description (PD) XML emitter for Plant MitoCarta maps.

Emits standard SBGN-ML 0.3 with PMCO annotation extensions inside <extension>.
Allows maps to be opened in standard SBGN viewers (Newt, SBGNviz, VANTED) and
inherits full pathway compatibility.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .layout import LaidOutNode
from .maps import Map

SBGN_NS = "http://sbgn.org/libsbgn/0.3"
PMCO_NS = "https://plant-mitocarta.org/pmco/1.0"

KIND_TO_GLYPH = {
    "macromolecule": "macromolecule",
    "complex": "complex",
    "simple_chemical": "simple chemical",
    "metabolite": "simple chemical",
    "channel_transporter": "macromolecule",
    "receptor_kinase": "macromolecule",
    "transcription_factor": "macromolecule",
    "process": "process",
    "compartment": "compartment",
    "contact_site": "unspecified entity",
}

EDGE_TO_ARC = {
    "electron_transfer": "consumption",
    "metabolite_flux": "production",
    "activates": "stimulation",
    "inhibits": "inhibition",
    "cleaved_by": "catalysis",
    "translocation": "logic arc",
}


def _bbox(el: ET.Element, x: float, y: float, w: float, h: float) -> None:
    ET.SubElement(
        el,
        "bbox",
        {
            "x": f"{x:.1f}",
            "y": f"{y:.1f}",
            "w": f"{w:.1f}",
            "h": f"{h:.1f}",
        },
    )


def map_to_sbgn(map_model: Map) -> str:
    """Compile a Map model to SBGN-ML PD 0.3 XML string."""
    ET.register_namespace("", SBGN_NS)
    ET.register_namespace("pmco", PMCO_NS)

    sbgn = ET.Element("sbgn", {"xmlns": SBGN_NS})
    sbgn_map = ET.SubElement(sbgn, "map", {"language": "process description", "id": map_model.id})

    _bbox(sbgn_map, 0, 0, map_model.canvas_box.w, map_model.canvas_box.h)

    # Compartments
    for comp in map_model.compartments:
        c_el = ET.SubElement(
            sbgn_map,
            "glyph",
            {"id": f"comp_{comp.id}", "class": "compartment"},
        )
        lbl = ET.SubElement(c_el, "label", {"text": comp.label})
        _bbox(c_el, comp.box.x, comp.box.y, comp.box.w, comp.box.h)

    # Nodes
    for node in map_model.nodes:
        kind = node.payload.get("kind", "macromolecule")
        glyph_cls = KIND_TO_GLYPH.get(kind, "macromolecule")
        g_el = ET.SubElement(
            sbgn_map,
            "glyph",
            {"id": node.id, "class": glyph_cls},
        )
        lbl_text = " ".join(node.lines)
        ET.SubElement(g_el, "label", {"text": lbl_text})
        _bbox(g_el, node.box.x, node.box.y, node.box.w, node.box.h)

        # PMCO Annotation extension
        ext = ET.SubElement(g_el, "extension")
        pmco_ann = ET.SubElement(ext, f"{{{PMCO_NS}}}annotation")
        if node.payload.get("pmco_id"):
            pmco_ann.set("pmco_id", node.payload["pmco_id"])
        if node.payload.get("evidence_tier"):
            pmco_ann.set("tier", node.payload["evidence_tier"])

    # Edges
    for idx, edge in enumerate(map_model.edges):
        arc_cls = EDGE_TO_ARC.get(edge.kind, "stimulation")
        a_el = ET.SubElement(
            sbgn_map,
            "arc",
            {"id": f"arc_{idx}", "class": arc_cls, "source": edge.src, "target": edge.dst},
        )
        src_b = map_model.node_boxes[edge.src]
        dst_b = map_model.node_boxes[edge.dst]
        ET.SubElement(a_el, "start", {"x": f"{src_b.cx:.1f}", "y": f"{src_b.cy:.1f}"})
        ET.SubElement(a_el, "end", {"x": f"{dst_b.cx:.1f}", "y": f"{dst_b.cy:.1f}"})

    return ET.tostring(sbgn, encoding="utf-8", xml_declaration=True).decode("utf-8")
