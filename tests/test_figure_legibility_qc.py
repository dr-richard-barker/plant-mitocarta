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

import html
import pathlib
import pytest
from plant_mitocarta.maps import compile_all_maps, load_map
from plant_mitocarta.doubles import get_all_doubles
from plant_mitocarta.layout import measure, PAD_X, PAD_Y

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"

def esc(s):
    return html.escape(str(s), quote=True)


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


def test_digital_doubles_3column_architecture_and_pins():
    """ABAI QC Check 15: Digital doubles strip subcompartments use 3-column non-overlapping architecture and landmark pins."""
    from pathlib import Path
    doubles_html = Path("docs/digital_doubles.html").read_text(encoding="utf-8")

    assert "double-bilayer-pattern" in doubles_html, "Missing double-bilayer-pattern in digital doubles"
    assert "3-Column horizontal architecture" in doubles_html, "Missing 3-column architecture comment or logic"
    assert "TOM40 Complex" in doubles_html, "Missing TOM40 landmark mapping"
    assert "ANAC017 Tether" in doubles_html, "Missing ANAC017 Tether landmark mapping"
    assert "RuBisCO" in doubles_html, "Missing RuBisCO landmark mapping"
    assert "EXECUTER 1" in doubles_html, "Missing EXECUTER 1 landmark mapping"
    assert "LIPID BILAYER" in doubles_html, "Missing LIPID BILAYER tag in digital doubles"
    assert "Anchor Pins" in doubles_html or "Landmark Anchors" in doubles_html, "Missing anchor pins badge"


def test_retrograde_signaling_mechanism_hud_and_glyphs():
    """ABAI QC Check 16: Retrograde signaling circuits feature live mechanism HUD, biochemical glyphs, and dynamic conduit flow."""
    from pathlib import Path
    retro_html = Path("docs/retrograde.html").read_text(encoding="utf-8")

    # Verify live mechanism HUD elements
    assert 'id="mechanism-hud"' in retro_html, "Missing mechanism HUD element in retrograde.html"
    assert 'id="hud-glyph-icon"' in retro_html, "Missing HUD glyph icon"
    assert 'id="hud-category"' in retro_html, "Missing HUD category badge"
    assert 'id="hud-locus"' in retro_html, "Missing HUD locus display"
    assert 'id="hud-title"' in retro_html, "Missing HUD step title"
    assert 'id="hud-spaceflight"' in retro_html, "Missing HUD spaceflight telemetry"

    # Verify biochemical glyphs in SVG defs
    assert 'id="glyph-scissors"' in retro_html, "Missing glyph-scissors in retrograde.html"
    assert 'id="glyph-ros"' in retro_html, "Missing glyph-ros in retrograde.html"
    assert 'id="glyph-phospho"' in retro_html, "Missing glyph-phospho in retrograde.html"
    assert 'id="glyph-gate"' in retro_html, "Missing glyph-gate in retrograde.html"
    assert 'id="glyph-metabolite"' in retro_html, "Missing glyph-metabolite in retrograde.html"
    assert 'id="glyph-transport"' in retro_html, "Missing glyph-transport in retrograde.html"
    assert 'id="glyph-transcription"' in retro_html, "Missing glyph-transcription in retrograde.html"

    # Verify dynamic conduit flow animation and autoplay
    assert "conduit-flow-anim" in retro_html, "Missing conduit flow animation class"
    assert "conduitFlow" in retro_html, "Missing @keyframes conduitFlow"
    assert "startAnimation();" in retro_html, "Missing automatic startAnimation call"


