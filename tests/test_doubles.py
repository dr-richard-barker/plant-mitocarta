"""
Unit tests for Digital Double models, subcompartments, and synoptic layout.
"""
import pytest
from plant_mitocarta.doubles import (
    get_all_doubles,
    get_mitochondrion_double,
    get_chloroplast_double,
    get_nucleus_double,
    get_plasma_membrane_double,
    get_synoptic_cell_layout,
)


def test_mitochondrion_double():
    mito = get_mitochondrion_double()
    assert mito.id == "mitochondrion"
    assert mito.go_cc == "GO:0005739"
    sub_ids = {s.id for s in mito.subcompartments}
    assert "mitochondrial_outer_membrane" in sub_ids
    assert "mitochondrial_inner_membrane" in sub_ids
    assert "cristae" in sub_ids
    assert "mitochondrial_matrix" in sub_ids


def test_chloroplast_double():
    chloro = get_chloroplast_double()
    assert chloro.id == "chloroplast"
    sub_ids = {s.id for s in chloro.subcompartments}
    assert "chloroplast_outer_envelope" in sub_ids
    assert "chloroplast_inner_envelope" in sub_ids
    assert "chloroplast_stroma" in sub_ids
    assert "thylakoid_membrane" in sub_ids


def test_nucleus_double():
    nucl = get_nucleus_double()
    assert nucl.id == "nucleus"
    sub_ids = {s.id for s in nucl.subcompartments}
    assert "nuclear_outer_membrane" in sub_ids
    assert "nucleoplasm" in sub_ids
    assert "nucleolus" in sub_ids


def test_plasma_membrane_double():
    pm = get_plasma_membrane_double()
    assert pm.id == "plasma_membrane"
    sub_ids = {s.id for s in pm.subcompartments}
    assert "apoplast" in sub_ids
    assert "plasma_membrane" in sub_ids
    assert "cytosol" in sub_ids


def test_all_doubles_and_synoptic_layout():
    doubles = get_all_doubles()
    assert len(doubles) == 4
    syn = get_synoptic_cell_layout()
    assert "canvas" in syn
    assert "doubles" in syn
    assert "conduits" in syn
    assert len(syn["conduits"]) >= 5
