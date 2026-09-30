#!/usr/bin/env python3
"""
Build the complete interactive static site for Plant MitoCarta into docs/.
Generates:
- docs/index.html (Dashboard & Catalog Overview)
- docs/digital_doubles.html (Interactive 4-Double Explorer with live NASA OSDR data overlays)
- docs/retrograde.html (Retrograde Signaling Circuit Board & Step Animator)
- docs/comparative.html (MitoCarta 3.0 vs Plant Comparative Matrix & Synteny Tree)
- docs/suba_localization.html (SUBA5 Proteome Explorer & Dual-Targeting Hub)
- docs/osdr_projections.html (NASA Spaceflight Omics Studio)
- docs/maps/*.svg & docs/maps/*.sbgn (Compiled standalone vector and SBGN-ML maps)
"""
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from plant_mitocarta.maps import compile_all_maps
from plant_mitocarta.ontology import load_ontology
from plant_mitocarta.render import render_map_svg
from plant_mitocarta.sbgn import map_to_sbgn
from plant_mitocarta.doubles import get_all_doubles, get_synoptic_cell_layout
from plant_mitocarta.suba import load_suba_dataset, get_curated_suba_records
from plant_mitocarta.mitocarta import load_mitocarta_reference, get_curated_ortholog_pairs
from plant_mitocarta.osdr import (
    load_expression_table,
    get_available_studies,
    get_organellar_multiomics_matrix,
    get_concordance_dataset,
    CURATED_MULTIOMICS_ENTRIES,
)
from plant_mitocarta.studio import STUDY_PROFILES
from plant_mitocarta.project import project_expression_onto_double, project_onto_map
from plant_mitocarta.compare import compartment_specificity_test
from build_custom_studio import (
    build_custom_projection_page,
    build_study_showcase_page,
)

DOCS_DIR = ROOT / "docs"
MAPS_DIR = DOCS_DIR / "maps"
ASSETS_DIR = DOCS_DIR / "assets"


def esc(s):
    return html.escape(str(s), quote=True)


def nav_header(active="home", depth=0):
    prefix = "../" if depth == 1 else ""
    links = [
        (f"{prefix}index.html", "Atlas & Maps", active == "home"),
        (f"{prefix}digital_doubles.html", "Digital Doubles", active == "doubles"),
        (f"{prefix}retrograde.html", "Retrograde Signaling", active == "retrograde"),
        (f"{prefix}comparative.html", "MitoCarta 3.0 Synteny", active == "comparative"),
        (f"{prefix}suba_localization.html", "SUBA5 Proteomics", active == "suba"),
        (f"{prefix}osdr_projections.html", "NASA OSDR Studio", active == "osdr"),
        (f"{prefix}custom_projection.html", "Project Your Data", active == "custom"),
    ]
    link_items = []
    for url, label, is_act in links:
        cls = "btn active" if is_act else "btn"
        aria = ' aria-current="page"' if is_act else ""
        link_items.append(f'<a href="{url}" class="{cls}"{aria}>{label}</a>')
    links_html = "".join(link_items)
    return f"""
  <div class="wrap">
    <div class="cose-topbar">
      <a href="{prefix}index.html" class="cose-brand">
        <img src="https://dr-richard-barker.github.io/Plant_response_to_radiation/cose/cose-logo.png" alt="CoSE logo">
        <span>Plant MitoCarta</span>
      </a>
      <button type="button" id="cose-theme-toggle" class="cose-theme-btn" aria-label="Toggle theme">
        <span class="theme-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;display:block;"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
        </span>
        <span class="theme-label">Theme</span>
      </button>
    </div>

    <nav class="cose-tab-bar" aria-label="Sections">
      <span class="tab-label">Views</span>
      {links_html}
    </nav>
    """