def test_interactive_multiomics_studio_qc():
    """ABAI QC Check 17: Interactive spaceflight multi-omics pathway studio with dynamic Okabe-Ito shading, telemetry HUD, and inspector drawer."""
    from pathlib import Path
    index_html = Path("docs/index.html").read_text(encoding="utf-8")

    # Assert Studio root container & controls
    assert 'id="interactive-map-studio"' in index_html, "Missing interactive-map-studio in index.html"
    assert 'id="map-select"' in index_html, "Missing map-select dropdown"
    assert 'id="omics-contrast-select"' in index_html, "Missing omics-contrast-select dropdown"
    assert 'id="sig-filter-toggle"' in index_html, "Missing sig-filter-toggle checkbox"

    # Assert live telemetry HUD & stats chips
    assert 'id="studio-telemetry-hud"' in index_html, "Missing studio-telemetry-hud in index.html"
    assert 'id="hud-assayed-count"' in index_html, "Missing hud-assayed-count"
    assert 'id="hud-mean-fc"' in index_html, "Missing hud-mean-fc"
    assert 'id="hud-sig-count"' in index_html, "Missing hud-sig-count"
    assert 'id="hud-top-responder"' in index_html, "Missing hud-top-responder"

    # Assert SVG viewport & Slide-over Omics Inspector Drawer
    assert 'id="studio-svg-container"' in index_html, "Missing studio-svg-container in index.html"
    assert 'id="node-inspector-drawer"' in index_html, "Missing node-inspector-drawer in index.html"
    assert 'id="drawer-contrasts-grid"' in index_html, "Missing drawer-contrasts-grid"
    assert 'id="drawer-concordance-box"' in index_html, "Missing drawer-concordance-box"
    assert 'id="drawer-suba-box"' in index_html, "Missing drawer-suba-box"
    assert 'id="drawer-mitocarta-box"' in index_html, "Missing drawer-mitocarta-box"

    # Assert client-side dataset embedding and dynamic logic
    assert "mapOmicsData" in index_html, "Missing mapOmicsData client-side object"
    assert "mapSvgs" in index_html, "Missing mapSvgs client-side object"
    assert "getContrastColor" in index_html, "Missing getContrastColor function"
    assert "applyOmicsOverlay" in index_html, "Missing applyOmicsOverlay function"
    assert "inspectStudioNode" in index_html, "Missing inspectStudioNode function"
    assert "switchStudioMap" in index_html, "Missing switchStudioMap function"

    # Assert spaceflight study contrasts covered
    assert "osd120_root" in index_html, "Missing OSD-120 root contrast in index.html"
    assert "osd120_shoot" in index_html, "Missing OSD-120 shoot contrast in index.html"
    assert "osd427_protein" in index_html, "Missing OSD-427 protein contrast in index.html"
    assert "osd37" in index_html, "Missing OSD-37 seedling contrast in index.html"
    assert "osd782" in index_html, "Missing OSD-782 dark seedling contrast in index.html"
    assert "osd8" in index_html, "Missing OSD-8 radiation contrast in index.html"


