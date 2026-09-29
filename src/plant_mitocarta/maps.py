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
    start_y = 100.0  # Room for title/subtitle

    current_x = start_x
    max_h_overall = 0.0

    lane_boxes: dict[str, list[Box]] = {}

    for lane_idx, lane in enumerate(lanes_spec):
        lane_id = lane["id"]
        comp_id = lane.get("compartment", "cell")
        lane_node_ids = lane.get("nodes", [])
        pref_w = float(lane.get("node_width", 200.0))

        current_y = start_y + 30.0
        lane_max_w = pref_w

        lane_boxes.setdefault(comp_id, [])

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
            units = n_spec.get("units", [])
            if units:
                sublabel = " • ".join(units)

            box, lines, sublines = size_node(
                label,
                font_size=12.5,
                sublabel=sublabel,
                preferred_width=pref_w,
                weight="bold",
            )
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
                lane=lane_id,
                row=row_idx,
                col=lane_idx,
                payload={
                    "pmco_id": pmco_id,
                    "evidence_tier": tier,
                    "description": desc,
                },
            )
            # Add dynamic attribute for tier
            lnode.evidence_tier = tier

            laid_out_nodes.append(lnode)
            node_boxes[nid] = box
            lane_boxes[comp_id].append(box)

            current_y += box.h + MIN_GUTTER_Y
            lane_max_w = max(lane_max_w, box.w)

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

    canvas_w = max(current_x + CANVAS_MARGIN, 1000.0)
    canvas_h = max(max_h_overall + CANVAS_MARGIN + 40.0, 650.0)
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
