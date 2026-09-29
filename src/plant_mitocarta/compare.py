"""
Comparative statistical tests and perturbation specificity analysis.

Evaluates:
- Organellar compartment enrichment under spaceflight stress via permutation testing.
- Cross-perturbation overlap between spaceflight microgravity (OSD-120) and radiation (OSD-8).
"""
from __future__ import annotations

import dataclasses
import random
import statistics
from typing import Sequence

from .osdr import OsdrExpressionTable

RESPONSE_THRESHOLD = 0.5
MIN_N_FOR_TEST = 10
DEFAULT_PERMUTATIONS = 5000
DEFAULT_SEED = 20260929


@dataclasses.dataclass(frozen=True)
class SpecificityResult:
    compartment: str
    n_loci: int
    mean_abs_fc: float
    background_mean: float
    p_value: float
    significant: bool


def compartment_specificity_test(
    table: OsdrExpressionTable,
    target_loci: Sequence[str],
    compartment_name: str,
    permutations: int = DEFAULT_PERMUTATIONS,
    seed: int = DEFAULT_SEED,
) -> SpecificityResult:
    """Permutation test assessing whether target organelle loci respond more strongly than chance."""
    all_stats = list(table.gene_stats.values())
    if len(all_stats) < MIN_N_FOR_TEST:
        raise ValueError("Insufficient background genes for permutation test")

    matched_fcs = [
        abs(table.gene_stats[loc].log2_fc)
        for loc in target_loci
        if loc in table.gene_stats
    ]

    if len(matched_fcs) < 3:
        return SpecificityResult(
            compartment=compartment_name,
            n_loci=len(matched_fcs),
            mean_abs_fc=statistics.fmean(matched_fcs) if matched_fcs else 0.0,
            background_mean=0.0,
            p_value=1.0,
            significant=False,
        )

    observed_stat = statistics.fmean(matched_fcs)
    all_fcs = [abs(g.log2_fc) for g in all_stats]
    bg_mean = statistics.fmean(all_fcs)

    k = len(matched_fcs)
    rng = random.Random(seed)
    greater_count = 0

    for _ in range(permutations):
        sample = rng.sample(all_fcs, k)
        if statistics.fmean(sample) >= observed_stat:
            greater_count += 1

    p_val = (greater_count + 1) / (permutations + 1)
    return SpecificityResult(
        compartment=compartment_name,
        n_loci=k,
        mean_abs_fc=observed_stat,
        background_mean=bg_mean,
        p_value=p_val,
        significant=p_val <= 0.05,
    )