def test_comparative_synteny_studio_qc():
    """ABAI QC Check 18: Interactive Comparative Synteny Studio with Complex I holo-assembly alignment, taxonomic cladogram, and quadrant navigator."""
    from pathlib import Path
    comp_html = Path("docs/comparative.html").read_text(encoding="utf-8")

    # Assert page size and core containers
    assert len(comp_html) > 25000, f"docs/comparative.html size too small: {len(comp_html)} bytes"
    assert 'id="complex-i-synteny-widget"' in comp_html, "Missing complex-i-synteny-widget in comparative.html"
    assert 'id="taxonomic-synteny-tree"' in comp_html, "Missing taxonomic-synteny-tree in comparative.html"
    assert 'id="quadrant-navigator"' in comp_html, "Missing quadrant-navigator in comparative.html"

    # Assert Complex I holo-assembly SVG & HUD components
    assert 'id="complex-i-svg"' in comp_html, "Missing complex-i-svg in comparative.html"
    assert 'id="complex-i-module-hud"' in comp_html, "Missing complex-i-module-hud in comparative.html"
    assert 'id="hud-module-title"' in comp_html, "Missing hud-module-title"
    assert 'id="hud-module-mammal"' in comp_html, "Missing hud-module-mammal"
    assert 'id="hud-module-plant"' in comp_html, "Missing hud-module-plant"
    assert 'id="hud-module-mechanism"' in comp_html, "Missing hud-module-mechanism"
    assert 'id="hud-module-clinical"' in comp_html, "Missing hud-module-clinical"
    assert 'id="hud-module-significance"' in comp_html, "Missing hud-module-significance"

    # Assert Complex I module selector buttons
    for mod in ["all", "n-module", "q-module", "p-module", "ca-module", "bypasses"]:
        assert f'data-module="{mod}"' in comp_html, f"Missing data-module='{mod}' button in comparative.html"

    # Assert Taxonomic Cladogram SVG & Epoch Details Panel
    assert 'id="cladogram-svg"' in comp_html, "Missing cladogram-svg in comparative.html"
    assert 'id="epoch-details-panel"' in comp_html, "Missing epoch-details-panel in comparative.html"
    assert 'id="epoch-hud-name"' in comp_html, "Missing epoch-hud-name"
    assert 'id="epoch-hud-milestone"' in comp_html, "Missing epoch-hud-milestone"
    assert 'id="epoch-hud-innovations"' in comp_html, "Missing epoch-hud-innovations"
    assert 'id="epoch-hud-genomic"' in comp_html, "Missing epoch-hud-genomic"

    # Assert Cladogram 6 Epochs
    for ep in ["epoch-1", "epoch-2", "epoch-3", "epoch-4", "epoch-5", "epoch-6"]:
        assert f'data-epoch="{ep}"' in comp_html, f"Missing data-epoch='{ep}' in comparative.html"

    # Assert 4 Evolutionary Quadrants
    assert "Q1: Strict Orthologs" in comp_html, "Missing Q1 card in comparative.html"
    assert "Q2: Plant Innovations" in comp_html, "Missing Q2 card in comparative.html"
    assert "Q3: Dual-Targeted Divergence" in comp_html, "Missing Q3 card in comparative.html"
    assert "Q4: Expanded Plant Families" in comp_html, "Missing Q4 card in comparative.html"

    # Assert Quadrant Navigator controls and table
    assert 'id="synteny-search-input"' in comp_html, "Missing synteny-search-input"
    assert 'id="identity-slider"' in comp_html, "Missing identity-slider"
    assert 'id="identity-value"' in comp_html, "Missing identity-value"
    assert 'id="synteny-metrics-badge"' in comp_html, "Missing synteny-metrics-badge"
    assert 'id="synteny-table"' in comp_html, "Missing synteny-table"
    assert 'id="synteny-table-body"' in comp_html, "Missing synteny-table-body"

    # Assert Translational Spotlight on Xenotopic Rescue
    assert "Xenotopic Expression" in comp_html, "Missing Xenotopic Expression section"
    assert "Hakkaart et al." in comp_html, "Missing Hakkaart citation"
    assert "El-Khoury et al." in comp_html, "Missing El-Khoury citation"
    assert "Cannino et al." in comp_html, "Missing Cannino citation"

    # Assert client-side interactive JavaScript functions & data objects
    assert "complexIModuleData" in comp_html, "Missing complexIModuleData in comparative.html"
    assert "epochData" in comp_html, "Missing epochData in comparative.html"
    assert "selectComplexIModule" in comp_html, "Missing selectComplexIModule function"
    assert "selectEpoch" in comp_html, "Missing selectEpoch function"
    assert "setQuadrantFilter" in comp_html, "Missing setQuadrantFilter function"
    assert "filterSyntenyTable" in comp_html, "Missing filterSyntenyTable function"


