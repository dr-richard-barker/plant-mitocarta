#!/usr/bin/env python3
"""
Build the published catalog manifest (catalog/manifest.json) and per-map sidecars (catalog/pmco/*.json).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from plant_mitocarta.maps import compile_all_maps
from plant_mitocarta.ontology import load_ontology

CATALOG_DIR = ROOT / "catalog"
PMCO_DIR = CATALOG_DIR / "pmco"


def main():
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    PMCO_DIR.mkdir(parents=True, exist_ok=True)

    ont = load_ontology()
    maps = compile_all_maps()

    all_entities = ont.all_entities()
    tier_counts = {}
    for e in all_entities:
        tier_counts[e.evidence_tier] = tier_counts.get(e.evidence_tier, 0) + 1

    distinct_loci = set()
    for e in all_entities:
        distinct_loci.update(e.agi_loci)

    manifest = {
        "name": "Plant MitoCarta & Inter-Organellar Atlas",
        "description": "Cross-compartment ontology, four digital doubles (Mitochondrion, Chloroplast, Nucleus, Plasma Membrane), retrograde signaling circuits, and mammalian MitoCarta comparative synthesis.",
        "version": "0.1.0",
        "base_url": "https://dr-richard-barker.github.io/plant-mitocarta",
        "license": {
            "maps": "CC-BY-4.0",
            "ontology": "CC-BY-4.0",
            "code": "MIT",
        },
        "evidence_tiers": ont.core_spec.get("evidence_tiers", []),
        "totals": {
            "maps": len(maps),
            "digital_doubles": 4,
            "entities": len(all_entities),
            "distinct_agi_loci": len(distinct_loci),
            "references": len(ont.references),
            "nodes_by_tier": tier_counts,
        },
        "maps": [
            {
                "id": m.id,
                "title": m.title,
                "subtitle": m.subtitle,
                "species_anchor": m.species_anchor,
                "n_nodes": len(m.nodes),
                "n_edges": len(m.edges),
                "n_compartments": len(m.compartments),
            }
            for m in maps
        ],
    }

    manifest_path = CATALOG_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {manifest_path}")

    # Per-map sidecars
    for m in maps:
        sidecar = {
            "map_id": m.id,
            "title": m.title,
            "nodes": [
                {
                    "id": n.id,
                    "pmco_id": n.payload.get("pmco_id"),
                    "tier": n.payload.get("evidence_tier"),
                    "lines": n.lines,
                    "box": {"x": n.box.x, "y": n.box.y, "w": n.box.w, "h": n.box.h},
                }
                for n in m.nodes
            ],
            "edges": [
                {
                    "source": e.src,
                    "target": e.dst,
                    "kind": e.kind,
                    "label": e.label,
                }
                for e in m.edges
            ],
        }
        sc_path = PMCO_DIR / f"{m.id}.json"
        with open(sc_path, "w", encoding="utf-8") as f:
            json.dump(sidecar, f, indent=2)
    print(f"Wrote {len(maps)} per-map sidecars in {PMCO_DIR}")


if __name__ == "__main__":
    main()
