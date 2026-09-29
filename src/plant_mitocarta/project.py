"""
Multi-omics projection engine for Plant MitoCarta maps and digital doubles.

Binds measured NASA OSDR spaceflight expression values (log2FC, p-values)
onto ontology-bound nodes with complete provenance tracking and Okabe-Ito color mapping.
"""
from __future__ import annotations

import dataclasses
import statistics
from typing import Callable, Optional, Sequence

from .doubles import DigitalDouble
from .maps import Map
from .ontology import Entity, Ontology
from .osdr import OsdrExpressionTable, OsdrGeneStat

# Color mapping: Blue (downregulated) -> Off-white/Gray -> Vermillion (upregulated)
COLOR_DOWN = (0, 114, 178)      # Okabe-Ito Blue
COLOR_MID = (245, 245, 245)     # Neutral background
COLOR_UP = (213, 94, 0)         # Okabe-Ito Vermillion


@dataclasses.dataclass
class ProjectedValue:
    node_id: str
    pmco_id: Optional[str]
    value: float
    p_value: float
    significant: bool
    loci_used: tuple[str, ...]
    aggregator: str
    provenance: str
    hex_color: str


AGGREGATORS: dict[str, Callable[[Sequence[float]], float]] = {
    "mean": lambda v: statistics.fmean(v),
    "median": lambda v: statistics.median(v),
    "extreme": lambda v: max(v, key=abs),
    "min": min,
    "max": max,
}


def log2fc_to_hex(val: float, max_clip: float = 2.0) -> str:
    """Map log2 fold change to Okabe-Ito color hex."""
    norm = max(-1.0, min(1.0, val / max_clip))
    if norm < 0:
        t = -norm
        r = int(COLOR_MID[0] + t * (COLOR_DOWN[0] - COLOR_MID[0]))
        g = int(COLOR_MID[1] + t * (COLOR_DOWN[1] - COLOR_MID[1]))
        b = int(COLOR_MID[2] + t * (COLOR_DOWN[2] - COLOR_MID[2]))
    else:
        t = norm
        r = int(COLOR_MID[0] + t * (COLOR_UP[0] - COLOR_MID[0]))
        g = int(COLOR_MID[1] + t * (COLOR_UP[1] - COLOR_MID[1]))
        b = int(COLOR_MID[2] + t * (COLOR_UP[2] - COLOR_MID[2]))
    return f"#{r:02x}{g:02x}{b:02x}"


def project_expression_onto_double(
    double: DigitalDouble,
    ontology: Ontology,
    table: OsdrExpressionTable,
    aggregator: str = "mean",
) -> dict[str, ProjectedValue]:
    """Project expression table onto subcompartments or nodes in a digital double."""
    agg_func = AGGREGATORS.get(aggregator, statistics.fmean)
    results = {}

    for sub in double.subcompartments:
        entities = ontology.filter_by_compartment(sub.id)
        vals = []
        pvals = []
        used_loci = []

        for ent in entities:
            for locus in ent.agi_loci:
                stat = table.get_gene(locus)
                if stat:
                    vals.append(stat.log2_fc)
                    pvals.append(stat.adj_p_value)
                    used_loci.append(locus)

        if vals:
            chosen_val = agg_func(vals)
            min_p = min(pvals)
            sig = min_p <= 0.05 and abs(chosen_val) >= 0.5
            hex_c = log2fc_to_hex(chosen_val)
            results[sub.id] = ProjectedValue(
                node_id=sub.id,
                pmco_id=None,
                value=chosen_val,
                p_value=min_p,
                significant=sig,
                loci_used=tuple(used_loci),
                aggregator=aggregator,
                provenance=f"{table.study_id}:{table.contrast_name}",
                hex_color=hex_c,
            )

    return results


def project_onto_map(
    map_model: Map,
    ontology: Ontology,
    table: OsdrExpressionTable,
    aggregator: str = "mean",
) -> dict[str, ProjectedValue]:
    """Project expression table onto specific map nodes."""
    agg_func = AGGREGATORS.get(aggregator, statistics.fmean)
    results = {}

    for node in map_model.nodes:
        pmco_id = node.payload.get("pmco_id")
        if not pmco_id:
            continue

        try:
            ent = ontology.get_entity(pmco_id)
        except KeyError:
            continue

        vals = []
        pvals = []
        used_loci = []

        for locus in ent.agi_loci:
            stat = table.get_gene(locus)
            if stat:
                vals.append(stat.log2_fc)
                pvals.append(stat.adj_p_value)
                used_loci.append(locus)

        if vals:
            chosen_val = agg_func(vals)
            min_p = min(pvals)
            sig = min_p <= 0.05 and abs(chosen_val) >= 0.5
            hex_c = log2fc_to_hex(chosen_val)
            results[node.id] = ProjectedValue(
                node_id=node.id,
                pmco_id=pmco_id,
                value=chosen_val,
                p_value=min_p,
                significant=sig,
                loci_used=tuple(used_loci),
                aggregator=aggregator,
                provenance=f"{table.study_id}:{table.contrast_name}",
                hex_color=hex_c,
            )

    return results