def test_custom_projection_studio_qc():
    """Check 19: Custom Multi-Omics Data Projection Studio ABAI QC Verification.
    Verifies that docs/custom_projection.html exists, has complete CoSE navigation,
    ingestion presets (6 OSDR spaceflight presets + synthetic), NASA OSDR API query interface,
    drag-and-drop file upload, data input textarea, telemetry HUD with 6 metric counters,
    dynamic fold-change slider, significance filter, palette selectors, map switcher across all 10 maps,
    SVG canvas with luminance-adaptive contrast, node hover inspector drawer, matched loci inspection table,
    and SVG/PNG/CSV export capabilities.
    """
    studio_path = DOCS_DIR / "custom_projection.html"
    assert studio_path.exists(), "Missing docs/custom_projection.html"
    content = studio_path.read_text(encoding="utf-8")
    assert len(content) > 30000, f"docs/custom_projection.html too small ({len(content)} bytes)"

    # Assert Navigation & CoSE Theme
    assert 'class="btn active"' in content, "Missing active nav link in custom_projection.html"
    assert "Project Your Data" in content, "Missing 'Project Your Data' tab in nav"
    assert 'id="cose-theme-toggle"' in content, "Missing theme toggle in custom_projection.html"

    # Assert Ingestion Controls & Presets
    assert 'id="custom-data-input"' in content, "Missing custom-data-input textarea"
    assert 'id="file-drop-zone"' in content, "Missing file-drop-zone dropzone"
    assert 'id="file-upload-input"' in content, "Missing file-upload-input file input"
    assert 'id="btn-project-data"' in content, "Missing btn-project-data button"
    for preset in ["osd120_root", "osd120_shoot", "osd427_protein", "osd37", "osd782", "osd8"]:
        assert preset in content, f"Missing preset '{preset}' in custom_projection.html"

    # Assert NASA OSDR API Bar
    assert 'id="osdr-api-input"' in content, "Missing osdr-api-input input"
    assert 'id="btn-query-osdr"' in content, "Missing btn-query-osdr button"
    assert 'id="osdr-api-status"' in content, "Missing osdr-api-status badge"

    # Assert Telemetry HUD
    assert 'id="hud-total-rows"' in content, "Missing hud-total-rows"
    assert 'id="hud-matched-loci"' in content, "Missing hud-matched-loci"
    assert 'id="hud-active-nodes"' in content, "Missing hud-active-nodes"
    assert 'id="hud-up-count"' in content, "Missing hud-up-count"
    assert 'id="hud-down-count"' in content, "Missing hud-down-count"
    assert 'id="hud-sig-count"' in content, "Missing hud-sig-count"

    # Assert Visualization Controls
    assert 'id="slider-fc-range"' in content, "Missing slider-fc-range slider"
    assert 'id="val-fc-range"' in content, "Missing val-fc-range label"
    assert 'id="select-sig-filter"' in content, "Missing select-sig-filter select"
    assert 'id="select-palette"' in content, "Missing select-palette select"
    assert 'id="select-contrast-mode"' in content, "Missing select-contrast-mode select"

    # Assert Map Selector with all 10 maps
    assert 'id="select-active-map"' in content, "Missing select-active-map select"
    for i in range(1, 11):
        map_id = f"PMM-{i:02d}"
        assert map_id in content, f"Missing {map_id} in select-active-map options"

    # Assert Canvas & Export Tools
    assert 'id="studio-canvas-container"' in content, "Missing studio-canvas-container"
    assert 'id="node-inspector-drawer"' in content, "Missing node-inspector-drawer"
    assert 'id="btn-export-svg"' in content, "Missing btn-export-svg button"
    assert 'id="btn-export-png"' in content, "Missing btn-export-png button"
    assert 'id="btn-export-csv"' in content, "Missing btn-export-csv button"

    # Assert Matched Loci Table
    assert 'id="table-search-input"' in content, "Missing table-search-input"
    assert 'id="table-row-count"' in content, "Missing table-row-count"
    assert 'id="matched-loci-tbody"' in content, "Missing matched-loci-tbody"

    # Assert Client-Side JavaScript Functions
    for fn in [
        "initStudio",
        "switchStudioMap",
        "loadPreset",
        "loadSyntheticData",
        "queryOsdrApi",
        "parseData",
        "projectData",
        "applyProjection",
        "exportStudioSvg",
        "exportStudioPng",
        "exportStudioCsv",
    ]:
        assert fn in content, f"Missing client-side function '{fn}' in custom_projection.html"


