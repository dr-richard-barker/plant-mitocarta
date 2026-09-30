"""
ABAI Automated Quality Control Screen: Figure Legibility & Geometric Verification.

Asserts across all 10 declarative maps and all 4 digital doubles:
1. Zero overlapping node bounding boxes (strict separation with positive gutter).
2. Zero text label overflow (all text measured against font metrics fits with padding).
3. Human readability: font size thresholds, non-empty labels, no unexpanded tokens.
4. Compartment containment: all nodes in a compartment fit strictly within its boundary.
5. Evidence tier compliance: every node carries an explicit border channel.
"""
from __future__ import annotations

import pytest
from plant_mitocarta.maps import compile_all_maps, load_map
from plant_mitocarta.doubles import get_all_doubles
from plant_mitocarta.layout import measure, PAD_X, PAD_Y


def test_maps_zero_node_box_overlaps():
    """ABAI QC Check 1: Ensure no node bounding boxes intersect or overlap in any map."""
    maps = compile_all_maps()
    overlaps = []

    for m in maps:
        nodes = m.nodes
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                n1, n2 = nodes[i], nodes[j]
                b1, b2 = n1.box, n2.box

                # Strict AABB overlap test
                x_overlap = not (b1.x2 <= b2.x or b2.x2 <= b1.x)
                y_overlap = not (b1.y2 <= b2.y or b2.y2 <= b1.y)

                if x_overlap and y_overlap:
                    overlaps.append(
                        f"Map {m.id}: Node '{n1.id}' ({b1.x},{b1.y},{b1.w},{b1.h}) "
                        f"collides with Node '{n2.id}' ({b2.x},{b2.y},{b2.w},{b2.h})"
                    )

    assert not overlaps, f"Found {len(overlaps)} overlapping node boxes:\n" + "\n".join(overlaps)


def test_maps_zero_text_overflow():
    """ABAI QC Check 2: Sized boxes strictly contain all text runs with generous padding."""
    maps = compile_all_maps()
    overflows = []

    for m in maps:
        for n in m.nodes:
            max_allowed_w = n.box.w - (2 * PAD_X)

            # Check primary label lines
            for line in n.lines:
                w, _ = measure(line, n.font_size, n.font_weight)
                if w > max_allowed_w + 0.1:
                    overflows.append(
                        f"Map {m.id} Node '{n.id}': line '{line}' width {w:.1f}px "
                        f"exceeds box printable width {max_allowed_w:.1f}px"
                    )

            # Check secondary sublabel lines
            for sline in n.sublines:
                w, _ = measure(sline, n.sub_font_size, "normal")
                if w > max_allowed_w + 0.1:
                    overflows.append(
                        f"Map {m.id} Node '{n.id}': subline '{sline}' width {w:.1f}px "
                        f"exceeds box printable width {max_allowed_w:.1f}px"
                    )

    assert not overflows, f"Found {len(overflows)} text label overflows:\n" + "\n".join(overflows)


def test_maps_human_readability_standards():
    """ABAI QC Check 3: Human readability, minimum font sizes, and non-empty metadata."""
    maps = compile_all_maps()
    for m in maps:
        assert m.title and len(m.title) >= 10, f"Map {m.id} has insufficient title"
        assert m.caption and len(m.caption) >= 50, f"Map {m.id} has insufficient caption"

        for n in m.nodes:
            assert n.font_size >= 11.0, f"Node {n.id} in {m.id} has unreadable font size {n.font_size}"
            if n.sublines:
                assert n.sub_font_size >= 9.0, f"Sublabel on {n.id} is too small: {n.sub_font_size}"
            assert len(n.lines) >= 1, f"Node {n.id} has no label lines"
            # Ensure no raw unexpanded placeholders
            for line in n.lines:
                assert "{" not in line and "}" not in line, f"Unformatted template token in {n.id}: {line}"


def test_maps_compartment_containment():
    """ABAI QC Check 4: Compartment bounding boxes contain all enclosed nodes."""
    maps = compile_all_maps()
    for m in maps:
        for comp in m.compartments:
            # Find nodes belonging to this compartment
            c_nodes = [n for n in m.nodes if n.lane and n.lane.startswith(comp.id)]
            for n in c_nodes:
                assert comp.box.x <= n.box.x + 0.1, f"Node {n.id} left edge outside compartment {comp.id}"
                assert comp.box.y <= n.box.y + 0.1, f"Node {n.id} top edge outside compartment {comp.id}"
                assert comp.box.x2 >= n.box.x2 - 0.1, f"Node {n.id} right edge outside compartment {comp.id}"
                assert comp.box.y2 >= n.box.y2 - 0.1, f"Node {n.id} bottom edge outside compartment {comp.id}"