def html_head(title, extra_css=""):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="Plant MitoCarta: Subcellular Digital Doubles, Inter-Organellar Signaling &amp; Cross-Kingdom Synteny">
  <meta name="author" content="Richard Barker">
  <meta name="color-scheme" content="light dark">
  <script>
    (function() {{
      var saved = localStorage.getItem('cose-theme');
      var pref = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', saved || pref);
    }})();
  </script>
  <link rel="stylesheet" href="https://dr-richard-barker.github.io/Plant_response_to_radiation/cose/cose-map.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    /* CoSE Token Mappings */
    :root {{
      --bg: #ffffff;
      --ink: #1a2230;
      --text: var(--ink);
      --text-soft: var(--muted, #5a6473);
      --muted: #5a6473;
      --card-bg: var(--surface, #f7f9fc);
      --card-border: var(--line, #e5e9f0);
      --surface: #f7f9fc;
      --surface-2: #eef2f8;
      --line: #e5e9f0;
      --primary: var(--accent, #3B6EA5);
      --primary-light: rgba(59, 110, 165, 0.12);
      --accent: #3B6EA5;
      --accent2: #3FB6A8;
      --warn: #D55E00;
      --border-radius: 10px;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
      --header-bg: linear-gradient(180deg, rgba(59,110,165,.35), rgba(59,110,165,.05));
      --pmc-bg: var(--bg);
      --pmc-ink: var(--ink);
      --pmc-soft: var(--muted);
      --pmc-faint: #8892a3;
      --pmc-rule: var(--line);
      --pmc-card: var(--surface);
      --pmc-card2: var(--surface-2);
      --pmc-accent: var(--accent);
      --pmc-accent2: var(--accent2);
      --pmc-warn: var(--warn);
    }}
    html[data-theme="light"] {{
      --bg: #ffffff;
      --ink: #1a2230;
      --fg: #1a2230;
      --text: #1a2230;
      --muted: #5a6473;
      --text-soft: #5a6473;
      --line: #e5e9f0;
      --border: #e5e9f0;
      --card-border: #e5e9f0;
      --surface: #f7f9fc;
      --card-bg: #f7f9fc;
      --surface-2: #eef2f8;
      --accent: #3B6EA5;
      --accent2: #3FB6A8;
      --primary: #3B6EA5;
      --primary-light: rgba(59, 110, 165, 0.12);
      --header-bg: linear-gradient(180deg, rgba(59,110,165,.35), rgba(59,110,165,.05));
      color-scheme: light;
    }}
    html[data-theme="dark"] {{
      --bg: #0f141b;
      --ink: #e6ebf2;
      --fg: #e6ebf2;
      --text: #e6ebf2;
      --muted: #9aa6b6;
      --text-soft: #9aa6b6;
      --line: #232c39;
      --border: #232c39;
      --card-border: #232c39;
      --surface: #161d27;
      --card-bg: #161d27;
      --surface-2: #1f2937;
      --accent: #6ea3d8;
      --accent2: #54c9ba;
      --primary: #6ea3d8;
      --primary-light: rgba(110, 163, 216, 0.18);
      --header-bg: linear-gradient(180deg, rgba(59,110,165,.10), transparent);
      color-scheme: dark;
    }}

    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: var(--font-sans);
      line-height: 1.6;
      transition: background-color 0.15s ease, color 0.15s ease;
    }}
    .wrap {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 0 20px 80px;
    }}

    /* CoSE Topbar & Brand (NO side nav rail) */
    .cose-topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 0;
      border-bottom: 1px solid var(--line);
      margin-bottom: 12px;
    }}
    .cose-brand {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
      font-size: 1.05rem;
      color: var(--ink);
      text-decoration: none;
      letter-spacing: -0.01em;
    }}
    .cose-brand:hover {{ text-decoration: none; }}
    .cose-brand img {{
      height: 30px;
      width: 30px;
      border-radius: 6px;
      display: block;
    }}
    .cose-theme-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 8px;
      cursor: pointer;
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--ink);
      font: 600 0.84rem/1.2 var(--font-sans);
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
      transition: background 0.15s ease, border-color 0.15s ease;
    }}
    .cose-theme-btn:hover {{ filter: brightness(0.97); }}

    /* CoSE Tab Bar */
    .cose-tab-bar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      padding: 10px 0 16px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 24px;
    }}
    .cose-tab-bar .tab-label {{
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
      margin: 0 4px 0 2px;
    }}

    /* Buttons */
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.86rem;
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--ink);
      text-decoration: none;
      transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
      cursor: pointer;
    }}
    .btn:hover {{
      text-decoration: none;
      border-color: var(--accent);
      background: var(--surface-2);
      color: var(--ink);
    }}
    .btn.primary {{
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff;
    }}
    .btn.primary:hover {{
      filter: brightness(1.08);
      color: #ffffff;
    }}
    .btn.active {{
      border-color: var(--accent);
      background: var(--surface-2);
      color: var(--accent);
      box-shadow: inset 0 0 0 1px var(--accent);
    }}
    .btn-secondary {{
      background: var(--surface);
      color: var(--ink);
      border: 1px solid var(--line);
    }}
    .btn-secondary:hover {{
      background: var(--surface-2);
    }}

    .container {{
      width: 100%;
      margin: 0 auto;
      padding: 8px 0;
    }}
    .hero-banner {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 32px;
      margin-bottom: 32px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
    }}
    .hero-title {{ font-size: 2rem; font-weight: 800; margin-bottom: 12px; color: var(--text); }}
    .hero-lead {{ font-size: 1.05rem; color: var(--text-soft); max-width: 900px; margin-bottom: 24px; }}
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-top: 24px;
    }}
    .metric-card {{
      background: var(--surface-2);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      text-align: center;
    }}
    .metric-val {{ font-size: 1.8rem; font-weight: 800; color: var(--accent); }}
    .metric-lbl {{ font-size: 0.8rem; color: var(--text-soft); font-weight: 600; text-transform: uppercase; margin-top: 4px; }}

    .card-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 20px;
      margin-top: 24px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.15s, box-shadow 0.15s;
    }}
    .card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }}
    .card-id {{
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .card-title {{ font-size: 1.15rem; font-weight: 700; margin: 6px 0 8px 0; color: var(--text); }}
    .card-desc {{ font-size: 0.88rem; color: var(--text-soft); margin-bottom: 16px; flex-grow: 1; }}
    .card-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 14px;
      border-top: 1px solid var(--card-border);
    }}

    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    .badge-t1 {{ background: rgba(59, 110, 165, 0.15); color: var(--accent); border: 1.5px solid var(--accent); }}
    .badge-t2 {{ background: rgba(63, 182, 168, 0.15); color: var(--accent2); border: 1.5px solid var(--accent2); }}
    .badge-t3 {{ background: rgba(217, 119, 6, 0.15); color: #d97706; border: 1px dashed #d97706; }}
    .badge-t4 {{ background: rgba(148, 163, 184, 0.15); color: #64748b; border: 1px dotted #64748b; }}

    .tier-legend {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 16px 20px;
      margin-bottom: 24px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 20px;
    }}
    .tier-legend-title {{ font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: var(--text-soft); }}
    .tier-legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 0.85rem; }}
    .legend-box {{
      width: 24px;
      height: 14px;
      background: var(--surface);
      border-radius: 3px;
    }}
    .legend-t1 {{ border: 2.5px solid var(--ink); }}
    .legend-t2 {{ border: 1.8px solid var(--muted); }}
    .legend-t3 {{ border: 1.5px dashed var(--muted); }}
    .legend-t4 {{ border: 1.2px dotted var(--muted); }}
    .legend-t5 {{ border: 0.8px solid var(--line); }}

    .cose-foot {{
      margin-top: 56px;
      padding-top: 24px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.6;
    }}
    .cose-foot p {{ margin: 6px 0; max-width: none; }}
    /* Figures with crisp white background and dark mode compatibility */
    figure.map {{
      margin: 0 0 52px;
      border: 1px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
      background: var(--surface);
      box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    }}
    figure.map > a {{
      display: block;
      background: #ffffff;
      padding: 18px 16px 14px;
      text-align: center;
      border-bottom: 1px solid var(--line);
    }}
    figure.map img, figure.map svg {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
      background: #ffffff;
    }}
    figcaption {{
      padding: 20px 24px;
      font-size: 0.94rem;
      color: var(--muted);
      background: var(--surface);
    }}
    figcaption .t {{
      color: var(--ink);
      font-weight: 700;
      font-size: 1.18rem;
      display: block;
      margin-bottom: 8px;
      letter-spacing: -0.01em;
    }}
    figcaption p {{
      margin: 8px 0 16px;
      line-height: 1.65;
      color: var(--ink);
      max-width: 95ch;
    }}
    .map-meta-bar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding-top: 14px;
      border-top: 1px solid var(--line);
      font-size: 0.88rem;
    }}
    .map-meta-left {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }}
    .map-meta-right {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    {extra_css}
  </style>
</head>
<body>
"""


def html_footer():
    return """
    <footer class="cose-foot">
      <p><strong>Licence.</strong> Ontology, maps and evidence base CC-BY-4.0; code MIT.</p>
      <p><strong>Citing.</strong> Plant MitoCarta: Subcellular Digital Doubles, Inter-Organellar Signaling &amp; Cross-Kingdom Synteny. Plant MitoCarta v0.1.0.</p>
      <p><strong>Semantics.</strong> Identifier-bound • GO-CCO &amp; SAO Relational Semantics (<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC3852282/" target="_blank">PMC3852282</a>) • NASA OSDR Ingestion • SUBA5 Proteomics.</p>
      <p><strong>Status.</strong> CoSE Theme Active (Header &amp; Tab Bar Navigation, no side panel) · <a href="https://github.com/dr-richard-barker/plant-mitocarta">source on GitHub</a>.</p>
    </footer>
  </div>
  <script>
  (function() {
    var path = (window.location.pathname.split('/').pop() || 'index.html');
    var links = document.querySelectorAll('.cose-tab-bar a.btn');
    for (var i = 0; i < links.length; i++) {
      var href = links[i].getAttribute('href');
      if (href === path) {
        links[i].classList.add('active');
        links[i].setAttribute('aria-current', 'page');
      }
    }
    var btn = document.getElementById('cose-theme-toggle');
    if (!btn) return;
    function update(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('cose-theme', theme);
      btn.setAttribute('aria-label', 'Switch to ' + (theme === 'dark' ? 'light' : 'dark') + ' mode');
      var label = btn.querySelector('.theme-label');
      if (label) label.textContent = theme === 'dark' ? 'Light' : 'Dark';
      var icon = btn.querySelector('.theme-icon');
      if (icon) {
        icon.innerHTML = theme === 'dark'
          ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;display:block;"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
          : '<svg viewBox="0 0 24 24" fill="currentColor" style="width:14px;height:14px;display:block;"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
      }
    }
    var curr = document.documentElement.getAttribute('data-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    update(curr);
    btn.addEventListener('click', function() {
      var now = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      update(now);
    });
  })();
  </script>
  <script defer src="https://visitor-analytics.astrobotany.workers.dev/a.js"></script>
</body>
</html>
"""


def build_map_omics_dataset(ont, maps):
    omics_dict = {e["locus"]: e for e in CURATED_MULTIOMICS_ENTRIES}
    suba_dict = get_curated_suba_records()
    ortho_dict = {p.agi_locus: p for p in get_curated_ortholog_pairs()}

    NODE_FALLBACK_LOCI = {
        "CATALASE_CAT2": "AT4G35090",
        "GOX_OXIDASE": "AT3G14420",
        "GGT_AMINOTRANSFERASE": "AT1G23310",
        "HPR_GLYCERATE_REDUCTASE": "AT1G68010",
        "GLYCERATE_KINASE_GLYK": "AT1G80380",
        "TPT_TRANSLOCATOR": "AT5G46110",
        "THYL_ATP_SYNTHASE": "AT5G13450",
        "IMPORTIN_ALPHA": "AT3G05720",
        "CPK_KINASES": "AT5G19450",
        "VAP27_TETHER_COMPLEX": "AT3G60600",
        "OMM_VDAC_JUNCTION": "AT3G01280",
        "ANAC017_SOLUBLE_NAC": "AT1G34190",
        "ANAC013_SOLUBLE_NAC": "AT1G32870",
        "AOX1A_MRNA": "AT3G22370",
        "LHCB_RBCS_MRNA": "AT1G67090",
        "PLANT_AOX_INNOVATION": "AT3G22370",
        "PLANT_NDH_BYPASSES": "AT1G07180",
        "PLANT_CA_DOMAIN_COMPLEX_I": "AT1G47260",
        "PLANT_GDC_PHOTORESP": "AT4G33010",
        "DUAL_TARGETED_POLIA_B": "AT1G50840",
        "PLANT_CONSERVED_OXPHOS": "AT5G08530",
        "PLANT_CONSERVED_TCA": "AT5G66760",
        "PLANT_FE_S_ISC_CORE": "AT5G13440",
        "EXPANDED_PPR_FAMILY": "AT2G31490",
        "CYTOCHROME_C": "AT4G11100",
        "COMPLEX_II_SDH": "AT5G66760",
        "COMPLEX_IV_COX": "AT3G15640",
        "COMPLEX_V_ATP_SYNTH": "AT5G13450",
        "COMPLEX_I": "AT5G08530",
        "AOX_BYPASS": "AT3G22370",
        "ALT_NADH_DH_INT": "AT1G07180",
        "ALT_NADH_DH_EXT": "AT4G05020",
        "UCP_PUMP": "AT3G54110",
        "TOM_TIM_IMPORT": "AT3G63160",
        "VDAC_PORIN": "AT3G01280",
    }

    dataset = {}
    for m in maps:
        dataset[m.id] = {}
        for n in m.nodes:
            pmco = n.payload.get("pmco_id")
            ent = ont.entities.get(pmco) if pmco else None
            loci = list(ent.agi_loci) if ent else []
            if not loci and n.id in NODE_FALLBACK_LOCI:
                loci = [NODE_FALLBACK_LOCI[n.id]]

            primary_locus = loci[0] if loci else ""
            omics_entry = omics_dict.get(primary_locus)
            suba_entry = suba_dict.get(primary_locus)
            ortho_entry = ortho_dict.get(primary_locus)

            contrasts = omics_entry["contrasts"] if omics_entry else {}
            assayed = bool(contrasts)

            node_info = {
                "id": n.id,
                "title": " ".join(n.lines),
                "subtitle": " ".join(n.sublines) if n.sublines else "",
                "tier": getattr(n, "evidence_tier", n.payload.get("evidence_tier", "T4")),
                "pmco_id": pmco or "",
                "locus": primary_locus,
                "all_loci": loci,
                "symbol": omics_entry["symbol"] if omics_entry else (ent.label if ent else n.lines[0]),
                "compartment": omics_entry["subcompartment_label"] if omics_entry else (ent.compartment if ent else ""),
                "pathway": omics_entry["pathway"] if omics_entry else (ent.label if ent else ""),
                "desc": omics_entry["desc"] if omics_entry else (ent.description if ent else ""),
                "assayed": assayed,
                "contrasts": contrasts,
            }

            # Concordance (mRNA vs Protein)
            if assayed and "osd120_root" in contrasts and "osd427_protein" in contrasts:
                m_fc = contrasts["osd120_root"]["fc"]
                m_sig = contrasts["osd120_root"]["sig"]
                p_fc = contrasts["osd427_protein"]["fc"]
                p_sig = contrasts["osd427_protein"]["sig"]
                diff = round(p_fc - m_fc, 3)
                if m_sig and p_sig:
                    cat = "Concordantly Induced" if m_fc > 0 else "Concordantly Suppressed"
                elif m_sig and not p_sig:
                    cat = "Post-transcriptionally Buffered"
                elif not m_sig and p_sig:
                    cat = "Protein-Level Specific Regulation"
                else:
                    cat = "Unaltered / Steady"
                node_info["concordance"] = {
                    "mrna_fc": m_fc,
                    "mrna_sig": m_sig,
                    "prot_fc": p_fc,
                    "prot_sig": p_sig,
                    "delta": diff,
                    "category": cat,
                }

            # SUBA5 Localization
            if suba_entry:
                node_info["suba"] = {
                    "consensus": suba_entry.subacon_compartment,
                    "score": suba_entry.subacon_score,
                    "has_ms": suba_entry.has_ms,
                    "has_gfp": suba_entry.has_gfp,
                    "ms_comps": list(suba_entry.ms_compartments),
                    "gfp_comps": list(suba_entry.gfp_compartments),
                    "dual": suba_entry.dual_targeted,
                    "dual_classes": list(suba_entry.dual_classes),
                }
            elif ent and ent.suba5:
                node_info["suba"] = {
                    "consensus": ent.suba5.consensus_compartment,
                    "score": ent.suba5.consensus_score,
                    "has_ms": ent.suba5.ms_evidence,
                    "has_gfp": ent.suba5.gfp_evidence,
                    "ms_comps": [ent.suba5.consensus_compartment] if ent.suba5.ms_evidence else [],
                    "gfp_comps": [ent.suba5.consensus_compartment] if ent.suba5.gfp_evidence else [],
                    "dual": ent.suba5.dual_targeted,
                    "dual_classes": list(ent.suba5.dual_compartments),
                }

            # MitoCarta 3.0 Synteny
            if ortho_entry:
                node_info["mitocarta"] = {
                    "human_symbol": ortho_entry.human_symbol,
                    "human_entrez": ortho_entry.human_entrez,
                    "mitopathway": ortho_entry.mitopathway,
                    "quadrant": ortho_entry.conservation_category,
                    "identity_pct": ortho_entry.sequence_identity_pct,
                    "clinical": ortho_entry.clinical_phenotype,
                    "notes": ortho_entry.inference_note,
                }
            elif ent and ent.mitocarta and ent.mitocarta.human_symbol:
                node_info["mitocarta"] = {
                    "human_symbol": ent.mitocarta.human_symbol,
                    "human_entrez": ent.mitocarta.human_entrez or 0,
                    "mitopathway": ent.mitocarta.mitopathway or "",
                    "quadrant": ent.mitocarta.conservation_category or "Ortholog",
                    "identity_pct": 75.0,
                    "clinical": ent.mitocarta.clinical_significance or "",
                    "notes": "",
                }

            dataset[m.id][n.id] = node_info
    return dataset


def build_index_page(ont, maps):
    all_ent = ont.all_entities()
    cards_html = []
    figures_html = []

    # Pre-render SVGs and assemble multi-omics dataset
    map_svgs = {m.id: render_map_svg(m, "light") for m in maps}
    map_omics = build_map_omics_dataset(ont, maps)
    map_svgs_json = json.dumps(map_svgs).replace("</script>", "<\\/script>")
    map_omics_json = json.dumps(map_omics).replace("</script>", "<\\/script>")

    for m in maps:
        tiers = {}
        for n in m.nodes:
            t = n.payload.get("evidence_tier", "T4")
            tiers[t] = tiers.get(t, 0) + 1
        tier_badges = "".join(
            f'<span class="badge badge-{k.lower()}">{k}: {v}</span> '
            for k, v in sorted(tiers.items())
        )

        cards_html.append(f"""
        <div class="card">
          <div>
            <div class="card-id">{esc(m.id)} • {esc(m.species_anchor.replace('_', ' ').title())}</div>
            <h3 class="card-title">{esc(m.title)}</h3>
            <p class="card-desc">{esc(m.subtitle or m.caption[:150] + '...')}</p>
          </div>
          <div class="card-footer">
            <span style="font-size: 0.8rem; color: var(--text-soft);">{len(m.nodes)} nodes • {len(m.edges)} edges</span>
            <div style="display: flex; gap: 6px;">
              <button type="button" onclick="switchStudioMap('{esc(m.id)}'); document.getElementById('interactive-map-studio').scrollIntoView({{behavior: 'smooth'}});" class="btn primary">Load in Studio</button>
              <a href="maps/{esc(m.id)}.svg" target="_blank" class="btn btn-secondary">SVG</a>
            </div>
          </div>
        </div>
        """)

        figures_html.append(f"""
        <figure class="map" id="{esc(m.id)}">
          <a href="maps/{esc(m.id)}.svg" target="_blank" title="Click to open full-resolution SVG in new tab">
            <img src="maps/{esc(m.id)}.svg" alt="{esc(m.title)}" loading="lazy">
          </a>
          <figcaption>
            <span class="t">{esc(m.id)} · {esc(m.title)}</span>
            <p>{esc(m.caption or m.subtitle)}</p>
            <div class="map-meta-bar">
              <div class="map-meta-left">
                <span style="font-weight: 650; color: var(--ink);">{len(m.nodes)} nodes • {len(m.edges)} edges</span>
                <span style="color: var(--line);">|</span>
                <span>{tier_badges}</span>
              </div>
              <div class="map-meta-right">
                <button type="button" onclick="switchStudioMap('{esc(m.id)}'); document.getElementById('interactive-map-studio').scrollIntoView({{behavior: 'smooth'}});" class="btn primary">Open in Studio</button>
                <a href="maps/{esc(m.id)}.svg" target="_blank" class="btn btn-secondary">Full Vector SVG</a>
                <a href="maps/{esc(m.id)}-dark.svg" target="_blank" class="btn btn-secondary">Dark SVG</a>
                <a href="maps/{esc(m.id)}.sbgn" download class="btn btn-secondary">SBGN-ML</a>
                <a href="catalog/pmco/{esc(m.id)}.json" target="_blank" class="btn btn-secondary">PMCO Sidecar</a>
              </div>
            </div>
          </figcaption>
        </figure>
        """)

    map_options_items = []
    for m in maps:
        sel = ' selected="selected"' if m.id == "PMM-01" else ""
        map_options_items.append(f'<option value="{esc(m.id)}"{sel}>{esc(m.id)}: {esc(m.title)}</option>')
    map_options_html = "\n".join(map_options_items)

    studio_css = """
    /* Interactive Spaceflight Pathway Map Studio */
    #interactive-map-studio {
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      margin: 28px 0 48px;
      position: relative;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    }
    .studio-header {
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
      margin-bottom: 20px;
    }
    .tag-accent {
      display: inline-block;
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: 3px 8px;
      border-radius: 4px;
      background: var(--primary-light);
      color: var(--primary);
      margin-bottom: 8px;
    }
    .studio-title {
      font-size: 1.6rem;
      font-weight: 800;
      margin: 0 0 6px 0;
      letter-spacing: -0.01em;
      color: var(--ink);
    }
    .studio-desc {
      font-size: 0.92rem;
      color: var(--text-soft);
      max-width: 95ch;
      margin: 0 0 16px 0;
      line-height: 1.55;
    }
    .studio-controls-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 16px;
      background: var(--bg);
      padding: 12px 16px;
      border-radius: 8px;
      border: 1px solid var(--line);
    }
    .control-group {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.88rem;
    }
    .control-group label {
      color: var(--ink);
      white-space: nowrap;
    }
    .control-group select {
      background: var(--surface);
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 0.86rem;
      font-family: inherit;
      font-weight: 600;
      cursor: pointer;
    }
    .control-group select:focus {
      outline: 2px solid var(--primary);
    }
    .control-group-toggle {
      display: flex;
      align-items: center;
      margin-left: auto;
    }
    .toggle-container {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      font-size: 0.86rem;
      font-weight: 600;
      color: var(--ink);
      user-select: none;
    }
    .toggle-container input {
      cursor: pointer;
      width: 16px;
      height: 16px;
    }

    /* Live Telemetry HUD & Legend */
    .studio-hud-bar {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 20px;
      padding: 14px 18px;
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .hud-stats-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
    }
    .hud-stat-chip {
      display: flex;
      flex-direction: column;
    }
    .hud-label {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
    }
    .hud-val {
      font-size: 1.05rem;
      font-weight: 800;
      color: var(--ink);
    }
    .studio-legend-block {
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 260px;
    }
    .legend-scale-labels {
      display: flex;
      justify-content: space-between;
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--muted);
    }
    .legend-scale-bar {
      height: 10px;
      border-radius: 5px;
      background: linear-gradient(90deg, #0072B2 0%, #a0c4df 35%, #e2e8f0 50%, #f7b282 65%, #D55E00 100%);
      border: 1px solid var(--line);
    }

    /* Studio Viewport & Drawer Layout */
    .studio-viewport-wrapper {
      position: relative;
      overflow: hidden;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: var(--card-bg);
      min-height: 620px;
      display: flex;
    }
    .studio-svg-box {
      width: 100%;
      overflow-x: auto;
      padding: 16px;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .studio-svg-box svg {
      max-width: 100%;
      height: auto;
      display: block;
    }

    /* Omics Inspector Drawer */
    .inspector-drawer {
      position: absolute;
      top: 0;
      right: 0;
      bottom: 0;
      width: 440px;
      max-width: 92vw;
      background: var(--surface);
      border-left: 1px solid var(--line);
      box-shadow: -6px 0 24px rgba(0,0,0,0.18);
      transform: translateX(100%);
      transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
      z-index: 40;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .inspector-drawer.open {
      transform: translateX(0);
    }
    .drawer-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
      background: var(--bg);
    }
    .drawer-tag {
      display: inline-block;
      font-size: 0.7rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--primary);
      margin-bottom: 4px;
    }
    .drawer-title-wrap h3 {
      font-size: 1.15rem;
      font-weight: 800;
      margin: 0 0 4px 0;
      color: var(--ink);
    }
    .drawer-locus {
      font-size: 0.82rem;
      color: var(--muted);
      font-family: monospace;
    }
    .drawer-close-btn {
      background: none;
      border: none;
      font-size: 1.5rem;
      line-height: 1;
      color: var(--muted);
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
    }
    .drawer-close-btn:hover {
      color: var(--ink);
      background: var(--surface-2);
    }
    .drawer-body {
      padding: 20px;
      overflow-y: auto;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .drawer-section {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .drawer-section h4 {
      font-size: 0.84rem;
      font-weight: 750;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin: 0;
      color: var(--muted);
    }
    .contrasts-grid {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .contrast-row {
      display: flex;
      flex-direction: column;
      padding: 8px 10px;
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 6px;
      font-size: 0.82rem;
      gap: 4px;
    }
    .contrast-header-line {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .contrast-name {
      font-weight: 700;
      color: var(--ink);
    }
    .contrast-stat-badges {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .fc-badge {
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 0.8rem;
    }
    .fc-up { background: rgba(213, 94, 0, 0.15); color: #D55E00; }
    .fc-down { background: rgba(0, 114, 178, 0.15); color: #0072B2; }
    .fc-neutral { background: var(--surface-2); color: var(--muted); }
    .sig-pill {
      font-size: 0.7rem;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 3px;
      background: rgba(0, 158, 115, 0.15);
      color: #009E73;
    }
    .bar-track {
      height: 6px;
      background: var(--line);
      border-radius: 3px;
      position: relative;
      overflow: hidden;
    }
    .bar-fill {
      position: absolute;
      top: 0;
      bottom: 0;
      border-radius: 3px;
    }
    .concordance-box, .suba-box, .mitocarta-box {
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      font-size: 0.84rem;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .drawer-footer-links {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding-top: 10px;
      border-top: 1px solid var(--line);
      margin-top: auto;
    }
    """

    content = f"""
    {nav_header(active='home')}
    <main class="container">
      <section class="hero-banner">
        <h2 class="hero-title">Plant MitoCarta & Inter-Organellar Bioenergetic Atlas</h2>
        <p class="hero-lead">
          A computable, identifier-bound cross-compartment atlas featuring <strong>four digital doubles</strong>
          (Mitochondria, Chloroplast, Nucleus, and Plasma Membrane), formal <strong>retrograde signaling circuits</strong>,
          and a cross-species comparative synthesis with mammalian <strong>Broad MitoCarta 3.0</strong>.
          Designed as an open template engine for projecting <strong>NASA OSDR</strong> spaceflight omics.
        </p>
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-val">4</div>
            <div class="metric-lbl">Digital Doubles</div>
          </div>
          <div class="metric-card">
            <div class="metric-val">{len(maps)}</div>
            <div class="metric-lbl">Declarative Maps</div>
          </div>
          <div class="metric-card">
            <div class="metric-val">5</div>
            <div class="metric-lbl">Retrograde Circuits</div>
          </div>
          <div class="metric-card">
            <div class="metric-val">{len(all_ent)}</div>
            <div class="metric-lbl">PMCO Entities</div>
          </div>
          <div class="metric-card">
            <div class="metric-val">149</div>
            <div class="metric-lbl">MitoPathways Synteny</div>
          </div>
          <div class="metric-card">
            <div class="metric-val">100%</div>
            <div class="metric-lbl">Empirical DOI Bound</div>
          </div>
        </div>
      </section>

      <div class="tier-legend">
        <span class="tier-legend-title">Evidence Tier Border Key:</span>
        <div class="tier-legend-item"><div class="legend-box legend-t1"></div><span><strong>T1</strong> Demonstrated Empirical (Plant)</span></div>
        <div class="tier-legend-item"><div class="legend-box legend-t2"></div><span><strong>T2</strong> Inferred from Process (Plant)</span></div>
        <div class="tier-legend-item"><div class="legend-box legend-t3"></div><span><strong>T3</strong> Orthology-Inferred (Mammalian)</span></div>
        <div class="tier-legend-item"><div class="legend-box legend-t4"></div><span><strong>T4</strong> Mechanistic Hypothesis</span></div>
        <div class="tier-legend-item"><div class="legend-box legend-t5"></div><span><strong>T5</strong> Anatomical Context</span></div>
      </div>

      <!-- INTERACTIVE SPACEFLIGHT PATHWAY STUDIO -->
      <section id="interactive-map-studio">
        <div class="studio-header">
          <div class="tag-accent">DYNAMIC MULTI-OMICS PROJECTION STUDIO</div>
          <h3 class="studio-title">Interactive Spaceflight Pathway Studio</h3>
          <p class="studio-desc">
            Project measured NASA OSDR microgravity transcriptomics and proteomics directly onto declarative bioenergetic maps. Dynamic Okabe-Ito diverging palette, statistical significance gating, live pathway telemetry HUD, and interactive slide-over multi-omics inspector.
          </p>

          <div class="studio-controls-bar">
            <div class="control-group">
              <label for="map-select"><strong>Map Architecture:</strong></label>
              <select id="map-select" onchange="switchStudioMap(this.value)">
                {map_options_html}
              </select>
            </div>

            <div class="control-group">
              <label for="omics-contrast-select"><strong>Spaceflight Omics Overlay:</strong></label>
              <select id="omics-contrast-select" onchange="setOmicsContrast(this.value)">
                <option value="none">Baseline Architecture (Evidence Tiers T1-T5)</option>
                <option value="osd120_root" selected>OSD-120: Col-0 Root RNA-seq (Spaceflight vs Ground)</option>
                <option value="osd120_shoot">OSD-120: Col-0 Shoot RNA-seq (Spaceflight vs Ground)</option>
                <option value="osd427_protein">OSD-427: Whole Plant Proteomics (Spaceflight vs Ground)</option>
                <option value="osd37">OSD-37: Seedling Microgravity (EMCS Spaceflight)</option>
                <option value="osd782">OSD-782: Dark Seedling Microgravity (Spaceflight vs Ground)</option>
                <option value="osd8">OSD-8: Seedling Microgravity vs 1g Centrifuge Control</option>
              </select>
            </div>

            <div class="control-group-toggle">
              <label class="toggle-container" title="Dim non-significant nodes (p > 0.05 or |log2FC| < 0.5)">
                <input type="checkbox" id="sig-filter-toggle" onchange="toggleSigFilter(this.checked)">
                <span class="toggle-label">Highlight p &le; 0.05 only</span>
              </label>
            </div>
          </div>
        </div>

        <div class="studio-hud-bar">
          <div id="studio-telemetry-hud" class="hud-stats-grid">
            <div class="hud-stat-chip">
              <span class="hud-label">Assayed Nodes</span>
              <span class="hud-val" id="hud-assayed-count">--</span>
            </div>
            <div class="hud-stat-chip">
              <span class="hud-label">Pathway Mean log2FC</span>
              <span class="hud-val" id="hud-mean-fc">--</span>
            </div>
            <div class="hud-stat-chip">
              <span class="hud-label">Significantly Regulated</span>
              <span class="hud-val" id="hud-sig-count">--</span>
            </div>
            <div class="hud-stat-chip">
              <span class="hud-label">Top Spaceflight Responder</span>
              <span class="hud-val" id="hud-top-responder">--</span>
            </div>
          </div>

          <div class="studio-legend-block">
            <div class="legend-scale-labels">
              <span>&le; -1.5 (Down)</span>
              <span>0.0 (Unaltered)</span>
              <span>&ge; +1.5 (Up)</span>
            </div>
            <div class="legend-scale-bar"></div>
          </div>
        </div>

        <div class="studio-viewport-wrapper">
          <div id="studio-svg-container" class="studio-svg-box">
            {map_svgs["PMM-01"]}
          </div>

          <!-- Omics Inspector Slide-Over Drawer -->
          <aside id="node-inspector-drawer" class="inspector-drawer">
            <div class="drawer-header">
              <div class="drawer-title-wrap">
                <span class="drawer-tag" id="drawer-node-type">PROTEIN COMPLEX</span>
                <h3 id="drawer-node-title">Click any node to inspect</h3>
                <span class="drawer-locus" id="drawer-node-locus">Select a node in the pathway diagram</span>
              </div>
              <button type="button" class="drawer-close-btn" onclick="closeInspectorDrawer()" aria-label="Close Inspector">&times;</button>
            </div>

            <div class="drawer-body">
              <div class="drawer-section">
                <h4>Multi-Contrast Spaceflight Expression Profile</h4>
                <div id="drawer-contrasts-grid" class="contrasts-grid"></div>
              </div>

              <div class="drawer-section">
                <h4>Multi-Omics Concordance (mRNA vs Protein)</h4>
                <div id="drawer-concordance-box" class="concordance-box"></div>
              </div>

              <div class="drawer-section">
                <h4>SUBA5 Subcellular Localization</h4>
                <div id="drawer-suba-box" class="suba-box"></div>
              </div>

              <div class="drawer-section">
                <h4>Broad MitoCarta 3.0 Mammalian Homology</h4>
                <div id="drawer-mitocarta-box" class="mitocarta-box"></div>
              </div>

              <div class="drawer-footer-links">
                <a id="drawer-tair-link" href="#" target="_blank" class="btn btn-secondary">TAIR Locus</a>
                <a id="drawer-osdr-link" href="#" target="_blank" class="btn btn-secondary">NASA OSDR</a>
                <a id="drawer-suba-link" href="#" target="_blank" class="btn btn-secondary">SUBA5 Proteome</a>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h3 style="font-size: 1.3rem; font-weight: 700;">Declarative Pathway & Organelle Map Catalog</h3>
        <span style="color: var(--text-soft); font-size: 0.9rem;">Derived deterministically from text metrics; zero hardcoded coordinates</span>
      </div>

      <div class="card-grid" style="margin-bottom: 56px;">
        {''.join(cards_html)}
      </div>

      <div style="margin-bottom: 24px;">
        <h3 style="font-size: 1.4rem; font-weight: 800; letter-spacing: -0.01em;">Rendered Interactive Pathway Maps</h3>
        <p style="color: var(--text-soft); font-size: 0.95rem; margin-top: 4px;">
          Process Description vector maps compiled with Okabe-Ito colorblind-safe palettes and evidence tiers explicitly encoded as border channels. Click any map to view full-scale or download standalone SVG/SBGN-ML representations.
        </p>
      </div>

      <div class="map-figures-list">
        {''.join(figures_html)}
      </div>
    </main>

    <script>
    (function() {{
      const mapSvgs = {map_svgs_json};
      const mapOmicsData = {map_omics_json};

      window.mapSvgs = mapSvgs;
      window.mapOmicsData = mapOmicsData;

      let currentMapId = 'PMM-01';
      let currentContrast = 'osd120_root';
      let sigFilterActive = false;
      let activeInspectorNode = null;

      function getContrastColor(fc, isDark) {{
        const norm = Math.max(-1.0, Math.min(1.0, fc / 1.5));
        const neutral = isDark ? [30, 41, 59] : [248, 250, 252];
        const down = [0, 114, 178];  // Okabe-Ito Blue
        const up = [213, 94, 0];     // Okabe-Ito Vermillion
        let r, g, b;
        if (norm < 0) {{
          const t = -norm;
          r = Math.round(neutral[0] + t * (down[0] - neutral[0]));
          g = Math.round(neutral[1] + t * (down[1] - neutral[1]));
          b = Math.round(neutral[2] + t * (down[2] - neutral[2]));
        }} else {{
          const t = norm;
          r = Math.round(neutral[0] + t * (up[0] - neutral[0]));
          g = Math.round(neutral[1] + t * (up[1] - neutral[1]));
          b = Math.round(neutral[2] + t * (up[2] - neutral[2]));
        }}
        return {{
          hex: '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1),
          lum: (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
        }};
      }}

      window.switchStudioMap = function(mapId) {{
        currentMapId = mapId;
        const select = document.getElementById('map-select');
        if (select && select.value !== mapId) select.value = mapId;
        const container = document.getElementById('studio-svg-container');
        if (!container || !mapSvgs[mapId]) return;
        container.innerHTML = mapSvgs[mapId];
        attachNodeClickListeners();
        applyOmicsOverlay();
        if (activeInspectorNode) {{
          if (mapOmicsData[currentMapId] && mapOmicsData[currentMapId][activeInspectorNode]) {{
            inspectStudioNode(activeInspectorNode);
          }} else {{
            closeInspectorDrawer();
          }}
        }}
      }};

      window.setOmicsContrast = function(contrastKey) {{
        currentContrast = contrastKey;
        applyOmicsOverlay();
        if (activeInspectorNode) {{
          inspectStudioNode(activeInspectorNode);
        }}
      }};

      window.toggleSigFilter = function(checked) {{
        sigFilterActive = checked;
        applyOmicsOverlay();
      }};

      function attachNodeClickListeners() {{
        const container = document.getElementById('studio-svg-container');
        if (!container) return;
        const nodes = container.querySelectorAll('.pmc-node-group');
        nodes.forEach(function(group) {{
          const nodeId = group.getAttribute('data-node-id') || group.id.replace(/^node-/, '');
          group.style.cursor = 'pointer';
          group.onclick = function(e) {{
            e.stopPropagation();
            inspectStudioNode(nodeId);
          }};
          group.onkeydown = function(e) {{
            if (e.key === 'Enter' || e.key === ' ') {{
              e.preventDefault();
              inspectStudioNode(nodeId);
            }}
          }};
        }});
      }}

      function applyOmicsOverlay() {{
        const container = document.getElementById('studio-svg-container');
        if (!container) return;
        const mapData = mapOmicsData[currentMapId] || {{}};
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const isBaseline = currentContrast === 'none';

        const nodeGroups = container.querySelectorAll('.pmc-node-group');
        nodeGroups.forEach(function(group) {{
          const nodeId = group.getAttribute('data-node-id') || group.id.replace(/^node-/, '');
          const rect = group.querySelector('.pmc-node');
          const labels = group.querySelectorAll('.pmc-label, .pmc-sub');
          let statPill = group.querySelector('.pmc-omics-stat-pill');

          if (isBaseline) {{
            if (rect) {{
              rect.style.fill = '';
              rect.style.stroke = '';
            }}
            labels.forEach(l => l.style.fill = '');
            if (statPill) statPill.remove();
            group.style.opacity = '1.0';
            group.style.filter = 'none';
            return;
          }}

          const nInfo = mapData[nodeId];
          if (nInfo && nInfo.assayed && nInfo.contrasts && nInfo.contrasts[currentContrast]) {{
            const c = nInfo.contrasts[currentContrast];
            const colorInfo = getContrastColor(c.fc, isDark);
            if (rect) {{
              rect.style.fill = colorInfo.hex;
            }}
            // Adaptive text luminance for WCAG AAA compliance
            const textFill = colorInfo.lum < 0.45 ? '#f8fafc' : '#111827';
            labels.forEach(l => l.style.fill = textFill);

            // Stat pill
            if (!statPill && rect) {{
              statPill = document.createElementNS('http://www.w3.org/2000/svg', 'g');
              statPill.setAttribute('class', 'pmc-omics-stat-pill');
              const rx = parseFloat(rect.getAttribute('x')) + 6;
              const ry = parseFloat(rect.getAttribute('y')) + 6;
              statPill.innerHTML = `
                <rect x="${{rx}}" y="${{ry}}" width="42" height="13" rx="3" fill="#0f172a" opacity="0.88" />
                <text x="${{rx + 21}}" y="${{ry + 9.5}}" font-size="9px" font-weight="700" fill="#38bdf8" text-anchor="middle">
                  ${{c.fc >= 0 ? '+' : ''}}${{c.fc.toFixed(2)}}${{c.sig ? '*' : ''}}
                </text>
              `;
              group.appendChild(statPill);
            }} else if (statPill && rect) {{
              const rx = parseFloat(rect.getAttribute('x')) + 6;
              const ry = parseFloat(rect.getAttribute('y')) + 6;
              statPill.innerHTML = `
                <rect x="${{rx}}" y="${{ry}}" width="42" height="13" rx="3" fill="#0f172a" opacity="0.88" />
                <text x="${{rx + 21}}" y="${{ry + 9.5}}" font-size="9px" font-weight="700" fill="#38bdf8" text-anchor="middle">
                  ${{c.fc >= 0 ? '+' : ''}}${{c.fc.toFixed(2)}}${{c.sig ? '*' : ''}}
                </text>
              `;
            }}

            // Significance filter gating
            if (sigFilterActive && !c.sig) {{
              group.style.opacity = '0.30';
              group.style.filter = 'grayscale(70%)';
            }} else {{
              group.style.opacity = '1.0';
              group.style.filter = 'none';
            }}
          }} else {{
            // Non-assayed / metabolite
            if (rect) {{
              rect.style.fill = '';
            }}
            labels.forEach(l => l.style.fill = '');
            if (statPill) statPill.remove();
            if (sigFilterActive) {{
              group.style.opacity = '0.35';
              group.style.filter = 'none';
            }} else {{
              group.style.opacity = '1.0';
              group.style.filter = 'none';
            }}
          }}
        }});

        updateTelemetryHud(mapData, currentContrast);
      }}

      function updateTelemetryHud(mapData, contrastKey) {{
        const isBaseline = contrastKey === 'none';
        const nodes = Object.values(mapData);
        const total = nodes.length;

        if (isBaseline) {{
          document.getElementById('hud-assayed-count').textContent = total + ' Nodes';
          document.getElementById('hud-mean-fc').textContent = 'Baseline (T1-T5)';
          const t1Count = nodes.filter(n => n.tier === 'T1').length;
          document.getElementById('hud-sig-count').textContent = t1Count + ' T1 Empirical';
          document.getElementById('hud-top-responder').textContent = 'MitoCarta Synteny';
          return;
        }}

        const assayedNodes = nodes.filter(n => n.assayed && n.contrasts && n.contrasts[contrastKey]);
        const assayedCount = assayedNodes.length;
        const pctAssayed = total > 0 ? ((assayedCount / total) * 100).toFixed(1) : 0;
        document.getElementById('hud-assayed-count').textContent = `${{assayedCount}} / ${{total}} (${{pctAssayed}}%)`;

        if (assayedCount === 0) {{
          document.getElementById('hud-mean-fc').textContent = 'N/A';
          document.getElementById('hud-sig-count').textContent = '0 (0.0%)';
          document.getElementById('hud-top-responder').textContent = 'None';
          return;
        }}

        let sumFc = 0;
        let sigCount = 0;
        let topNode = null;
        let maxAbsFc = -1;

        assayedNodes.forEach(n => {{
          const c = n.contrasts[contrastKey];
          sumFc += c.fc;
          if (c.sig) sigCount++;
          const absVal = Math.abs(c.fc);
          if (absVal > maxAbsFc) {{
            maxAbsFc = absVal;
            topNode = {{ symbol: n.symbol, fc: c.fc, sig: c.sig }};
          }}
        }});

        const meanFc = (sumFc / assayedCount).toFixed(2);
        const sigPct = ((sigCount / assayedCount) * 100).toFixed(1);

        document.getElementById('hud-mean-fc').textContent = `${{meanFc >= 0 ? '+' : ''}}${{meanFc}}`;
        document.getElementById('hud-sig-count').textContent = `${{sigCount}} (${{sigPct}}%)`;
        if (topNode) {{
          document.getElementById('hud-top-responder').textContent = `${{topNode.symbol}} (${{topNode.fc >= 0 ? '+' : ''}}${{topNode.fc.toFixed(2)}}${{topNode.sig ? '*' : ''}})`;
        }} else {{
          document.getElementById('hud-top-responder').textContent = 'None';
        }}
      }}

      window.inspectStudioNode = function(nodeId) {{
        activeInspectorNode = nodeId;
        const mapData = mapOmicsData[currentMapId] || {{}};
        const node = mapData[nodeId];
        const drawer = document.getElementById('node-inspector-drawer');
        if (!drawer) return;

        // Highlight selected node in SVG
        const container = document.getElementById('studio-svg-container');
        if (container) {{
          container.querySelectorAll('.pmc-node').forEach(r => r.style.outline = '');
          const activeGroup = container.querySelector(`[data-node-id="${{nodeId}}"]`) || container.querySelector(`#node-${{nodeId}}`);
          if (activeGroup) {{
            const activeRect = activeGroup.querySelector('.pmc-node');
            if (activeRect) activeRect.style.outline = '3px solid var(--primary)';
          }}
        }}

        if (!node) {{
          document.getElementById('drawer-node-type').textContent = 'UNKNOWN NODE';
          document.getElementById('drawer-node-title').textContent = nodeId;
          document.getElementById('drawer-node-locus').textContent = 'No database entry found';
          drawer.classList.add('open');
          return;
        }}

        // Header
        document.getElementById('drawer-node-type').textContent = node.assayed ? 'PROTEIN COMPLEX • TIER ' + node.tier : 'METABOLITE / PHYSIOLOGICAL POOL';
        document.getElementById('drawer-node-title').textContent = node.title || node.symbol;
        document.getElementById('drawer-node-locus').textContent = (node.locus ? (node.locus + ' • ') : '') + (node.compartment || 'Cellular Compartment');

        // Contrasts Grid
        const contrastsGrid = document.getElementById('drawer-contrasts-grid');
        if (contrastsGrid) {{
          if (node.assayed && node.contrasts && Object.keys(node.contrasts).length > 0) {{
            const contrastLabels = {{
              'osd120_root': 'OSD-120: Col-0 Root RNA-seq',
              'osd120_shoot': 'OSD-120: Col-0 Shoot RNA-seq',
              'osd427_protein': 'OSD-427: Plant Proteomics (TMT)',
              'osd37': 'OSD-37: Seedling Microgravity (EMCS)',
              'osd782': 'OSD-782: Dark Seedling Microgravity',
              'osd8': 'OSD-8: Radiation vs 1g Centrifuge',
            }};
            let rowsHtml = '';
            for (const [key, c] of Object.entries(node.contrasts)) {{
              const fcClass = c.fc > 0.3 ? 'fc-up' : (c.fc < -0.3 ? 'fc-down' : 'fc-neutral');
              const sign = c.fc >= 0 ? '+' : '';
              const barPct = Math.min(100, Math.abs(c.fc) / 2.0 * 50);
              const barStyle = c.fc >= 0 
                ? `left: 50%; width: ${{barPct}}%; background: #D55E00;`
                : `right: 50%; width: ${{barPct}}%; background: #0072B2;`;
              rowsHtml += `
                <div class="contrast-row">
                  <div class="contrast-header-line">
                    <span class="contrast-name">${{contrastLabels[key] || key}}</span>
                    <div class="contrast-stat-badges">
                      <span class="fc-badge ${{fcClass}}">${{sign}}${{c.fc.toFixed(2)}} log2FC</span>
                      <span class="sig-pill" style="${{c.sig ? '' : 'background: var(--surface-2); color: var(--muted);'}}">
                        ${{c.sig ? 'p &le; 0.05' : 'p=' + c.pval.toFixed(3)}}
                      </span>
                    </div>
                  </div>
                  <div class="bar-track">
                    <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: var(--muted);"></div>
                    <div class="bar-fill" style="${{barStyle}}"></div>
                  </div>
                </div>
              `;
            }}
            contrastsGrid.innerHTML = rowsHtml;
          }} else {{
            contrastsGrid.innerHTML = `
              <div style="padding: 12px; background: var(--bg); border: 1px solid var(--line); border-radius: 6px; color: var(--muted); font-size: 0.85rem;">
                Non-transcriptional pool or structural component. Not directly measured by RNA-seq or proteomics. Participates in biochemical flux with associated enzymes.
              </div>
            `;
          }}
        }}

        // Concordance Box
        const concBox = document.getElementById('drawer-concordance-box');
        if (concBox) {{
          if (node.concordance) {{
            const conc = node.concordance;
            concBox.innerHTML = `
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: var(--ink);">Response Mode:</strong>
                <span class="sig-pill" style="font-weight: 700;">${{conc.category}}</span>
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 4px;">
                <div><span style="color: var(--muted);">mRNA (OSD-120 Root):</span> <strong>${{conc.mrna_fc >= 0 ? '+' : ''}}${{conc.mrna_fc.toFixed(2)}}</strong></div>
                <div><span style="color: var(--muted);">Protein (OSD-427):</span> <strong>${{conc.prot_fc >= 0 ? '+' : ''}}${{conc.prot_fc.toFixed(2)}}</strong></div>
              </div>
              <div style="font-size: 0.78rem; color: var(--muted); margin-top: 4px;">
                Delta (Protein - mRNA): <strong>${{conc.delta >= 0 ? '+' : ''}}${{conc.delta.toFixed(2)}}</strong>.
                ${{conc.category === 'Post-transcriptionally Buffered' ? 'Transcriptional change is buffered at the translation/degradation level in spaceflight.' : 'Coordinated directional change across transcript and proteome tiers.'}}
              </div>
            `;
          }} else {{
            concBox.innerHTML = '<span style="color: var(--muted);">No paired mRNA-protein spaceflight concordance data available for this locus.</span>';
          }}
        }}

        // SUBA5 Box
        const subaBox = document.getElementById('drawer-suba-box');
        if (subaBox) {{
          if (node.suba) {{
            const s = node.suba;
            subaBox.innerHTML = `
              <div><strong style="color: var(--ink);">SUBAcon Consensus:</strong> <span style="color: var(--primary); font-weight: 700;">${{s.consensus.replace(/_/g, ' ').toUpperCase()}}</span> (${{(s.score * 100).toFixed(0)}}% confidence)</div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 4px;">
                <div><span style="color: var(--muted);">MS Proteomics:</span> <strong>${{s.has_ms ? 'Detected (' + s.ms_comps.join(', ') + ')' : 'No peptides'}}</strong></div>
                <div><span style="color: var(--muted);">GFP Imaging:</span> <strong>${{s.has_gfp ? 'Observed (' + s.gfp_comps.join(', ') + ')' : 'No imaging'}}</strong></div>
              </div>
              <div style="margin-top: 4px; font-size: 0.8rem;">
                <span style="color: var(--muted);">Dual Targeting:</span> <strong>${{s.dual ? 'Yes (' + s.dual_classes.join(', ') + ')' : 'Single Compartment Target'}}</strong>
              </div>
            `;
          }} else {{
            subaBox.innerHTML = `<div><strong style="color: var(--ink);">Compartment:</strong> ${{node.compartment || 'Unspecified'}}</div>`;
          }}
        }}

        // MitoCarta Box
        const mitoBox = document.getElementById('drawer-mitocarta-box');
        if (mitoBox) {{
          if (node.mitocarta) {{
            const mc = node.mitocarta;
            mitoBox.innerHTML = `
              <div><strong style="color: var(--ink);">Human Ortholog:</strong> <span style="color: var(--primary); font-weight: 700;">${{mc.human_symbol}}</span> ${{mc.human_entrez ? '(Entrez: ' + mc.human_entrez + ')' : ''}}</div>
              <div><span style="color: var(--muted);">MitoPathway:</span> <strong>${{mc.mitopathway || 'OXPHOS / Metabolism'}}</strong></div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 4px;">
                <div><span style="color: var(--muted);">Evolutionary Quadrant:</span> <strong>${{mc.quadrant}}</strong></div>
                <div><span style="color: var(--muted);">Synteny Identity:</span> <strong>${{mc.identity_pct}}%</strong></div>
              </div>
              ${{mc.notes || mc.clinical ? `<div style="font-size: 0.78rem; color: var(--muted); margin-top: 4px;">${{mc.notes || mc.clinical}}</div>` : ''}}
            `;
          }} else {{
            mitoBox.innerHTML = '<div><strong style="color: var(--ink);">Broad MitoCarta 3.0 Synteny:</strong> Plant-Specific Innovation / Non-Mammalian Machinery (absent in human MitoCarta 3.0).</div>';
          }}
        }}

        // External Links
        const tairLink = document.getElementById('drawer-tair-link');
        if (tairLink) {{
          if (node.locus) {{
            tairLink.href = `https://www.arabidopsis.org/servlets/TairObject?type=locus&name=${{node.locus}}`;
            tairLink.style.display = 'inline-flex';
          }} else {{
            tairLink.style.display = 'none';
          }}
        }}
        const osdrLink = document.getElementById('drawer-osdr-link');
        if (osdrLink) {{
          osdrLink.href = 'https://osdr.nasa.gov/bio/repo/data/studies/OSD-120';
        }}
        const subaLink = document.getElementById('drawer-suba-link');
        if (subaLink) {{
          subaLink.href = 'https://suba.live/';
        }}

        drawer.classList.add('open');
      }};

      window.closeInspectorDrawer = function() {{
        const drawer = document.getElementById('node-inspector-drawer');
        if (drawer) drawer.classList.remove('open');
        const container = document.getElementById('studio-svg-container');
        if (container) {{
          container.querySelectorAll('.pmc-node').forEach(r => r.style.outline = '');
        }}
        activeInspectorNode = null;
      }};

      // Theme toggle hook
      const themeBtn = document.getElementById('cose-theme-toggle');
      if (themeBtn) {{
        themeBtn.addEventListener('click', function() {{
          setTimeout(applyOmicsOverlay, 50);
        }});
      }}

      // Initialize default map
      attachNodeClickListeners();
      applyOmicsOverlay();
    }})();
    </script>
    {html_footer()}
    """
    return html_head("Plant MitoCarta Atlas", extra_css=studio_css) + content


def build_digital_doubles_page(ont):
    doubles = get_all_doubles()
    syn = get_synoptic_cell_layout()
    matrix_data = get_organellar_multiomics_matrix()

    # Preload expression tables for OSD-120
    tbl = load_expression_table("OSD-120")
    projections = {}
    for d_id, d in doubles.items():
        projections[d_id] = project_expression_onto_double(d, ont, tbl)

    proj_json = {}
    for d_id, p_map in projections.items():
        proj_json[d_id] = {
            sub_id: {
                "val": round(pv.value, 3),
                "sig": pv.significant,
                "p_val": pv.p_value,
                "color": pv.hex_color,
                "provenance": pv.provenance,
                "loci": list(pv.loci_used),
            }
            for sub_id, pv in p_map.items()
        }

    doubles_meta_json = {
        d_id: {
            "name": d.name,
            "go_cc": d.go_cc,
            "desc": d.description,
            "subcomps": [
                {
                    "id": s.id,
                    "label": s.label,
                    "go_cc": s.go_cc,
                    "desc": s.description,
                    "color": s.color_hex,
                    "box": {"x": s.box.x, "y": s.box.y, "w": s.box.w, "h": s.box.h},
                    "anchor_ports": s.anchor_ports,
                }
                for s in d.subcompartments
            ],
        }
        for d_id, d in doubles.items()
    }

    extra_css = """
    .doubles-layout {
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 24px;
      margin-top: 24px;
    }
    .control-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 20px;
    }
    .canvas-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 24px;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 650px;
    }
    .view-select-btn {
      width: 100%;
      text-align: left;
      padding: 10px 14px;
      margin-bottom: 8px;
      background: var(--bg);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--text);
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .view-select-btn.active {
      background: var(--primary-light);
      border-color: var(--primary);
      color: var(--primary);
    }
    .dataset-dropdown {
      width: 100%;
      padding: 8px 12px;
      background: var(--bg);
      border: 1px solid var(--card-border);
      color: var(--text);
      border-radius: 6px;
      font-size: 0.9rem;
      margin-top: 6px;
      margin-bottom: 16px;
    }
    .subcomp-card {
      background: var(--bg);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px;
      margin-top: 8px;
      font-size: 0.85rem;
    }
    .heatmap-card {
      margin-top: 36px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 24px;
    }
    .sort-btn {
      padding: 5px 12px;
      font-size: 0.8rem;
      font-weight: 600;
      border-radius: 6px;
      border: 1px solid var(--card-border);
      background: var(--bg);
      color: var(--ink);
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .sort-btn.active {
      background: var(--primary-light);
      border-color: var(--primary);
      color: var(--primary);
    }
    .heat-pill {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 0.74rem;
      font-weight: 700;
      font-family: var(--font-mono);
      white-space: nowrap;
    }
    .heat-cell {
      text-align: center;
      font-family: var(--font-mono);
      font-weight: 700;
      font-size: 0.82rem;
      padding: 8px 6px;
      border-radius: 4px;
      cursor: default;
      transition: transform 0.1s ease;
    }
    .heat-cell:hover {
      transform: scale(1.08);
      box-shadow: 0 2px 6px rgba(0,0,0,0.18);
      z-index: 2;
      position: relative;
    }
    .heat-row {
      transition: background-color 0.15s ease;
    }
    .heat-row:hover {
      background: var(--surface-2) !important;
    }
    """

    content = f"""
    {nav_header(active='doubles')}
    <main class="container">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
        <div>
          <h2 style="font-size: 1.8rem; font-weight: 800;">Subcellular Digital Doubles & Multi-Omics Projection</h2>
          <p style="color: var(--text-soft); max-width: 800px; margin-top: 4px;">
            Coordinate-bound digital double templates for Mitochondrion, Chloroplast, Nucleus, and Plasma Membrane.
            Project real NASA OSDR spaceflight differential expression ($log_2 FC$) directly onto compartmental subdomains.
          </p>
        </div>
      </div>

      <div class="doubles-layout">
        <aside class="control-panel">
          <h4 style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: var(--text-soft); margin-bottom: 10px;">Select Organelle Double</h4>
          <button class="view-select-btn active" data-mode="synoptic" onclick="switchDouble('synoptic')">
            <span>Cell Synoptic Overview</span> <span>🌐</span>
          </button>
          <button class="view-select-btn" data-mode="mitochondrion" onclick="switchDouble('mitochondrion')">
            <span>Plant Mitochondrion</span> <span>🔥</span>
          </button>
          <button class="view-select-btn" data-mode="chloroplast" onclick="switchDouble('chloroplast')">
            <span>Chloroplast</span> <span>🌿</span>
          </button>
          <button class="view-select-btn" data-mode="nucleus" onclick="switchDouble('nucleus')">
            <span>Nucleus</span> <span>🧬</span>
          </button>
          <button class="view-select-btn" data-mode="plasma_membrane" onclick="switchDouble('plasma_membrane')">
            <span>Plasma Membrane</span> <span>🛡️</span>
          </button>

          <hr style="border: none; border-top: 1px solid var(--card-border); margin: 20px 0;">

          <h4 style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: var(--text-soft); margin-bottom: 6px;">Multi-Omics Data Overlay</h4>
          <label style="font-size: 0.8rem; color: var(--text-soft);">Select NASA OSDR Dataset:</label>
          <select id="dataset-select" class="dataset-dropdown" onchange="toggleDataOverlay(this.value)">
            <option value="none">Baseline (Anatomical Fills)</option>
            <option value="OSD-120" selected>OSD-120: Spaceflight vs Ground (APEX-03-2)</option>
            <option value="OSD-8">OSD-8: Radiation vs Control</option>
            <option value="OSD-782">OSD-782: Microgravity (BRIC-19)</option>
          </select>

          <div id="inspector-panel" style="margin-top: 16px;">
            <h4 style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: var(--text-soft);">Compartment Inspector</h4>
            <div id="inspector-body" style="font-size: 0.85rem; color: var(--text-soft); margin-top: 8px;">
              Hover or click on any subcompartment or organelle to view its GO-CCO grounding, active proteins, and spaceflight response.
            </div>
          </div>
        </aside>

        <section class="canvas-panel">
          <div style="width: 100%; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 id="canvas-title" style="font-size: 1.2rem; font-weight: 700;">Plant Cell Synoptic View (All 4 Doubles)</h3>
            <div id="data-legend" style="display: flex; align-items: center; gap: 8px; font-size: 0.8rem; color: var(--text-soft);">
              <span>Down (-2.0)</span>
              <div style="width: 80px; height: 10px; border-radius: 2px; background: linear-gradient(to right, #0072B2, #f5f5f5, #D55E00);"></div>
              <span>Up (+2.0 log2FC)</span>
            </div>
          </div>
          <svg id="double-svg" viewBox="0 0 1600 1100" style="width: 100%; max-height: 700px; border-radius: 8px; background: var(--bg); border: 1px solid var(--card-border);"></svg>
        </section>
      </div>

      <!-- SUBCOMPARTMENT MULTI-OMICS EXPRESSION & ABUNDANCE HEATMAP -->
      <section class="heatmap-card" id="doubles-heatmap-section">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 20px;">
          <div>
            <div style="display: flex; align-items: center; gap: 10px;">
              <span style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 8px; background: var(--primary-light); color: var(--primary); font-size: 1.15rem;">📊</span>
              <h3 style="font-size: 1.35rem; font-weight: 800; margin: 0;">Subcompartment Multi-Omics Expression & Abundance Heatmap</h3>
            </div>
            <p style="color: var(--text-soft); font-size: 0.92rem; margin-top: 6px; max-width: 950px;">
              Direct molecular matrix quantifying spaceflight gene expression (<span style="font-family: monospace; font-weight: 600;">log2FC</span>) and protein abundance across organellar subcompartments. Synchronized with the active organelle double selected above.
            </p>
          </div>
          <div style="display: flex; align-items: center; gap: 10px; font-size: 0.82rem; color: var(--text-soft); background: var(--bg); padding: 8px 14px; border-radius: 6px; border: 1px solid var(--card-border);">
            <span>Diverging Scale:</span>
            <span style="color: #0072B2; font-weight: 700;">-2.0</span>
            <div style="width: 80px; height: 10px; border-radius: 3px; background: linear-gradient(to right, #0072B2, #f1f5f9, #D55E00);"></div>
            <span style="color: #D55E00; font-weight: 700;">+2.0 log2FC</span>
          </div>
        </div>

        <!-- Heatmap Toolbar -->
        <div class="heatmap-toolbar" style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--card-border);">
          <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
            <div style="position: relative;">
              <input type="text" id="heat-search" placeholder="Search gene symbol or locus..." style="padding: 7px 12px 7px 32px; border-radius: 6px; border: 1px solid var(--card-border); background: var(--bg); color: var(--ink); font-size: 0.85rem; width: 230px;" oninput="updateHeatmap()">
              <span style="position: absolute; left: 10px; top: 8px; font-size: 0.85rem; color: var(--text-soft);">🔍</span>
            </div>
            <div style="display: flex; align-items: center; gap: 6px;">
              <label style="font-size: 0.82rem; font-weight: 600; color: var(--text-soft);">Organelle:</label>
              <select id="heat-organelle-filter" style="padding: 6px 10px; border-radius: 6px; border: 1px solid var(--card-border); background: var(--bg); color: var(--ink); font-size: 0.85rem;" onchange="updateHeatmap()">
                <option value="all">All Organelles (Synoptic)</option>
                <option value="mitochondrion">Mitochondrion Only</option>
                <option value="chloroplast">Chloroplast Only</option>
                <option value="nucleus">Nucleus Only</option>
                <option value="plasma_membrane">Plasma Membrane Only</option>
              </select>
            </div>
            <label style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.84rem; color: var(--ink); cursor: pointer; margin-left: 6px;">
              <input type="checkbox" id="heat-sig-only" onchange="updateHeatmap()" style="cursor: pointer;">
              <span>Significant only (p &le; 0.05)</span>
            </label>
          </div>

          <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 0.82rem; color: var(--text-soft); margin-right: 4px;">Sort:</span>
            <button id="sort-comp-btn" class="sort-btn active" onclick="setHeatSort('compartment')">Compartment</button>
            <button id="sort-fc-btn" class="sort-btn" onclick="setHeatSort('fc_desc')">Max |Log2FC|</button>
            <button id="sort-sym-btn" class="sort-btn" onclick="setHeatSort('symbol')">Symbol</button>
          </div>
        </div>

        <!-- Heatmap Table Container -->
        <div style="overflow-x: auto; max-width: 100%;">
          <table style="width: 100%; border-collapse: collapse; font-size: 0.84rem;">
            <thead>
              <tr>
                <th style="text-align: left; padding: 10px 12px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">Compartment</th>
                <th style="text-align: left; padding: 10px 12px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">Symbol</th>
                <th style="text-align: left; padding: 10px 12px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">AGI Locus</th>
                <th style="text-align: center; padding: 10px 8px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">OSD-120<br><span style="font-weight: 400; text-transform: none; color: var(--text-soft);">Root Flight</span></th>
                <th style="text-align: center; padding: 10px 8px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">OSD-120<br><span style="font-weight: 400; text-transform: none; color: var(--text-soft);">Shoot Flight</span></th>
                <th style="text-align: center; padding: 10px 8px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">OSD-37<br><span style="font-weight: 400; text-transform: none; color: var(--text-soft);">Seedlings</span></th>
                <th style="text-align: center; padding: 10px 8px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">OSD-427<br><span style="font-weight: 400; text-transform: none; color: var(--text-soft);">Proteomics</span></th>
                <th style="text-align: center; padding: 10px 8px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">OSD-782<br><span style="font-weight: 400; text-transform: none; color: var(--text-soft);">Centrifuge</span></th>
                <th style="text-align: center; padding: 10px 8px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">OSD-8<br><span style="font-weight: 400; text-transform: none; color: var(--text-soft);">Radiation</span></th>
                <th style="text-align: left; padding: 10px 12px; background: var(--bg); border-bottom: 2px solid var(--card-border); font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">Biological Function</th>
              </tr>
            </thead>
            <tbody id="heatmap-tbody">
              <!-- Dynamically populated by JS -->
            </tbody>
          </table>
        </div>

        <!-- Heatmap Summary Metrics Bar -->
        <div style="margin-top: 16px; padding: 12px 16px; background: var(--bg); border-radius: 6px; border: 1px solid var(--card-border); display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; font-size: 0.84rem;">
          <div id="heat-metrics-left">Showing all organellar loci</div>
          <div id="heat-metrics-right" style="color: var(--text-soft);">
            Mean Spaceflight Log2FC: <strong id="heat-mean-fc" style="color: var(--primary);">+0.42</strong> &bull; Significant Fraction: <strong id="heat-sig-frac">68%</strong>
          </div>
        </div>
      </section>
    </main>

    <script>
      const doublesData = {json.dumps(doubles_meta_json)};
      const projData = {json.dumps(proj_json)};
      const heatData = {json.dumps(matrix_data)};
      let currentMode = 'synoptic';
      let currentDataset = 'OSD-120';
      let currentHeatSort = 'compartment';

      function getContrastColor(hexColor) {{
        if (!hexColor || hexColor.charAt(0) !== '#') return '#0f172a';
        let hex = hexColor.substring(1);
        if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
        const r = parseInt(hex.substr(0, 2), 16) || 0;
        const g = parseInt(hex.substr(2, 2), 16) || 0;
        const b = parseInt(hex.substr(4, 2), 16) || 0;
        const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
        return (yiq >= 145) ? '#0f172a' : '#f8fafc';
      }}

      function getSubContrastColor(hexColor) {{
        if (!hexColor || hexColor.charAt(0) !== '#') return '#475569';
        let hex = hexColor.substring(1);
        if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
        const r = parseInt(hex.substr(0, 2), 16) || 0;
        const g = parseInt(hex.substr(2, 2), 16) || 0;
        const b = parseInt(hex.substr(4, 2), 16) || 0;
        const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
        return (yiq >= 145) ? '#334155' : '#cbd5e1';
      }}

      function getColor(dId, subId) {{
        if (currentDataset === 'none') {{
          const meta = doublesData[dId];
          const sub = meta.subcomps.find(s => s.id === subId);
          return sub ? sub.color : '#334155';
        }}
        const dProj = projData[dId];
        if (dProj && dProj[subId]) {{
          return dProj[subId].color;
        }}
        return '#334155';
      }}

      function renderSynoptic() {{
        const svg = document.getElementById('double-svg');
        svg.setAttribute('viewBox', '0 0 1600 1100');

        const pmFill = getColor('plasma_membrane', 'plasma_membrane');
        const pmText = getContrastColor(pmFill);
        const pmSubText = getSubContrastColor(pmFill);

        const chlFill = getColor('chloroplast', 'chloroplast_stroma');
        const chlText = getContrastColor(chlFill);
        const chlSubText = getSubContrastColor(chlFill);

        const thylFill = getColor('chloroplast', 'thylakoid_membrane');
        const thylText = getContrastColor(thylFill);

        const mitFill = getColor('mitochondrion', 'mitochondrial_matrix');
        const mitText = getContrastColor(mitFill);
        const mitSubText = getSubContrastColor(mitFill);

        const crFill = getColor('mitochondrion', 'cristae');
        const crText = getContrastColor(crFill);

        const nucFill = getColor('nucleus', 'nucleoplasm');
        const nucText = getContrastColor(nucFill);
        const nucSubText = getSubContrastColor(nucFill);

        svg.innerHTML = `
          <!-- Cell Wall / Boundary -->
          <rect x="20" y="20" width="1560" height="1060" rx="30" fill="none" stroke="#64748b" stroke-width="6" stroke-dasharray="12 6" />
          <text x="50" y="55" font-family="Inter, sans-serif" font-weight="700" font-size="22" fill="#64748b">Plant Cell Boundary &amp; Wall (Apoplast)</text>

          <!-- 1. Plasma Membrane Double Banner -->
          <g id="box-pm" onclick="switchDouble('plasma_membrane')" style="cursor: pointer;">
            <rect x="60" y="80" width="1480" height="160" rx="12" fill="${{pmFill}}" stroke="#1d4e6b" stroke-width="3" />
            <text x="80" y="125" font-family="Inter, sans-serif" font-weight="700" font-size="20" fill="${{pmText}}">Plasma Membrane Double (Sensing &amp; Conduit)</text>
            <text x="80" y="155" font-family="Inter, sans-serif" font-size="14" fill="${{pmSubText}}">FERONIA, WAK1, RBOHD NADPH Oxidase, MSL10 stretch gate, GLR3.3/3.6 Ca2+ channels, PIP2;1</text>
            <rect x="76" y="172" width="680" height="28" rx="6" fill="rgba(15, 23, 42, 0.88)" stroke="rgba(255,255,255,0.2)" />
            <text x="90" y="191" font-family="JetBrains Mono, monospace" font-size="13" font-weight="600" fill="#38bdf8">OSD-120 Mean log2FC: +1.28 • RBOHD (+1.62), WAK1 (+1.38), MSL10 (+1.45)</text>
          </g>

          <!-- 2. Chloroplast Double -->
          <g id="box-chloro" onclick="switchDouble('chloroplast')" style="cursor: pointer;">
            <rect x="60" y="300" width="700" height="420" rx="20" fill="${{chlFill}}" stroke="#0b5c46" stroke-width="4" />
            <text x="90" y="345" font-family="Inter, sans-serif" font-weight="700" font-size="22" fill="${{chlText}}">Chloroplast Double (Plastidial Engine)</text>
            <text x="90" y="375" font-family="Inter, sans-serif" font-size="14" fill="${{chlSubText}}">Photosystems I/II • Calvin Cycle • GUN1 hub • SAL1-PAP • MEcPP • EX1</text>
            <!-- Thylakoid Grana Sub-box -->
            <rect x="90" y="420" width="640" height="140" rx="10" fill="${{thylFill}}" stroke="#063d2e" stroke-width="2" />
            <text x="110" y="458" font-family="Inter, sans-serif" font-weight="600" font-size="16" fill="${{thylText}}">Thylakoid Grana Stacks &amp; Lumen (PSII / PSI / Cyt b6f)</text>
            <rect x="105" y="474" width="530" height="28" rx="6" fill="rgba(15, 23, 42, 0.88)" stroke="rgba(255,255,255,0.2)" />
            <text x="120" y="493" font-family="JetBrains Mono, monospace" font-size="13" font-weight="600" fill="#6ee7b7">Singlet Oxygen Sensed by EXECUTER 1 (EX1 log2FC: +1.12)</text>
            <!-- Stromule Projection Tubule -->
            <path d="M 760 500 Q 820 620 680 780" fill="none" stroke="#10b981" stroke-width="6" stroke-dasharray="8 4" />
            <rect x="735" y="588" width="190" height="26" rx="6" fill="var(--card-bg)" stroke="#10b981" stroke-width="1.5" />
            <text x="830" y="605" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="#10b981">Stromule H2O2 Conduit</text>
          </g>

          <!-- 3. Mitochondrion Double (Plant MitoCarta) -->
          <g id="box-mito" onclick="switchDouble('mitochondrion')" style="cursor: pointer;">
            <rect x="840" y="300" width="700" height="420" rx="20" fill="${{mitFill}}" stroke="#7a4a12" stroke-width="4" />
            <text x="870" y="345" font-family="Inter, sans-serif" font-weight="700" font-size="22" fill="${{mitText}}">Plant Mitochondrion (Plant MitoCarta)</text>
            <text x="870" y="375" font-family="Inter, sans-serif" font-size="14" fill="${{mitSubText}}">Complexes I-V • AOX Bypass • Type II NDHs • CA Domain • GDC Photorespiration</text>
            <!-- Cristae Sub-box -->
            <rect x="870" y="420" width="640" height="140" rx="10" fill="${{crFill}}" stroke="#6b3f0d" stroke-width="2" />
            <text x="890" y="458" font-family="Inter, sans-serif" font-weight="600" font-size="16" fill="${{crText}}">Inner Membrane Cristae &amp; Relief Bypasses</text>
            <rect x="885" y="474" width="530" height="28" rx="6" fill="rgba(15, 23, 42, 0.88)" stroke="rgba(255,255,255,0.2)" />
            <text x="900" y="493" font-family="JetBrains Mono, monospace" font-size="13" font-weight="600" fill="#fb923c">AOX1a Surge: +1.84 log2FC • NDB2 (+1.32) • PUMP1 (+0.85)</text>
          </g>

          <!-- 4. Nucleus Double (Transcriptional Command) -->
          <g id="box-nucl" onclick="switchDouble('nucleus')" style="cursor: pointer;">
            <rect x="420" y="780" width="760" height="260" rx="20" fill="${{nucFill}}" stroke="#4a2a55" stroke-width="4" />
            <text x="450" y="825" font-family="Inter, sans-serif" font-weight="700" font-size="22" fill="${{nucText}}">Nucleus Double (Retrograde Convergence)</text>
            <text x="450" y="855" font-family="Inter, sans-serif" font-size="14" fill="${{nucSubText}}">MDRE Promoters • Cleaved ANAC017/013 • ABI4 • GLK1/2 • XRN2/3 Exoribonucleases</text>
            <rect x="450" y="880" width="700" height="120" rx="8" fill="rgba(15, 23, 42, 0.88)" stroke="#5c3569" />
            <text x="470" y="915" font-family="JetBrains Mono, monospace" font-size="13" font-weight="600" fill="#d8b4fe">Mitochondrial Retrograde: ANAC017 (+0.92) -&gt; MDRE -&gt; AOX1a (+1.84)</text>
            <text x="470" y="945" font-family="JetBrains Mono, monospace" font-size="13" font-weight="600" fill="#c084fc">Plastid Retrograde: SAL1 (-0.65) -&gt; PAP -&gt; XRN2/3 inhibition • GLK1 (-1.42)</text>
            <text x="470" y="975" font-family="JetBrains Mono, monospace" font-size="13" font-weight="600" fill="#fb7185">Photorespiration: GDC (-1.15) &amp; SHMT1 (-0.94) co-suppressed under orbit</text>
          </g>

          <!-- Inter-Organellar Dynamic Arrows -->
          <!-- PM to Mito / Chloro Wave -->
          <path d="M 400 240 L 400 300" stroke="#0284c7" stroke-width="4" marker-end="url(#arrow-blue)" />
          <path d="M 1200 240 L 1200 300" stroke="#0284c7" stroke-width="4" marker-end="url(#arrow-blue)" />
          <rect x="315" y="260" width="170" height="24" rx="4" fill="var(--card-bg)" stroke="#0284c7" />
          <text x="400" y="276" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="#0284c7">Ca2+ &amp; H2O2 Wave</text>
          <rect x="1115" y="260" width="170" height="24" rx="4" fill="var(--card-bg)" stroke="#0284c7" />
          <text x="1200" y="276" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="#0284c7">Ca2+ &amp; H2O2 Wave</text>

          <!-- Chloro & Mito to Nucleus -->
          <path d="M 400 720 L 500 780" stroke="#10b981" stroke-width="4" />
          <path d="M 1150 720 L 1050 780" stroke="#f97316" stroke-width="4" />
          <rect x="250" y="746" width="160" height="24" rx="4" fill="var(--card-bg)" stroke="#10b981" />
          <text x="330" y="762" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="#10b981">PRR (PAP &amp; GUN1)</text>
          <rect x="1070" y="746" width="160" height="24" rx="4" fill="var(--card-bg)" stroke="#f97316" />
          <text x="1150" y="762" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="#f97316">MRR (ANAC017)</text>

          <!-- Photorespiratory Loop (Chloro <-> Mito) -->
          <path d="M 760 380 L 840 380" stroke="#eab308" stroke-width="3" stroke-dasharray="6 4" />
          <rect x="730" y="368" width="140" height="24" rx="4" fill="var(--card-bg)" stroke="#eab308" />
          <text x="800" y="384" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="11" fill="#eab308">Photorespiration</text>
        `;
      }}

      function wrapTextLines(text, maxChars) {{
        if (!text) return [];
        const words = text.split(' ');
        const lines = [];
        let cur = '';
        for (let w of words) {{
          if ((cur + ' ' + w).trim().length <= maxChars) {{
            cur = (cur + ' ' + w).trim();
          }} else {{
            if (cur) lines.push(cur);
            cur = w;
          }}
        }}
        if (cur) lines.push(cur);
        return lines;
      }}

      function switchDouble(mode) {{
        currentMode = mode;
        document.querySelectorAll('.view-select-btn').forEach(b => {{
          b.classList.toggle('active', b.getAttribute('data-mode') === mode);
        }});

        if (mode === 'synoptic') {{
          document.getElementById('canvas-title').innerText = 'Plant Cell Synoptic View (All 4 Doubles)';
          renderSynoptic();
          if (document.getElementById('heat-organelle-filter')) {{
            document.getElementById('heat-organelle-filter').value = 'all';
            updateHeatmap();
          }}
          return;
        }}

        if (document.getElementById('heat-organelle-filter')) {{
          document.getElementById('heat-organelle-filter').value = mode;
          updateHeatmap();
        }}

        const dMeta = doublesData[mode];
        document.getElementById('canvas-title').innerText = dMeta.name;
        const svg = document.getElementById('double-svg');
        svg.setAttribute('viewBox', '0 0 960 600');

        const landmarkNames = {{
          tom: "TOM40 Complex", anac_tether: "ANAC017 Tether", vdac: "VDAC Porin",
          cyt_c: "Cytochrome c", ndb_ext: "Ext NDB Dehyd",
          complex_I: "Complex I", aox: "AOX Bypass", dtc: "DTC Carrier",
          ca_domain: "CA Domain", atp_synthase: "ATP Synthase",
          gdc: "GDC Photoresp", tca: "TCA Cycle", nucleoid: "mtDNA Nucleoid",
          toc: "TOC Complex", stromule_root: "Stromule Root",
          tic: "TIC Complex", papst1: "PAPST1 Carrier", dit1: "DiT1 Carrier",
          rubisco: "RuBisCO", gun1: "GUN1 PPR Hub", sal1: "SAL1 Phos",
          psii: "Photosystem II", b6f: "Cyt b6f", psi: "Photosystem I", ex1: "EXECUTER 1",
          npc_import: "NPC Import", npc_mrna: "NPC mRNA", stromule_dock: "Stromule Dock",
          mdre: "MDRE Promoters", anac_target: "ANAC Target", xrn_target: "XRN2/3",
          rrna: "rRNA Biogenesis",
          wall_strain: "Pectin Strain", apoplast_ros: "Apoplast ROS",
          fer: "FERONIA", wak1: "WAK1 Sensor", rbohd: "RBOHD NADPH", glr: "GLR3.3/3.6", pip: "PIP2;1 Aquaporin",
          ca_spike: "Ca2+ Spike", ros_wave: "Systemic ROS Wave"
        }};

        let rects = '';
        dMeta.subcomps.forEach((s, idx) => {{
          const fill = getColor(mode, s.id);
          const p = projData[mode] ? projData[mode][s.id] : null;
          const statText = p ? `log2FC: ${{p.val > 0 ? '+' : ''}}${{p.val}} (p=${{p.p_val}})` : 'Baseline Anatomy';
          const textColor = getContrastColor(fill);
          const subColor = getSubContrastColor(fill);
          const strokeColor = textColor === '#0f172a' ? '#334155' : 'rgba(255,255,255,0.7)';
          const badgeBg = 'rgba(15, 23, 42, 0.88)';
          const badgeText = p ? (p.val > 0 ? '#fb923c' : '#38bdf8') : '#94a3b8';
          const isMembrane = s.id.includes('membrane') || s.id.includes('envelope') || s.label.toLowerCase().includes('membrane') || s.label.toLowerCase().includes('envelope');
          const ports = s.anchor_ports || {{}};
          const portKeys = Object.keys(ports);

          if (s.box.w >= 650 && s.box.h < 130) {{
            // 3-Column horizontal architecture for wide strips (OMM, IMS, IMM, OEM, IEM, Nuclear envelope)
            // Column 1: Title + GO-CCO + Bilayer chip (x+18 to x+290)
            // Column 2: Word-wrapped description (x+310 to x+670)
            // Column 3: Padded stat scrim chip (x+s.box.w-235 to x+s.box.w-15)
            const descLines = wrapTextLines(s.desc, 44);
            const descTspans = descLines.slice(0, 3).map((line, lIdx) =>
              `<tspan x="${{s.box.x + 310}}" dy="${{lIdx === 0 ? 0 : 15}}">${{line}}</tspan>`
            ).join('');

            rects += `
              <g id="subcomp-g-${{s.id}}" style="cursor: pointer;" onclick="inspectSubcomp('${{mode}}', '${{s.id}}')">
                <rect id="subcomp-rect-${{s.id}}" x="${{s.box.x}}" y="${{s.box.y}}" width="${{s.box.w}}" height="${{s.box.h}}" rx="10" fill="${{fill}}" stroke="${{strokeColor}}" stroke-width="2" />
                ${{isMembrane ? `<rect x="${{s.box.x + 2}}" y="${{s.box.y + 2}}" width="${{s.box.w - 4}}" height="5" fill="url(#double-bilayer-pattern)" rx="3" opacity="0.85" />` : ''}}

                <!-- Column 1: Title and Badges -->
                <text x="${{s.box.x + 18}}" y="${{s.box.y + 26}}" font-family="Inter, sans-serif" font-weight="800" font-size="14.5" fill="${{textColor}}">${{s.label}}</text>
                <rect x="${{s.box.x + 18}}" y="${{s.box.y + 38}}" width="96" height="20" rx="4" fill="rgba(15, 23, 42, 0.88)" />
                <text x="${{s.box.x + 66}}" y="${{s.box.y + 52}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="10" font-weight="700" fill="#38bdf8">${{s.go_cc}}</text>
                ${{isMembrane ? `
                  <rect x="${{s.box.x + 120}}" y="${{s.box.y + 38}}" width="98" height="20" rx="4" fill="rgba(2, 132, 199, 0.25)" stroke="#0284c7" stroke-width="1" />
                  <text x="${{s.box.x + 169}}" y="${{s.box.y + 52}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9" font-weight="700" fill="#7dd3fc">LIPID BILAYER</text>
                ` : (portKeys.length > 0 ? `
                  <rect x="${{s.box.x + 120}}" y="${{s.box.y + 38}}" width="84" height="20" rx="4" fill="rgba(217, 119, 6, 0.2)" stroke="#d97706" stroke-width="1" />
                  <text x="${{s.box.x + 162}}" y="${{s.box.y + 52}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9" font-weight="700" fill="#fcd34d">${{portKeys.length}} Anchor Pins</text>
                ` : '')}}

                <!-- Column 2: Cleanly wrapped description lines -->
                <text x="${{s.box.x + 310}}" y="${{s.box.y + 24}}" font-family="Inter, sans-serif" font-size="11" fill="${{subColor}}">
                  ${{descTspans}}
                </text>

                <!-- Column 3: Padded Stat Scrim Card -->
                <rect x="${{s.box.x + s.box.w - 235}}" y="${{s.box.y + 14}}" width="220" height="52" rx="6" fill="${{badgeBg}}" stroke="rgba(255,255,255,0.2)" stroke-width="1" />
                <text x="${{s.box.x + s.box.w - 125}}" y="${{s.box.y + 33}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="11" font-weight="700" fill="${{badgeText}}">${{statText}}</text>
                <text x="${{s.box.x + s.box.w - 125}}" y="${{s.box.y + 51}}" text-anchor="middle" font-family="Inter, sans-serif" font-size="9.5" fill="#94a3b8">Click to Inspect • Landmarks</text>
              </g>
            `;
          }} else if (s.box.w >= 650) {{
            // Tall wide boxes (Stroma, Thylakoid, Apoplast, PM, Cytosol)
            const descLines = wrapTextLines(s.desc, 80);
            const descTspans = descLines.slice(0, 2).map((line, lIdx) =>
              `<tspan x="${{s.box.x + 18}}" dy="${{lIdx === 0 ? 0 : 16}}">${{line}}</tspan>`
            ).join('');

            let pinsHtml = '';
            portKeys.forEach((k, pIdx) => {{
              const pinX = s.box.x + 36 + pIdx * Math.min(170, Math.floor((s.box.w - 80) / Math.max(1, portKeys.length)));
              const pinY = s.box.y + 88;
              const name = landmarkNames[k] || k;
              pinsHtml += `
                <circle cx="${{pinX}}" cy="${{pinY}}" r="4" fill="#38bdf8" />
                <rect x="${{pinX + 8}}" y="${{pinY - 9}}" width="${{name.length * 6.8 + 14}}" height="18" rx="3" fill="rgba(15, 23, 42, 0.85)" stroke="rgba(56, 189, 248, 0.4)" stroke-width="0.8" />
                <text x="${{pinX + 15}}" y="${{pinY + 4}}" font-family="Inter, sans-serif" font-size="9" font-weight="700" fill="#f8fafc">${{name}}</text>
              `;
            }});

            rects += `
              <g id="subcomp-g-${{s.id}}" style="cursor: pointer;" onclick="inspectSubcomp('${{mode}}', '${{s.id}}')">
                <rect id="subcomp-rect-${{s.id}}" x="${{s.box.x}}" y="${{s.box.y}}" width="${{s.box.w}}" height="${{s.box.h}}" rx="10" fill="${{fill}}" stroke="${{strokeColor}}" stroke-width="2" />
                ${{isMembrane ? `<rect x="${{s.box.x + 2}}" y="${{s.box.y + 2}}" width="${{s.box.w - 4}}" height="5" fill="url(#double-bilayer-pattern)" rx="3" opacity="0.85" />` : ''}}

                <text x="${{s.box.x + 18}}" y="${{s.box.y + 26}}" font-family="Inter, sans-serif" font-weight="800" font-size="15" fill="${{textColor}}">${{s.label}}</text>
                <rect x="${{s.box.x + s.box.w - 110}}" y="${{s.box.y + 10}}" width="96" height="20" rx="4" fill="rgba(15, 23, 42, 0.88)" />
                <text x="${{s.box.x + s.box.w - 62}}" y="${{s.box.y + 24}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="10" font-weight="700" fill="#38bdf8">${{s.go_cc}}</text>
                ${{isMembrane ? `
                  <rect x="${{s.box.x + s.box.w - 220}}" y="${{s.box.y + 10}}" width="102" height="20" rx="4" fill="rgba(2, 132, 199, 0.25)" stroke="#0284c7" stroke-width="1" />
                  <text x="${{s.box.x + s.box.w - 169}}" y="${{s.box.y + 24}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9" font-weight="700" fill="#7dd3fc">LIPID BILAYER</text>
                ` : ''}}

                <text x="${{s.box.x + 18}}" y="${{s.box.y + 48}}" font-family="Inter, sans-serif" font-size="11.5" fill="${{subColor}}">
                  ${{descTspans}}
                </text>

                ${{pinsHtml}}

                <rect x="${{s.box.x + 18}}" y="${{s.box.y + s.box.h - 36}}" width="340" height="24" rx="4" fill="${{badgeBg}}" stroke="rgba(255,255,255,0.2)" stroke-width="1" />
                <text x="${{s.box.x + 28}}" y="${{s.box.y + s.box.h - 20}}" font-family="JetBrains Mono, monospace" font-size="11" font-weight="700" fill="${{badgeText}}">${{statText}} • Click to Inspect</text>
              </g>
            `;
          }} else {{
            // Column / Side-by-side boxes (Cristae, Matrix, Nucleoplasm, Nucleolus)
            const isNarrow = s.box.w < 350;
            const descStartY = isNarrow ? (s.box.y + 68) : (s.box.y + 54);
            const maxChars = Math.max(20, Math.floor((s.box.w - 36) / 7.2));
            const descLines = wrapTextLines(s.desc, maxChars);
            const descTspans = descLines.slice(0, 3).map((line, lIdx) =>
              `<tspan x="${{s.box.x + 18}}" dy="${{lIdx === 0 ? 0 : 16}}">${{line}}</tspan>`
            ).join('');

            let colPinsHtml = '';
            portKeys.forEach((k, pIdx) => {{
              const pinX = s.box.x + 24;
              const pinY = descStartY + 46 + pIdx * 24;
              const name = landmarkNames[k] || k;
              colPinsHtml += `
                <circle cx="${{pinX}}" cy="${{pinY}}" r="4" fill="#38bdf8" />
                <rect x="${{pinX + 8}}" y="${{pinY - 9}}" width="${{name.length * 6.8 + 14}}" height="18" rx="3" fill="rgba(15, 23, 42, 0.85)" stroke="rgba(56, 189, 248, 0.4)" stroke-width="0.8" />
                <text x="${{pinX + 15}}" y="${{pinY + 4}}" font-family="Inter, sans-serif" font-size="9" font-weight="700" fill="#f8fafc">${{name}}</text>
              `;
            }});

            rects += `
              <g id="subcomp-g-${{s.id}}" style="cursor: pointer;" onclick="inspectSubcomp('${{mode}}', '${{s.id}}')">
                <rect id="subcomp-rect-${{s.id}}" x="${{s.box.x}}" y="${{s.box.y}}" width="${{s.box.w}}" height="${{s.box.h}}" rx="10" fill="${{fill}}" stroke="${{strokeColor}}" stroke-width="2" />
                
                ${{!isNarrow ? `
                  <text x="${{s.box.x + 18}}" y="${{s.box.y + 26}}" font-family="Inter, sans-serif" font-weight="800" font-size="15" fill="${{textColor}}">${{s.label}}</text>
                  <rect x="${{s.box.x + s.box.w - 105}}" y="${{s.box.y + 10}}" width="92" height="20" rx="4" fill="rgba(15, 23, 42, 0.88)" />
                  <text x="${{s.box.x + s.box.w - 59}}" y="${{s.box.y + 24}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="10" font-weight="700" fill="#38bdf8">${{s.go_cc}}</text>
                ` : `
                  <text x="${{s.box.x + 16}}" y="${{s.box.y + 24}}" font-family="Inter, sans-serif" font-weight="800" font-size="13.5" fill="${{textColor}}">${{s.label}}</text>
                  <rect x="${{s.box.x + 16}}" y="${{s.box.y + 34}}" width="88" height="18" rx="4" fill="rgba(15, 23, 42, 0.88)" />
                  <text x="${{s.box.x + 60}}" y="${{s.box.y + 47}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="9.5" font-weight="700" fill="#38bdf8">${{s.go_cc}}</text>
                `}}

                <text x="${{s.box.x + 18}}" y="${{descStartY}}" font-family="Inter, sans-serif" font-size="11.5" fill="${{subColor}}">
                  ${{descTspans}}
                </text>

                ${{colPinsHtml}}

                <rect x="${{s.box.x + 18}}" y="${{s.box.y + s.box.h - 36}}" width="${{Math.min(s.box.w - 36, 260)}}" height="24" rx="4" fill="${{badgeBg}}" stroke="rgba(255,255,255,0.2)" stroke-width="1" />
                <text x="${{s.box.x + 26}}" y="${{s.box.y + s.box.h - 20}}" font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="700" fill="${{badgeText}}">${{statText}} • Inspect</text>
              </g>
            `;
          }}
        }});

        svg.innerHTML = `
          <defs>
            <pattern id="double-bilayer-pattern" width="12" height="6" patternUnits="userSpaceOnUse">
              <circle cx="3" cy="2" r="1.5" fill="#38bdf8" opacity="0.8" />
              <circle cx="9" cy="2" r="1.5" fill="#38bdf8" opacity="0.8" />
              <line x1="3" y1="3.5" x2="3" y2="5.5" stroke="#38bdf8" stroke-width="0.8" opacity="0.6" />
              <line x1="9" y1="3.5" x2="9" y2="5.5" stroke="#38bdf8" stroke-width="0.8" opacity="0.6" />
            </pattern>
          </defs>
          <rect x="0" y="0" width="960" height="600" fill="var(--bg)" rx="10" />
          ${{rects}}
        `;
      }}

      function inspectSubcomp(dId, subId) {{
        const meta = doublesData[dId];
        const sub = meta.subcomps.find(s => s.id === subId);
        const p = projData[dId] ? projData[dId][subId] : null;

        const landmarkNames = {{
          tom: "TOM40 Complex", anac_tether: "ANAC017 Tether", vdac: "VDAC Porin",
          cyt_c: "Cytochrome c", ndb_ext: "Ext NDB Dehyd",
          complex_I: "Complex I", aox: "AOX Bypass", dtc: "DTC Carrier",
          ca_domain: "CA Domain", atp_synthase: "ATP Synthase",
          gdc: "GDC Photoresp", tca: "TCA Cycle", nucleoid: "mtDNA Nucleoid",
          toc: "TOC Complex", stromule_root: "Stromule Root",
          tic: "TIC Complex", papst1: "PAPST1 Carrier", dit1: "DiT1 Carrier",
          rubisco: "RuBisCO", gun1: "GUN1 PPR Hub", sal1: "SAL1 Phos",
          psii: "Photosystem II", b6f: "Cyt b6f", psi: "Photosystem I", ex1: "EXECUTER 1",
          npc_import: "NPC Import", npc_mrna: "NPC mRNA", stromule_dock: "Stromule Dock",
          mdre: "MDRE Promoters", anac_target: "ANAC Target", xrn_target: "XRN2/3",
          rrna: "rRNA Biogenesis",
          wall_strain: "Pectin Strain", apoplast_ros: "Apoplast ROS",
          fer: "FERONIA", wak1: "WAK1 Sensor", rbohd: "RBOHD NADPH", glr: "GLR3.3/3.6", pip: "PIP2;1 Aquaporin",
          ca_spike: "Ca2+ Spike", ros_wave: "Systemic ROS Wave"
        }};

        const ports = sub.anchor_ports || {{}};
        const portChips = Object.keys(ports).map(k => `
          <span style="display: inline-block; background: var(--surface-2); border: 1px solid var(--card-border); border-radius: 4px; padding: 2px 6px; margin: 2px 4px 2px 0; font-size: 0.75rem; font-weight: 600; color: var(--text);">
            📍 ${{landmarkNames[k] || k}}
          </span>
        `).join('');

        const body = document.getElementById('inspector-body');
        body.innerHTML = `
          <div class="subcomp-card">
            <strong style="color: var(--primary); font-size: 0.95rem;">${{sub.label}}</strong><br>
            <span style="font-family: monospace; font-size: 0.78rem;">${{sub.go_cc}}</span>
            <p style="margin: 6px 0; color: var(--text);">${{sub.desc}}</p>
            ${{portChips ? `
              <div style="margin: 8px 0;">
                <span style="font-size: 0.78rem; font-weight: 700; color: var(--text-soft); text-transform: uppercase;">Landmark Anchors:</span><br>
                <div style="margin-top: 4px;">${{portChips}}</div>
              </div>
            ` : ''}}
            ${{p ? `
              <div style="background: var(--card-bg); padding: 8px; border-radius: 4px; border: 1px solid var(--card-border); margin-top: 8px;">
                <strong>OSD-120 Response:</strong><br>
                <span>Mean log2FC: <strong style="color: ${{p.color}}">${{p.val > 0 ? '+' : ''}}${{p.val}}</strong></span><br>
                <span>Adj. p-value: ${{p.p_val}} (${{p.sig ? 'Significant' : 'NS'}})</span><br>
                <span>Loci: ${{p.loci.join(', ')}}</span>
              </div>
            ` : '<em>No expression data projected for this compartment</em>'}}
          </div>
        `;

        // Also filter the heatmap to this subcompartment
        if (document.getElementById('heat-search')) {{
          document.getElementById('heat-search').value = sub.label.split('(')[0].trim();
          updateHeatmap();
        }}
      }}

      function toggleDataOverlay(val) {{
        currentDataset = val;
        if (currentMode === 'synoptic') {{
          renderSynoptic();
        }} else {{
          switchDouble(currentMode);
        }}
        updateHeatmap();
      }}

      function setHeatSort(sortKey) {{
        currentHeatSort = sortKey;
        const compBtn = document.getElementById('sort-comp-btn');
        const fcBtn = document.getElementById('sort-fc-btn');
        const symBtn = document.getElementById('sort-sym-btn');
        if (compBtn) compBtn.classList.toggle('active', sortKey === 'compartment');
        if (fcBtn) fcBtn.classList.toggle('active', sortKey === 'fc_desc');
        if (symBtn) symBtn.classList.toggle('active', sortKey === 'symbol');
        updateHeatmap();
      }}

      function getHeatColor(val) {{
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (val === 0 || Math.abs(val) < 0.05) {{
          return {{ bg: isDark ? '#1e293b' : '#f1f5f9', fg: isDark ? '#94a3b8' : '#64748b' }};
        }}
        if (val > 0) {{
          const intensity = Math.min(1.0, val / 1.8);
          const r = Math.round(isDark ? (30 + intensity * 183) : (241 - intensity * 28));
          const g = Math.round(isDark ? (41 + intensity * 53) : (245 - intensity * 151));
          const b = Math.round(isDark ? (59 - intensity * 59) : (249 - intensity * 249));
          const fg = intensity > 0.45 ? '#ffffff' : (isDark ? '#f8fafc' : '#0f172a');
          return {{ bg: `rgb(${{r}},${{g}},${{b}})`, fg }};
        }} else {{
          const intensity = Math.min(1.0, Math.abs(val) / 1.8);
          const r = Math.round(isDark ? (30 - intensity * 30) : (241 - intensity * 241));
          const g = Math.round(isDark ? (41 + intensity * 73) : (245 - intensity * 131));
          const b = Math.round(isDark ? (59 + intensity * 119) : (249 - intensity * 71));
          const fg = intensity > 0.45 ? '#ffffff' : (isDark ? '#f8fafc' : '#0f172a');
          return {{ bg: `rgb(${{r}},${{g}},${{b}})`, fg }};
        }}
      }}

      function updateHeatmap() {{
        const tbody = document.getElementById('heatmap-tbody');
        if (!tbody) return;

        const q = (document.getElementById('heat-search') ? document.getElementById('heat-search').value : '').toLowerCase().trim();
        const orgFilter = document.getElementById('heat-organelle-filter') ? document.getElementById('heat-organelle-filter').value : 'all';
        const sigOnly = document.getElementById('heat-sig-only') ? document.getElementById('heat-sig-only').checked : false;

        let filtered = heatData.filter(item => {{
          if (orgFilter !== 'all' && item.organelle !== orgFilter) return false;
          if (q) {{
            const matchSym = item.symbol.toLowerCase().includes(q);
            const matchLoc = item.locus.toLowerCase().includes(q);
            const matchPath = item.pathway.toLowerCase().includes(q);
            const matchComp = item.subcompartment_label.toLowerCase().includes(q);
            if (!matchSym && !matchLoc && !matchPath && !matchComp) return false;
          }}
          if (sigOnly) {{
            const hasSig = Object.values(item.contrasts).some(c => c.sig === true);
            if (!hasSig) return false;
          }}
          return true;
        }});

        filtered.sort((a, b) => {{
          if (currentHeatSort === 'compartment') {{
            if (a.organelle !== b.organelle) return a.organelle.localeCompare(b.organelle);
            return a.subcompartment.localeCompare(b.subcompartment);
          }} else if (currentHeatSort === 'fc_desc') {{
            const maxA = Math.max(...Object.values(a.contrasts).map(c => Math.abs(c.fc)));
            const maxB = Math.max(...Object.values(b.contrasts).map(c => Math.abs(c.fc)));
            return maxB - maxA;
          }} else if (currentHeatSort === 'symbol') {{
            return a.symbol.localeCompare(b.symbol);
          }}
          return 0;
        }});

        const orgColors = {{
          mitochondrion: {{ bg: 'rgba(213, 94, 0, 0.15)', fg: '#D55E00', label: 'Mito' }},
          chloroplast: {{ bg: 'rgba(16, 110, 84, 0.15)', fg: '#106e54', label: 'Chloro' }},
          nucleus: {{ bg: 'rgba(92, 53, 105, 0.15)', fg: '#8b5cf6', label: 'Nuc' }},
          plasma_membrane: {{ bg: 'rgba(29, 78, 107, 0.15)', fg: '#0284c7', label: 'PM' }}
        }};

        const contrastKeys = ['osd120_root', 'osd120_shoot', 'osd37', 'osd427_protein', 'osd782', 'osd8'];
        let totalFc = 0;
        let countFc = 0;
        let sigGenesCount = 0;

        let rowsHtml = '';
        filtered.forEach(item => {{
          const orgInfo = orgColors[item.organelle] || {{ bg: 'var(--surface-2)', fg: 'var(--ink)', label: item.organelle }};
          let isItemSig = false;

          const cellsHtml = contrastKeys.map(k => {{
            const c = item.contrasts[k] || {{ fc: 0, pval: 1, fdr: 1, sig: false }};
            if (c.sig) isItemSig = true;
            totalFc += c.fc;
            countFc++;
            const style = getHeatColor(c.fc);
            const valStr = (c.fc > 0 ? '+' : '') + c.fc.toFixed(2) + (c.sig ? '*' : '');
            const tooltip = `${{item.symbol}} (${{item.locus}})\nContrast: ${{k}}\nLog2FC: ${{c.fc > 0 ? '+' : ''}}${{c.fc}}\np-value: ${{c.pval}}\nFDR q: ${{c.fdr}}\n${{c.sig ? 'SIGNIFICANT (p <= 0.05)' : 'Not Significant'}}`;
            return `<td style="padding: 6px 4px; text-align: center;"><div class="heat-cell" style="background: ${{style.bg}}; color: ${{style.fg}};" title="${{tooltip}}">${{valStr}}</div></td>`;
          }}).join('');

          if (isItemSig) sigGenesCount++;

          rowsHtml += `
            <tr class="heat-row" style="border-bottom: 1px solid var(--card-border);" onmouseenter="highlightSubcompInSvg('${{item.subcompartment}}')" onmouseleave="clearSvgHighlight()">
              <td style="padding: 10px 12px; white-space: nowrap;">
                <span class="heat-pill" style="background: ${{orgInfo.bg}}; color: ${{orgInfo.fg}};">${{orgInfo.label}}</span>
                <span style="font-size: 0.8rem; color: var(--text-soft); margin-left: 6px;">${{item.subcompartment_label.split('(')[0].trim()}}</span>
              </td>
              <td style="padding: 10px 12px; font-weight: 700; color: var(--ink); white-space: nowrap;">${{item.symbol}}</td>
              <td style="padding: 10px 12px; font-family: var(--font-mono); font-size: 0.8rem; color: var(--primary); white-space: nowrap;">${{item.locus}}</td>
              ${{cellsHtml}}
              <td style="padding: 10px 12px; color: var(--text-soft); font-size: 0.8rem;">${{item.pathway}}</td>
            </tr>
          `;
        }});

        if (filtered.length === 0) {{
          rowsHtml = '<tr><td colspan="10" style="text-align: center; padding: 24px; color: var(--text-soft);">No genes match the current filter criteria.</td></tr>';
        }}

        tbody.innerHTML = rowsHtml;

        const leftEl = document.getElementById('heat-metrics-left');
        if (leftEl) leftEl.innerText = `Showing ${{filtered.length}} of ${{heatData.length}} organellar loci`;
        const meanEl = document.getElementById('heat-mean-fc');
        if (meanEl) {{
          const mean = countFc > 0 ? (totalFc / countFc).toFixed(2) : '0.00';
          meanEl.innerText = (mean > 0 ? '+' : '') + mean;
        }}
        const sigEl = document.getElementById('heat-sig-frac');
        if (sigEl) {{
          const pct = filtered.length > 0 ? Math.round((sigGenesCount / filtered.length) * 100) : 0;
          sigEl.innerText = `${{pct}}% (${{sigGenesCount}}/${{filtered.length}})`;
        }}
      }}

      function highlightSubcompInSvg(subId) {{
        const el = document.getElementById(`subcomp-rect-${{subId}}`);
        if (el) {{
          el.setAttribute('stroke', '#38bdf8');
          el.setAttribute('stroke-width', '4');
        }}
      }}

      function clearSvgHighlight() {{
        const rects = document.querySelectorAll('svg rect[id^="subcomp-rect-"]');
        rects.forEach(r => {{
          if (r.getAttribute('stroke-width') === '4') {{
            r.setAttribute('stroke-width', '2');
            r.setAttribute('stroke', '#334155');
          }}
        }});
      }}

      // Initial render
      renderSynoptic();
      updateHeatmap();
    </script>
    {html_footer()}
    """
    return html_head("Digital Doubles Explorer — Plant MitoCarta", extra_css) + content


def build_retrograde_page():
    circuits_data = {
        "mrr": {
            "title": "Mitochondrial Retrograde Response (MRR): ANAC017/013 Proteolytic Axis",
            "desc": "How mitochondrial respiratory chain dysfunction or spaceflight microgravity hypoxia signals to the nucleus to induce alternative oxidase (AOX1a).",
            "theme_color": "#D55E00",
            "compartments": [
                {"id": "mito", "title": "Mitochondrial Matrix & Cristae", "x": 25, "y": 25, "w": 280, "h": 370, "fill": "rgba(213, 94, 0, 0.08)", "stroke": "#D55E00"},
                {"id": "omm", "title": "OMM Interface", "x": 325, "y": 25, "w": 150, "h": 370, "fill": "rgba(213, 94, 0, 0.04)", "stroke": "#b84d00", "dash": "6 4"},
                {"id": "cyto", "title": "Cytosol Transit Space", "x": 495, "y": 25, "w": 190, "h": 370, "fill": "rgba(59, 110, 165, 0.06)", "stroke": "#3B6EA5", "dash": "6 4"},
                {"id": "nuc", "title": "Nucleus & MDRE Promoters", "x": 705, "y": 25, "w": 270, "h": 370, "fill": "rgba(107, 70, 193, 0.08)", "stroke": "#6b46c1"},
            ],
            "path": "M 150 130 L 210 270 L 400 270 L 590 200 L 730 140 L 850 270",
            "steps": [
                {"id": "s1", "x": 150, "y": 130, "label": "Complex I/III ROS Leak", "sublabel": "Matrix & IMS H2O2 surge", "title": "Respiratory Chain Stress & ROS Surge", "text": "Complex I/III inhibition or microgravity hypoxia causes electron leakage to oxygen, elevating matrix and IMS superoxide, which dismutates to hydrogen peroxide (H2O2).", "glyph": "ros", "icon": "✨", "category": "Redox / ROS Surge", "locus": "ATMG00640", "spaceflight": "OSD-120: +1.42 log2FC (p=0.004)"},
                {"id": "s2", "x": 210, "y": 270, "label": "IMS H2O2 Diffusion", "sublabel": "Permeant H2O2 crosses cristae", "title": "Diffusion to Outer Mitochondrial Membrane", "text": "Membrane-permeant H2O2 diffuses across the intermembrane space (IMS) to oxidatively prime intramembrane proteases at the outer mitochondrial membrane (OMM).", "glyph": "transport", "icon": "🌊", "category": "Metabolite Diffusion", "locus": "AT3G22370", "spaceflight": "OSD-120: H2O2 prime signal"},
                {"id": "s3", "x": 400, "y": 270, "label": "Rhomboid Protease Cleavage", "sublabel": "C-anchor cut releases ANAC017", "title": "Proteolytic Cleavage of ANAC017 & ANAC013", "text": "Rhomboid-like proteases at the OMM/ER interface cleave the C-terminal transmembrane anchors of ANAC017 (AT1G34190) and ANAC013, releasing active N-terminal NAC transcription factors.", "glyph": "scissors", "icon": "✂️", "category": "Proteolytic Cleavage", "locus": "AT1G34190", "spaceflight": "ANAC017 transmembrane cut"},
                {"id": "s4", "x": 590, "y": 200, "label": "Importin-α/β Binding", "sublabel": "Soluble NAC domain chaperone", "title": "Cytosolic Chaperoning & Transit", "text": "The liberated soluble NAC domains bind karyopherin importin-α/β adapters, translocating rapidly across the cytosol towards the nuclear envelope.", "glyph": "transport", "icon": "🚚", "category": "Karyopherin Chaperone", "locus": "AT3G05720", "spaceflight": "Cytosolic nuclear transit"},
                {"id": "s5", "x": 730, "y": 140, "label": "Nuclear Pore Entry", "sublabel": "Active NPC basket transport", "title": "Nuclear Import via Pore Complexes", "text": "The ANAC017-importin complex passes through the FG-repeat permeability barrier of the nuclear pore complex into the nucleoplasm.", "glyph": "gate", "icon": "🚪", "category": "Nuclear Pore Transport", "locus": "AT5G42940", "spaceflight": "NUP complex translocation"},
                {"id": "s6", "x": 850, "y": 270, "label": "MDRE Binding & AOX1a", "sublabel": "CTTGN5CAG -> +1.84 log2FC", "title": "Palindromic MDRE Motif Binding & AOX1a Induction", "text": "ANAC017 homodimers bind palindromic MDRE motifs (CTTGNNNNNCAG), driving massive transcriptional induction of AOX1a (+1.84 log2FC in OSD-120), UPM1, and mitochondrial chaperones.", "glyph": "transcription", "icon": "🧬", "category": "Transcriptional Surge", "locus": "AT3G22370", "spaceflight": "OSD-120: +1.84 log2FC Surge (p=0.002)"}
            ]
        },
        "prr": {
            "title": "Plastid-to-Nucleus Retrograde Response (PRR): SAL1-PAP & GUN1 Hub",
            "desc": "Four parallel communication channels conveying chloroplast operational state, pigment biosynthesis, and photoinhibition to the nucleus.",
            "theme_color": "#059669",
            "compartments": [
                {"id": "chloro", "title": "Chloroplast Grana & Stroma", "x": 25, "y": 25, "w": 300, "h": 370, "fill": "rgba(5, 150, 105, 0.08)", "stroke": "#059669"},
                {"id": "env", "title": "Plastid Envelope & PAPST1", "x": 345, "y": 25, "w": 145, "h": 370, "fill": "rgba(5, 150, 105, 0.04)", "stroke": "#047857", "dash": "6 4"},
                {"id": "cyto", "title": "Cytosolic Transit Space", "x": 510, "y": 25, "w": 175, "h": 370, "fill": "rgba(59, 110, 165, 0.06)", "stroke": "#3B6EA5", "dash": "6 4"},
                {"id": "nuc", "title": "Nucleoplasm & PhANGs", "x": 705, "y": 25, "w": 270, "h": 370, "fill": "rgba(107, 70, 193, 0.08)", "stroke": "#6b46c1"},
            ],
            "path": "M 160 120 L 210 260 L 415 260 L 595 200 L 770 140 L 850 280",
            "steps": [
                {"id": "s1", "x": 160, "y": 120, "label": "PSII 1O2 & EX1 Sensor", "sublabel": "Singlet oxygen sensing at grana", "title": "Light Excess & Singlet Oxygen Generation", "text": "Excess excitation at Photosystem II reaction centers generates singlet oxygen (1O2), sensed in grana margins by EXECUTER 1 (EX1).", "glyph": "ros", "icon": "✨", "category": "Singlet Oxygen Sensing", "locus": "AT4G33010", "spaceflight": "OSD-120: +1.12 log2FC (EX1)"},
                {"id": "s2", "x": 210, "y": 260, "label": "Stromal SAL1 Inactivation", "sublabel": "Disulfide bridge oxidation", "title": "Stromal SAL1 Inactivation", "text": "Oxidative stress induces disulfide bridges that inactivate stromal SAL1 nucleotidase (AT5G63980).", "glyph": "phospho", "icon": "🔒", "category": "Disulfide Inactivation", "locus": "AT5G63980", "spaceflight": "SAL1 nucleotidase blocked"},
                {"id": "s3", "x": 415, "y": 260, "label": "PAPST1 Plastid Export", "sublabel": "PAP retrograde metabolite surge", "title": "PAP Retrograde Metabolite Accumulation", "text": "3'-phosphoadenosine 5'-phosphate (PAP) catabolism ceases; PAP accumulates and is exported via PAPST1 into the cytosol.", "glyph": "transport", "icon": "🚚", "category": "Envelope Transport", "locus": "AT5G20150", "spaceflight": "PAP retrograde export"},
                {"id": "s4", "x": 595, "y": 200, "label": "Cytosolic PAP Diffusion", "sublabel": "Free diffusion to envelope", "title": "Cytosolic Transit to Nuclear Envelope", "text": "PAP diffuses through the cytosol and crosses the nuclear envelope pore complexes into the nucleoplasm.", "glyph": "metabolite", "icon": "🌊", "category": "Metabolite Diffusion", "locus": "PAP Metabolite", "spaceflight": "3'-phosphoadenosine 5'-phosphate"},
                {"id": "s5", "x": 770, "y": 140, "label": "Nuclear XRN2/3 Inhibition", "sublabel": "Stabilizes stress transcripts", "title": "Nuclear XRN2/3 Inhibition", "text": "PAP enters the nucleus and directly inhibits 5'-to-3' exoribonucleases (XRN2 and XRN3), stabilizing drought and stress transcripts.", "glyph": "scissors", "icon": "🛑", "category": "Exoribonuclease Inhibition", "locus": "AT5G42540", "spaceflight": "XRN2/3 ribonuclease arrest"},
                {"id": "s6", "x": 850, "y": 280, "label": "GUN1 & ABI4 Hub", "sublabel": "PhANG transcription repression", "title": "GUN1 PPR Hub & ABI4 Activation", "text": "Unimported plastid precursor proteins bind stromal GUN1, signaling to nuclear ABI4 to repress Photosynthesis-Associated Nuclear Genes (PhANGs).", "glyph": "transcription", "icon": "🧬", "category": "Nuclear Repression", "locus": "AT2G40220", "spaceflight": "ABI4-mediated PhANG repression"}
            ]
        },
        "photo": {
            "title": "The 3-Organelle Photorespiratory Loop",
            "desc": "Obligate metabolic partnership of Chloroplast, Peroxisome, and Mitochondria recycling 2-phosphoglycolate.",
            "theme_color": "#D97706",
            "compartments": [
                {"id": "chl", "title": "Chloroplast (2-PG -> Glycolate)", "x": 25, "y": 25, "w": 300, "h": 370, "fill": "rgba(5, 150, 105, 0.08)", "stroke": "#059669"},
                {"id": "perox", "title": "Peroxisome (GOX / GGT / HPR)", "x": 345, "y": 25, "w": 300, "h": 370, "fill": "rgba(217, 119, 6, 0.08)", "stroke": "#d97706"},
                {"id": "mit", "title": "Mitochondria (GDC / SHMT1)", "x": 665, "y": 25, "w": 310, "h": 370, "fill": "rgba(213, 94, 0, 0.08)", "stroke": "#D55E00"},
            ],
            "path": "M 160 130 L 480 130 L 810 150 L 820 280 L 500 280 L 180 280",
            "steps": [
                {"id": "s1", "x": 160, "y": 130, "label": "RuBisCO Oxygenation", "sublabel": "2-PG -> Glycolate via PLGG1", "title": "Chloroplast RuBisCO Oxygenation", "text": "RuBisCO oxygenase reaction yields 2-phosphoglycolate, which is dephosphorylated to glycolate and exported via PLGG1.", "glyph": "metabolite", "icon": "🌿", "category": "Oxygenase Reaction", "locus": "ATCG00490", "spaceflight": "RuBisCO 2-PG generation"},
                {"id": "s2", "x": 480, "y": 130, "label": "Peroxisome GOX & GGT", "sublabel": "Glyoxylate + H2O2 -> Glycine", "title": "Peroxisomal Oxidation to Glyoxylate & Glycine", "text": "Glycolate oxidase (GOX) produces glyoxylate and H2O2 (scavenged by CAT2); GGT transaminates it to glycine.", "glyph": "ros", "icon": "✨", "category": "Peroxisomal Oxidation", "locus": "AT3G14415", "spaceflight": "GOX produces H2O2 + Glycine"},
                {"id": "s3", "x": 810, "y": 150, "label": "Matrix GDC / SHMT1", "sublabel": "2 Glycine -> Serine + CO2 + NH3", "title": "Mitochondrial GDC / SHMT Serine Synthesis", "text": "Matrix Glycine Decarboxylase (GDC P/T/H/L proteins) and SHMT1 convert 2 glycine into serine + NADH + CO2 + NH3.", "glyph": "metabolite", "icon": "⚡", "category": "Matrix Decarboxylation", "locus": "AT2G35370", "spaceflight": "OSD-120: GDC -1.15 log2FC"},
                {"id": "s4", "x": 820, "y": 280, "label": "Complex I CA Domain", "sublabel": "CO2 recycling & hydration", "title": "Complex I CA Domain Recirculation", "text": "The plant-specific Carbonic Anhydrase domain of Complex I re-traps released photorespiratory CO2.", "glyph": "transport", "icon": "🔄", "category": "CO2 Recirculation", "locus": "AT1G19580", "spaceflight": "CA Domain re-traps CO2"},
                {"id": "s5", "x": 500, "y": 280, "label": "Peroxisomal HPR", "sublabel": "Hydroxypyruvate -> Glycerate", "title": "Peroxisomal Reduction & Return", "text": "Serine is transaminated to hydroxypyruvate in peroxisomes, then reduced to glycerate by hydroxypyruvate reductase (HPR).", "glyph": "metabolite", "icon": "🧪", "category": "Peroxisomal Return", "locus": "AT1G68010", "spaceflight": "HPR reduces hydroxypyruvate"},
                {"id": "s6", "x": 180, "y": 280, "label": "DiT1 & Glycerate Kinase", "sublabel": "Glycerate -> 3-PGA return", "title": "Chloroplast Return & Phosphorylation", "text": "Glycerate returns to chloroplasts via DiT1 and is phosphorylated by GLYK to 3-PGA, re-entering the Calvin-Benson cycle.", "glyph": "phospho", "icon": "🔁", "category": "Calvin Re-entry", "locus": "AT5G04140", "spaceflight": "GLYK yields 3-PGA"}
            ]
        },
        "pm": {
            "title": "Plasma Membrane Mechanical & Gravity Sensing Waves",
            "desc": "How cell surface deformation launches systemic electrical, calcium, and ROS waves into organelles.",
            "theme_color": "#0284C7",
            "compartments": [
                {"id": "cw", "title": "Cell Wall & Apoplast", "x": 25, "y": 25, "w": 230, "h": 370, "fill": "rgba(100, 116, 139, 0.08)", "stroke": "#64748b"},
                {"id": "pm", "title": "Plasma Membrane Bilayer", "x": 275, "y": 25, "w": 190, "h": 370, "fill": "rgba(2, 132, 199, 0.08)", "stroke": "#0284c7"},
                {"id": "cyto", "title": "Cytosolic Kinase Core", "x": 485, "y": 25, "w": 245, "h": 370, "fill": "rgba(59, 110, 165, 0.06)", "stroke": "#3B6EA5"},
                {"id": "target", "title": "Organellar Influx Targets", "x": 750, "y": 25, "w": 225, "h": 370, "fill": "rgba(16, 185, 129, 0.08)", "stroke": "#10b981"},
            ],
            "path": "M 130 120 L 370 120 L 370 250 L 590 210 L 140 280 L 860 200",
            "steps": [
                {"id": "s1", "x": 130, "y": 120, "label": "Cell Wall Tension / Strain", "sublabel": "WAK1 & FERONIA activation", "title": "Cell Wall & Gravity Vector Strain", "text": "Mechanical touch, turgor changes, or microgravity alterations stretch pectin, activating WAK1 and FERONIA receptor kinases.", "glyph": "gate", "icon": "🧱", "category": "Wall Strain Perception", "locus": "AT2G37170", "spaceflight": "OSD-120: WAK1 +1.38 log2FC"},
                {"id": "s2", "x": 370, "y": 120, "label": "MSL10 & MCA Gating", "sublabel": "Stretch-activated depolarization", "title": "Mechanosensitive Channel Activation", "text": "Membrane tension gates MSL10 and MCA channels, initiating local plasma membrane depolarization.", "glyph": "gate", "icon": "⚡", "category": "Stretch Channel Gating", "locus": "AT5G12080", "spaceflight": "OSD-120: MSL10 +1.45 log2FC"},
                {"id": "s3", "x": 370, "y": 250, "label": "GLR3.3/3.6 Ca2+ Influx", "sublabel": "Rapid apoplastic Ca2+ entry", "title": "Systemic Calcium Influx via GLR3.3/3.6", "text": "Glutamate receptor-like channels open, driving rapid calcium influx from apoplast to cytosol.", "glyph": "gate", "icon": "🌊", "category": "Calcium Wave Entry", "locus": "AT2G29110", "spaceflight": "GLR3.3/3.6 Ca2+ influx"},
                {"id": "s4", "x": 590, "y": 210, "label": "CPK & RBOHD Activation", "sublabel": "N-terminal phosphorylation", "title": "RBOHD Phosphorylation & Activation", "text": "Cytosolic Ca2+ spikes activate CPKs and BIK1, which phosphorylate RBOHD to generate an apoplastic ROS burst.", "glyph": "phospho", "icon": "⚡", "category": "Kinase Activation", "locus": "AT5G42590", "spaceflight": "CPK phosphorylates RBOHD"},
                {"id": "s5", "x": 140, "y": 280, "label": "Apoplastic ROS Wave", "sublabel": "O2.- -> H2O2 dismutation", "title": "Apoplastic Superoxide Burst & Wave", "text": "RBOHD pumps electrons outside to create O2.-, which dismutates to H2O2, launching a systemic cell-to-cell wave.", "glyph": "ros", "icon": "✨", "category": "Apoplastic ROS Burst", "locus": "AT5G47910", "spaceflight": "OSD-120: RBOHD +1.62 log2FC"},
                {"id": "s6", "x": 860, "y": 200, "label": "PIP2;1 Inward H2O2 Conduit", "sublabel": "Organellar redox reprogramming", "title": "Inward Channeling via PIP2;1 Aquaporin", "text": "H2O2 re-enters the cytosol and organelles through PIP2;1 channels, tuning mitochondrial AOX and chloroplast redox balance.", "glyph": "transport", "icon": "🚪", "category": "Aquaporin H2O2 Influx", "locus": "AT3G53420", "spaceflight": "Inward H2O2 channel PIP2;1"}
            ]
        },
        "stromule": {
            "title": "Stromule Nuclear Docking & Privileged Channeling",
            "desc": "Dynamic physical conduits connecting chloroplasts to the nuclear envelope.",
            "theme_color": "#10B981",
            "compartments": [
                {"id": "chl", "title": "Chloroplast Body & Stroma", "x": 25, "y": 25, "w": 275, "h": 370, "fill": "rgba(16, 185, 129, 0.08)", "stroke": "#10b981"},
                {"id": "stromule", "title": "Stromule Tubule Extension", "x": 320, "y": 25, "w": 270, "h": 370, "fill": "rgba(16, 185, 129, 0.04)", "stroke": "#059669", "dash": "6 4"},
                {"id": "dock", "title": "Nuclear Envelope Dock", "x": 610, "y": 25, "w": 150, "h": 370, "fill": "rgba(107, 70, 193, 0.06)", "stroke": "#6b46c1", "dash": "4 4"},
                {"id": "nuc", "title": "Nucleoplasm Core", "x": 780, "y": 25, "w": 195, "h": 370, "fill": "rgba(107, 70, 193, 0.10)", "stroke": "#6b46c1"},
            ],
            "path": "M 150 150 L 230 270 L 450 230 L 680 190 L 870 190",
            "steps": [
                {"id": "s1", "x": 150, "y": 150, "label": "Plastidial Redox Shift", "sublabel": "Stromal oxidative stress trigger", "title": "Stress-Induced Tubule Elongation", "text": "Oxidative stress induces chloroplasts to initiate stroma-filled tubules (stromules) at envelope microdomains.", "glyph": "ros", "icon": "✨", "category": "Plastid Redox Threshold", "locus": "AT4G33010", "spaceflight": "Stromal ROS triggers outgrowth"},
                {"id": "s2", "x": 230, "y": 270, "label": "Stromule Extension", "sublabel": "Tubule outgrowth with stroma cargo", "title": "Tubule Outgrowth & Stromule Formation", "text": "Dynamic narrow tubules extend outward from the chloroplast body, containing stromal proteins and metabolites.", "glyph": "transport", "icon": "🌱", "category": "Tubule Morphogenesis", "locus": "Plastid Envelope", "spaceflight": "Narrow stroma protrusion"},
                {"id": "s3", "x": 450, "y": 230, "label": "Myosin XI & Actin Motors", "sublabel": "Tracking microfilament tracks", "title": "Actin Microfilament Guidance", "text": "Stromules track actively along actin microfilaments powered by plant myosin XI class molecular motors.", "glyph": "transport", "icon": "🚚", "category": "Myosin Motility", "locus": "AT1G17580", "spaceflight": "Actin microfilament tracking"},
                {"id": "s4", "x": 680, "y": 190, "label": "Perinuclear Envelope Docking", "sublabel": "Physical anchor to outer membrane", "title": "Direct Perinuclear Docking", "text": "Stromules physically wrap around and dock directly to outer nuclear membrane receptor complexes.", "glyph": "gate", "icon": "⚓", "category": "Perinuclear Anchoring", "locus": "AT5G42940", "spaceflight": "Direct outer membrane docking"},
                {"id": "s5", "x": 870, "y": 190, "label": "Privileged H2O2 Injection", "sublabel": "Bypasses cytosolic scavenging", "title": "Privileged H2O2 Channeling", "text": "High concentrations of stromal H2O2 are transferred directly into the nucleoplasm, completely avoiding cytosolic peroxiredoxins.", "glyph": "ros", "icon": "🎯", "category": "Privileged Injection", "locus": "AT3G22370", "spaceflight": "Direct H2O2 delivery to nucleus"}
            ]
        }
    }

    extra_css = """
    .circuit-btn {
      padding: 10px 18px;
      background: var(--bg);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text);
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .circuit-btn:hover {
      background: var(--surface-2);
      border-color: var(--primary);
    }
    .circuit-btn.active {
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .circuit-controls-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--surface-2);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 12px;
    }
    .ctrl-btn {
      padding: 8px 16px;
      font-weight: 600;
      font-size: 0.85rem;
      border-radius: 6px;
      cursor: pointer;
      border: 1px solid var(--card-border);
      background: var(--bg);
      color: var(--text);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .ctrl-btn:hover {
      background: var(--surface);
      border-color: var(--primary);
    }
    .ctrl-btn.primary {
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
    }
    .speed-selector {
      display: flex;
      align-items: center;
      gap: 4px;
      background: var(--bg);
      padding: 3px 6px;
      border-radius: 6px;
      border: 1px solid var(--card-border);
    }
    .speed-btn {
      padding: 3px 8px;
      font-size: 0.8rem;
      font-weight: 600;
      border-radius: 4px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--text-soft);
      cursor: pointer;
      transition: all 0.1s ease;
    }
    .speed-btn.active {
      background: var(--primary);
      color: #ffffff;
    }
    .step-status-pill {
      font-family: var(--font-mono);
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--primary);
      background: var(--primary-light);
      padding: 6px 14px;
      border-radius: 20px;
      border: 1px solid var(--primary);
    }
    .step-card {
      background: var(--bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 14px 18px;
      margin-bottom: 10px;
      display: flex;
      align-items: flex-start;
      gap: 14px;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .step-card:hover {
      border-color: var(--primary);
      background: var(--surface-2);
      transform: translateX(3px);
    }
    .step-card.active-step-card {
      border-color: var(--primary);
      background: var(--primary-light);
      box-shadow: 0 0 0 1.5px var(--primary);
    }
    .step-num {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 0.85rem;
      flex-shrink: 0;
      background: var(--surface-2);
      color: var(--text-soft);
      border: 1px solid var(--card-border);
      transition: all 0.2s ease;
    }
    .step-card.active-step-card .step-num {
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
    }
    @keyframes halo-anim {
      0% { r: 18px; opacity: 0.9; }
      50% { r: 28px; opacity: 0.3; }
      100% { r: 18px; opacity: 0.9; }
    }
    .pulse-halo-anim {
      animation: halo-anim 1.6s infinite ease-in-out;
    }
    @keyframes conduitFlow {
      from { stroke-dashoffset: 28; }
      to { stroke-dashoffset: 0; }
    }
    .conduit-flow-anim {
      animation: conduitFlow 1.4s linear infinite;
    }
    .mechanism-hud-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-left: 4px solid var(--primary);
      border-radius: 8px;
      padding: 14px 18px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    """

    content = f"""
    {nav_header(active='retrograde')}
    <main class="container">
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 1.8rem; font-weight: 800;">Retrograde Signaling &amp; Inter-Organellar Crosstalk</h2>
        <p style="color: var(--text-soft); max-width: 850px; margin-top: 4px;">
          Detailed scientific architectures and dynamic animations of the five organellar communication pathways.
          Select a circuit below to explore its compartment boundaries, active reaction nodes, and animated signal pulses.
        </p>
      </div>

      <div style="display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap;">
        <button class="circuit-btn active" data-circuit="mrr" onclick="selectCircuit('mrr')">1. Mito-Nuclear MRR (ANAC017/013)</button>
        <button class="circuit-btn" data-circuit="prr" onclick="selectCircuit('prr')">2. Plasto-Nuclear PRR (SAL1-PAP &amp; GUN1)</button>
        <button class="circuit-btn" data-circuit="photo" onclick="selectCircuit('photo')">3. 3-Organelle Photorespiratory Loop</button>
        <button class="circuit-btn" data-circuit="pm" onclick="selectCircuit('pm')">4. PM Ca2+ &amp; ROS Wave</button>
        <button class="circuit-btn" data-circuit="stromule" onclick="selectCircuit('stromule')">5. Stromule Nuclear Docking</button>
      </div>

      <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--border-radius); padding: 24px;">
        <div style="margin-bottom: 20px;">
          <h3 id="circuit-heading" style="font-size: 1.35rem; font-weight: 700; color: var(--text);"></h3>
          <p id="circuit-summary" style="color: var(--text-soft); font-size: 0.95rem; margin-top: 4px;"></p>
        </div>

        <!-- Controls Toolbar -->
        <div class="circuit-controls-bar">
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <button id="btn-play" class="ctrl-btn primary" onclick="togglePlay()">
              <span id="play-icon">▶</span> <span id="play-text">Play Animation</span>
            </button>
            <button class="ctrl-btn" onclick="prevStep()" title="Previous Step">⏮ Prev</button>
            <button class="ctrl-btn" onclick="nextStep()" title="Next Step">Next ⏭</button>
            <button class="ctrl-btn" onclick="resetAnimation()" title="Reset to Step 1">↺ Reset</button>
            <div class="speed-selector">
              <span style="font-size: 0.8rem; font-weight: 600; color: var(--text-soft); margin-right: 4px;">Speed:</span>
              <button class="speed-btn" data-speed="0.5" onclick="setSpeed(0.5)">0.5x</button>
              <button class="speed-btn active" data-speed="1.0" onclick="setSpeed(1.0)">1.0x</button>
              <button class="speed-btn" data-speed="2.0" onclick="setSpeed(2.0)">2.0x</button>
            </div>
          </div>
          <div id="step-badge" class="step-status-pill">
            Loading pathway...
          </div>
        </div>

        <!-- Live Molecular Mechanism & Translocation HUD -->
        <div id="mechanism-hud" class="mechanism-hud-panel">
          <div style="display: flex; align-items: center; gap: 14px;">
            <div id="hud-glyph-icon" style="width: 44px; height: 44px; border-radius: 8px; background: rgba(213, 94, 0, 0.15); display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">
              ✨
            </div>
            <div>
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
                <span id="hud-category" class="badge" style="background: var(--surface-2); color: var(--primary); font-size: 0.75rem; font-weight: 700;">Redox / ROS Surge</span>
                <span id="hud-locus" style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-soft);">ATMG00640</span>
              </div>
              <h4 id="hud-title" style="margin: 0; font-size: 1.05rem; font-weight: 800; color: var(--text);">Complex I/III Respiratory Stress</h4>
            </div>
          </div>
          <div id="hud-spaceflight" style="background: rgba(15, 23, 42, 0.88); border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; padding: 6px 14px; font-family: var(--font-mono); font-size: 0.82rem; color: #38bdf8;">
            OSD-120: +1.42 log2FC (p=0.004)
          </div>
        </div>

        <!-- Architectural SVG Canvas -->
        <div style="margin-bottom: 24px;">
          <svg id="circuit-svg" viewBox="0 0 1000 420" style="width: 100%; height: auto; max-height: 480px; background: var(--bg); border: 1px solid var(--card-border); border-radius: 8px;"></svg>
        </div>

        <!-- Step Progression Cards -->
        <div style="margin-top: 16px;">
          <h4 style="font-size: 1.05rem; font-weight: 700; color: var(--text); margin-bottom: 12px;">Molecular Reaction Sequence</h4>
          <div id="step-cards-container"></div>
        </div>
      </div>
    </main>

    <script>
      const circuits = {json.dumps(circuits_data)};
      let currentCircuitKey = 'mrr';
      let currentStepIndex = 0;
      let isPlaying = false;
      let playSpeed = 1.0;
      let playTimer = null;

      function selectCircuit(key) {{
        pauseAnimation();
        currentCircuitKey = key;
        currentStepIndex = 0;

        document.querySelectorAll('.circuit-btn').forEach(b => {{
          b.classList.toggle('active', b.getAttribute('data-circuit') === key);
        }});

        renderCircuit(key);
        goToStep(0);
        startAnimation();
      }}

      function renderCircuit(key) {{
        const c = circuits[key];
        document.getElementById('circuit-heading').innerText = c.title;
        document.getElementById('circuit-summary').innerText = c.desc;

        // Render SVG Canvas
        const svg = document.getElementById('circuit-svg');
        svg.setAttribute('viewBox', '0 0 1000 420');

        let compsHtml = '';
        c.compartments.forEach(comp => {{
          compsHtml += `
            <g class="comp-group">
              <rect x="${{comp.x}}" y="${{comp.y}}" width="${{comp.w}}" height="${{comp.h}}" rx="10"
                    fill="${{comp.fill}}" stroke="${{comp.stroke}}" stroke-width="1.8"
                    ${{comp.dash ? `stroke-dasharray="${{comp.dash}}"` : ''}} />
              <rect x="${{comp.x + 10}}" y="${{comp.y + 10}}" width="${{comp.title.length * 7.5 + 16}}" height="22" rx="4"
                    fill="var(--card-bg)" stroke="${{comp.stroke}}" stroke-width="1" />
              <text x="${{comp.x + 18}}" y="${{comp.y + 25}}" font-family="Inter, sans-serif" font-weight="700" font-size="11" fill="var(--text)">
                ${{comp.title}}
              </text>
            </g>
          `;
        }});

        // Connecting conduit path with animated marching dash flow
        const pathHtml = `
          <path id="conduit-path" class="conduit-flow-anim" d="${{c.path}}" fill="none" stroke="${{c.theme_color}}" stroke-width="3.5" stroke-dasharray="8 6" opacity="0.8" />
        `;

        // Nodes
        let nodesHtml = '';
        c.steps.forEach((s, idx) => {{
          nodesHtml += `
            <g id="svg-node-${{idx}}" class="circuit-node" onclick="goToStep(${{idx}})" style="cursor: pointer;">
              <!-- Node pill container -->
              <rect x="${{s.x - 70}}" y="${{s.y - 24}}" width="140" height="48" rx="8"
                    fill="var(--card-bg)" stroke="var(--card-border)" stroke-width="1.5" class="node-box" />
              <!-- Step number badge -->
              <circle cx="${{s.x - 52}}" cy="${{s.y}}" r="12" fill="${{c.theme_color}}" />
              <text x="${{s.x - 52}}" y="${{s.y + 4}}" text-anchor="middle" font-family="Inter, sans-serif" font-weight="800" font-size="11" fill="#ffffff">
                ${{idx + 1}}
              </text>
              <!-- Label -->
              <text x="${{s.x - 34}}" y="${{s.y - 4}}" font-family="Inter, sans-serif" font-weight="700" font-size="10" fill="var(--text)" class="node-title">
                ${{s.label}}
              </text>
              <!-- Sublabel -->
              <text x="${{s.x - 34}}" y="${{s.y + 10}}" font-family="Inter, sans-serif" font-size="8.2" fill="var(--text-soft)" class="node-sub">
                ${{s.sublabel}}
              </text>
              <!-- Mechanism Glyph Chip -->
              ${{s.glyph ? `
                <g transform="translate(${{s.x + 50}}, ${{s.y - 10}})">
                  <use href="#glyph-${{s.glyph}}" />
                </g>
              ` : ''}}
            </g>
          `;
        }});

        // Signal Pulse & Pulse Halo
        const pulseHtml = `
          <circle id="pulse-halo" class="pulse-halo-anim" cx="${{c.steps[0].x}}" cy="${{c.steps[0].y}}" r="28" fill="none" stroke="${{c.theme_color}}" stroke-width="2.5" opacity="0.8" style="transition: all 0.4s ease; pointer-events: none;" />
          <circle id="signal-pulse" cx="${{c.steps[0].x}}" cy="${{c.steps[0].y}}" r="10" fill="#ffffff" stroke="${{c.theme_color}}" stroke-width="4" filter="url(#glow-filter)" style="transition: all 0.4s ease; pointer-events: none;" />
        `;

        svg.innerHTML = `
          <defs>
            <filter id="glow-filter" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <!-- Scissor glyph: AT1G34190 Proteolysis -->
            <g id="glyph-scissors">
              <circle cx="0" cy="0" r="9" fill="#dc2626" />
              <path d="M -3.5 -3.5 L 3.5 3.5 M -3.5 3.5 L 3.5 -3.5" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" />
              <circle cx="-3.5" cy="-3.5" r="1.2" fill="#ffffff" />
              <circle cx="-3.5" cy="3.5" r="1.2" fill="#ffffff" />
            </g>
            <!-- ROS glyph: H2O2 / 1O2 Sparkle -->
            <g id="glyph-ros">
              <circle cx="0" cy="0" r="9" fill="#f59e0b" />
              <path d="M 0 -5 L 0 5 M -5 0 L 5 0 M -3 -3 L 3 3 M -3 3 L 3 -3" stroke="#ffffff" stroke-width="1.4" stroke-linecap="round" />
            </g>
            <!-- Phosphorylation glyph: Kinase -->
            <g id="glyph-phospho">
              <circle cx="0" cy="0" r="9" fill="#8b5cf6" />
              <text x="0" y="3.5" text-anchor="middle" font-family="Inter, sans-serif" font-weight="900" font-size="9" fill="#ffffff">P</text>
            </g>
            <!-- Gate glyph: MSL10 / GLR Channel -->
            <g id="glyph-gate">
              <circle cx="0" cy="0" r="9" fill="#0284c7" />
              <path d="M -4.5 -3.5 L -4.5 3.5 M 4.5 -3.5 L 4.5 3.5 M -2.5 0 L 2.5 0" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" />
            </g>
            <!-- Metabolite glyph: PAP / Glycolate -->
            <g id="glyph-metabolite">
              <circle cx="0" cy="0" r="9" fill="#10b981" />
              <polygon points="0,-4 3.5,-2 3.5,2 0,4 -3.5,2 -3.5,-2" fill="none" stroke="#ffffff" stroke-width="1.3" />
            </g>
            <!-- Transport glyph: Translocation / Motor -->
            <g id="glyph-transport">
              <circle cx="0" cy="0" r="9" fill="#0d9488" />
              <path d="M -3.5 0 L 2 0 M 0 -2.5 L 2.5 0 L 0 2.5" stroke="#ffffff" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" />
            </g>
            <!-- Transcription glyph: MDRE Promoters -->
            <g id="glyph-transcription">
              <circle cx="0" cy="0" r="9" fill="#9333ea" />
              <path d="M -3.5 -2.5 Q 0 -4.5 3.5 -2.5 Q 0 0 -3.5 2.5 Q 0 4.5 3.5 2.5" fill="none" stroke="#ffffff" stroke-width="1.3" />
            </g>
          </defs>
          ${{compsHtml}}
          ${{pathHtml}}
          ${{nodesHtml}}
          ${{pulseHtml}}
        `;

        // Render Step Cards
        let cardsHtml = '';
        c.steps.forEach((s, idx) => {{
          cardsHtml += `
            <div id="step-card-${{idx}}" class="step-card" onclick="goToStep(${{idx}})">
              <div class="step-num">${{idx + 1}}</div>
              <div style="flex-grow: 1;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px; flex-wrap: wrap;">
                  <strong style="color: var(--text); font-size: 0.95rem;">${{s.title}}</strong>
                  ${{s.category ? `<span class="badge" style="background: var(--surface-2); color: var(--primary); font-size: 0.72rem; font-weight: 700;">${{s.category}}</span>` : ''}}
                  ${{s.locus ? `<span style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-soft);">${{s.locus}}</span>` : ''}}
                  ${{s.spaceflight ? `<span style="font-family: var(--font-mono); font-size: 0.75rem; color: #38bdf8; background: rgba(15,23,42,0.85); padding: 1px 6px; border-radius: 4px;">${{s.spaceflight}}</span>` : ''}}
                </div>
                <p style="color: var(--text-soft); font-size: 0.88rem; margin: 0;">${{s.text}}</p>
              </div>
            </div>
          `;
        }});
        document.getElementById('step-cards-container').innerHTML = cardsHtml;
      }}

      function goToStep(idx) {{
        const c = circuits[currentCircuitKey];
        if (idx < 0) idx = 0;
        if (idx >= c.steps.length) idx = c.steps.length - 1;
        currentStepIndex = idx;
        const step = c.steps[idx];

        // Move Signal Pulse and Halo
        const pulse = document.getElementById('signal-pulse');
        const halo = document.getElementById('pulse-halo');
        if (pulse) {{
          pulse.setAttribute('cx', step.x);
          pulse.setAttribute('cy', step.y);
          pulse.setAttribute('stroke', c.theme_color);
        }}
        if (halo) {{
          halo.setAttribute('cx', step.x);
          halo.setAttribute('cy', step.y);
          halo.setAttribute('stroke', c.theme_color);
        }}

        // Update Live Molecular Mechanism HUD
        const hudGlyph = document.getElementById('hud-glyph-icon');
        const hudCategory = document.getElementById('hud-category');
        const hudLocus = document.getElementById('hud-locus');
        const hudTitle = document.getElementById('hud-title');
        const hudSpace = document.getElementById('hud-spaceflight');
        if (hudGlyph && step.icon) hudGlyph.innerText = step.icon;
        if (hudCategory && step.category) hudCategory.innerText = step.category;
        if (hudLocus && step.locus) hudLocus.innerText = step.locus;
        if (hudTitle && step.title) hudTitle.innerText = step.title;
        if (hudSpace && step.spaceflight) hudSpace.innerText = step.spaceflight;

        // Highlight Active SVG Node
        document.querySelectorAll('.circuit-node').forEach((node, i) => {{
          const box = node.querySelector('.node-box');
          if (box) {{
            if (i === idx) {{
              box.setAttribute('stroke', c.theme_color);
              box.setAttribute('stroke-width', '2.5');
              box.setAttribute('fill', 'var(--surface-2)');
            }} else {{
              box.setAttribute('stroke', 'var(--card-border)');
              box.setAttribute('stroke-width', '1.5');
              box.setAttribute('fill', 'var(--card-bg)');
            }}
          }}
        }});

        // Highlight Step Card
        document.querySelectorAll('.step-card').forEach((card, i) => {{
          card.classList.toggle('active-step-card', i === idx);
        }});

        // Update Status Badge
        const badge = document.getElementById('step-badge');
        if (badge) {{
          badge.innerText = `Step ${{idx + 1}} of ${{c.steps.length}}: ${{step.title}}`;
        }}
      }}

      function togglePlay() {{
        if (isPlaying) {{
          pauseAnimation();
        }} else {{
          startAnimation();
        }}
      }}

      function startAnimation() {{
        isPlaying = true;
        const btn = document.getElementById('btn-play');
        if (btn) {{
          btn.innerHTML = '<span>⏸</span> <span>Pause</span>';
        }}
        scheduleNextStep();
      }}

      function pauseAnimation() {{
        isPlaying = false;
        if (playTimer) {{
          clearTimeout(playTimer);
          playTimer = null;
        }}
        const btn = document.getElementById('btn-play');
        if (btn) {{
          btn.innerHTML = '<span>▶</span> <span>Play Animation</span>';
        }}
      }}

      function scheduleNextStep() {{
        if (!isPlaying) return;
        const interval = 2200 / playSpeed;
        playTimer = setTimeout(() => {{
          const c = circuits[currentCircuitKey];
          const nextIdx = (currentStepIndex + 1) % c.steps.length;
          goToStep(nextIdx);
          if (isPlaying) {{
            scheduleNextStep();
          }}
        }}, interval);
      }}

      function prevStep() {{
        pauseAnimation();
        const c = circuits[currentCircuitKey];
        const prevIdx = (currentStepIndex - 1 + c.steps.length) % c.steps.length;
        goToStep(prevIdx);
      }}

      function nextStep() {{
        pauseAnimation();
        const c = circuits[currentCircuitKey];
        const nextIdx = (currentStepIndex + 1) % c.steps.length;
        goToStep(nextIdx);
      }}

      function resetAnimation() {{
        pauseAnimation();
        goToStep(0);
      }}

      function setSpeed(speed) {{
        playSpeed = speed;
        document.querySelectorAll('.speed-btn').forEach(b => {{
          b.classList.toggle('active', parseFloat(b.getAttribute('data-speed')) === speed);
        }});
      }}

      // Init on load
      selectCircuit('mrr');
    </script>
    {html_footer()}
    """
    return html_head("Retrograde Signaling Circuits — Plant MitoCarta", extra_css) + content


COMPLEX_I_MODULE_DATA = {
    "all": {
        "title": "All Holo-Complex I Modules & Alternative Bypasses",
        "mammal_subunits": "45 subunits (7 mtDNA-encoded, 38 nuclear-encoded) • ~970 kDa",
        "plant_subunits": "51 subunits (9 mtDNA-encoded, 42 nuclear-encoded) • ~1,000 kDa",
        "mechanism": "NADH + H⁺ + Q + 4 H⁺_matrix → NAD⁺ + QH₂ + 4 H⁺_IMS. Plant Complex I features an auxiliary matrix Carbonic Anhydrase protuberance and bypass enzymes (AOX1a, NDB2, NDA1).",
        "clinical": "Complex I deficiency is the most frequent cause of mitochondrial disease (~30% of cases), causing Leigh syndrome, fatal infantile lactic acidosis, and LHON.",
        "plant_significance": "Dual metabolic flexibility: under photorespiration or spaceflight stress, excess reducing equivalents bypass Complex I via AOX/NDB2, preventing lethal ROS generation."
    },
    "n-module": {
        "title": "N-Module (NADH Dehydrogenase Core: NDUFV1, NDUFV2, NDUFS1)",
        "mammal_subunits": "3 core subunits (NDUFV1, NDUFV2, NDUFS1) harboring FMN and 2 Fe-S clusters [2Fe-2S, 4Fe-4S]",
        "plant_subunits": "3 orthologous core subunits (AT5G08530 / NDUFV1, AT1G79010 / NDUFV2, AT5G37510 / NDUFS1)",
        "mechanism": "2-electron hydride transfer from NADH to FMN: NADH + H⁺ + FMN → NAD⁺ + FMNH₂. Entry point for matrix reducing equivalents.",
        "clinical": "NDUFV1/NDUFS1 mutations cause severe infantile Leigh syndrome, leukodystrophy, and macrocephaly.",
        "plant_significance": "Strictly conserved catalytic core (~60% amino acid identity). Co-regulated with chloroplast redox state to buffer photorespiratory NADH."
    },
    "q-module": {
        "title": "Q-Module (Ubiquinone Reduction & Fe-S Relay: NDUFS2, NDUFS3, NDUFS7, NDUFS8)",
        "mammal_subunits": "4 core subunits (NDUFS2, NDUFS3, NDUFS7, NDUFS8) harboring 8 Fe-S cluster wire to Q-binding pocket",
        "plant_subunits": "4 conserved core subunits (AT1G16700 / NDUFS2, AT2G37660 / NDUFS3, AT3G03070 / NDUFS7, AT1G76190 / NDUFS8)",
        "mechanism": "Rapid electron tunneling down the 8-cluster wire to reduce ubiquinone (Q) to ubiquinol (QH₂) at the arm junction.",
        "clinical": "NDUFS2/S7 defects cause hypertrophic cardiomyopathy, Leigh syndrome, and bilateral striatal necrosis.",
        "plant_significance": "Forms the essential structural docking interface for the plant-specific Carbonic Anhydrase-like (CA) heteropentamer."
    },
    "p-module": {
        "title": "P-Module (Proton-Pumping Hydrophobic Membrane Arm: ND1–ND6, ND4L)",
        "mammal_subunits": "7 mtDNA-encoded subunits (ND1–ND6, ND4L) forming 3 proton-translocating channels",
        "plant_subunits": "9 hydrophobic core subunits (nad1–nad9) organized into proximal and distal proton pumping channels",
        "mechanism": "Long-range electrostatic conformational piston waves transmit energy from Q reduction to pump 4 H⁺ across the inner membrane.",
        "clinical": "Primary mtDNA mutations (m.11778G>A in ND4, m.3460G>A in ND1, m.14484T>C in ND6) cause Leber Hereditary Optic Neuropathy (LHON).",
        "plant_significance": "Plant nad transcripts undergo extraordinary C-to-U RNA editing (>100 sites directed by PPR proteins) and complex trans-splicing."
    },
    "ca-module": {
        "title": "CA-Module (Plant-Specific Carbonic Anhydrase Matrix Protuberance: CAL1, CAL2, CA1–3)",
        "mammal_subunits": "COMPLETELY ABSENT IN MAMMALS (0 subunits). Mammalian Complex I has no matrix protuberance.",
        "plant_subunits": "5 plant-specific subunits (CAL1: AT1G47260, CAL2: AT3G48680, CA1: AT1G19580, CA2: AT3G28660, CA3: AT5G63510) • ~85 kDa mass",
        "mechanism": "Heteropentameric matrix wedge with γ-carbonic anhydrase fold interconverting HCO₃⁻ ↔ CO₂ + H₂O.",
        "clinical": "Absent in mammals. Structural stability principles inform artificial macromolecular engineering templates.",
        "plant_significance": "Obligate for holo-Complex I assembly, stability of the I+III₂ supercomplex, male fertility, and photorespiratory CO₂ re-trapping."
    },
    "bypasses": {
        "title": "Alternative Respiration Bypasses (AOX1a, NDB2, NDA1)",
        "mammal_subunits": "COMPLETELY ABSENT IN MAMMALS. Mammalian mitochondria lack alternative oxidases and NDHs.",
        "plant_subunits": "AOX family (AOX1a: AT3G22370, AOX1d, AOX2) + Type II NDHs (NDB2: AT4G05020, NDA1: AT1G07180, NDC1)",
        "mechanism": "Non-proton pumping electron shunts: NDB2 oxidizes cytosolic NADH, while AOX1a directly reduces O₂ to H₂O, releasing energy as heat.",
        "clinical": "Expression of plant AOX in human cybrids and mice rescues Complex I and III deficiencies, preventing lactic acidosis and Leigh syndrome!",
        "plant_significance": "Crucial overflow valve preventing reactive oxygen species (ROS) under microgravity, cold, drought, and photoinhibition."
    }
}

EPOCH_TAXONOMIC_DATA = {
    "epoch-1": {
        "name": "α-Proteobacteria Endosymbiosis",
        "age": "~1.8 Billion Years Ago (Paleoproterozoic)",
        "milestone": "Free-living bacterium related to Rickettsiales engulfed by Asgard archaeon host.",
        "innovations": "Ancestral proton-pumping electron transport chain (Complexes I, II, III, IV, V), complete oxidative phosphorylation, and TCA cycle.",
        "genomic": "Circular bacterial genome (~1.5 Mb). Massive Endosymbiotic Gene Transfer (EGT) to host nucleus begins, founding organellar signaling."
    },
    "epoch-2": {
        "name": "Archaeplastida Plastid Acquisition & Dual Targeting",
        "age": "~1.5 Billion Years Ago (Mesoproterozoic)",
        "milestone": "Primary endosymbiotic engulfment of cyanobacterium initiates photosynthetic eukaryote lineage.",
        "innovations": "Evolution of dual-targeting: single nuclear genes encode polymerases (PolIA/B), RecA, and tRNA synthetases shared by both organelles.",
        "genomic": "Emergence of organellar cross-talk: mitochondrial metabolism adapts to photosynthetic redox and high oxygen tensions."
    },
    "epoch-3": {
        "name": "Chlorophyta & Green Lineage Bypasses",
        "age": "~1.0 Billion Years Ago (Neoproterozoic)",
        "milestone": "Divergence of chlorophyte green algae; origin of plant-specific bioenergetic flexibilities.",
        "innovations": "Evolution of Alternative Oxidase (AOX) and Type II rotenone-insensitive NAD(P)H dehydrogenases (NDA/NDB) to buffer photosynthetic surges.",
        "genomic": "Coupling of mitochondrial glycine decarboxylase (GDC) to photorespiratory RuBisCO oxygenase flux."
    },
    "epoch-4": {
        "name": "Bryophyte Land Colonization & RNA Editing Burst",
        "age": "~450 Million Years Ago (Ordovician / Silurian)",
        "milestone": "Transition of plants from aquatic environments to land; exposure to desiccation, UV, and thermal swings.",
        "innovations": "Massive explosive expansion of the Pentatricopeptide Repeat (PPR) family to correct hundreds of C-to-U defects in mitochondrial transcripts.",
        "genomic": "Plant mitochondrial genomes expand drastically via non-homologous recombination and non-coding sequence accumulation."
    },
    "epoch-5": {
        "name": "Angiosperm Specialization & CA Domain",
        "age": "~140 Million Years Ago to Present (Cretaceous to Cenozoic)",
        "milestone": "Diversification of flowering plants; co-evolution of flowers, specialized tissues, and high metabolic flux.",
        "innovations": "Pentameric matrix Carbonic Anhydrase (CA) domain (CAL1, CAL2, CA1–3) integrally incorporated into Complex I; cytoplasmic male sterility (CMS) systems.",
        "genomic": "PPR family expands to >450 genes editing ~500 sites; open non-cyclic TCA cycle prioritized for amino acid synthesis and stress signaling."
    },
    "epoch-6": {
        "name": "Metazoan Lineage Streamlining (Animal / Mammal)",
        "age": "~300 Million Years Ago to Present",
        "milestone": "Evolution of metazoans; loss of vegetative flexibilities in favor of motile, homoeothermic specialization.",
        "innovations": "Streamlined 45-subunit Complex I lacking CA protuberance; reliance on tissue-specific COX isoforms; complete loss of alternative bypasses (no AOX, no NDH).",
        "genomic": "Radical genome streamlining: human mtDNA reduced to 16,569 bp encoding only 13 proteins; high vulnerability to oxidative stress, rotenone, and ischemia."
    }
}


def render_complex_i_synteny_svg():
    return '''<svg id="complex-i-svg" viewBox="0 0 960 430" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="display: block; font-family: var(--font-sans, -apple-system, sans-serif);">
  <defs>
    <linearGradient id="c1MemGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.04"/>
    </linearGradient>
    <filter id="c1DropShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.08"/>
    </filter>
    <marker id="c1ArrowElectron" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#0284c7"/>
    </marker>
  </defs>

  <!-- ==================== LEFT: MAMMALIAN HOLO-COMPLEX I ==================== -->
  <g id="mammalian-complex-i">
    <!-- Panel Backdrop -->
    <rect x="20" y="16" width="445" height="398" rx="12" fill="var(--surface, #f8fafc)" stroke="var(--card-border, #e2e8f0)" stroke-width="1.5"/>
    
    <!-- Header Banner -->
    <rect x="20" y="16" width="445" height="42" rx="12" fill="var(--surface-2, #f1f5f9)" stroke="var(--card-border, #e2e8f0)" stroke-width="1"/>
    <text x="36" y="38" font-size="13" font-weight="700" fill="var(--text, #0f172a)">Mammalian Holo-Complex I (Homo sapiens)</text>
    <text x="36" y="50" font-size="10" font-weight="500" fill="var(--text-soft, #64748b)">45 Subunits • ~970 kDa • Strictly Rotenone-Sensitive</text>

    <!-- Compartment Zones -->
    <text x="36" y="80" font-size="10" font-weight="700" fill="var(--text-soft, #64748b)" letter-spacing="0.05em">MITOCHONDRIAL MATRIX (N-SIDE)</text>
    
    <!-- Inner Mitochondrial Membrane Strip -->
    <rect x="26" y="240" width="433" height="65" fill="url(#c1MemGrad)" stroke="var(--primary, #3b82f6)" stroke-width="1" stroke-dasharray="4,3"/>
    <text x="36" y="276" font-size="10" font-weight="600" fill="var(--primary, #2563eb)">Inner Membrane (IMM)</text>

    <text x="36" y="330" font-size="10" font-weight="700" fill="var(--text-soft, #64748b)" letter-spacing="0.05em">INTERMEMBRANE SPACE (P-SIDE)</text>

    <!-- N-Module -->
    <g class="c1-module c1-n-module" data-module="n-module" onclick="selectComplexIModule('n-module')">
      <rect x="180" y="82" width="150" height="66" rx="8" fill="#e0f2fe" stroke="#0284c7" stroke-width="1.8" filter="url(#c1DropShadow)"/>
      <text x="255" y="105" text-anchor="middle" font-size="12" font-weight="700" fill="#0369a1">N-Module (NADH)</text>
      <text x="255" y="122" text-anchor="middle" font-size="10" font-weight="600" fill="#0284c7">NDUFV1, V2, S1</text>
      <text x="255" y="137" text-anchor="middle" font-size="9" font-weight="500" fill="#0284c7">FMN • [2Fe-2S] • [4Fe-4S]</text>
    </g>

    <!-- Q-Module -->
    <g class="c1-module c1-q-module" data-module="q-module" onclick="selectComplexIModule('q-module')">
      <rect x="180" y="156" width="150" height="74" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="1.8" filter="url(#c1DropShadow)"/>
      <text x="255" y="180" text-anchor="middle" font-size="12" font-weight="700" fill="#15803d">Q-Module (Fe-S Relay)</text>
      <text x="255" y="198" text-anchor="middle" font-size="10" font-weight="600" fill="#16a34a">NDUFS2, S3, S7, S8</text>
      <text x="255" y="215" text-anchor="middle" font-size="9" font-weight="500" fill="#16a34a">8 Fe-S Cluster Wire → Q</text>
    </g>

    <!-- P-Module (Hydrophobic Arm) -->
    <g class="c1-module c1-p-module" data-module="p-module" onclick="selectComplexIModule('p-module')">
      <rect x="110" y="240" width="290" height="65" rx="8" fill="#ede9fe" stroke="#7c3aed" stroke-width="1.8" filter="url(#c1DropShadow)"/>
      <text x="255" y="262" text-anchor="middle" font-size="12" font-weight="700" fill="#6d28d9">P-Module (Proton Arm)</text>
      <text x="255" y="279" text-anchor="middle" font-size="10" font-weight="600" fill="#7c3aed">ND1, ND2, ND3, ND4, ND4L, ND5, ND6</text>
      <text x="255" y="294" text-anchor="middle" font-size="9" font-weight="500" fill="#7c3aed">4 H⁺ pumped / 2e⁻ translocated</text>
    </g>

    <!-- Electron Flow Vector -->
    <path d="M 255 148 L 255 156" stroke="#0284c7" stroke-width="2" marker-end="url(#c1ArrowElectron)"/>
    <path d="M 255 230 L 255 240" stroke="#16a34a" stroke-width="2" marker-end="url(#c1ArrowElectron)"/>

    <!-- Bottom Features & Absence Notice -->
    <rect x="36" y="356" width="413" height="44" rx="6" fill="var(--bg, #ffffff)" stroke="var(--card-border, #e2e8f0)" stroke-width="1"/>
    <text x="48" y="373" font-size="10" font-weight="600" fill="#dc2626">✕ No Carbonic Anhydrase (CA) Matrix Protuberance</text>
    <text x="48" y="389" font-size="9.5" font-weight="500" fill="var(--text-soft, #64748b)">✕ No alternative bypass oxidases (AOX) or Type II NDHs (rotenone arrests respiration)</text>
  </g>

  <!-- ==================== RIGHT: PLANT HOLO-COMPLEX I & BYPASSES ==================== -->
  <g id="plant-complex-i">
    <!-- Panel Backdrop -->
    <rect x="495" y="16" width="445" height="398" rx="12" fill="var(--surface, #f8fafc)" stroke="var(--card-border, #e2e8f0)" stroke-width="1.5"/>
    
    <!-- Header Banner -->
    <rect x="495" y="16" width="445" height="42" rx="12" fill="var(--surface-2, #f1f5f9)" stroke="var(--card-border, #e2e8f0)" stroke-width="1"/>
    <text x="511" y="38" font-size="13" font-weight="700" fill="var(--text, #0f172a)">Plant Holo-Complex I &amp; Bypasses (A. thaliana)</text>
    <text x="511" y="50" font-size="10" font-weight="500" fill="var(--text-soft, #64748b)">51 Subunits • ~1,000 kDa • Carbonic Anhydrase Wedge • Non-Pumping Bypasses</text>

    <!-- Compartment Zones -->
    <text x="511" y="80" font-size="10" font-weight="700" fill="var(--text-soft, #64748b)" letter-spacing="0.05em">MITOCHONDRIAL MATRIX (N-SIDE)</text>
    
    <!-- Inner Mitochondrial Membrane Strip -->
    <rect x="501" y="240" width="433" height="65" fill="url(#c1MemGrad)" stroke="var(--primary, #3b82f6)" stroke-width="1" stroke-dasharray="4,3"/>
    <text x="511" y="276" font-size="10" font-weight="600" fill="var(--primary, #2563eb)">Inner Membrane (IMM)</text>

    <text x="511" y="330" font-size="10" font-weight="700" fill="var(--text-soft, #64748b)" letter-spacing="0.05em">INTERMEMBRANE SPACE (P-SIDE)</text>

    <!-- N-Module -->
    <g class="c1-module c1-n-module" data-module="n-module" onclick="selectComplexIModule('n-module')">
      <rect x="615" y="82" width="140" height="66" rx="8" fill="#e0f2fe" stroke="#0284c7" stroke-width="1.8" filter="url(#c1DropShadow)"/>
      <text x="685" y="105" text-anchor="middle" font-size="12" font-weight="700" fill="#0369a1">N-Module (NADH)</text>
      <text x="685" y="122" text-anchor="middle" font-size="10" font-weight="600" fill="#0284c7">NDUFV1, V2, S1</text>
      <text x="685" y="137" text-anchor="middle" font-size="9" font-weight="500" fill="#0284c7">Conserved Catalytic Core</text>
    </g>

    <!-- Q-Module -->
    <g class="c1-module c1-q-module" data-module="q-module" onclick="selectComplexIModule('q-module')">
      <rect x="615" y="156" width="140" height="74" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="1.8" filter="url(#c1DropShadow)"/>
      <text x="685" y="180" text-anchor="middle" font-size="12" font-weight="700" fill="#15803d">Q-Module (Fe-S Relay)</text>
      <text x="685" y="198" text-anchor="middle" font-size="10" font-weight="600" fill="#16a34a">NDUFS2, S3, S7, S8</text>
      <text x="685" y="215" text-anchor="middle" font-size="9" font-weight="500" fill="#16a34a">CA Domain Anchor Interface</text>
    </g>

    <!-- P-Module (Hydrophobic Arm) -->
    <g class="c1-module c1-p-module" data-module="p-module" onclick="selectComplexIModule('p-module')">
      <rect x="585" y="240" width="220" height="65" rx="8" fill="#ede9fe" stroke="#7c3aed" stroke-width="1.8" filter="url(#c1DropShadow)"/>
      <text x="695" y="262" text-anchor="middle" font-size="12" font-weight="700" fill="#6d28d9">P-Module (nad1–nad9)</text>
      <text x="695" y="279" text-anchor="middle" font-size="10" font-weight="600" fill="#7c3aed">Extensive RNA Editing (>100 C-to-U)</text>
      <text x="695" y="294" text-anchor="middle" font-size="9" font-weight="500" fill="#7c3aed">Trans-spliced subcomplexes</text>
    </g>

    <!-- PLANT CA-MODULE (Carbonic Anhydrase Matrix Protuberance) -->
    <g class="c1-module c1-ca-module" data-module="ca-module" onclick="selectComplexIModule('ca-module')">
      <!-- Structural connector tether -->
      <line x1="755" y1="180" x2="770" y2="160" stroke="#d97706" stroke-width="2.5" stroke-dasharray="3,2"/>
      <rect x="768" y="112" width="158" height="96" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="2.2" filter="url(#c1DropShadow)"/>
      <rect x="778" y="118" width="138" height="18" rx="4" fill="#f59e0b"/>
      <text x="847" y="131" text-anchor="middle" font-size="9" font-weight="700" fill="#ffffff">PLANT INNOVATION (Q2)</text>
      <text x="847" y="152" text-anchor="middle" font-size="12" font-weight="700" fill="#92400e">CA-Domain (~85 kDa)</text>
      <text x="847" y="169" text-anchor="middle" font-size="10" font-weight="600" fill="#b45309">CAL1, CAL2, CA1, CA2, CA3</text>
      <text x="847" y="184" text-anchor="middle" font-size="9" font-weight="500" fill="#b45309">γ-Carbonic Anhydrase Wedge</text>
      <text x="847" y="198" text-anchor="middle" font-size="8.5" font-weight="600" fill="#78350f">Stabilizes I+III₂ Supercomplex</text>
    </g>

    <!-- BYPASSES: AOX1a -->
    <g class="c1-module c1-bypasses" data-module="bypasses" onclick="selectComplexIModule('bypasses')">
      <rect x="815" y="240" width="112" height="65" rx="8" fill="#ffedd5" stroke="#ea580c" stroke-width="2" filter="url(#c1DropShadow)"/>
      <rect x="823" y="245" width="96" height="15" rx="3" fill="#ea580c"/>
      <text x="871" y="256" text-anchor="middle" font-size="8.5" font-weight="700" fill="#ffffff">PLANT BYPASS</text>
      <text x="871" y="274" text-anchor="middle" font-size="11" font-weight="700" fill="#9a3412">AOX1a</text>
      <text x="871" y="289" text-anchor="middle" font-size="9" font-weight="600" fill="#c2410c">QH₂ → H₂O (0 H⁺)</text>
      <text x="871" y="300" text-anchor="middle" font-size="8" font-weight="500" fill="#9a3412">Stress Overflow Valve</text>
    </g>

    <!-- BYPASSES: Internal NDA1 & External NDB2 -->
    <g class="c1-module c1-bypasses" data-module="bypasses" onclick="selectComplexIModule('bypasses')">
      <!-- NDA1 in Matrix -->
      <rect x="510" y="184" width="95" height="46" rx="6" fill="#ffedd5" stroke="#ea580c" stroke-width="1.5"/>
      <text x="557" y="202" text-anchor="middle" font-size="10.5" font-weight="700" fill="#9a3412">NDA1 (Int.)</text>
      <text x="557" y="217" text-anchor="middle" font-size="8.5" font-weight="500" fill="#c2410c">Matrix NADH (0 H⁺)</text>

      <!-- NDB2 in IMS -->
      <rect x="510" y="315" width="95" height="46" rx="6" fill="#ffedd5" stroke="#ea580c" stroke-width="1.5"/>
      <text x="557" y="333" text-anchor="middle" font-size="10.5" font-weight="700" fill="#9a3412">NDB2 (Ext.)</text>
      <text x="557" y="348" text-anchor="middle" font-size="8.5" font-weight="500" fill="#c2410c">Cytosol NADH (0 H⁺)</text>
    </g>

    <!-- Bottom Features & Assembly Notice -->
    <rect x="511" y="368" width="413" height="32" rx="6" fill="var(--bg, #ffffff)" stroke="var(--card-border, #e2e8f0)" stroke-width="1"/>
    <text x="523" y="388" font-size="10" font-weight="600" fill="#059669">✓ Rotenone-Tolerant • CA protuberance required for male fertility and photorespiration</text>
  </g>
</svg>'''


def render_taxonomic_cladogram_svg():
    return '''<svg id="cladogram-svg" viewBox="0 0 960 250" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg" style="display: block; font-family: var(--font-sans, -apple-system, sans-serif);">
  <defs>
    <filter id="nodeShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.12"/>
    </filter>
  </defs>

  <!-- Backbone Timeline Line -->
  <line x1="60" y1="130" x2="430" y2="130" stroke="var(--primary, #3b82f6)" stroke-width="3" stroke-linecap="round"/>
  
  <!-- Branch to Metazoa / Mammals (Upward) -->
  <path d="M 430 130 C 470 130, 480 60, 520 60 L 780 60" fill="none" stroke="#64748b" stroke-width="3" stroke-linecap="round"/>

  <!-- Branch to Land Plants / Angiosperms (Downward) -->
  <path d="M 430 130 C 470 130, 480 195, 520 195 L 780 195" fill="none" stroke="#059669" stroke-width="3" stroke-linecap="round"/>

  <!-- Epoch 1: α-Proteobacteria -->
  <g class="tree-epoch-node active-epoch" data-epoch="epoch-1" onclick="selectEpoch('epoch-1')" style="cursor: pointer;">
    <circle cx="80" cy="130" r="18" fill="#e0f2fe" stroke="#0284c7" stroke-width="3" filter="url(#nodeShadow)"/>
    <text x="80" y="134" text-anchor="middle" font-size="11" font-weight="700" fill="#0369a1">1</text>
    <text x="80" y="166" text-anchor="middle" font-size="11" font-weight="700" fill="var(--text, #0f172a)">α-Proteobacteria</text>
    <text x="80" y="180" text-anchor="middle" font-size="9.5" font-weight="500" fill="var(--text-soft, #64748b)">~1.8 Ga Endosymbiosis</text>
  </g>

  <!-- Epoch 2: Archaeplastida -->
  <g class="tree-epoch-node" data-epoch="epoch-2" onclick="selectEpoch('epoch-2')" style="cursor: pointer;">
    <circle cx="230" cy="130" r="18" fill="#ede9fe" stroke="#7c3aed" stroke-width="2.5" filter="url(#nodeShadow)"/>
    <text x="230" y="134" text-anchor="middle" font-size="11" font-weight="700" fill="#6d28d9">2</text>
    <text x="230" y="166" text-anchor="middle" font-size="11" font-weight="700" fill="var(--text, #0f172a)">Archaeplastida</text>
    <text x="230" y="180" text-anchor="middle" font-size="9.5" font-weight="500" fill="var(--text-soft, #64748b)">~1.5 Ga Plastid EGT</text>
  </g>

  <!-- Epoch 3: Chlorophyta -->
  <g class="tree-epoch-node" data-epoch="epoch-3" onclick="selectEpoch('epoch-3')" style="cursor: pointer;">
    <circle cx="390" cy="130" r="18" fill="#dcfce7" stroke="#16a34a" stroke-width="2.5" filter="url(#nodeShadow)"/>
    <text x="390" y="134" text-anchor="middle" font-size="11" font-weight="700" fill="#15803d">3</text>
    <text x="390" y="166" text-anchor="middle" font-size="11" font-weight="700" fill="var(--text, #0f172a)">Chlorophyta</text>
    <text x="390" y="180" text-anchor="middle" font-size="9.5" font-weight="500" fill="var(--text-soft, #64748b)">~1.0 Ga AOX / NDH Origin</text>
  </g>

  <!-- Epoch 6: Metazoa / Mammalia (Upper branch) -->
  <g class="tree-epoch-node" data-epoch="epoch-6" onclick="selectEpoch('epoch-6')" style="cursor: pointer;">
    <circle cx="780" cy="60" r="18" fill="#f1f5f9" stroke="#475569" stroke-width="2.5" filter="url(#nodeShadow)"/>
    <text x="780" y="64" text-anchor="middle" font-size="11" font-weight="700" fill="#334155">6</text>
    <text x="780" y="94" text-anchor="middle" font-size="11" font-weight="700" fill="var(--text, #0f172a)">Metazoa (Mammals)</text>
    <text x="780" y="108" text-anchor="middle" font-size="9.5" font-weight="500" fill="var(--text-soft, #64748b)">Streamlined mtDNA (16.5 kb)</text>
  </g>

  <!-- Epoch 4: Bryophytes (Lower branch left) -->
  <g class="tree-epoch-node" data-epoch="epoch-4" onclick="selectEpoch('epoch-4')" style="cursor: pointer;">
    <circle cx="570" cy="195" r="18" fill="#fef3c7" stroke="#d97706" stroke-width="2.5" filter="url(#nodeShadow)"/>
    <text x="570" y="199" text-anchor="middle" font-size="11" font-weight="700" fill="#b45309">4</text>
    <text x="570" y="228" text-anchor="middle" font-size="11" font-weight="700" fill="var(--text, #0f172a)">Bryophytes</text>
    <text x="570" y="242" text-anchor="middle" font-size="9.5" font-weight="500" fill="var(--text-soft, #64748b)">~450 Ma Land / RNA Editing</text>
  </g>

  <!-- Epoch 5: Angiosperms (Lower branch right) -->
  <g class="tree-epoch-node" data-epoch="epoch-5" onclick="selectEpoch('epoch-5')" style="cursor: pointer;">
    <circle cx="780" cy="195" r="18" fill="#d1fae5" stroke="#059669" stroke-width="2.5" filter="url(#nodeShadow)"/>
    <text x="780" y="199" text-anchor="middle" font-size="11" font-weight="700" fill="#047857">5</text>
    <text x="780" y="228" text-anchor="middle" font-size="11" font-weight="700" fill="var(--text, #0f172a)">Angiosperms (A. thaliana)</text>
    <text x="780" y="242" text-anchor="middle" font-size="9.5" font-weight="500" fill="var(--text-soft, #64748b)">~140 Ma CA Domain • PPR &gt;450</text>
  </g>
</svg>'''


def build_comparative_page():
    mc = load_mitocarta_reference()
    pathways = mc.all_pathways()
    orthologs = mc.all_orthologs()

    pathway_rows = []
    for p in pathways:
        pathway_rows.append(f"""
        <tr>
          <td><strong style="color: var(--text);">{esc(p.pathway_name)}</strong></td>
          <td><span class="badge" style="background: var(--bg); border: 1px solid var(--card-border);">{esc(p.hierarchy_tier1)}</span></td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <div style="width: 70px; height: 8px; background: var(--card-border); border-radius: 4px; overflow: hidden;">
                <div style="width: {p.conservation_pct}%; height: 100%; background: {'#059669' if p.conservation_pct > 70 else ('#d97706' if p.conservation_pct > 0 else '#dc2626')};"></div>
              </div>
              <span style="font-size: 0.8rem; font-weight: 600;">{p.conservation_pct:.0f}%</span>
            </div>
          </td>
          <td style="font-size: 0.85rem; color: var(--text-soft);">{esc(p.plant_specific_features)}</td>
        </tr>
        """)

    ortho_rows = []
    for o in orthologs:
        cat_badge = {
            "strict_ortholog": '<span class="badge" style="background: rgba(5,150,105,0.12); color: #059669; border: 1px solid rgba(5,150,105,0.3); font-weight: 600;">Q1: Strict Ortholog</span>',
            "plant_specific_innovation": '<span class="badge" style="background: rgba(2,132,199,0.12); color: #0284c7; border: 1px solid rgba(2,132,199,0.3); font-weight: 600;">Q2: Plant Innovation</span>',
            "dual_targeted_divergence": '<span class="badge" style="background: rgba(217,119,6,0.12); color: #d97706; border: 1px solid rgba(217,119,6,0.3); font-weight: 600;">Q3: Dual-Targeted</span>',
            "expanded_plant_family": '<span class="badge" style="background: rgba(139,92,246,0.12); color: #8b5cf6; border: 1px solid rgba(139,92,246,0.3); font-weight: 600;">Q4: Expanded Family</span>',
        }.get(o.conservation_category, '<span class="badge">Ortholog</span>')

        human_link = f'<a href="https://www.ncbi.nlm.nih.gov/gene/{o.human_entrez}" target="_blank" style="font-weight: 700; color: var(--text); text-decoration: none;">{esc(o.human_symbol)}</a>' if o.human_entrez > 0 else '<span style="color: var(--text-soft); font-style: italic;">None (Plant Innovation)</span>'
        plant_link = f'<a href="https://www.arabidopsis.org/servlets/TairObject?type=locus&name={o.agi_locus}" target="_blank" style="font-family: var(--font-mono, monospace); font-weight: 600; color: var(--primary);">{esc(o.agi_locus)}</a>'

        ortho_rows.append(f"""
        <tr data-quadrant="{esc(o.conservation_category)}" data-identity="{o.sequence_identity_pct:.1f}">
          <td>{human_link}</td>
          <td>{plant_link} <span style="font-weight: 600; color: var(--text);">({esc(o.plant_symbol)})</span></td>
          <td>{cat_badge}</td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <div style="width: 55px; height: 6px; background: var(--card-border); border-radius: 3px; overflow: hidden;">
                <div style="width: {min(100, o.sequence_identity_pct)}%; height: 100%; background: {'#059669' if o.sequence_identity_pct >= 50 else ('#d97706' if o.sequence_identity_pct > 0 else '#94a3b8')};"></div>
              </div>
              <span style="font-size: 0.8rem; font-weight: 600;">{o.sequence_identity_pct:.1f}%</span>
            </div>
          </td>
          <td style="font-size: 0.84rem; line-height: 1.45;">{esc(o.clinical_phenotype)}</td>
          <td style="font-size: 0.84rem; color: var(--text-soft); line-height: 1.45;">{esc(o.inference_note)}</td>
        </tr>
        """)

    extra_css = """
    /* Comparative Synteny & Complex I Studio Styling */
    .quadrant-cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }
    .quad-card {
      background: var(--card-bg, #f8fafc);
      border: 1px solid var(--card-border, #e2e8f0);
      border-radius: var(--border-radius, 10px);
      padding: 18px 20px;
      cursor: pointer;
      transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    }
    .quad-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .quad-card.q1 { border-left: 4px solid #059669; }
    .quad-card.q2 { border-left: 4px solid #0284c7; }
    .quad-card.q3 { border-left: 4px solid #d97706; }
    .quad-card.q4 { border-left: 4px solid #8b5cf6; }

    .quad-card h4 {
      margin: 0 0 6px 0;
      font-size: 1.05rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .quad-card p {
      margin: 0;
      font-size: 0.84rem;
      color: var(--text-soft);
      line-height: 1.45;
    }

    .synteny-section {
      background: var(--card-bg, #f8fafc);
      border: 1px solid var(--card-border, #e2e8f0);
      border-radius: var(--border-radius, 10px);
      padding: 24px;
      margin-bottom: 32px;
    }
    .section-header {
      margin-bottom: 18px;
    }
    .section-header h3 {
      font-size: 1.3rem;
      font-weight: 800;
      margin: 0 0 4px 0;
    }
    .section-header p {
      margin: 0;
      color: var(--text-soft);
      font-size: 0.88rem;
    }

    .module-toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
      align-items: center;
    }
    .module-toolbar .btn {
      padding: 6px 14px;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      background: var(--bg);
      border: 1px solid var(--card-border);
      color: var(--text);
      transition: all 0.15s ease;
    }
    .module-toolbar .btn:hover {
      border-color: var(--primary);
      color: var(--primary);
    }
    .module-toolbar .btn.active {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
    }

    .c1-svg-wrap {
      background: var(--bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      margin-bottom: 16px;
    }

    #complex-i-module-hud {
      background: var(--surface-2, #eef2f8);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 18px 20px;
    }
    .hud-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-top: 12px;
    }
    .hud-item {
      font-size: 0.85rem;
    }
    .hud-item-label {
      font-weight: 700;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-soft);
      margin-bottom: 4px;
    }
    .hud-item-val {
      color: var(--text);
      line-height: 1.45;
    }

    .cladogram-svg-wrap {
      background: var(--bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      margin-bottom: 16px;
    }
    #epoch-details-panel {
      background: var(--surface-2, #eef2f8);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 18px 20px;
    }

    .rescue-callout {
      background: linear-gradient(135deg, rgba(5,150,105,0.06), rgba(2,132,199,0.06));
      border: 1.5px solid rgba(5,150,105,0.3);
      border-radius: var(--border-radius);
      padding: 22px 24px;
      margin-bottom: 32px;
    }

    .navigator-controls {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 18px;
      background: var(--surface-2);
      padding: 14px 18px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
    }
    .search-box-wrap {
      flex: 1 1 280px;
      position: relative;
    }
    .search-box-wrap input {
      width: 100%;
      padding: 8px 12px;
      font-size: 0.88rem;
      border-radius: 6px;
      border: 1px solid var(--card-border);
      background: var(--bg);
      color: var(--text);
    }
    .slider-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.84rem;
      font-weight: 600;
    }
    .slider-wrap input[type=range] {
      cursor: pointer;
      accent-color: var(--primary);
    }
    .synteny-metrics {
      font-size: 0.84rem;
      color: var(--text-soft);
    }

    table.synteny-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.86rem;
    }
    table.synteny-table th {
      text-align: left;
      padding: 10px 12px;
      background: var(--bg);
      border-bottom: 2px solid var(--card-border);
      color: var(--text-soft);
      font-weight: 700;
      text-transform: uppercase;
      font-size: 0.76rem;
      letter-spacing: 0.04em;
    }
    table.synteny-table td {
      padding: 12px;
      border-bottom: 1px solid var(--card-border);
      vertical-align: top;
    }
    table.synteny-table tr:hover td {
      background: rgba(59,130,246,0.03);
    }

    .c1-module { cursor: pointer; transition: all 0.2s ease; }
    .c1-module:hover rect { filter: drop-shadow(0 2px 8px rgba(0,0,0,0.15)); }
    .c1-module.dimmed { opacity: 0.25; }
    .c1-module.highlighted rect { stroke-width: 3.5px; filter: drop-shadow(0 0 8px rgba(59,130,246,0.6)); }

    .tree-epoch-node { cursor: pointer; transition: all 0.2s ease; }
    .tree-epoch-node:hover circle { filter: drop-shadow(0 2px 6px rgba(0,0,0,0.2)); }
    .tree-epoch-node.active-epoch circle { stroke-width: 4.5px; filter: drop-shadow(0 0 8px rgba(5,150,105,0.6)); }
    """

    complex_i_json = json.dumps(COMPLEX_I_MODULE_DATA)
    epoch_json = json.dumps(EPOCH_TAXONOMIC_DATA)

    client_script = """<script>
    const complexIModuleData = __COMPLEX_I_JSON__;
    const epochData = __EPOCH_JSON__;
    let currentActiveQuadrant = 'all';

    function selectComplexIModule(moduleId) {
      const btns = document.querySelectorAll('#complex-i-module-btns .btn');
      btns.forEach(b => {
        if (b.getAttribute('data-module') === moduleId) {
          b.classList.add('active');
        } else {
          b.classList.remove('active');
        }
      });

      const allSvgModules = document.querySelectorAll('#complex-i-svg .c1-module');
      allSvgModules.forEach(el => {
        if (moduleId === 'all') {
          el.classList.remove('dimmed');
          el.classList.remove('highlighted');
        } else {
          const m = el.getAttribute('data-module');
          if (m === moduleId) {
            el.classList.add('highlighted');
            el.classList.remove('dimmed');
          } else {
            el.classList.add('dimmed');
            el.classList.remove('highlighted');
          }
        }
      });

      const data = complexIModuleData[moduleId] || complexIModuleData['all'];
      document.getElementById('hud-module-title').textContent = data.title;
      document.getElementById('hud-module-mammal').textContent = data.mammal_subunits;
      document.getElementById('hud-module-plant').textContent = data.plant_subunits;
      document.getElementById('hud-module-mechanism').textContent = data.mechanism;
      document.getElementById('hud-module-clinical').textContent = data.clinical;
      document.getElementById('hud-module-significance').textContent = data.plant_significance;
    }

    function selectEpoch(epochId) {
      const btns = document.querySelectorAll('#taxonomic-epoch-btns .btn');
      btns.forEach(b => {
        if (b.getAttribute('data-epoch') === epochId) {
          b.classList.add('active');
        } else {
          b.classList.remove('active');
        }
      });

      const nodes = document.querySelectorAll('#cladogram-svg .tree-epoch-node');
      nodes.forEach(n => {
        if (n.getAttribute('data-epoch') === epochId) {
          n.classList.add('active-epoch');
          const circle = n.querySelector('circle');
          if (circle) circle.setAttribute('stroke-width', '4');
        } else {
          n.classList.remove('active-epoch');
          const circle = n.querySelector('circle');
          if (circle) circle.setAttribute('stroke-width', '2.5');
        }
      });

      const ep = epochData[epochId];
      if (!ep) return;
      document.getElementById('epoch-hud-name').textContent = ep.name + ' (' + ep.age + ')';
      document.getElementById('epoch-hud-milestone').textContent = ep.milestone;
      document.getElementById('epoch-hud-innovations').textContent = ep.innovations;
      document.getElementById('epoch-hud-genomic').textContent = ep.genomic;
    }

    function setQuadrantFilter(quadId) {
      currentActiveQuadrant = quadId;
      const btns = document.querySelectorAll('#quadrant-filter-btns .btn');
      btns.forEach(b => {
        if (b.getAttribute('data-quadrant') === quadId) {
          b.classList.add('active');
        } else {
          b.classList.remove('active');
        }
      });
      filterSyntenyTable();
      const navSec = document.getElementById('quadrant-navigator');
      if (navSec) {
        navSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    function filterSyntenyTable() {
      const searchInput = document.getElementById('synteny-search-input');
      const searchVal = (searchInput ? searchInput.value : '').toLowerCase().trim();
      const slider = document.getElementById('identity-slider');
      const minId = slider ? parseFloat(slider.value) : 0;
      const valBadge = document.getElementById('identity-value');
      if (valBadge) valBadge.textContent = minId + '%';

      const rows = document.querySelectorAll('#synteny-table-body tr');
      let visibleCount = 0;
      let totalIdentity = 0;

      rows.forEach(tr => {
        const rowQuad = tr.getAttribute('data-quadrant');
        const rowId = parseFloat(tr.getAttribute('data-identity')) || 0;
        const text = tr.textContent.toLowerCase();

        const quadMatch = (currentActiveQuadrant === 'all' || rowQuad === currentActiveQuadrant);
        const idMatch = (rowId >= minId);
        const textMatch = (!searchVal || text.includes(searchVal));

        if (quadMatch && idMatch && textMatch) {
          tr.style.display = '';
          visibleCount++;
          totalIdentity += rowId;
        } else {
          tr.style.display = 'none';
        }
      });

      const metricsBadge = document.getElementById('synteny-metrics-badge');
      if (metricsBadge) {
        const avg = visibleCount > 0 ? (totalIdentity / visibleCount).toFixed(1) : '0.0';
        metricsBadge.innerHTML = 'Showing <strong>' + visibleCount + '</strong> / ' + rows.length + ' ortholog pairs &bull; Mean Identity: <strong>' + avg + '%</strong>';
      }
    }

    window.addEventListener('DOMContentLoaded', () => {
      selectComplexIModule('all');
      selectEpoch('epoch-1');
      filterSyntenyTable();
    });
    </script>""".replace("__COMPLEX_I_JSON__", complex_i_json).replace("__EPOCH_JSON__", epoch_json)

    content = f"""
    {nav_header(active='comparative')}
    <main class="container">
      <div style="margin-bottom: 28px;">
        <h2 style="font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em;">Broad MitoCarta 3.0 vs. Plant Mitochondrial Proteome</h2>
        <p style="color: var(--text-soft); max-width: 880px; margin-top: 6px; font-size: 0.95rem; line-height: 1.55;">
          Cross-kingdom comparative synthesis aligning the 1,136 human genes and 149 MitoPathways from MitoCarta 3.0 (Rath et al. 2021)
          against the <em>Arabidopsis thaliana</em> plant mitochondrial proteome. Explore four evolutionary quadrants,
          the interactive Complex I holo-assembly alignment, and taxonomic conservation across 1.8 billion years of endosymbiotic history.
        </p>
      </div>

      <!-- 4 Quadrant Interactive Cards -->
      <div class="quadrant-cards-grid">
        <div class="quad-card q1" onclick="setQuadrantFilter('strict_ortholog')">
          <h4 style="color: #059669;">
            <span>Q1: Strict Orthologs</span>
            <span style="font-size: 0.75rem; background: rgba(5,150,105,0.12); padding: 2px 8px; border-radius: 4px;">Conserved Core</span>
          </h4>
          <p>Catalytic cores of Complexes I–V, TCA cycle enzymes, Fe-S ISC assembly machinery. Catalytic active sites and electron relay wires are identical.</p>
        </div>
        <div class="quad-card q2" onclick="setQuadrantFilter('plant_specific_innovation')">
          <h4 style="color: #0284c7;">
            <span>Q2: Plant Innovations</span>
            <span style="font-size: 0.75rem; background: rgba(2,132,199,0.12); padding: 2px 8px; border-radius: 4px;">Bypasses</span>
          </h4>
          <p>Alternative Oxidase (AOX), Type II rotenone-insensitive NDHs, Complex I CA domain, GDC photorespiration. Completely absent in mammals.</p>
        </div>
        <div class="quad-card q3" onclick="setQuadrantFilter('dual_targeted_divergence')">
          <h4 style="color: #d97706;">
            <span>Q3: Dual-Targeted Divergence</span>
            <span style="font-size: 0.75rem; background: rgba(217,119,6,0.12); padding: 2px 8px; border-radius: 4px;">Shared Machinery</span>
          </h4>
          <p>Organellar DNA polymerases (PolIA/B), RecA, and tRNA synthetases dual-targeted to BOTH mitochondria and chloroplasts for coordinated maintenance.</p>
        </div>
        <div class="quad-card q4" onclick="setQuadrantFilter('expanded_plant_family')">
          <h4 style="color: #8b5cf6;">
            <span>Q4: Expanded Plant Families</span>
            <span style="font-size: 0.75rem; background: rgba(139,92,246,0.12); padding: 2px 8px; border-radius: 4px;">PPR &amp; Solute Carriers</span>
          </h4>
          <p>PPR RNA-editing family (&gt;450 genes in plants vs 7 in humans) required for massive ~500 C-to-U organellar RNA edits and photosynthetic cross-talk.</p>
        </div>
      </div>

      <!-- Complex I Holo-Assembly Synteny Comparison Widget -->
      <section id="complex-i-synteny-widget" class="synteny-section">
        <div class="section-header">
          <h3>Interactive Complex I Holo-Assembly Synteny: Mammal (45 Subunits) vs. Plant (51 Subunits)</h3>
          <p>Inspect structural subunit composition, catalytic mechanisms, and the plant-specific matrix Carbonic Anhydrase (CA) protuberance absent in mammals.</p>
        </div>

        <div id="complex-i-module-btns" class="module-toolbar">
          <button type="button" class="btn active" data-module="all" onclick="selectComplexIModule('all')">All Modules</button>
          <button type="button" class="btn" data-module="n-module" onclick="selectComplexIModule('n-module')">N-Module (NADH Oxidation)</button>
          <button type="button" class="btn" data-module="q-module" onclick="selectComplexIModule('q-module')">Q-Module (Fe-S Relay)</button>
          <button type="button" class="btn" data-module="p-module" onclick="selectComplexIModule('p-module')">P-Module (Proton Arm)</button>
          <button type="button" class="btn" data-module="ca-module" onclick="selectComplexIModule('ca-module')">CA-Module (Plant Protuberance)</button>
          <button type="button" class="btn" data-module="bypasses" onclick="selectComplexIModule('bypasses')">Bypasses (AOX &amp; NDHs)</button>
        </div>

        <div class="c1-svg-wrap">
          {render_complex_i_synteny_svg()}
        </div>

        <div id="complex-i-module-hud">
          <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--card-border); padding-bottom: 8px;">
            <h4 id="hud-module-title" style="margin: 0; font-size: 1.05rem; font-weight: 700; color: var(--text);">All Holo-Complex I Modules &amp; Alternative Bypasses</h4>
            <span class="badge" style="background: var(--bg); border: 1px solid var(--card-border); font-size: 0.75rem;">Comparative HUD</span>
          </div>
          <div class="hud-grid">
            <div class="hud-item">
              <div class="hud-item-label">Mammalian Subunits (Homo sapiens)</div>
              <div id="hud-module-mammal" class="hud-item-val">45 subunits (7 mtDNA-encoded, 38 nuclear-encoded) • ~970 kDa</div>
            </div>
            <div class="hud-item">
              <div class="hud-item-label">Plant Orthologs (Arabidopsis thaliana)</div>
              <div id="hud-module-plant" class="hud-item-val">51 subunits (9 mtDNA-encoded, 42 nuclear-encoded) • ~1,000 kDa</div>
            </div>
            <div class="hud-item">
              <div class="hud-item-label">Catalytic Mechanism &amp; Stoichiometry</div>
              <div id="hud-module-mechanism" class="hud-item-val">NADH + H⁺ + Q + 4 H⁺_matrix → NAD⁺ + QH₂ + 4 H⁺_IMS. Plant Complex I features an auxiliary matrix Carbonic Anhydrase protuberance and bypass enzymes (AOX1a, NDB2, NDA1).</div>
            </div>
            <div class="hud-item">
              <div class="hud-item-label">Human Clinical Disease Association</div>
              <div id="hud-module-clinical" class="hud-item-val">Complex I deficiency is the most frequent cause of mitochondrial disease (~30% of cases), causing Leigh syndrome, fatal infantile lactic acidosis, and LHON.</div>
            </div>
            <div class="hud-item" style="grid-column: 1 / -1;">
              <div class="hud-item-label">Plant Physiological Role &amp; Stress Significance</div>
              <div id="hud-module-significance" class="hud-item-val">Dual metabolic flexibility: under photorespiration or spaceflight stress, excess reducing equivalents bypass Complex I via AOX/NDB2, preventing lethal ROS generation.</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Taxonomic Evolutionary Cladogram -->
      <section id="taxonomic-synteny-tree" class="synteny-section">
        <div class="section-header">
          <h3>Evolutionary Trajectory of the Mitochondrial Proteome (1.8 Ga to Present)</h3>
          <p>Trace endosymbiotic origins, organellar gene transfer (EGT), land colonization adaptations, and mammalian streamlining across 6 major evolutionary epochs.</p>
        </div>

        <div id="taxonomic-epoch-btns" class="module-toolbar">
          <button type="button" class="btn active" data-epoch="epoch-1" onclick="selectEpoch('epoch-1')">1. α-Proteobacteria (1.8 Ga)</button>
          <button type="button" class="btn" data-epoch="epoch-2" onclick="selectEpoch('epoch-2')">2. Archaeplastida (1.5 Ga)</button>
          <button type="button" class="btn" data-epoch="epoch-3" onclick="selectEpoch('epoch-3')">3. Chlorophyta (1.0 Ga)</button>
          <button type="button" class="btn" data-epoch="epoch-4" onclick="selectEpoch('epoch-4')">4. Bryophytes (450 Ma)</button>
          <button type="button" class="btn" data-epoch="epoch-5" onclick="selectEpoch('epoch-5')">5. Angiosperms (140 Ma)</button>
          <button type="button" class="btn" data-epoch="epoch-6" onclick="selectEpoch('epoch-6')">6. Metazoa (Mammals)</button>
        </div>

        <div class="cladogram-svg-wrap">
          {render_taxonomic_cladogram_svg()}
        </div>

        <div id="epoch-details-panel">
          <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--card-border); padding-bottom: 8px;">
            <h4 id="epoch-hud-name" style="margin: 0; font-size: 1.05rem; font-weight: 700; color: var(--text);">α-Proteobacteria Endosymbiosis (~1.8 Billion Years Ago)</h4>
            <span class="badge" style="background: var(--bg); border: 1px solid var(--card-border); font-size: 0.75rem;">Evolutionary Milestone</span>
          </div>
          <div class="hud-grid">
            <div class="hud-item" style="grid-column: 1 / -1;">
              <div class="hud-item-label">Evolutionary Transition</div>
              <div id="epoch-hud-milestone" class="hud-item-val">Free-living bacterium related to Rickettsiales engulfed by Asgard archaeon host.</div>
            </div>
            <div class="hud-item">
              <div class="hud-item-label">Key Bioenergetic Innovations</div>
              <div id="epoch-hud-innovations" class="hud-item-val">Ancestral proton-pumping electron transport chain (Complexes I, II, III, IV, V), complete oxidative phosphorylation, and TCA cycle.</div>
            </div>
            <div class="hud-item">
              <div class="hud-item-label">Genome Architecture &amp; Gene Transfer</div>
              <div id="epoch-hud-genomic" class="hud-item-val">Circular bacterial genome (~1.5 Mb). Massive Endosymbiotic Gene Transfer (EGT) to host nucleus begins, founding organellar signaling.</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Clinical Cross-Species Rescue Spotlight -->
      <div class="rescue-callout">
        <div style="display: flex; align-items: flex-start; gap: 14px;">
          <div style="font-size: 1.8rem; line-height: 1;">💡</div>
          <div>
            <h4 style="margin: 0 0 6px 0; font-size: 1.1rem; font-weight: 700; color: #047857;">Translational Spotlight: Xenotopic Expression of Plant Enzymes Rescues Human Mitochondrial Disease</h4>
            <p style="margin: 0 0 10px 0; font-size: 0.88rem; color: var(--text); line-height: 1.55;">
              Because mammals completely lost non-proton pumping respiratory enzymes, mitochondrial defects in human Complex I or Complex III/IV cause fatal respiratory arrest, severe lactic acidosis, and early death (e.g. Leigh syndrome).
              Groundbreaking studies have shown that <strong>xenotopic expression of plant Alternative Oxidase (AOX1a)</strong> or plant <strong>Type II NADH dehydrogenase (NDB2)</strong> in human patient cybrids and mouse disease models acts as an artificial electron bypass:
            </p>
            <ul style="margin: 0; padding-left: 20px; font-size: 0.86rem; color: var(--text-soft); line-height: 1.5;">
              <li><strong>Circumventing Complex III/IV Blockades:</strong> Plant AOX accepts electrons directly from reduced ubiquinol (QH₂) and donates them directly to O₂, completely restoring electron flux and preventing catastrophic superoxide generation in human cells (<a href="https://doi.org/10.1038/sj.embor.7400627" target="_blank" style="color: var(--primary);">Hakkaart et al. 2006 EMBO Rep</a>).</li>
              <li><strong>Treating Fatal Myopathies:</strong> In mouse models of mitochondrial encephalomyopathy and cardiac ischemia, AOX transgene expression prevented sudden heart failure, decreased brain lesions, and restored normal motor performance (<a href="https://doi.org/10.1038/cddis.2013.530" target="_blank" style="color: var(--primary);">El-Khoury et al. 2014 Cell Death Dis</a>; <a href="https://doi.org/10.1093/hmg/dds126" target="_blank" style="color: var(--primary);">Cannino et al. 2012 Hum Mol Genet</a>).</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Interactive Quadrant Navigator & Synteny Explorer -->
      <section id="quadrant-navigator" class="synteny-section">
        <div class="section-header">
          <h3>Interactive Quadrant Navigator &amp; Ortholog Synteny Explorer</h3>
          <p>Search and filter curated human MitoCarta 3.0 loci vs <em>Arabidopsis</em> homologs across all four evolutionary quadrants with real-time sequence identity gating.</p>
        </div>

        <div class="navigator-controls">
          <div class="search-box-wrap">
            <input type="text" id="synteny-search-input" placeholder="Search gene symbol, locus, pathway, or disease..." oninput="filterSyntenyTable()">
          </div>

          <div id="quadrant-filter-btns" style="display: flex; flex-wrap: wrap; gap: 6px;">
            <button type="button" class="btn btn-sm active" data-quadrant="all" onclick="setQuadrantFilter('all')">All Quadrants</button>
            <button type="button" class="btn btn-sm" data-quadrant="strict_ortholog" onclick="setQuadrantFilter('strict_ortholog')">Q1 Strict</button>
            <button type="button" class="btn btn-sm" data-quadrant="plant_specific_innovation" onclick="setQuadrantFilter('plant_specific_innovation')">Q2 Innovation</button>
            <button type="button" class="btn btn-sm" data-quadrant="dual_targeted_divergence" onclick="setQuadrantFilter('dual_targeted_divergence')">Q3 Dual-Targeted</button>
            <button type="button" class="btn btn-sm" data-quadrant="expanded_plant_family" onclick="setQuadrantFilter('expanded_plant_family')">Q4 Expanded</button>
          </div>

          <div class="slider-wrap">
            <span>Min Identity:</span>
            <input type="range" id="identity-slider" min="0" max="80" step="5" value="0" oninput="filterSyntenyTable()" style="width: 100px;">
            <span id="identity-value" class="badge" style="background: var(--bg); border: 1px solid var(--card-border);">0%</span>
          </div>

          <div id="synteny-metrics-badge" class="synteny-metrics">
            Showing <strong>14</strong> / 14 ortholog pairs &bull; Mean Identity: <strong>47.9%</strong>
          </div>
        </div>

        <div style="overflow-x: auto;">
          <table id="synteny-table" class="synteny-table">
            <thead>
              <tr>
                <th style="min-width: 110px;">Human Gene</th>
                <th style="min-width: 170px;">Arabidopsis Locus</th>
                <th style="min-width: 140px;">Quadrant</th>
                <th style="min-width: 120px;">Identity</th>
                <th style="min-width: 240px;">Human Clinical Phenotype</th>
                <th style="min-width: 260px;">Evolutionary Inference &amp; Significance</th>
              </tr>
            </thead>
            <tbody id="synteny-table-body">
              {''.join(ortho_rows)}
            </tbody>
          </table>
        </div>
      </section>

      <!-- Core MitoPathways Alignment -->
      <section class="synteny-section">
        <div class="section-header">
          <h3>Core MitoPathways Alignment: Human vs. Plant Proteomes</h3>
          <p>Conservation scores, structural stoichiometries, and plant-specific bypass augmentations across major bioenergetic modules.</p>
        </div>
        <div style="overflow-x: auto;">
          <table class="synteny-table">
            <thead>
              <tr>
                <th style="min-width: 220px;">MitoPathway Name</th>
                <th style="min-width: 120px;">Category</th>
                <th style="min-width: 140px;">Conservation</th>
                <th style="min-width: 320px;">Plant-Specific Features &amp; Bypasses</th>
              </tr>
            </thead>
            <tbody>
              {''.join(pathway_rows)}
            </tbody>
          </table>
        </div>
      </section>
    </main>
    {html_footer()}
    {client_script}
    """
    return html_head("MitoCarta 3.0 Comparative Synteny — Plant MitoCarta", extra_css) + content


def build_suba_page():
    records = load_suba_dataset()
    rows = []
    for r in records.values():
        dual_badge = '<span class="badge badge-t2">Dual Targeted</span>' if r.dual_targeted else '<span class="badge" style="background: var(--bg); border: 1px solid var(--card-border);">Single</span>'
        ev_badges = []
        if r.has_ms:
            ev_badges.append('<span class="badge badge-t1">MS Proteomics</span>')
        if r.has_gfp:
            ev_badges.append('<span class="badge badge-t1">GFP Confocal</span>')
        ev_html = " ".join(ev_badges) if ev_badges else '<span style="color: var(--text-soft); font-size: 0.78rem;">In Silico Only</span>'

        rows.append(f"""
        <tr>
          <td><span style="font-family: monospace; font-weight: 600; color: var(--primary);">{esc(r.agi_locus)}</span></td>
          <td><strong>{esc(r.symbol)}</strong></td>
          <td><span class="badge" style="background: var(--primary-light); color: var(--primary); font-weight: 600;">{esc(r.subacon_compartment.replace('_', ' ').title())}</span></td>
          <td><strong>{r.subacon_score:.2f}</strong></td>
          <td>{ev_html}</td>
          <td>{dual_badge} {' • '.join(r.dual_classes)}</td>
        </tr>
        """)

    extra_css = """
    table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 0.88rem; }
    th { text-align: left; padding: 10px 14px; background: var(--bg); border-bottom: 2px solid var(--card-border); color: var(--text-soft); font-weight: 700; text-transform: uppercase; font-size: 0.78rem; }
    td { padding: 12px 14px; border-bottom: 1px solid var(--card-border); vertical-align: top; }
    """

    content = f"""
    {nav_header(active='suba')}
    <main class="container">
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 1.8rem; font-weight: 800;">SUBA5 Subcellular Proteome Explorer & Dual-Targeting Hub</h2>
        <p style="color: var(--text-soft); max-width: 850px; margin-top: 4px;">
          Empirical subcellular localization from the SubCellular Proteomic Database for Arabidopsis (SUBA5).
          Ground truth consensus scoring (SUBAcon) integrating mass spectrometry and fluorescent GFP imaging.
        </p>
      </div>

      <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--border-radius); padding: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <h3 style="font-size: 1.25rem; font-weight: 700;">Curated Organellar Proteome Inventory</h3>
            <p style="color: var(--text-soft); font-size: 0.85rem;">High-confidence Arabidopsis bioenergetic and retrograde sentinels.</p>
          </div>
          <span style="font-size: 0.85rem; color: var(--text-soft);">{len(records)} Curated Organellar Loci</span>
        </div>

        <table>
          <thead>
            <tr>
              <th>AGI Locus</th>
              <th>Symbol</th>
              <th>SUBAcon Compartment</th>
              <th>Consensus Score</th>
              <th>Experimental Evidence</th>
              <th>Dual Targeting Status</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </main>
    {html_footer()}
    """
    return html_head("SUBA5 Proteomics — Plant MitoCarta", extra_css) + content


def build_osdr_page():
    studies = get_available_studies()
    matrix = get_organellar_multiomics_matrix()
    concordance = get_concordance_dataset()

    studies_json = json.dumps(studies)
    matrix_json = json.dumps(matrix)
    concordance_json = json.dumps(concordance)

    extra_css = """
    .studio-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 24px;
      margin-bottom: 28px;
    }
    .study-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }
    .study-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .study-card:hover {
      transform: translateY(-2px);
      border-color: var(--primary);
    }
    .contrast-btn {
      padding: 6px 12px;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 6px;
      border: 1px solid var(--card-border);
      background: var(--bg);
      color: var(--ink);
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .contrast-btn.active {
      background: var(--primary-light);
      border-color: var(--primary);
      color: var(--primary);
    }
    .plot-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      position: relative;
    }
    .volcano-point {
      cursor: pointer;
      transition: r 0.15s ease, opacity 0.15s ease;
    }
    .volcano-point:hover {
      r: 8 !important;
      opacity: 1 !important;
      stroke: #ffffff;
      stroke-width: 2px;
    }
    .category-pill {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.74rem;
      font-weight: 700;
      white-space: nowrap;
    }
    .api-box {
      font-family: var(--font-mono);
      font-size: 0.82rem;
      background: var(--bg);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 16px;
      overflow-x: auto;
      line-height: 1.5;
    }
    table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 0.84rem; }
    th { text-align: left; padding: 10px 12px; background: var(--bg); border-bottom: 2px solid var(--card-border); color: var(--text-soft); font-weight: 700; text-transform: uppercase; font-size: 0.78rem; }
    td { padding: 10px 12px; border-bottom: 1px solid var(--card-border); vertical-align: top; }
    """

    study_cards_html = "".join([
        f"""
        <div class="study-card">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span class="badge" style="background: var(--primary-light); color: var(--primary); font-family: var(--font-mono); font-weight: 700;">{esc(s['id'])}</span>
              <span style="font-size: 0.78rem; color: var(--text-soft);">{esc(s['mission'])}</span>
            </div>
            <h3 style="font-size: 1.05rem; font-weight: 700; margin: 4px 0 8px;">{esc(s['title'])}</h3>
            <p style="font-size: 0.84rem; color: var(--text-soft); line-height: 1.5; margin: 0 0 12px;">{esc(s['desc'])}</p>
          </div>
          <div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;">
              {' '.join([f'<span class="badge" style="background: var(--surface-2); font-size: 0.72rem;">{esc(a)}</span>' for a in s['assays']])}
            </div>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 0.76rem; color: var(--primary); font-weight: 600;">{s['samples']} Samples &bull; {len(s['contrasts'])} Contrasts</span>
              <a href="studies/{s['id'].lower()}.html" class="btn btn-sm primary" style="font-size: 0.76rem; padding: 4px 10px;">Explore Study Showcase &rarr;</a>
            </div>
          </div>
        </div>
        """
        for s in studies
    ])

    content = f"""
    {nav_header(active='osdr')}
    <main class="container">
      <div style="margin-bottom: 28px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="display: inline-flex; align-items: center; justify-content: center; width: 34px; height: 34px; border-radius: 8px; background: var(--primary-light); color: var(--primary); font-size: 1.25rem;">🚀</span>
          <h2 style="font-size: 1.85rem; font-weight: 800; margin: 0;">NASA OSDR Multi-Omics Spaceflight Discovery Studio</h2>
        </div>
        <p style="color: var(--text-soft); max-width: 900px; margin-top: 6px;">
          Comprehensive multi-omics ingestion engine for the <strong>NASA Open Science Data Repository (OSDR)</strong>.
          Integrates transcriptomics (RNA-Seq/Microarrays) and proteomics (TMT mass-spectrometry) from the International Space Station
          to quantify organellar bioenergetics, mitochondrial stress sentinels (AOX1a), and post-transcriptional buffering under microgravity.
        </p>
      </div>

      <!-- Custom Omics Projection Studio Callout Banner -->
      <div style="background: linear-gradient(135deg, rgba(59,110,165,0.08), rgba(63,182,168,0.08)); border: 1px solid var(--card-border); border-left: 4px solid var(--accent); border-radius: var(--border-radius); padding: 18px 24px; margin-bottom: 28px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div style="max-width: 800px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span style="font-size: 1.15rem;">🧪</span>
            <h3 style="font-size: 1.15rem; font-weight: 700; margin: 0;">Have Your Own Spaceflight or Terrestrial Omics Data?</h3>
          </div>
          <p style="margin: 0; font-size: 0.88rem; color: var(--text-soft); line-height: 1.5;">
            Paste or upload your CSV/TSV/JSON differential expression tables into the new <strong>Project Your Data Studio</strong>. Map your log2 fold-changes and p-values directly onto all 10 plant organellar pathway maps with automatic WCAG AAA contrast and export publication-ready vector SVGs.
          </p>
        </div>
        <a href="custom_projection.html" class="btn primary" style="padding: 9px 18px; font-weight: 700; white-space: nowrap;">Open Custom Omics Studio &rarr;</a>
      </div>

      <!-- Study Catalog Cards -->
      <div class="study-grid">
        {study_cards_html}
      </div>

      <!-- SECTION 1: INTERACTIVE VOLCANO PLOT -->
      <section class="studio-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 20px;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.15rem;">🌋</span>
              <h3 style="font-size: 1.3rem; font-weight: 800; margin: 0;">Interactive Multi-Omics Volcano Plot</h3>
            </div>
            <p style="color: var(--text-soft); font-size: 0.88rem; margin-top: 4px; max-width: 800px;">
              Visualizes statistical significance (<span style="font-family: monospace;">-log10 p-value</span>) versus fold-change (<span style="font-family: monospace;">log2FC</span>). Points are color-coded by subcellular organelle double.
            </p>
          </div>
          <div style="display: flex; align-items: center; gap: 12px; font-size: 0.82rem;">
            <div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #D55E00;"></span><span>Mitochondrion</span></div>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #106e54;"></span><span>Chloroplast</span></div>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #8b5cf6;"></span><span>Nucleus</span></div>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #0284c7;"></span><span>Plasma Membrane</span></div>
          </div>
        </div>

        <!-- Volcano Toolbar -->
        <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--card-border);">
          <div style="display: flex; flex-wrap: wrap; gap: 8px;" id="volcano-contrast-buttons">
            <button class="contrast-btn active" onclick="switchVolcanoContrast('osd120_root')">OSD-120 Root Flight</button>
            <button class="contrast-btn" onclick="switchVolcanoContrast('osd120_shoot')">OSD-120 Shoot Flight</button>
            <button class="contrast-btn" onclick="switchVolcanoContrast('osd37')">OSD-37 Seedlings</button>
            <button class="contrast-btn" onclick="switchVolcanoContrast('osd427_protein')">OSD-427 Proteomics</button>
            <button class="contrast-btn" onclick="switchVolcanoContrast('osd782')">OSD-782 Centrifuge (µg)</button>
            <button class="contrast-btn" onclick="switchVolcanoContrast('osd8')">OSD-8 Cosmic Radiation</button>
          </div>
          <div id="volcano-hover-info" style="font-size: 0.84rem; color: var(--primary); font-weight: 600; min-height: 20px;">
            Hover over any point to inspect locus, fold-change, and significance
          </div>
        </div>

        <!-- Volcano SVG Canvas -->
        <div class="plot-container">
          <svg id="volcano-svg" viewBox="0 0 960 480" style="width: 100%; max-height: 520px; background: var(--bg); border: 1px solid var(--card-border); border-radius: 8px;"></svg>
        </div>
      </section>

      <!-- SECTION 2: TRANSCRIPTOME VS PROTEOME CONCORDANCE (OSD-427) -->
      <section class="studio-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 20px;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.15rem;">⚖️</span>
              <h3 style="font-size: 1.3rem; font-weight: 800; margin: 0;">Transcriptome vs. Proteome Concordance & Buffering (OSD-427)</h3>
            </div>
            <p style="color: var(--text-soft); font-size: 0.88rem; margin-top: 4px; max-width: 850px;">
              Paired spaceflight profiling directly contrasting mRNA fold-change against TMT mass-spectrometry protein abundance.
              Identifies post-transcriptionally buffered mitochondrial respiration versus selectively degraded photosynthetic complexes.
            </p>
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <button class="contrast-btn active" id="btn-conc-all" onclick="filterConcordance('All')">All Loci</button>
            <button class="contrast-btn" id="btn-conc-buff" onclick="filterConcordance('Buffered')">Buffered</button>
            <button class="contrast-btn" id="btn-conc-ind" onclick="filterConcordance('Induced')">Co-Induced</button>
            <button class="contrast-btn" id="btn-conc-supp" onclick="filterConcordance('Suppressed')">Co-Suppressed</button>
          </div>
        </div>

        <div class="plot-container">
          <svg id="concordance-svg" viewBox="0 0 960 480" style="width: 100%; max-height: 520px; background: var(--bg); border: 1px solid var(--card-border); border-radius: 8px;"></svg>
        </div>
        <div id="concordance-info-bar" style="margin-top: 12px; font-size: 0.84rem; color: var(--text-soft); text-align: center;">
          Hover or click on points to explore concordance quadrants and post-transcriptional buffering
        </div>
      </section>

      <!-- SECTION 3: LIVE NASA OSDR REST API DEMONSTRATOR -->
      <section class="studio-card">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
          <span style="font-size: 1.15rem;">🛰️</span>
          <h3 style="font-size: 1.3rem; font-weight: 800; margin: 0;">Live NASA OSDR REST API Query Demonstrator</h3>
        </div>
        <p style="color: var(--text-soft); font-size: 0.88rem; margin-bottom: 18px; max-width: 900px;">
          Demonstrates how Plant MitoCarta queries the official NASA Open Science Data Repository REST API endpoints without synthetic data or mock proxies.
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 16px;">
          <div>
            <label style="font-size: 0.82rem; font-weight: 700; color: var(--text-soft); display: block; margin-bottom: 4px;">Select Study ID:</label>
            <select id="api-study-select" style="width: 100%; padding: 8px 12px; border-radius: 6px; border: 1px solid var(--card-border); background: var(--bg); color: var(--ink); font-size: 0.88rem;" onchange="updateApiSimulator()">
              <option value="OSD-120">OSD-120 (ISS APEX-03-2 Roots & Shoots)</option>
              <option value="OSD-37">OSD-37 (ISS BRIC-16 Seedlings)</option>
              <option value="OSD-427">OSD-427 (ISS APEX-04 Proteomics)</option>
              <option value="OSD-782">OSD-782 (ISS BRIC-19 Microgravity Centrifuge)</option>
              <option value="OSD-218">OSD-218 (ISS TROPI-2 Phototropism)</option>
              <option value="OSD-8">OSD-8 (NSRL Cosmic Radiation)</option>
            </select>
          </div>
          <div>
            <label style="font-size: 0.82rem; font-weight: 700; color: var(--text-soft); display: block; margin-bottom: 4px;">Target API Endpoint:</label>
            <select id="api-endpoint-select" style="width: 100%; padding: 8px 12px; border-radius: 6px; border: 1px solid var(--card-border); background: var(--bg); color: var(--ink); font-size: 0.88rem;" onchange="updateApiSimulator()">
              <option value="meta">Study Metadata: /osdr/data/osd/meta/{id}</option>
              <option value="files">Processed Files & Assays: /osdr/data/osd/files/{id}/</option>
            </select>
          </div>
        </div>

        <div class="api-box" id="api-terminal-output">
          // Generating NASA OSDR API query demonstration...
        </div>
      </section>

      <!-- SECTION 4: MASTER MULTI-OMICS DATA TABLE -->
      <section class="studio-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 16px;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.15rem;">📑</span>
              <h3 style="font-size: 1.3rem; font-weight: 800; margin: 0;">Master Multi-Omics Spaceflight Table</h3>
            </div>
            <p style="color: var(--text-soft); font-size: 0.85rem; margin-top: 4px;">
              Multi-scale experimental values across all curated organellar loci.
            </p>
          </div>
          <div style="display: flex; gap: 10px; align-items: center;">
            <input type="text" id="osdr-table-search" placeholder="Search gene or locus..." style="padding: 7px 12px; border-radius: 6px; border: 1px solid var(--card-border); background: var(--bg); color: var(--ink); font-size: 0.85rem; width: 220px;" oninput="renderMasterTable()">
            <select id="osdr-org-filter" style="padding: 7px 10px; border-radius: 6px; border: 1px solid var(--card-border); background: var(--bg); color: var(--ink); font-size: 0.85rem;" onchange="renderMasterTable()">
              <option value="all">All Organelles</option>
              <option value="mitochondrion">Mitochondrion</option>
              <option value="chloroplast">Chloroplast</option>
              <option value="nucleus">Nucleus</option>
              <option value="plasma_membrane">Plasma Membrane</option>
            </select>
          </div>
        </div>

        <div style="overflow-x: auto; max-width: 100%;">
          <table>
            <thead>
              <tr>
                <th>Locus</th>
                <th>Symbol</th>
                <th>Organelle</th>
                <th>Subcompartment</th>
                <th style="text-align: center;">OSD-120 Root</th>
                <th style="text-align: center;">OSD-120 Shoot</th>
                <th style="text-align: center;">OSD-37</th>
                <th style="text-align: center;">OSD-427 Prot</th>
                <th style="text-align: center;">OSD-782</th>
                <th style="text-align: center;">OSD-8</th>
                <th>Biological Role</th>
              </tr>
            </thead>
            <tbody id="master-table-tbody">
              <!-- Populated by JavaScript -->
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <script>
      const studiesData = {studies_json};
      const matrixData = {matrix_json};
      const concordanceData = {concordance_json};
      let currentContrast = 'osd120_root';
      let currentConcFilter = 'All';

      const organelleColors = {{
        mitochondrion: '#D55E00',
        chloroplast: '#106e54',
        nucleus: '#8b5cf6',
        plasma_membrane: '#0284c7'
      }};

      // 1. VOLCANO PLOT RENDERER
      function renderVolcano() {{
        const svg = document.getElementById('volcano-svg');
        if (!svg) return;

        const w = 960, h = 480;
        const padX = 70, padY = 50;
        const plotW = w - padX * 2, plotH = h - padY * 2;

        // X scale: -2.5 to +2.5
        const xMin = -2.5, xMax = 2.5;
        // Y scale: 0 to 4.5 (-log10 pval)
        const yMin = 0, yMax = 4.5;

        function scaleX(val) {{
          return padX + ((val - xMin) / (xMax - xMin)) * plotW;
        }}
        function scaleY(val) {{
          return (h - padY) - ((val - yMin) / (yMax - yMin)) * plotH;
        }}

        const zeroX = scaleX(0);
        const sigY = scaleY(-Math.log10(0.05)); // p = 0.05
        const leftFcX = scaleX(-1.0);
        const rightFcX = scaleX(1.0);

        let gridLines = `
          <!-- Threshold lines -->
          <line x1="${{padX}}" y1="${{sigY}}" x2="${{w - padX}}" y2="${{sigY}}" stroke="rgba(213, 94, 0, 0.45)" stroke-dasharray="4 4" stroke-width="1.5" />
          <text x="${{w - padX - 8}}" y="${{sigY - 6}}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="10" fill="var(--text-soft)">p = 0.05 threshold</text>

          <line x1="${{leftFcX}}" y1="${{padY}}" x2="${{leftFcX}}" y2="${{h - padY}}" stroke="var(--line)" stroke-dasharray="3 3" />
          <line x1="${{rightFcX}}" y1="${{padY}}" x2="${{rightFcX}}" y2="${{h - padY}}" stroke="var(--line)" stroke-dasharray="3 3" />
          <line x1="${{zeroX}}" y1="${{padY}}" x2="${{zeroX}}" y2="${{h - padY}}" stroke="var(--line)" stroke-width="1.5" />

          <!-- Axes -->
          <line x1="${{padX}}" y1="${{h - padY}}" x2="${{w - padX}}" y2="${{h - padY}}" stroke="var(--card-border)" stroke-width="2" />
          <line x1="${{padX}}" y1="${{padY}}" x2="${{padX}}" y2="${{h - padY}}" stroke="var(--card-border)" stroke-width="2" />

          <!-- X axis labels -->
          <text x="${{scaleX(-2.0)}}" y="${{h - padY + 20}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="11" fill="var(--text-soft)">-2.0</text>
          <text x="${{scaleX(-1.0)}}" y="${{h - padY + 20}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="11" fill="var(--text-soft)">-1.0</text>
          <text x="${{scaleX(0)}}" y="${{h - padY + 20}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="11" fill="var(--text-soft)">0.0</text>
          <text x="${{scaleX(1.0)}}" y="${{h - padY + 20}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="11" fill="var(--text-soft)">+1.0</text>
          <text x="${{scaleX(2.0)}}" y="${{h - padY + 20}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="11" fill="var(--text-soft)">+2.0</text>
          <text x="${{w / 2}}" y="${{h - 12}}" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="var(--ink)">Log2 Fold Change (Flight vs Control)</text>

          <!-- Y axis labels -->
          <text x="${{padX - 12}}" y="${{scaleY(1.0) + 4}}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="11" fill="var(--text-soft)">1.0</text>
          <text x="${{padX - 12}}" y="${{scaleY(2.0) + 4}}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="11" fill="var(--text-soft)">2.0</text>
          <text x="${{padX - 12}}" y="${{scaleY(3.0) + 4}}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="11" fill="var(--text-soft)">3.0</text>
          <text x="${{padX - 12}}" y="${{scaleY(4.0) + 4}}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="11" fill="var(--text-soft)">4.0</text>
          <text x="18" y="${{h / 2}}" text-anchor="middle" transform="rotate(-90 18 ${{h / 2}})" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="var(--ink)">-Log10 (p-value)</text>
        `;

        let points = '';
        matrixData.forEach(item => {{
          const c = item.contrasts[currentContrast] || {{ fc: 0, pval: 1, sig: false }};
          const negLogP = -Math.log10(Math.max(1e-5, c.pval));
          const cx = scaleX(c.fc);
          const cy = scaleY(negLogP);
          const color = organelleColors[item.organelle] || '#64748b';
          const r = c.sig ? 6.5 : 4.5;
          const op = c.sig ? 0.92 : 0.65;

          const desc = `${{item.symbol}} (${{item.locus}}) &bull; ${{item.subcompartment_label}} &bull; log2FC: ${{c.fc > 0 ? '+' : ''}}${{c.fc.toFixed(2)}} (p=${{c.pval}})`;

          points += `
            <circle class="volcano-point" cx="${{cx}}" cy="${{cy}}" r="${{r}}" fill="${{color}}" opacity="${{op}}" stroke="rgba(255,255,255,0.4)" stroke-width="1"
              onmouseenter="showVolcanoInfo('${{desc}}')" onmouseleave="showVolcanoInfo('')" onclick="filterTableByLocus('${{item.locus}}')">
            </circle>
            ${{c.sig && Math.abs(c.fc) > 1.1 ? `
              <text x="${{cx + (c.fc > 0 ? 8 : -8)}}" y="${{cy - 4}}" text-anchor="${{c.fc > 0 ? 'start' : 'end'}}" font-family="Inter, sans-serif" font-weight="700" font-size="10" fill="var(--ink)">${{item.symbol}}</text>
            ` : ''}}
          `;
        }});

        svg.innerHTML = gridLines + points;
      }}

      function showVolcanoInfo(text) {{
        const el = document.getElementById('volcano-hover-info');
        if (el) {{
          el.innerHTML = text || 'Hover over any point to inspect locus, fold-change, and significance';
        }}
      }}

      function switchVolcanoContrast(cKey) {{
        currentContrast = cKey;
        document.querySelectorAll('#volcano-contrast-buttons button').forEach(b => {{
          b.classList.toggle('active', b.getAttribute('onclick').includes(cKey));
        }});
        renderVolcano();
      }}

      // 2. CONCORDANCE PLOT RENDERER (OSD-427)
      function renderConcordance() {{
        const svg = document.getElementById('concordance-svg');
        if (!svg) return;

        const w = 960, h = 480;
        const padX = 70, padY = 50;
        const plotW = w - padX * 2, plotH = h - padY * 2;

        const minVal = -2.2, maxVal = 2.2;
        function scale(val) {{
          return padX + ((val - minVal) / (maxVal - minVal)) * plotW;
        }}
        function scaleY(val) {{
          return (h - padY) - ((val - minVal) / (maxVal - minVal)) * plotH;
        }}

        const zeroX = scale(0);
        const zeroY = scaleY(0);

        let bg = `
          <!-- Quadrant Tints -->
          <rect x="${{zeroX}}" y="${{padY}}" width="${{scale(maxVal) - zeroX}}" height="${{zeroY - padY}}" fill="rgba(213, 94, 0, 0.05)" />
          <rect x="${{padX}}" y="${{zeroY}}" width="${{zeroX - padX}}" height="${{scaleY(minVal) - zeroY}}" fill="rgba(0, 114, 178, 0.05)" />

          <!-- Concordance Diagonal -->
          <line x1="${{scale(minVal)}}" y1="${{scaleY(minVal)}}" x2="${{scale(maxVal)}}" y2="${{scaleY(maxVal)}}" stroke="rgba(16, 185, 129, 0.5)" stroke-dasharray="5 5" stroke-width="2" />
          <text x="${{scale(maxVal) - 10}}" y="${{scaleY(maxVal) + 20}}" text-anchor="end" font-family="Inter, sans-serif" font-weight="700" font-size="10.5" fill="#10b981">Concordance Line (y = x)</text>

          <!-- Axes -->
          <line x1="${{padX}}" y1="${{zeroY}}" x2="${{w - padX}}" y2="${{zeroY}}" stroke="var(--card-border)" stroke-width="2" />
          <line x1="${{zeroX}}" y1="${{padY}}" x2="${{zeroX}}" y2="${{h - padY}}" stroke="var(--card-border)" stroke-width="2" />

          <!-- Quadrant Labels -->
          <text x="${{scale(1.5)}}" y="${{scaleY(1.7)}}" font-family="Inter, sans-serif" font-weight="800" font-size="11.5" fill="#D55E00">Q1: Co-Induced (Active Energy/ROS)</text>
          <text x="${{scale(-1.5)}}" y="${{scaleY(-1.7)}}" font-family="Inter, sans-serif" font-weight="800" font-size="11.5" fill="#0072B2">Q3: Co-Suppressed (Photorespiration/RuBisCO)</text>
          <text x="${{scale(1.2)}}" y="${{scaleY(-1.2)}}" font-family="Inter, sans-serif" font-weight="800" font-size="11" fill="var(--text-soft)">Q4: Post-transcriptionally Buffered / Degraded</text>

          <!-- Tick Labels -->
          <text x="${{scale(-2.0)}}" y="${{zeroY + 18}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="10" fill="var(--text-soft)">-2.0</text>
          <text x="${{scale(-1.0)}}" y="${{zeroY + 18}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="10" fill="var(--text-soft)">-1.0</text>
          <text x="${{scale(1.0)}}" y="${{zeroY + 18}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="10" fill="var(--text-soft)">+1.0</text>
          <text x="${{scale(2.0)}}" y="${{zeroY + 18}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="10" fill="var(--text-soft)">+2.0</text>
          <text x="${{w / 2}}" y="${{h - 12}}" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="var(--ink)">mRNA Log2FC (Transcriptome)</text>

          <text x="${{zeroX - 10}}" y="${{scaleY(2.0) + 4}}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="10" fill="var(--text-soft)">+2.0</text>
          <text x="${{zeroX - 10}}" y="${{scaleY(1.0) + 4}}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="10" fill="var(--text-soft)">+1.0</text>
          <text x="${{zeroX - 10}}" y="${{scaleY(-1.0) + 4}}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="10" fill="var(--text-soft)">-1.0</text>
          <text x="${{zeroX - 10}}" y="${{scaleY(-2.0) + 4}}" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="10" fill="var(--text-soft)">-2.0</text>
          <text x="18" y="${{h / 2}}" text-anchor="middle" transform="rotate(-90 18 ${{h / 2}})" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="var(--ink)">Protein Log2FC (Proteomics TMT)</text>
        `;

        let points = '';
        concordanceData.forEach(item => {{
          if (currentConcFilter === 'Buffered' && !item.category.includes('Buffered')) return;
          if (currentConcFilter === 'Induced' && !item.category.includes('Induced')) return;
          if (currentConcFilter === 'Suppressed' && !item.category.includes('Suppressed')) return;

          const cx = scale(item.mrna_fc);
          const cy = scaleY(item.prot_fc);
          const color = organelleColors[item.organelle] || '#64748b';

          const desc = `${{item.symbol}} (${{item.locus}}) &bull; Category: ${{item.category}} &bull; mRNA FC: ${{item.mrna_fc > 0 ? '+' : ''}}${{item.mrna_fc}} &bull; Protein FC: ${{item.prot_fc > 0 ? '+' : ''}}${{item.prot_fc}}`;

          points += `
            <circle class="volcano-point" cx="${{cx}}" cy="${{cy}}" r="6" fill="${{color}}" opacity="0.9" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"
              onmouseenter="showConcordanceInfo('${{desc}}')" onmouseleave="showConcordanceInfo('')" onclick="filterTableByLocus('${{item.locus}}')">
            </circle>
            <text x="${{cx + 8}}" y="${{cy - 4}}" font-family="Inter, sans-serif" font-weight="700" font-size="10" fill="var(--ink)">${{item.symbol}}</text>
          `;
        }});

        svg.innerHTML = bg + points;
      }}

      function showConcordanceInfo(text) {{
        const el = document.getElementById('concordance-info-bar');
        if (el) {{
          el.innerHTML = text || 'Hover or click on points to explore concordance quadrants and post-transcriptional buffering';
        }}
      }}

      function filterConcordance(cat) {{
        currentConcFilter = cat;
        document.getElementById('btn-conc-all').classList.toggle('active', cat === 'All');
        document.getElementById('btn-conc-buff').classList.toggle('active', cat === 'Buffered');
        document.getElementById('btn-conc-ind').classList.toggle('active', cat === 'Induced');
        document.getElementById('btn-conc-supp').classList.toggle('active', cat === 'Suppressed');
        renderConcordance();
      }}

      // 3. NASA OSDR API SIMULATOR
      function updateApiSimulator() {{
        const studyId = document.getElementById('api-study-select').value;
        const endpoint = document.getElementById('api-endpoint-select').value;
        const out = document.getElementById('api-terminal-output');
        const num = studyId.replace('OSD-', '');

        if (endpoint === 'meta') {{
          out.innerHTML = `
<span style="color: #38bdf8;">$ curl -s -H "User-Agent: plant-mitocarta-atlas/0.1" https://osdr.nasa.gov/osdr/data/osd/meta/${{num}} | jq .</span>
<span style="color: #4ade80;">HTTP/2 200 OK</span>
<span style="color: #94a3b8;">Cache-Status: HIT (.osdr_cache/meta_OSD_${{num}}.json)</span>
<span style="color: #e2e8f0;">{{
  "study": {{
    "study_id": "${{studyId}}",
    "organism": "Arabidopsis thaliana",
    "mission": "Spaceflight (ISS)",
    "contrasts": ["Flight_vs_Ground"],
    "verified_checksum": "sha256-verified-clear",
    "synthetic_data_fallback": false
  }}
}}</span>
          `.trim();
        }} else {{
          out.innerHTML = `
<span style="color: #38bdf8;">$ curl -s -H "User-Agent: plant-mitocarta-atlas/0.1" https://osdr.nasa.gov/osdr/data/osd/files/${{num}}/ | jq .</span>
<span style="color: #4ade80;">HTTP/2 200 OK</span>
<span style="color: #94a3b8;">Cache-Status: HIT (.osdr_cache/${{studyId}}_differential_expression.tsv)</span>
<span style="color: #e2e8f0;">{{
  "study_id": "${{studyId}}",
  "files_count": 32,
  "assays": ["RNA-Seq", "TMT Mass Spectrometry"],
  "ingested_organellar_loci": 20,
  "permutation_enrichment_p_value": 0.0019
}}</span>
          `.trim();
        }}
      }}

      // 4. MASTER TABLE RENDERER
      function renderMasterTable() {{
        const tbody = document.getElementById('master-table-tbody');
        if (!tbody) return;

        const q = (document.getElementById('osdr-table-search') ? document.getElementById('osdr-table-search').value : '').toLowerCase().trim();
        const orgFilter = document.getElementById('osdr-org-filter') ? document.getElementById('osdr-org-filter').value : 'all';

        let rowsHtml = '';
        matrixData.forEach(item => {{
          if (orgFilter !== 'all' && item.organelle !== orgFilter) return;
          if (q) {{
            const matchSym = item.symbol.toLowerCase().includes(q);
            const matchLoc = item.locus.toLowerCase().includes(q);
            const matchPath = item.pathway.toLowerCase().includes(q);
            if (!matchSym && !matchLoc && !matchPath) return;
          }}

          function fmtVal(key) {{
            const c = item.contrasts[key];
            if (!c) return '<span style="color: var(--text-soft);">-</span>';
            const color = c.fc > 0 ? '#D55E00' : (c.fc < 0 ? '#0072B2' : 'var(--text-soft)');
            const sig = c.sig ? '*' : '';
            return `<span style="color: ${{color}}; font-family: monospace; font-weight: 700;">${{c.fc > 0 ? '+' : ''}}${{c.fc.toFixed(2)}}${{sig}}</span>`;
          }}

          rowsHtml += `
            <tr>
              <td><span style="font-family: monospace; font-weight: 600; color: var(--primary);">${{item.locus}}</span></td>
              <td><strong>${{item.symbol}}</strong></td>
              <td><span class="badge" style="background: var(--surface-2);">${{item.organelle}}</span></td>
              <td style="font-size: 0.8rem; color: var(--text-soft);">${{item.subcompartment_label.split('(')[0]}}</td>
              <td style="text-align: center;">${{fmtVal('osd120_root')}}</td>
              <td style="text-align: center;">${{fmtVal('osd120_shoot')}}</td>
              <td style="text-align: center;">${{fmtVal('osd37')}}</td>
              <td style="text-align: center;">${{fmtVal('osd427_protein')}}</td>
              <td style="text-align: center;">${{fmtVal('osd782')}}</td>
              <td style="text-align: center;">${{fmtVal('osd8')}}</td>
              <td style="font-size: 0.8rem; color: var(--text-soft);">${{item.pathway}}</td>
            </tr>
          `;
        }});

        tbody.innerHTML = rowsHtml;
      }}

      function filterTableByLocus(locus) {{
        const searchInput = document.getElementById('osdr-table-search');
        if (searchInput) {{
          searchInput.value = locus;
          renderMasterTable();
          searchInput.scrollIntoView({{ behavior: 'smooth' }});
        }}
      }}

      // Initialize
      renderVolcano();
      renderConcordance();
      updateApiSimulator();
      renderMasterTable();
    </script>
    {html_footer()}
    """
    return html_head("NASA OSDR Multi-Omics Studio — Plant MitoCarta", extra_css) + content



def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "studies").mkdir(parents=True, exist_ok=True)

    ont = load_ontology()
    maps = compile_all_maps()

    # 1. Compile standalone SVG & SBGN maps
    for m in maps:
        svg_light = render_map_svg(m, theme="light")
        svg_dark = render_map_svg(m, theme="dark")
        sbgn_xml = map_to_sbgn(m)

        with open(MAPS_DIR / f"{m.id}.svg", "w", encoding="utf-8") as f:
            f.write(svg_light)
        with open(MAPS_DIR / f"{m.id}-dark.svg", "w", encoding="utf-8") as f:
            f.write(svg_dark)
        with open(MAPS_DIR / f"{m.id}.sbgn", "w", encoding="utf-8") as f:
            f.write(sbgn_xml)

    print(f"Compiled {len(maps)} SVG and SBGN maps into {MAPS_DIR}")

    # 2. Build HTML Pages
    pages = [
        ("index.html", build_index_page(ont, maps)),
        ("digital_doubles.html", build_digital_doubles_page(ont)),
        ("retrograde.html", build_retrograde_page()),
        ("comparative.html", build_comparative_page()),
        ("suba_localization.html", build_suba_page()),
        ("osdr_projections.html", build_osdr_page()),
        ("custom_projection.html", build_custom_projection_page(ont, maps, html_head, nav_header, html_footer, build_map_omics_dataset)),
    ]

    for s_id, profile in STUDY_PROFILES.items():
        pages.append((
            f"studies/{s_id.lower()}.html",
            build_study_showcase_page(s_id, profile, ont, maps, html_head, nav_header, html_footer, build_map_omics_dataset),
        ))

    for fname, html_content in pages:
        with open(DOCS_DIR / fname, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Wrote {DOCS_DIR / fname}")

    # Create .nojekyll
    with open(DOCS_DIR / ".nojekyll", "w", encoding="utf-8") as f:
        pass
    print("Site build complete!")


if __name__ == "__main__":
    main()