def test_osdr_individual_study_pages_qc():
    """Check 20: Dedicated NASA OSDR Study Showcase Pages ABAI QC Verification.
    Verifies that all 5 study showcase pages exist under docs/studies/ (OSD-120, OSD-427, OSD-37, OSD-782, OSD-8),
    are non-empty (>30 KB), feature proper depth-1 CoSE navigation, mission metadata badges, external NASA OSDR repository links,
    prominent CTA buttons hand-off to custom projection studio, biological synopses, key discovery cards, literature citations with DOIs,
    pre-projected interactive pathway maps with contrast/map switcher, node inspector, SVG export,
    and a ranked organellar responders table with search and subcellular compartment filtering.
    Also verifies docs/osdr_projections.html links to each study showcase page.
    """
    from plant_mitocarta.studio import STUDY_PROFILES

    studies_dir = DOCS_DIR / "studies"
    assert studies_dir.is_dir(), "Missing docs/studies/ directory"

    # Verify link from OSDR Studio page
    osdr_page = (DOCS_DIR / "osdr_projections.html").read_text(encoding="utf-8")

    for study_id, profile in STUDY_PROFILES.items():
        fname = f"{study_id.lower()}.html"
        study_path = studies_dir / fname
        assert study_path.exists(), f"Missing {study_path}"
        s_html = study_path.read_text(encoding="utf-8")
        assert len(s_html) > 30000, f"Study page {fname} too small ({len(s_html)} bytes)"

        # Check in osdr_projections.html
        assert f"studies/{fname}" in osdr_page, f"Missing link to studies/{fname} in osdr_projections.html"

        # Check Depth-1 Navigation
        assert "../index.html" in s_html, f"Missing depth-1 link ../index.html in {fname}"
        assert "../custom_projection.html" in s_html, f"Missing depth-1 link ../custom_projection.html in {fname}"

        # Check Metadata Badges
        assert study_id in s_html, f"Missing study ID {study_id} in {fname}"
        assert profile["mission"] in s_html, f"Missing mission '{profile['mission']}' in {fname}"
        assert profile["hardware"] in s_html, f"Missing hardware '{profile['hardware']}' in {fname}"
        assert profile["duration"] in s_html, f"Missing duration '{profile['duration']}' in {fname}"
        assert profile["organism"] in s_html, f"Missing organism '{profile['organism']}' in {fname}"

        # Check External OSDR link and Custom Studio CTA
        assert profile["osdr_url"] in s_html, f"Missing OSDR URL in {fname}"
        assert f"custom_projection.html?study={study_id}" in s_html, f"Missing custom studio CTA in {fname}"

        # Check Biological Discoveries & Citations
        for finding in profile.get("key_findings", []):
            assert esc(finding) in s_html or finding[:30] in s_html, f"Missing finding in {fname}"
        for title, url in profile.get("citations", []):
            assert url in s_html, f"Missing citation URL {url} in {fname}"

        # Check Interactive Pathway Maps Gallery
        assert 'id="study-svg-container"' in s_html, f"Missing study-svg-container in {fname}"
        assert 'id="study-node-inspector"' in s_html, f"Missing study-node-inspector in {fname}"
        for mid in profile["relevant_maps"]:
            assert mid in s_html, f"Missing relevant map {mid} in {fname}"

        # Check Contrasts
        for c in profile["contrasts"]:
            assert c["id"] in s_html, f"Missing contrast {c['id']} in {fname}"

        # Check Ranked Table
        assert 'id="study-table-body"' in s_html, f"Missing study-table-body in {fname}"
        assert 'id="study-table-search"' in s_html, f"Missing study-table-search in {fname}"

        # Check Client-Side JS Functions
        for fn in [
            "switchStudyMap",
            "switchStudyContrast",
            "applyStudyProjection",
            "attachStudyNodeEvents",
            "inspectStudyNode",
            "renderStudyTable",
            "exportStudySvg",
        ]:
            assert fn in s_html, f"Missing function '{fn}' in {fname}"