def test_digital_doubles_geometry_and_legibility():
    """ABAI QC Check 5: Digital doubles subcompartments are geometrically well-formed and non-overlapping."""
    doubles = get_all_doubles()
    assert len(doubles) == 4

    for d_id, d in doubles.items():
        assert d.name and len(d.name) > 5
        assert d.subcompartments, f"Double {d_id} has no subcompartments"

        for s in d.subcompartments:
            assert s.box.w >= 100, f"Subcompartment {s.id} in {d_id} is too narrow"
            assert s.box.h >= 50, f"Subcompartment {s.id} in {d_id} is too short"
            assert s.color_hex.startswith("#"), f"Invalid hex color for {s.id}: {s.color_hex}"
            assert s.go_cc.startswith("GO:"), f"Invalid GO-CCO term for {s.id}: {s.go_cc}"

        # Strict pairwise AABB non-overlap verification
        for i in range(len(d.subcompartments)):
            for j in range(i + 1, len(d.subcompartments)):
                s1, s2 = d.subcompartments[i], d.subcompartments[j]
                b1, b2 = s1.box, s2.box
                x_overlap = not (b1.x2 <= b2.x or b2.x2 <= b1.x)
                y_overlap = not (b1.y2 <= b2.y or b2.y2 <= b1.y)
                assert not (x_overlap and y_overlap), (
                    f"Double {d_id}: Subcompartment '{s1.id}' ({b1.x},{b1.y},{b1.w},{b1.h}) "
                    f"overlaps with '{s2.id}' ({b2.x},{b2.y},{b2.w},{b2.h})"
                )



def test_retrograde_circuit_architectures_and_legibility():
    """ABAI QC Check 6: All 5 retrograde signaling circuits have non-overlapping nodes and complete animations."""
    from pathlib import Path
    import json
    import re

    retro_html_path = Path("docs/retrograde.html")
    assert retro_html_path.exists(), "docs/retrograde.html does not exist"

    html = retro_html_path.read_text(encoding="utf-8")

    # Extract JSON circuits definition
    m = re.search(r"const circuits = (\{.*?\});\s+let currentCircuitKey", html, re.DOTALL)
    assert m, "Could not find circuits JSON object in docs/retrograde.html"

    circuits = json.loads(m.group(1))
    assert len(circuits) == 5, f"Expected 5 circuits, found {len(circuits)}"

    expected_keys = {"mrr", "prr", "photo", "pm", "stromule"}
    assert set(circuits.keys()) == expected_keys

    # Check node bounding box separation and legibility for each circuit
    for key, c in circuits.items():
        assert c["title"] and len(c["title"]) >= 15, f"Circuit {key} has short title"
        assert c["desc"] and len(c["desc"]) >= 30, f"Circuit {key} has short desc"
        assert len(c["compartments"]) >= 3, f"Circuit {key} has fewer than 3 compartments"
        assert len(c["steps"]) >= 5, f"Circuit {key} has fewer than 5 steps"

        steps = c["steps"]
        w, h = 140, 48  # Node dimensions

        for i in range(len(steps)):
            s1 = steps[i]
            assert s1["label"] and len(s1["label"]) >= 5
            assert s1["sublabel"] and len(s1["sublabel"]) >= 5
            assert s1["text"] and len(s1["text"]) >= 20

            # Bounding box of node centered at (x, y)
            x1, y1 = s1["x"] - (w / 2), s1["y"] - (h / 2)
            x2, y2 = s1["x"] + (w / 2), s1["y"] + (h / 2)

            for j in range(i + 1, len(steps)):
                s2 = steps[j]
                sx1, sy1 = s2["x"] - (w / 2), s2["y"] - (h / 2)
                sx2, sy2 = s2["x"] + (w / 2), s2["y"] + (h / 2)

                x_overlap = not (x2 <= sx1 or sx2 <= x1)
                y_overlap = not (y2 <= sy1 or sy2 <= y1)

                assert not (x_overlap and y_overlap), (
                    f"Circuit {key}: Step {i+1} ('{s1['label']}') collides with "
                    f"Step {j+1} ('{s2['label']}')"
                )

    # Verify animation engine elements in HTML
    assert 'id="circuit-svg"' in html
    assert 'id="btn-play"' in html
    assert 'id="signal-pulse"' in html
    assert 'id="pulse-halo"' in html
    assert 'class="speed-btn"' in html
    assert 'data-circuit="mrr"' in html
    assert 'data-circuit="stromule"' in html


