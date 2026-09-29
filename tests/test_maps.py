"""
Unit tests for declarative map compiler, layout engine, SVG and SBGN-ML emitters.
"""
import pytest
from plant_mitocarta.maps import compile_all_maps, load_map
from plant_mitocarta.ontology import load_ontology
from plant_mitocarta.render import render_map_svg
from plant_mitocarta.sbgn import map_to_sbgn


def test_compile_all_maps():
    maps = compile_all_maps()
    assert len(maps) == 10
    map_ids = {m.id for m in maps}
    expected = {
        "PMM-01", "PMM-02", "PMM-03", "PMM-04", "PMM-05",
        "PMM-06", "PMM-07", "PMM-08", "PMM-09", "PMM-10"
    }
    assert expected.issubset(map_ids)


def test_pmm01_details():
    m = load_map("PMM-01")
    assert m.title.startswith("Plant Mitochondrial")
    assert len(m.nodes) >= 15
    assert len(m.edges) >= 15
    assert len(m.compartments) >= 3

    # Check bounding box validity
    assert m.canvas_box.w > 500
    assert m.canvas_box.h > 400

    # Ensure all nodes have valid dimensions
    for n in m.nodes:
        assert n.box.w > 50
        assert n.box.h > 20
        assert n.box.x >= 0
        assert n.box.y >= 0


def test_svg_rendering():
    m = load_map("PMM-01")
    svg_light = render_map_svg(m, theme="light")
    assert "<svg" in svg_light
    assert "</svg>" in svg_light
    assert "data-theme=\"light\"" in svg_light
    assert "pmc-canvas" in svg_light

    svg_dark = render_map_svg(m, theme="dark")
    assert "data-theme=\"dark\"" in svg_dark


def test_sbgn_emission():
    m = load_map("PMM-01")
    sbgn_xml = map_to_sbgn(m)
    assert "<sbgn" in sbgn_xml
    assert "</sbgn>" in sbgn_xml
    assert "language=\"process description\"" in sbgn_xml
    assert "glyph" in sbgn_xml
    assert "arc" in sbgn_xml
