"""
Declarative map compiler for Plant MitoCarta.

Loads declarative YAML map specifications from maps/src/*.yaml, binds nodes to
PMCO ontology entities, computes text-measured box dimensions and multi-lane
compartmental placement, and generates the compiled Map model for SVG and SBGN emission.
"""
from __future__ import annotations

import dataclasses
import pathlib
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .layout import (
    Box,
    CANVAS_MARGIN,
    COMPARTMENT_PAD,
    LaidOutNode,
    MIN_GUTTER_X,
    MIN_GUTTER_Y,
    PAD_X,
    size_node,
)
from .ontology import Entity, Ontology, load_ontology

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAPS_SRC_DIR = ROOT / "maps" / "src"


@dataclasses.dataclass
class MapEdge:
    src: str
    dst: str
    kind: str
    label: str = ""


@dataclasses.dataclass
class MapCompartment:
    id: str
    label: str
    box: Box


@dataclasses.dataclass
class Map:
    id: str
    title: str
    subtitle: str
    species_anchor: str
    caption: str
    nodes: list[LaidOutNode]
    edges: list[MapEdge]
    compartments: list[MapCompartment]
    node_boxes: dict[str, Box]
    canvas_box: Box
    raw_source: dict[str, Any]


def load_map_source(path: pathlib.Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def classify_unit(unit_str: str) -> tuple[str | None, str | None]:
    """Classify a unit string into (badge_text, badge_type) or (None, None)."""
    u = unit_str.strip()
    u_lower = u.lower()

    # 1. Catalytic cofactors & coenzymes
    if "8 × fe/s" in u_lower or "8 x fe/s" in u_lower:
        return ("8×Fe-S", "cofactor")
    if "3 × fe/s" in u_lower or "3 x fe/s" in u_lower:
        return ("3×Fe-S", "cofactor")
    if "rieske" in u_lower and "fe-2s" in u_lower:
        return ("Rieske 2Fe-2S", "cofactor")
    if u in ("[2Fe-2S]", "Fe/S", "Fe-S"):
        return ("Fe-S", "cofactor")
    if u == "FMN":
        return ("FMN", "cofactor")
    if u == "FAD":
        return ("FAD", "cofactor")
    if "heme a3/cub" in u_lower:
        return ("heme a3/CuB", "cofactor")
    if "di-iron" in u_lower:
        return ("di-iron Fe-Fe", "cofactor")
    if "splits h2o" in u_lower or "mn4cao5" in u_lower:
        return ("Mn4CaO5 cluster", "cofactor")
    if u in ("Cyt b", "Cyt c1"):
        return (u, "cofactor")

    # 2. Plant respiratory bypasses
    if u_lower in ("bypass", "stress bypass"):
        return ("PLANT BYPASS", "bypass")
    if "cyanide-resistant" in u_lower:
        return ("CN-RESISTANT", "bypass")
    if "no h+ pumped" in u_lower:
        return ("NO H+ PUMP", "bypass")
    if "rotenone-insensitive" in u_lower:
        return ("ROT-INSENSITIVE", "bypass")
    if "alternative respiration" in u_lower:
        return ("ALT-RESPIRATION", "bypass")

    # 3. Plant-specific innovations
    if "plant-specific" in u_lower:
        return ("PLANT-SPECIFIC", "plant_spec")
    if "carbonic anhydrase domain" in u_lower:
        return ("CA DOMAIN", "plant_spec")

    # 4. Retrograde sensors, transducers & gates
    if "1o2 sensor" in u_lower:
        return ("1O2 SENSOR", "sensor")
    if "stretch-activated" in u_lower:
        return ("MECHANO-GATED", "sensor")
    if "master mrr factor" in u_lower:
        return ("MRR MASTER", "sensor")
    if "master plastid integrator" in u_lower:
        return ("PRR MASTER", "sensor")
    if "intramembrane serine protease" in u_lower:
        return ("SERINE PROTEASE", "sensor")
    if "er/omm anchored" in u_lower:
        return ("ER/OMM TETHER", "sensor")
    if "cleaved n-fragment" in u_lower:
        return ("CLEAVED NAC", "sensor")
    if "cttgnnnnncag" in u_lower:
        return ("MDM MOTIF", "sensor")
    if "matrix photorespiratory engine" in u_lower:
        return ("GDC MULTIENZYME", "sensor")

    return (None, None)


def compile_map(source: dict[str, Any], ontology: Ontology) -> Map:
    map_id = source["id"]
    title = source.get("title", "")
    subtitle = source.get("subtitle", "")
    caption = source.get("caption", "")
    species_anchor = source.get("species_anchor", "arabidopsis_thaliana")

    lanes_spec = source.get("lanes", [])
    nodes_spec = {n["id"]: n for n in source.get("nodes", [])}
    edges_spec = source.get("edges", [])

    # 1. Size all nodes from text and ontology metadata
    laid_out_nodes: list[LaidOutNode] = []
    node_boxes: dict[str, Box] = {}

    start_x = CANVAS_MARGIN + 20.0
    start_y = 110.0  # Room for title/subtitle and overhead highway

    current_x = start_x
    max_h_overall = 0.0

    lane_boxes: dict[str, list[Box]] = {}

    for lane_idx, lane in enumerate(lanes_spec):
        lane_id = lane["id"]
        comp_id = lane.get("compartment", "cell")
        lane_node_ids = lane.get("nodes", [])
        pref_w = float(lane.get("node_width", 200.0))

        lane_boxes.setdefault(comp_id, [])

        # Pass 1: Size all nodes in this lane to find maximum required width
        temp_sized = []
        for row_idx, nid in enumerate(lane_node_ids):
            n_spec = nodes_spec.get(nid, {})
            pmco_id = n_spec.get("pmco")

            label = n_spec.get("label")
            sublabel = ""
            tier = "T4"
            desc = ""

            if pmco_id:
                try:
                    ent = ontology.get_entity(pmco_id)
                    label = label or ent.label
                    tier = ent.evidence_tier
                    desc = ent.description
                except KeyError:
                    pass

            label = label or nid
            raw_units = n_spec.get("units", [])
            badges: list[tuple[str, str]] = []
            descs: list[str] = []
            for u in raw_units:
                b_text, b_type = classify_unit(u)
                if b_text and (b_text, b_type) not in badges:
                    badges.append((b_text, b_type))
                else:
                    descs.append(u)

            if descs:
                sublabel = " • ".join(descs)

            box, lines, sublines = size_node(
                label,
                font_size=12.5,
                sublabel=sublabel,
                preferred_width=pref_w,
                weight="bold",
            )

            # Accommodate badges row
            if badges:
                total_badges_w = sum(len(b[0]) * 5.6 + 12.0 for b in badges) + max(0, len(badges) - 1) * 6.0
                box.w = max(box.w, total_badges_w + 2 * PAD_X)
                box.h += 18.0

            temp_sized.append((nid, box, lines, sublines, lane_id, row_idx, pmco_id, tier, desc, badges))

        lane_max_w = max([pref_w] + [item[1].w for item in temp_sized])

        # Pass 2: Place all nodes with uniform width in this lane
        current_y = start_y + 36.0
        for nid, box, lines, sublines, l_id, row_idx, pmco_id, tier, desc, badges in temp_sized:
            box.w = lane_max_w
            box.x = current_x
            box.y = current_y

            lnode = LaidOutNode(
                id=nid,
                box=box,
                lines=lines,
                font_size=12.5,
                font_weight="bold",
                sublines=sublines,
                sub_font_size=10.0,
                lane=l_id,
                row=row_idx,
                col=lane_idx,
                badges=badges,
                payload={
                    "pmco_id": pmco_id,
                    "evidence_tier": tier,
                    "description": desc,
                },
            )
            lnode.evidence_tier = tier

            laid_out_nodes.append(lnode)
            node_boxes[nid] = box
            lane_boxes[comp_id].append(box)

            current_y += box.h + MIN_GUTTER_Y

        max_h_overall = max(max_h_overall, current_y)
        current_x += lane_max_w + MIN_GUTTER_X

    # 2. Derive compartment bounding boxes
    compartments: list[MapCompartment] = []
    for comp_id, boxes in lane_boxes.items():
        if not boxes:
            continue
        min_x = min(b.x for b in boxes) - COMPARTMENT_PAD
        min_y = min(b.y for b in boxes) - COMPARTMENT_PAD - 12.0
        max_x = max(b.x2 for b in boxes) + COMPARTMENT_PAD
        max_y = max(b.y2 for b in boxes) + COMPARTMENT_PAD
        comp_box = Box(min_x, min_y, max_x - min_x, max_y - min_y)

        try:
            comp_meta = ontology.get_compartment_meta(comp_id)
            comp_label = comp_meta.get("label", comp_id)
        except KeyError:
            comp_label = comp_id.replace("_", " ").title()

        compartments.append(MapCompartment(id=comp_id, label=comp_label, box=comp_box))

    # 3. Parse edges
    edges: list[MapEdge] = []
    for e in edges_spec:
        if isinstance(e, list) and len(e) >= 3:
            src = e[0]
            dst = e[1]
            kind = e[2]
            elbl = e[3] if len(e) > 3 else ""
            if src in node_boxes and dst in node_boxes:
                edges.append(MapEdge(src=src, dst=dst, kind=kind, label=elbl))

    canvas_w = max(current_x + CANVAS_MARGIN, 1150.0)
    canvas_h = max(max_h_overall + CANVAS_MARGIN + 60.0, 720.0)
    canvas_box = Box(0, 0, canvas_w, canvas_h)

    return Map(
        id=map_id,
        title=title,
        subtitle=subtitle,
        species_anchor=species_anchor,
        caption=caption,
        nodes=laid_out_nodes,
        edges=edges,
        compartments=compartments,
        node_boxes=node_boxes,
        canvas_box=canvas_box,
        raw_source=source,
    )


def load_map(map_id: str, maps_dir: pathlib.Path = MAPS_SRC_DIR) -> Map:
    ont = load_ontology()
    for yf in maps_dir.glob("*.yaml"):
        with open(yf, "r", encoding="utf-8") as f:
            src = yaml.safe_load(f)
        if src.get("id") == map_id:
            return compile_map(src, ont)
    raise FileNotFoundError(f"Map with ID {map_id} not found in {maps_dir}")


def compile_all_maps(maps_dir: pathlib.Path = MAPS_SRC_DIR) -> list[Map]:
    ont = load_ontology()
    results = []
    for yf in sorted(maps_dir.glob("*.yaml")):
        with open(yf, "r", encoding="utf-8") as f:
            src = yaml.safe_load(f)
        if src and "id" in src:
            results.append(compile_map(src, ont))
    return results