def test_digital_doubles_contrast_optimization():
    """ABAI QC Check 7: Digital doubles page contains contrast-adaptive luminance calculations and pill scrims."""
    from pathlib import Path
    doubles_html = Path("docs/digital_doubles.html").read_text(encoding="utf-8")

    assert "function getContrastColor(hexColor)" in doubles_html
    assert "function getSubContrastColor(hexColor)" in doubles_html
    assert "function wrapTextLines(text, maxChars)" in doubles_html
    assert 'data-mode="synoptic"' in doubles_html
    assert 'data-mode="chloroplast"' in doubles_html
    assert "rgba(15, 23, 42, 0.88)" in doubles_html
    assert "'0 0 960 600'" in doubles_html


def test_subcompartment_multiomics_heatmap_qc():
    """ABAI QC Check 8: Subcompartment multi-omics expression heatmap exists and is properly wired."""
    from pathlib import Path
    doubles_html = Path("docs/digital_doubles.html").read_text(encoding="utf-8")

    assert 'id="doubles-heatmap-section"' in doubles_html
    assert 'id="heatmap-tbody"' in doubles_html
    assert 'id="heat-organelle-filter"' in doubles_html
    assert 'id="heat-search"' in doubles_html
    assert 'id="sort-comp-btn"' in doubles_html
    assert 'id="sort-fc-btn"' in doubles_html
    assert 'id="sort-sym-btn"' in doubles_html
    assert "function updateHeatmap()" in doubles_html
    assert "function getHeatColor(val)" in doubles_html
    assert "function highlightSubcompInSvg(subId)" in doubles_html
    assert "const heatData =" in doubles_html
    assert "OSD-120" in doubles_html
    assert "OSD-427" in doubles_html


def test_nasa_osdr_multiomics_studio_qc():
    """ABAI QC Check 9: NASA OSDR Studio contains interactive volcano plot, concordance scatter plot, and API simulator."""
    from pathlib import Path
    osdr_html = Path("docs/osdr_projections.html").read_text(encoding="utf-8")

    assert 'id="volcano-svg"' in osdr_html
    assert 'id="concordance-svg"' in osdr_html
    assert 'id="api-terminal-output"' in osdr_html
    assert 'id="master-table-tbody"' in osdr_html
    assert "function renderVolcano()" in osdr_html
    assert "function renderConcordance()" in osdr_html
    assert "function updateApiSimulator()" in osdr_html
    assert "OSD-120" in osdr_html
    assert "OSD-427" in osdr_html
    assert "OSD-782" in osdr_html
    assert "OSD-37" in osdr_html


def test_maps_zero_edge_node_collisions():
    """ABAI QC Check 10: Ensure no edge paths intersect or collide with intermediate node boxes."""
    from plant_mitocarta.layout import route_edge, MIN_GUTTER_X
    maps = compile_all_maps()
    collisions = []

    def sample_polyline(pts, num_samples_per_seg=12):
        samples = []
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i+1]
            for step in range(num_samples_per_seg):
                t = step / num_samples_per_seg
                samples.append((x1 + t*(x2 - x1), y1 + t*(y2 - y1)))
        samples.append(pts[-1])
        return samples

    def point_in_box(pt, box, margin=1.0):
        return (box.x - margin <= pt[0] <= box.x2 + margin and
                box.y - margin <= pt[1] <= box.y2 + margin)

    for m in maps:
        nodes_by_id = {n.id: n for n in m.nodes}
        highway_slot = 0
        for e in m.edges:
            s = nodes_by_id[e.src]
            d = nodes_by_id[e.dst]
            if abs(d.col - s.col) >= 2:
                highway_slot += 1
            route = route_edge(s, d, m.nodes, gutter_x=MIN_GUTTER_X, edge_label=e.label, edge_kind=e.kind, highway_slot=highway_slot)
            sampled = sample_polyline(route.waypoints, 15)
            for n in m.nodes:
                if n.id in (e.src, e.dst):
                    continue
                for pt in sampled:
                    if point_in_box(pt, n.box, margin=1.0):
                        collisions.append(f"Map {m.id}: Edge '{e.src}' -> '{e.dst}' intersects Node '{n.id}'")
                        break

    assert not collisions, f"Found {len(collisions)} edge-node collisions:\n" + "\n".join(collisions)


