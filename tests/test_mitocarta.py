"""
Unit tests for MitoCarta 3.0 comparative synthesis and orthology.
"""
import pytest
from plant_mitocarta.mitocarta import load_mitocarta_reference


def test_mitocarta_pathways():
    mc = load_mitocarta_reference()
    pathways = mc.all_pathways()
    assert len(pathways) >= 8
    ci = mc.get_pathway("OXPHOS_CI")
    assert ci.hierarchy_tier1 == "OXPHOS"
    assert "CAL1" in ci.plant_specific_features or "Carbonic Anhydrase" in ci.plant_specific_features

    aox_path = mc.get_pathway("PLANT_BYPASS_AOX")
    assert aox_path.conservation_pct == 0.0


def test_ortholog_classification():
    mc = load_mitocarta_reference()
    orthologs = mc.all_orthologs()
    assert len(orthologs) >= 5

    strict = mc.filter_by_category("strict_ortholog")
    assert len(strict) >= 3

    plant_innovations = mc.filter_by_category("plant_specific_innovation")
    assert len(plant_innovations) >= 1
    assert plant_innovations[0].plant_symbol == "AOX1a"
