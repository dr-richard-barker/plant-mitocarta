"""
Unit tests for SUBA5 localization parsing, scoring, and dual targeting.
"""
import pytest
from plant_mitocarta.suba import load_suba_dataset, classify_dual_targeting


def test_suba_dataset_loading():
    records = load_suba_dataset()
    assert len(records) >= 25
    assert "AT3G22370" in records  # AOX1a
    aox = records["AT3G22370"]
    assert aox.subacon_compartment == "mitochondrion"
    assert aox.subacon_score >= 0.95
    assert aox.has_ms is True


def test_dual_targeting_classification():
    records = load_suba_dataset()
    pol1a = records["AT1G50840"]
    assert pol1a.dual_targeted is True
    assert "DUAL_MITO_CHLORO" in pol1a.dual_classes

    anac017 = records["AT1G34190"]
    assert anac017.dual_targeted is True
    assert "DUAL_MITO_NUCLEUS" in anac017.dual_classes


def test_classify_dual_logic():
    is_dual, classes = classify_dual_targeting(
        "mitochondrion",
        ["mitochondrion", "chloroplast"],
        ["mitochondrion"],
    )
    assert is_dual is True
    assert "DUAL_MITO_CHLORO" in classes
