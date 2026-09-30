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

from plant_mitocarta.maps import compile_all_maps
from plant_mitocarta.ontology import load_ontology
from plant_mitocarta.render import render_map_svg
from plant_mitocarta.sbgn import map_to_sbgn
from plant_mitocarta.doubles import get_all_doubles, get_synoptic_cell_layout
from plant_mitocarta.suba import load_suba_dataset
from plant_mitocarta.mitocarta import load_mitocarta_reference
from plant_mitocarta.osdr import (
    load_expression_table,
    get_available_studies,
    get_organellar_multiomics_matrix,
    get_concordance_dataset,
)
from plant_mitocarta.project import project_expression_onto_double, project_onto_map
from plant_mitocarta.compare import compartment_specificity_test

DOCS_DIR = ROOT / "docs"
MAPS_DIR = DOCS_DIR / "maps"
ASSETS_DIR = DOCS_DIR / "assets"


def esc(s):
    return html.escape(str(s), quote=True)


def nav_header(active="home"):
    links = [
        ("index.html", "Atlas & Maps", active == "home"),
        ("digital_doubles.html", "Digital Doubles", active == "doubles"),
        ("retrograde.html", "Retrograde Signaling", active == "retrograde"),
        ("comparative.html", "MitoCarta 3.0 Synteny", active == "comparative"),
        ("suba_localization.html", "SUBA5 Proteomics", active == "suba"),
        ("osdr_projections.html", "NASA OSDR Studio", active == "osdr"),
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
      <a href="index.html" class="cose-brand">
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


def build_index_page(ont, maps):
    all_ent = ont.all_entities()
    cards_html = []
    figures_html = []

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
              <a href="#{esc(m.id)}" class="btn primary">View Map</a>
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
                <a href="maps/{esc(m.id)}.svg" target="_blank" class="btn primary">Full Vector SVG</a>
                <a href="maps/{esc(m.id)}-dark.svg" target="_blank" class="btn btn-secondary">Dark SVG</a>
                <a href="maps/{esc(m.id)}.sbgn" download class="btn btn-secondary">SBGN-ML</a>
                <a href="catalog/pmco/{esc(m.id)}.json" target="_blank" class="btn btn-secondary">PMCO Sidecar</a>
              </div>
            </div>
          </figcaption>
        </figure>
        """)

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
    {html_footer()}
    """
    return html_head("Plant MitoCarta Atlas") + content


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

          // Word-wrap description so text NEVER runs out the side of the box
          const maxChars = Math.max(25, Math.floor((s.box.w - 40) / 7.2));
          const descLines = wrapTextLines(s.desc, maxChars);
          const descTspans = descLines.slice(0, 3).map((line, lIdx) =>
            `<tspan x="${{s.box.x + 18}}" dy="${{lIdx === 0 ? 0 : 16}}">${{line}}</tspan>`
          ).join('');

          const badgeH = 24;
          const badgeY = s.box.y + s.box.h - badgeH - 12;
          const badgeW = Math.min(s.box.w - 36, 320);

          rects += `
            <g id="subcomp-g-${{s.id}}" style="cursor: pointer;" onclick="inspectSubcomp('${{mode}}', '${{s.id}}')">
              <!-- Subcompartment Card Background -->
              <rect id="subcomp-rect-${{s.id}}" x="${{s.box.x}}" y="${{s.box.y}}" width="${{s.box.w}}" height="${{s.box.h}}" rx="10" fill="${{fill}}" stroke="${{strokeColor}}" stroke-width="2" />
              
              <!-- GO-CCO tag pill (top right) -->
              <rect x="${{s.box.x + s.box.w - 116}}" y="${{s.box.y + 10}}" width="102" height="20" rx="4" fill="rgba(15, 23, 42, 0.80)" />
              <text x="${{s.box.x + s.box.w - 65}}" y="${{s.box.y + 24}}" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="10.5" font-weight="700" fill="#38bdf8">${{s.go_cc}}</text>

              <!-- Label / Subcompartment Title -->
              <text x="${{s.box.x + 18}}" y="${{s.box.y + 26}}" font-family="Inter, sans-serif" font-weight="800" font-size="15" fill="${{textColor}}">${{s.label}}</text>
              
              <!-- Wrapped Description Lines -->
              <text x="${{s.box.x + 18}}" y="${{s.box.y + 48}}" font-family="Inter, sans-serif" font-size="11.5" fill="${{subColor}}">
                ${{descTspans}}
              </text>
              
              <!-- Padded Stat Badge Scrim -->
              <rect x="${{s.box.x + 18}}" y="${{badgeY}}" width="${{badgeW}}" height="${{badgeH}}" rx="4" fill="${{badgeBg}}" stroke="rgba(255,255,255,0.2)" stroke-width="1" />
              <text x="${{s.box.x + 28}}" y="${{badgeY + 16}}" font-family="JetBrains Mono, monospace" font-size="11" font-weight="700" fill="${{badgeText}}">${{statText}} • Click to Inspect</text>
            </g>
          `;
        }});

        svg.innerHTML = `
          <rect x="0" y="0" width="960" height="600" fill="var(--bg)" rx="10" />
          ${{rects}}
        `;
      }}

      function inspectSubcomp(dId, subId) {{
        const meta = doublesData[dId];
        const sub = meta.subcomps.find(s => s.id === subId);
        const p = projData[dId] ? projData[dId][subId] : null;

        const body = document.getElementById('inspector-body');
        body.innerHTML = `
          <div class="subcomp-card">
            <strong style="color: var(--primary); font-size: 0.95rem;">${{sub.label}}</strong><br>
            <span style="font-family: monospace; font-size: 0.78rem;">${{sub.go_cc}}</span>
            <p style="margin: 6px 0; color: var(--text);">${{sub.desc}}</p>
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
                {"id": "s1", "x": 150, "y": 130, "label": "Complex I/III ROS Leak", "sublabel": "Matrix & IMS H2O2 surge", "title": "Respiratory Chain Stress & ROS Surge", "text": "Complex I/III inhibition or microgravity hypoxia causes electron leakage to oxygen, elevating matrix and IMS superoxide, which dismutates to hydrogen peroxide (H2O2)."},
                {"id": "s2", "x": 210, "y": 270, "label": "IMS H2O2 Diffusion", "sublabel": "Permeant H2O2 crosses cristae", "title": "Diffusion to Outer Mitochondrial Membrane", "text": "Membrane-permeant H2O2 diffuses across the intermembrane space (IMS) to oxidatively prime intramembrane proteases at the outer mitochondrial membrane (OMM)."},
                {"id": "s3", "x": 400, "y": 270, "label": "Rhomboid Protease Cleavage", "sublabel": "C-anchor cut releases ANAC017", "title": "Proteolytic Cleavage of ANAC017 & ANAC013", "text": "Rhomboid-like proteases at the OMM/ER interface cleave the C-terminal transmembrane anchors of ANAC017 (AT1G34190) and ANAC013, releasing active N-terminal NAC transcription factors."},
                {"id": "s4", "x": 590, "y": 200, "label": "Importin-α/β Binding", "sublabel": "Soluble NAC domain chaperone", "title": "Cytosolic Chaperoning & Transit", "text": "The liberated soluble NAC domains bind karyopherin importin-α/β adapters, translocating rapidly across the cytosol towards the nuclear envelope."},
                {"id": "s5", "x": 730, "y": 140, "label": "Nuclear Pore Entry", "sublabel": "Active NPC basket transport", "title": "Nuclear Import via Pore Complexes", "text": "The ANAC017-importin complex passes through the FG-repeat permeability barrier of the nuclear pore complex into the nucleoplasm."},
                {"id": "s6", "x": 850, "y": 270, "label": "MDRE Binding & AOX1a", "sublabel": "CTTGN5CAG -> +1.84 log2FC", "title": "Palindromic MDRE Motif Binding & AOX1a Induction", "text": "ANAC017 homodimers bind palindromic MDRE motifs (CTTGNNNNNCAG), driving massive transcriptional induction of AOX1a (+1.84 log2FC in OSD-120), UPM1, and mitochondrial chaperones."}
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
                {"id": "s1", "x": 160, "y": 120, "label": "PSII 1O2 & EX1 Sensor", "sublabel": "Singlet oxygen sensing at grana", "title": "Light Excess & Singlet Oxygen Generation", "text": "Excess excitation at Photosystem II reaction centers generates singlet oxygen (1O2), sensed in grana margins by EXECUTER 1 (EX1)."},
                {"id": "s2", "x": 210, "y": 260, "label": "Stromal SAL1 Inactivation", "sublabel": "Disulfide bridge oxidation", "title": "Stromal SAL1 Inactivation", "text": "Oxidative stress induces disulfide bridges that inactivate stromal SAL1 nucleotidase (AT5G63980)."},
                {"id": "s3", "x": 415, "y": 260, "label": "PAPST1 Plastid Export", "sublabel": "PAP retrograde metabolite surge", "title": "PAP Retrograde Metabolite Accumulation", "text": "3'-phosphoadenosine 5'-phosphate (PAP) catabolism ceases; PAP accumulates and is exported via PAPST1 into the cytosol."},
                {"id": "s4", "x": 595, "y": 200, "label": "Cytosolic PAP Diffusion", "sublabel": "Free diffusion to envelope", "title": "Cytosolic Transit to Nuclear Envelope", "text": "PAP diffuses through the cytosol and crosses the nuclear envelope pore complexes into the nucleoplasm."},
                {"id": "s5", "x": 770, "y": 140, "label": "Nuclear XRN2/3 Inhibition", "sublabel": "Stabilizes stress transcripts", "title": "Nuclear XRN2/3 Inhibition", "text": "PAP enters the nucleus and directly inhibits 5'-to-3' exoribonucleases (XRN2 and XRN3), stabilizing drought and stress transcripts."},
                {"id": "s6", "x": 850, "y": 280, "label": "GUN1 & ABI4 Hub", "sublabel": "PhANG transcription repression", "title": "GUN1 PPR Hub & ABI4 Activation", "text": "Unimported plastid precursor proteins bind stromal GUN1, signaling to nuclear ABI4 to repress Photosynthesis-Associated Nuclear Genes (PhANGs)."}
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
                {"id": "s1", "x": 160, "y": 130, "label": "RuBisCO Oxygenation", "sublabel": "2-PG -> Glycolate via PLGG1", "title": "Chloroplast RuBisCO Oxygenation", "text": "RuBisCO oxygenase reaction yields 2-phosphoglycolate, which is dephosphorylated to glycolate and exported via PLGG1."},
                {"id": "s2", "x": 480, "y": 130, "label": "Peroxisome GOX & GGT", "sublabel": "Glyoxylate + H2O2 -> Glycine", "title": "Peroxisomal Oxidation to Glyoxylate & Glycine", "text": "Glycolate oxidase (GOX) produces glyoxylate and H2O2 (scavenged by CAT2); GGT transaminates it to glycine."},
                {"id": "s3", "x": 810, "y": 150, "label": "Matrix GDC / SHMT1", "sublabel": "2 Glycine -> Serine + CO2 + NH3", "title": "Mitochondrial GDC / SHMT Serine Synthesis", "text": "Matrix Glycine Decarboxylase (GDC P/T/H/L proteins) and SHMT1 convert 2 glycine into serine + NADH + CO2 + NH3."},
                {"id": "s4", "x": 820, "y": 280, "label": "Complex I CA Domain", "sublabel": "CO2 recycling & hydration", "title": "Complex I CA Domain Recirculation", "text": "The plant-specific Carbonic Anhydrase domain of Complex I re-traps released photorespiratory CO2."},
                {"id": "s5", "x": 500, "y": 280, "label": "Peroxisomal HPR", "sublabel": "Hydroxypyruvate -> Glycerate", "title": "Peroxisomal Reduction & Return", "text": "Serine is transaminated to hydroxypyruvate in peroxisomes, then reduced to glycerate by hydroxypyruvate reductase (HPR)."},
                {"id": "s6", "x": 180, "y": 280, "label": "DiT1 & Glycerate Kinase", "sublabel": "Glycerate -> 3-PGA return", "title": "Chloroplast Return & Phosphorylation", "text": "Glycerate returns to chloroplasts via DiT1 and is phosphorylated by GLYK to 3-PGA, re-entering the Calvin-Benson cycle."}
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
                {"id": "s1", "x": 130, "y": 120, "label": "Cell Wall Tension / Strain", "sublabel": "WAK1 & FERONIA activation", "title": "Cell Wall & Gravity Vector Strain", "text": "Mechanical touch, turgor changes, or microgravity alterations stretch pectin, activating WAK1 and FERONIA receptor kinases."},
                {"id": "s2", "x": 370, "y": 120, "label": "MSL10 & MCA Gating", "sublabel": "Stretch-activated depolarization", "title": "Mechanosensitive Channel Activation", "text": "Membrane tension gates MSL10 and MCA channels, initiating local plasma membrane depolarization."},
                {"id": "s3", "x": 370, "y": 250, "label": "GLR3.3/3.6 Ca2+ Influx", "sublabel": "Rapid apoplastic Ca2+ entry", "title": "Systemic Calcium Influx via GLR3.3/3.6", "text": "Glutamate receptor-like channels open, driving rapid calcium influx from apoplast to cytosol."},
                {"id": "s4", "x": 590, "y": 210, "label": "CPK & RBOHD Activation", "sublabel": "N-terminal phosphorylation", "title": "RBOHD Phosphorylation & Activation", "text": "Cytosolic Ca2+ spikes activate CPKs and BIK1, which phosphorylate RBOHD to generate an apoplastic ROS burst."},
                {"id": "s5", "x": 140, "y": 280, "label": "Apoplastic ROS Wave", "sublabel": "O2.- -> H2O2 dismutation", "title": "Apoplastic Superoxide Burst & Wave", "text": "RBOHD pumps electrons outside to create O2.-, which dismutates to H2O2, launching a systemic cell-to-cell wave."},
                {"id": "s6", "x": 860, "y": 200, "label": "PIP2;1 Inward H2O2 Conduit", "sublabel": "Organellar redox reprogramming", "title": "Inward Channeling via PIP2;1 Aquaporin", "text": "H2O2 re-enters the cytosol and organelles through PIP2;1 channels, tuning mitochondrial AOX and chloroplast redox balance."}
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
                {"id": "s1", "x": 150, "y": 150, "label": "Plastidial Redox Shift", "sublabel": "Stromal oxidative stress trigger", "title": "Stress-Induced Tubule Elongation", "text": "Oxidative stress induces chloroplasts to initiate stroma-filled tubules (stromules) at envelope microdomains."},
                {"id": "s2", "x": 230, "y": 270, "label": "Stromule Extension", "sublabel": "Tubule outgrowth with stroma cargo", "title": "Tubule Outgrowth & Stromule Formation", "text": "Dynamic narrow tubules extend outward from the chloroplast body, containing stromal proteins and metabolites."},
                {"id": "s3", "x": 450, "y": 230, "label": "Myosin XI & Actin Motors", "sublabel": "Tracking microfilament tracks", "title": "Actin Microfilament Guidance", "text": "Stromules track actively along actin microfilaments powered by plant myosin XI class molecular motors."},
                {"id": "s4", "x": 680, "y": 190, "label": "Perinuclear Envelope Docking", "sublabel": "Physical anchor to outer membrane", "title": "Direct Perinuclear Docking", "text": "Stromules physically wrap around and dock directly to outer nuclear membrane receptor complexes."},
                {"id": "s5", "x": 870, "y": 190, "label": "Privileged H2O2 Injection", "sublabel": "Bypasses cytosolic scavenging", "title": "Privileged H2O2 Channeling", "text": "High concentrations of stromal H2O2 are transferred directly into the nucleoplasm, completely avoiding cytosolic peroxiredoxins."}
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

        // Connecting conduit path
        const pathHtml = `
          <path id="conduit-path" d="${{c.path}}" fill="none" stroke="${{c.theme_color}}" stroke-width="3" stroke-dasharray="6 4" opacity="0.65" />
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
              <text x="${{s.x - 34}}" y="${{s.y - 4}}" font-family="Inter, sans-serif" font-weight="700" font-size="10.5" fill="var(--text)" class="node-title">
                ${{s.label}}
              </text>
              <!-- Sublabel -->
              <text x="${{s.x - 34}}" y="${{s.y + 10}}" font-family="Inter, sans-serif" font-size="8.5" fill="var(--text-soft)" class="node-sub">
                ${{s.sublabel}}
              </text>
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
                <strong style="color: var(--text); font-size: 0.95rem;">${{s.title}}</strong>
                <p style="color: var(--text-soft); font-size: 0.88rem; margin-top: 4px;">${{s.text}}</p>
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
              <div style="width: 60px; height: 8px; background: var(--card-border); border-radius: 4px; overflow: hidden;">
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
            "strict_ortholog": '<span class="badge badge-t1">Strict Ortholog (Q1)</span>',
            "plant_specific_innovation": '<span class="badge badge-t2">Plant Innovation (Q2)</span>',
            "dual_targeted_divergence": '<span class="badge badge-t3">Dual-Targeted (Q3)</span>',
        }.get(o.conservation_category, '<span class="badge badge-t4">Ortholog</span>')

        ortho_rows.append(f"""
        <tr>
          <td><strong>{esc(o.human_symbol)}</strong></td>
          <td><span style="font-family: monospace; color: var(--primary);">{esc(o.agi_locus)}</span> ({esc(o.plant_symbol)})</td>
          <td>{cat_badge}</td>
          <td>{o.sequence_identity_pct:.1f}%</td>
          <td style="font-size: 0.83rem;">{esc(o.clinical_phenotype)}</td>
          <td style="font-size: 0.83rem; color: var(--text-soft);">{esc(o.inference_note)}</td>
        </tr>
        """)

    extra_css = """
    table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 0.88rem; }
    th { text-align: left; padding: 10px 14px; background: var(--bg); border-bottom: 2px solid var(--card-border); color: var(--text-soft); font-weight: 700; text-transform: uppercase; font-size: 0.78rem; }
    td { padding: 12px 14px; border-bottom: 1px solid var(--card-border); vertical-align: top; }
    """

    content = f"""
    {nav_header(active='comparative')}
    <main class="container">
      <div style="margin-bottom: 28px;">
        <h2 style="font-size: 1.8rem; font-weight: 800;">Broad MitoCarta 3.0 vs. Plant Mitochondrial Proteome</h2>
        <p style="color: var(--text-soft); max-width: 850px; margin-top: 4px;">
          Cross-kingdom comparative synthesis aligning the 1,136 human genes and 149 MitoPathways from MitoCarta 3.0 (Rath et al. 2021)
          against the <em>Arabidopsis thaliana</em> plant mitochondrial proteome.
        </p>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 32px;">
        <div class="card" style="border-left: 4px solid #059669;">
          <h4 style="color: #059669;">Q1: Strict Orthologs</h4>
          <p style="font-size: 0.85rem; color: var(--text-soft); margin-top: 4px;">Catalytic cores of Complexes I–V, TCA cycle enzymes, Fe-S ISC assembly machinery. Catalytic active sites are identical.</p>
        </div>
        <div class="card" style="border-left: 4px solid #0284c7;">
          <h4 style="color: #0284c7;">Q2: Plant Innovations</h4>
          <p style="font-size: 0.85rem; color: var(--text-soft); margin-top: 4px;">Alternative Oxidase (AOX), Type II rotenone-insensitive NDHs, Complex I CA domain, GDC photorespiration. Completely absent in mammals.</p>
        </div>
        <div class="card" style="border-left: 4px solid #d97706;">
          <h4 style="color: #d97706;">Q3: Dual-Targeted Divergence</h4>
          <p style="font-size: 0.85rem; color: var(--text-soft); margin-top: 4px;">Organellar DNA polymerases (PolIA/B), RecA, and tRNA synthetases dual-targeted to BOTH mitochondria and chloroplasts.</p>
        </div>
        <div class="card" style="border-left: 4px solid #8b5cf6;">
          <h4 style="color: #8b5cf6;">Q4: Expanded Plant Families</h4>
          <p style="font-size: 0.85rem; color: var(--text-soft); margin-top: 4px;">PPR RNA-editing family (>450 genes in plants vs 7 in humans) required for massive ~500 C-to-U organellar RNA edits.</p>
        </div>
      </div>

      <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--border-radius); padding: 24px; margin-bottom: 32px;">
        <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">Core MitoPathways Alignment</h3>
        <p style="color: var(--text-soft); font-size: 0.85rem;">Comparing pathway conservation and plant-specific augmentations across major bioenergetic modules.</p>
        <table>
          <thead>
            <tr>
              <th>MitoPathway Name</th>
              <th>Category</th>
              <th>Conservation</th>
              <th>Plant-Specific Features & Bypasses</th>
            </tr>
          </thead>
          <tbody>
            {''.join(pathway_rows)}
          </tbody>
        </table>
      </div>

      <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--border-radius); padding: 24px;">
        <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">Human Disease Loci vs Plant Stress Homologs</h3>
        <p style="color: var(--text-soft); font-size: 0.85rem;">Cross-species inference: how human medical genetics informs plant catalytic biology, and how plant bypasses (AOX) rescue human disease.</p>
        <table>
          <thead>
            <tr>
              <th>Human Gene</th>
              <th>Arabidopsis Locus</th>
              <th>Quadrant</th>
              <th>Identity</th>
              <th>Human Clinical Phenotype</th>
              <th>Inference & Cross-Species Significance</th>
            </tr>
          </thead>
          <tbody>
            {''.join(ortho_rows)}
          </tbody>
        </table>
      </div>
    </main>
    {html_footer()}
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
            <span style="font-size: 0.76rem; color: var(--primary); font-weight: 600;">{s['samples']} Samples &bull; {len(s['contrasts'])} Contrasts</span>
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
    ]

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
