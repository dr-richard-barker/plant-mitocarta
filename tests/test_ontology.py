"""
Unit tests for PMCO ontology, schema validation, and reference integrity.
"""
import pytest
from plant_mitocarta.ontology import load_ontology, load_references, OntologyError


def test_references_load():
    refs = load_references()
    assert len(refs) >= 10
    for r in refs.values():
        assert r.doi.startswith("10.")
        assert len(r.title) > 0


def test_ontology_load_and_validation():
    ont = load_ontology()
    entities = ont.all_entities()
    assert len(entities) >= 30

    # Test key entities presence
    aox1a = ont.get_entity("PMCO:AOX1A")
    assert aox1a.label == "Alternative Oxidase 1A (AOX1a)"
    assert aox1a.evidence_tier == "T1"
    assert "AT3G22370" in aox1a.agi_loci
    assert aox1a.mitocarta.conservation_category == "plant_specific_innovation"

    anac017 = ont.get_entity("PMCO:ANAC017_NUCLEAR")
    assert anac017.evidence_tier == "T1"
    assert anac017.retrograde.cleavage_required is True

    gun1 = ont.get_entity("PMCO:GUN1_HUB")
    assert gun1.compartment == "chloroplast_stroma"

    rbohd = ont.get_entity("PMCO:RBOHD_NADPH_OXIDASE")
    assert rbohd.compartment == "plasma_membrane"


def test_suba5_dual_targeting():
    ont = load_ontology()
    pol1a = ont.get_entity("PMCO:POLIA_POLYMERASE")
    assert pol1a.suba5.dual_targeted is True
    assert "chloroplast" in pol1a.suba5.dual_compartments
    assert "mitochondrion" in pol1a.suba5.dual_compartments


def test_agi_locus_index():
    ont = load_ontology()
    results = ont.find_by_locus("AT3G22370")
    assert len(results) >= 1
    assert results[0].id == "PMCO:AOX1A"