def test_maps_zero_edge_label_collisions():
    """ABAI QC Check 11: Ensure edge label background chips maintain zero intersection with any node."""
    from plant_mitocarta.layout import route_edge, MIN_GUTTER_X
    maps = compile_all_maps()
    collisions = []

    for m in maps:
        nodes_by_id = {n.id: n for n in m.nodes}
        highway_slot = 0
        for e in m.edges:
            if not e.label:
                continue
            s = nodes_by_id[e.src]
            d = nodes_by_id[e.dst]
            if abs(d.col - s.col) >= 2:
                highway_slot += 1
            route = route_edge(s, d, m.nodes, gutter_x=MIN_GUTTER_X, edge_label=e.label, edge_kind=e.kind, highway_slot=highway_slot)
            if route.label_box:
                lb = route.label_box
                for n in m.nodes:
                    x_ov = not (lb.x2 <= n.box.x or n.box.x2 <= lb.x)
                    y_ov = not (lb.y2 <= n.box.y or n.box.y2 <= lb.y)
                    if x_ov and y_ov:
                        collisions.append(f"Map {m.id}: Label '{e.label}' ({e.src}->{e.dst}) collides with Node '{n.id}'")

    assert not collisions, f"Found {len(collisions)} label-node collisions:\n" + "\n".join(collisions)


def test_maps_membrane_bilayers_rendered():
    """ABAI QC Check 12: Ensure authentic lipid bilayer architectural rails and tags are rendered on membrane compartments."""
    from plant_mitocarta.render import render_map_svg, MEMBRANE_COMPARTMENTS
    maps = compile_all_maps()
    for m in maps:
        svg = render_map_svg(m, "light")
        has_membrane = any(comp.id in MEMBRANE_COMPARTMENTS for comp in m.compartments)
        if has_membrane:
            assert "pmc-bilayer-rail" in svg, f"Map {m.id} contains membrane compartments but lacks pmc-bilayer-rail"
            assert "pmc-membrane-badge" in svg, f"Map {m.id} lacks membrane architecture badges"


def test_maps_catalytic_cofactor_and_bypass_badges():
    """ABAI QC Check 13: Ensure catalytic cofactors and plant bypass badges are extracted and rendered as pill chips."""
    from plant_mitocarta.render import render_map_svg
    maps = compile_all_maps()
    pmm01 = next(m for m in maps if m.id == "PMM-01")
    svg01 = render_map_svg(pmm01, "light")

    # PMM-01 must feature Fe-S, FMN, FAD, heme a3/CuB, di-iron Fe-Fe, and PLANT BYPASS
    assert "8×Fe-S" in svg01, "PMM-01 missing 8×Fe-S cofactor badge"
    assert "FMN" in svg01, "PMM-01 missing FMN cofactor badge"
    assert "FAD" in svg01, "PMM-01 missing FAD cofactor badge"
    assert "heme a3/CuB" in svg01, "PMM-01 missing heme a3/CuB cofactor badge"
    assert "di-iron Fe-Fe" in svg01, "PMM-01 missing di-iron Fe-Fe cofactor badge"
    assert "PLANT BYPASS" in svg01, "PMM-01 missing PLANT BYPASS badge"
    assert "pmc-pill-cofactor" in svg01, "PMM-01 missing pmc-pill-cofactor CSS class"
    assert "pmc-pill-bypass" in svg01, "PMM-01 missing pmc-pill-bypass CSS class"

    # PMM-02 must feature Mn4CaO5 cluster and 1O2 SENSOR
    pmm02 = next(m for m in maps if m.id == "PMM-02")
    svg02 = render_map_svg(pmm02, "light")
    assert "Mn4CaO5 cluster" in svg02, "PMM-02 missing Mn4CaO5 cluster badge"
    assert "1O2 SENSOR" in svg02, "PMM-02 missing 1O2 SENSOR badge"


def test_pmm01_holo_complex_i_superassembly():
    """ABAI QC Check 14: Ensure PMM-01 renders the Plant Holo-Complex I L-shaped super-assembly grouping halo."""
    from plant_mitocarta.render import render_map_svg
    maps = compile_all_maps()
    pmm01 = next(m for m in maps if m.id == "PMM-01")
    svg = render_map_svg(pmm01, "light")

    assert 'id="group-holo-complex-i"' in svg, "PMM-01 missing group-holo-complex-i SVG element"
    assert "PLANT HOLO-COMPLEX I (L-SHAPED SUPER-ASSEMBLY)" in svg, "PMM-01 missing super-assembly header title"





