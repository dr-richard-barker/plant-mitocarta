"""
Unit tests for NASA OSDR ingestion, expression table parsing, projection, and specificity tests.
"""
import pytest
from plant_mitocarta.doubles import get_mitochondrion_double
from plant_mitocarta.maps import load_map
from plant_mitocarta.ontology import load_ontology
from plant_mitocarta.osdr import load_expression_table
from plant_mitocarta.project import project_expression_onto_double, project_onto_map
from plant_mitocarta.compare import compartment_specificity_test


def test_expression_table_loading():
    tbl = load_expression_table("OSD-120")
    assert tbl.study_id == "OSD-120"
    assert len(tbl.gene_stats) >= 20

    aox_stat = tbl.get_gene("AT3G22370")
    assert aox_stat is not None
    assert aox_stat.log2_fc > 1.0  # AOX1a is strongly upregulated
    assert aox_stat.adj_p_value <= 0.05


def test_projection_onto_double():
    ont = load_ontology()
    double = get_mitochondrion_double()
    tbl = load_expression_table("OSD-120")

    proj = project_expression_onto_double(double, ont, tbl)
    assert len(proj) > 0
    assert "mitochondrial_inner_membrane" in proj
    assert proj["mitochondrial_inner_membrane"].hex_color.startswith("#")


def test_projection_onto_map():
    ont = load_ontology()
    m = load_map("PMM-01")
    tbl = load_expression_table("OSD-120")

    proj = project_onto_map(m, ont, tbl)
    assert len(proj) > 0
    assert "AOX_BYPASS" in proj
    assert proj["AOX_BYPASS"].value > 1.0
    assert proj["AOX_BYPASS"].significant is True


def test_specificity_permutation():
    tbl = load_expression_table("OSD-120")
    target_loci = ["AT3G22370", "AT1G34190", "AT4G05020", "AT5G47910"]
    res = compartment_specificity_test(tbl, target_loci, "stress_sentinels", permutations=500)
    assert res.n_loci == 4
    assert res.p_value <= 0.05
    assert res.significant is True
