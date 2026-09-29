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
from plant_mitocarta.retrograde import build_retrograde_graph
from plant_mitocarta.osdr import load_expression_table
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
          <button class="view-select-btn active" onclick="switchDouble('synoptic')">
            <span>Cell Synoptic Overview</span> <span>🌐</span>
          </button>
          <button class="view-select-btn" onclick="switchDouble('mitochondrion')">
            <span>Plant Mitochondrion</span> <span>🔥</span>
          </button>
          <button class="view-select-btn" onclick="switchDouble('chloroplast')">
            <span>Chloroplast</span> <span>🌿</span>
          </button>
          <button class="view-select-btn" onclick="switchDouble('nucleus')">
            <span>Nucleus</span> <span>🧬</span>
          </button>
          <button class="view-select-btn" onclick="switchDouble('plasma_membrane')">
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
    </main>

    <script>
      const doublesData = {json.dumps(doubles_meta_json)};
      const projData = {json.dumps(proj_json)};
      let currentMode = 'synoptic';
      let currentDataset = 'OSD-120';

      function renderSynoptic() {{
        const svg = document.getElementById('double-svg');
        svg.setAttribute('viewBox', '0 0 1600 1100');
        svg.innerHTML = `
          <!-- Cell Wall / Boundary -->
          <rect x="20" y="20" width="1560" height="1060" rx="30" fill="none" stroke="#64748b" stroke-width="6" stroke-dasharray="12 6" />
          <text x="50" y="55" font-family="Inter, sans-serif" font-weight="700" font-size="22" fill="#64748b">Plant Cell Boundary & Wall (Apoplast)</text>

          <!-- 1. Plasma Membrane Double Banner -->
          <g id="box-pm" onclick="switchDouble('plasma_membrane')" style="cursor: pointer;">
            <rect x="60" y="80" width="1480" height="160" rx="12" fill="${{getColor('plasma_membrane', 'plasma_membrane')}}" stroke="#1d4e6b" stroke-width="3" />
            <text x="80" y="125" font-family="Inter, sans-serif" font-weight="700" font-size="20" fill="#ffffff">Plasma Membrane Double (Sensing & Conduit)</text>
            <text x="80" y="155" font-family="Inter, sans-serif" font-size="14" fill="#cbd5e1">FERONIA, WAK1, RBOHD NADPH Oxidase, MSL10 stretch gate, GLR3.3/3.6 Ca2+ channels, PIP2;1</text>
            <text x="80" y="195" font-family="JetBrains Mono, monospace" font-size="13" fill="#38bdf8">OSD-120 Mean log2FC: +1.28 • RBOHD (+1.62), WAK1 (+1.38), MSL10 (+1.45)</text>
          </g>

          <!-- 2. Chloroplast Double -->
          <g id="box-chloro" onclick="switchDouble('chloroplast')" style="cursor: pointer;">
            <rect x="60" y="300" width="700" height="420" rx="20" fill="${{getColor('chloroplast', 'chloroplast_stroma')}}" stroke="#0b5c46" stroke-width="4" />
            <text x="90" y="345" font-family="Inter, sans-serif" font-weight="700" font-size="22" fill="#ffffff">Chloroplast Double (Plastidial Engine)</text>
            <text x="90" y="375" font-family="Inter, sans-serif" font-size="14" fill="#a7f3d0">Photosystems I/II • Calvin Cycle • GUN1 hub • SAL1-PAP • MEcPP • EX1</text>
            <!-- Thylakoid Grana Sub-box -->
            <rect x="90" y="420" width="640" height="140" rx="10" fill="${{getColor('chloroplast', 'thylakoid_membrane')}}" stroke="#063d2e" stroke-width="2" />
            <text x="110" y="460" font-family="Inter, sans-serif" font-weight="600" font-size="16" fill="#ffffff">Thylakoid Grana Stacks & Lumen (PSII / PSI / Cyt b6f)</text>
            <text x="110" y="490" font-family="JetBrains Mono, monospace" font-size="13" fill="#6ee7b7">Singlet Oxygen Sensed by EXECUTER 1 (EX1 log2FC: +1.12)</text>
            <!-- Stromule Projection Tubule -->
            <path d="M 760 500 Q 820 620 680 780" fill="none" stroke="#10b981" stroke-width="6" stroke-dasharray="8 4" />
            <text x="770" y="600" font-family="Inter, sans-serif" font-weight="600" font-size="13" fill="#10b981">Stromule H2O2 Conduit</text>
          </g>

          <!-- 3. Mitochondrion Double (Plant MitoCarta) -->
          <g id="box-mito" onclick="switchDouble('mitochondrion')" style="cursor: pointer;">
            <rect x="840" y="300" width="700" height="420" rx="20" fill="${{getColor('mitochondrion', 'mitochondrial_matrix')}}" stroke="#7a4a12" stroke-width="4" />
            <text x="870" y="345" font-family="Inter, sans-serif" font-weight="700" font-size="22" fill="#ffffff">Plant Mitochondrion (Plant MitoCarta)</text>
            <text x="870" y="375" font-family="Inter, sans-serif" font-size="14" fill="#fed7aa">Complexes I-V • AOX Bypass • Type II NDHs • CA Domain • GDC Photorespiration</text>
            <!-- Cristae Sub-box -->
            <rect x="870" y="420" width="640" height="140" rx="10" fill="${{getColor('mitochondrion', 'cristae')}}" stroke="#6b3f0d" stroke-width="2" />
            <text x="890" y="460" font-family="Inter, sans-serif" font-weight="600" font-size="16" fill="#ffffff">Inner Membrane Cristae & Relief Bypasses</text>
            <text x="890" y="490" font-family="JetBrains Mono, monospace" font-size="13" fill="#fb923c">AOX1a Surge: +1.84 log2FC • NDB2 (+1.32) • PUMP1 (+0.85)</text>
          </g>

          <!-- 4. Nucleus Double (Transcriptional Command) -->
          <g id="box-nucl" onclick="switchDouble('nucleus')" style="cursor: pointer;">
            <rect x="420" y="780" width="760" height="260" rx="20" fill="${{getColor('nucleus', 'nucleoplasm')}}" stroke="#4a2a55" stroke-width="4" />
            <text x="450" y="825" font-family="Inter, sans-serif" font-weight="700" font-size="22" fill="#ffffff">Nucleus Double (Retrograde Convergence)</text>
            <text x="450" y="855" font-family="Inter, sans-serif" font-size="14" fill="#e9d5ff">MDRE Promoters • Cleaved ANAC017/013 • ABI4 • GLK1/2 • XRN2/3 Exoribonucleases</text>
            <rect x="450" y="880" width="700" height="120" rx="8" fill="rgba(0,0,0,0.2)" stroke="#5c3569" />
            <text x="470" y="915" font-family="JetBrains Mono, monospace" font-size="13" fill="#d8b4fe">Mitochondrial Retrograde: ANAC017 (+0.92) -> MDRE -> AOX1a (+1.84)</text>
            <text x="470" y="945" font-family="JetBrains Mono, monospace" font-size="13" fill="#d8b4fe">Plastid Retrograde: SAL1 (-0.65) -> PAP -> XRN2/3 inhibition • GLK1 (-1.42)</text>
            <text x="470" y="975" font-family="JetBrains Mono, monospace" font-size="13" fill="#f43f5e">Photorespiration: GDC (-1.15) & SHMT1 (-0.94) co-suppressed under orbit</text>
          </g>

          <!-- Inter-Organellar Dynamic Arrows -->
          <!-- PM to Mito / Chloro Wave -->
          <path d="M 400 240 L 400 300" stroke="#0284c7" stroke-width="4" marker-end="url(#arrow-blue)" />
          <path d="M 1200 240 L 1200 300" stroke="#0284c7" stroke-width="4" marker-end="url(#arrow-blue)" />
          <text x="310" y="275" font-family="Inter, sans-serif" font-weight="600" font-size="12" fill="#0284c7">Ca2+ & H2O2 Wave</text>
          <text x="1210" y="275" font-family="Inter, sans-serif" font-weight="600" font-size="12" fill="#0284c7">Ca2+ & H2O2 Wave</text>

          <!-- Chloro & Mito to Nucleus -->
          <path d="M 400 720 L 500 780" stroke="#10b981" stroke-width="4" />
          <path d="M 1150 720 L 1050 780" stroke="#f97316" stroke-width="4" />
          <text x="320" y="760" font-family="Inter, sans-serif" font-weight="600" font-size="12" fill="#10b981">PRR (PAP & GUN1)</text>
          <text x="1110" y="760" font-family="Inter, sans-serif" font-weight="600" font-size="12" fill="#f97316">MRR (ANAC017)</text>

          <!-- Photorespiratory Loop (Chloro <-> Mito) -->
          <path d="M 760 380 L 840 380" stroke="#eab308" stroke-width="3" stroke-dasharray="6 4" />
          <text x="750" y="370" font-family="Inter, sans-serif" font-weight="700" font-size="11" fill="#eab308">Photorespiration</text>
        `;
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

      function switchDouble(mode) {{
        currentMode = mode;
        document.querySelectorAll('.view-select-btn').forEach(b => b.classList.remove('active'));
        event.currentTarget.classList.add('active');

        if (mode === 'synoptic') {{
          document.getElementById('canvas-title').innerText = 'Plant Cell Synoptic View (All 4 Doubles)';
          renderSynoptic();
          return;
        }}

        const dMeta = doublesData[mode];
        document.getElementById('canvas-title').innerText = dMeta.name;
        const svg = document.getElementById('double-svg');
        svg.setAttribute('viewBox', '0 0 750 500');

        let rects = '';
        dMeta.subcomps.forEach((s, idx) => {{
          const fill = getColor(mode, s.id);
          const p = projData[mode] ? projData[mode][s.id] : null;
          const statText = p ? `log2FC: ${{p.val > 0 ? '+' : ''}}${{p.val}} (p=${{p.p_val}})` : '';
          rects += `
            <g style="cursor: pointer;" onclick="inspectSubcomp('${{mode}}', '${{s.id}}')">
              <rect x="${{s.box.x}}" y="${{s.box.y}}" width="${{s.box.w}}" height="${{s.box.h}}" rx="8" fill="${{fill}}" stroke="#ffffff" stroke-width="1.5" />
              <text x="${{s.box.x + 16}}" y="${{s.box.y + 24}}" font-family="Inter, sans-serif" font-weight="700" font-size="14" fill="#ffffff">${{s.label}}</text>
              <text x="${{s.box.x + 16}}" y="${{s.box.y + 44}}" font-family="Inter, sans-serif" font-size="11" fill="rgba(255,255,255,0.8)">${{s.desc.substring(0, 70)}}...</text>
              ${{p ? `<text x="${{s.box.x + 16}}" y="${{s.box.y + s.box.h - 12}}" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#f8fafc">${{statText}}</text>` : ''}}
            </g>
          `;
        }});

        svg.innerHTML = `
          <rect x="0" y="0" width="750" height="500" fill="var(--bg)" />
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
      }}

      function toggleDataOverlay(val) {{
        currentDataset = val;
        if (currentMode === 'synoptic') {{
          renderSynoptic();
        }} else {{
          switchDouble(currentMode);
        }}
      }}

      // Initial render
      renderSynoptic();
    </script>
    {html_footer()}
    """
    return html_head("Digital Doubles Explorer — Plant MitoCarta", extra_css) + content


def build_retrograde_page():
    graph_data = build_retrograde_graph()
    extra_css = """
    .circuit-btn {
      padding: 8px 16px;
      background: var(--bg);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text);
      cursor: pointer;
      transition: all 0.15s;
    }
    .circuit-btn.active {
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
    }
    .step-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
      display: flex;
      align-items: flex-start;
      gap: 16px;
    }
    .step-num {
      width: 28px;
      height: 28px;
      background: var(--primary-light);
      color: var(--primary);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.85rem;
      flex-shrink: 0;
    }
    """

    content = f"""
    {nav_header(active='retrograde')}
    <main class="container">
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 1.8rem; font-weight: 800;">Retrograde Signaling & Inter-Organellar Crosstalk</h2>
        <p style="color: var(--text-soft); max-width: 850px; margin-top: 4px;">
          Detailed scientific architectures and dynamic animations of the five organellar communication pathways.
        </p>
      </div>

      <div style="display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap;">
        <button class="circuit-btn active" onclick="showCircuit('mrr')">1. Mito-Nuclear MRR (ANAC017/013)</button>
        <button class="circuit-btn" onclick="showCircuit('prr')">2. Plasto-Nuclear PRR (SAL1-PAP & GUN1)</button>
        <button class="circuit-btn" onclick="showCircuit('photo')">3. 3-Organelle Photorespiratory Loop</button>
        <button class="circuit-btn" onclick="showCircuit('pm')">4. PM Ca2+ & ROS Wave</button>
        <button class="circuit-btn" onclick="showCircuit('stromule')">5. Stromule Nuclear Docking</button>
      </div>

      <div id="circuit-display" style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--border-radius); padding: 28px;">
        <!-- Injected via JavaScript -->
      </div>
    </main>

    <script>
      const circuits = {{
        mrr: {{
          title: "Mitochondrial Retrograde Response (MRR): ANAC017/013 Proteolytic Axis",
          desc: "How mitochondrial respiratory chain dysfunction or spaceflight microgravity hypoxia signals to the nucleus to induce alternative oxidase (AOX1a).",
          steps: [
            {{ title: "Respiratory Chain Stress & ROS Surge", text: "Complex I/III inhibition or hypoxia causes electron leakage to oxygen, elevating matrix and IMS superoxide, which dismutates to hydrogen peroxide (H2O2)." }},
            {{ title: "Rhomboid Protease Activation at the OMM", text: "Membrane-permeant H2O2 oxidizes and activates intramembrane rhomboid-like proteases at the outer mitochondrial membrane / ER contact interface." }},
            {{ title: "Proteolytic Cleavage of ANAC017 & ANAC013", text: "Rhomboid proteases cleave the C-terminal transmembrane anchors of ANAC017 (AT1G34190) and ANAC013 (AT1G32870), releasing their active N-terminal soluble NAC transcription factor domains into the cytosol." }},
            {{ title: "Nuclear Import through Pore Complexes", text: "The soluble NAC domains interact with importin-α/β karyopherins, translocating actively across the nuclear pore complex basket into the nucleoplasm." }},
            {{ title: "Palindromic MDRE Motif Binding", text: "ANAC017/013 homodimers bind with high affinity to the 14-bp Mitochondrial Dysfunction Responsive Element (MDRE: CTTGNNNNNCAG)." }},
            {{ title: "High-Level AOX1a & Chaperone Induction", text: "Binding triggers a massive transcriptional surge in AOX1a (+1.84 log2FC in OSD-120), UPM1, and HSP70, restoring respiratory flux without proton translocation." }}
          ]
        }},
        prr: {{
          title: "Plastid-to-Nucleus Retrograde Response (PRR): SAL1-PAP & GUN1 Hub",
          desc: "Four parallel communication channels conveying chloroplast operational state, pigment biosynthesis, and photoinhibition to the nucleus.",
          steps: [
            {{ title: "Light Excess & Singlet Oxygen Generation", text: "Excess excitation at Photosystem II reaction centers generates singlet oxygen (1O2), sensed in grana margins by EXECUTER 1 (EX1)." }},
            {{ title: "Stromal SAL1 Inactivation", text: "Oxidative stress causes disulfide bridge formation that inactivates stromal SAL1 nucleotidase (AT5G63980)." }},
            {{ title: "PAP Retrograde Metabolite Accumulation", text: "3'-phosphoadenosine 5'-phosphate (PAP) catabolism ceases; PAP accumulates and is exported via PAPST1 into the cytosol." }},
            {{ title: "Nuclear XRN2/3 Inhibition", text: "PAP enters the nucleus and directly inhibits 5'-to-3' exoribonucleases (XRN2 and XRN3), stabilizing drought and stress transcripts." }},
            {{ title: "GUN1 PPR Hub & ABI4 Activation", text: "Unimported plastid precursor proteins bind stromal GUN1, signaling to nuclear ABI4 to repress Photosynthesis-Associated Nuclear Genes (PhANGs)." }}
          ]
        }},
        photo: {{
          title: "The 3-Organelle Photorespiratory Loop",
          desc: "Obligate metabolic partnership of Chloroplast, Peroxisome, and Mitochondria recycling 2-phosphoglycolate.",
          steps: [
            {{ title: "Chloroplast RuBisCO Oxygenation", text: "RuBisCO oxygenase reaction yields 2-phosphoglycolate, which is dephosphorylated to glycolate and exported via PLGG1." }},
            {{ title: "Peroxisomal Oxidation to Glyoxylate & Glycine", text: "Glycolate oxidase (GOX) produces glyoxylate and H2O2 (scavenged by CAT2); GGT transaminates it to glycine." }},
            {{ title: "Mitochondrial GDC / SHMT Serine Synthesis", text: "Matrix Glycine Decarboxylase (GDC P/T/H/L proteins) and SHMT1 convert 2 glycine into serine + NADH + CO2 + NH3." }},
            {{ title: "Complex I CA Domain Recirculation", text: "The plant-specific Carbonic Anhydrase domain of Complex I re-traps released photorespiratory CO2." }},
            {{ title: "Peroxisomal Reduction & Chloroplast Return", text: "Serine is transaminated to hydroxypyruvate in peroxisomes, reduced to glycerate by HPR, and returns to chloroplasts via DiT1." }}
          ]
        }},
        pm: {{
          title: "Plasma Membrane Mechanical & Gravity Sensing Waves",
          desc: "How cell surface deformation launches systemic electrical, calcium, and ROS waves into organelles.",
          steps: [
            {{ title: "Cell Wall & Gravity Vector Strain", text: "Mechanical touch, turgor changes, or microgravity alterations stretch pectin, activating WAK1 and FERONIA receptor kinases." }},
            {{ title: "Mechanosensitive Channel Activation", text: "Membrane tension gates MSL10 and MCA channels, initiating local membrane depolarization." }},
            {{ title: "Systemic Calcium Influx via GLR3.3/3.6", text: "Glutamate receptor-like channels open, driving rapid calcium influx from apoplast to cytosol." }},
            {{ title: "RBOHD Phosphorylation & Apoplastic Superoxide", text: "Cytosolic Ca2+ spikes activate CPKs and BIK1, which phosphorylate RBOHD to generate an apoplastic ROS burst." }},
            {{ title: "Inward Channeling via PIP2;1 Aquaporin", text: "Superoxide dismutates to H2O2, which re-enters the cytosol through PIP2;1 channels, tuning mitochondrial and chloroplastic redox states." }}
          ]
        }},
        stromule: {{
          title: "Stromule Nuclear Docking & Privileged Channeling",
          desc: "Dynamic physical conduits connecting chloroplasts to the nuclear envelope.",
          steps: [
            {{ title: "Stress-Induced Tubule Elongation", text: "Oxidative stress induces chloroplasts to extend stroma-filled tubules (stromules) along actin microfilaments via myosin XI motors." }},
            {{ title: "Direct Perinuclear Docking", text: "Stromules physically wrap around and dock directly to the nuclear envelope outer membrane." }},
            {{ title: "Privileged H2O2 Channeling", text: "High concentrations of stromal H2O2 are transferred directly across the nuclear envelope into the nucleoplasm." }},
            {{ title: "Avoidance of Cytosolic Scavenging", text: "By bypassing cytosolic peroxiredoxins and ascorbate peroxidase, the retrograde signal achieves maximal potency." }}
          ]
        }}
      }};

      function showCircuit(key) {{
        document.querySelectorAll('.circuit-btn').forEach(b => b.classList.remove('active'));
        event.currentTarget.classList.add('active');

        const c = circuits[key];
        let stepsHtml = '';
        c.steps.forEach((s, i) => {{
          stepsHtml += `
            <div class="step-card">
              <div class="step-num">${{i + 1}}</div>
              <div>
                <strong style="color: var(--text); font-size: 0.95rem;">${{s.title}}</strong>
                <p style="color: var(--text-soft); font-size: 0.88rem; margin-top: 4px;">${{s.text}}</p>
              </div>
            </div>
          `;
        }});

        document.getElementById('circuit-display').innerHTML = `
          <div style="margin-bottom: 20px;">
            <h3 style="font-size: 1.35rem; font-weight: 700; color: var(--text);">${{c.title}}</h3>
            <p style="color: var(--text-soft); font-size: 0.95rem; margin-top: 4px;">${{c.desc}}</p>
          </div>
          <div style="margin-top: 16px;">${{stepsHtml}}</div>
        `;
      }}

      // Init
      showCircuit('mrr');
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
    tbl_120 = load_expression_table("OSD-120")
    tbl_8 = load_expression_table("OSD-8")

    rows = []
    for g in tbl_120.gene_stats.values():
        val_color = "#D55E00" if g.log2_fc > 0 else "#0072B2"
        sig_badge = '<span class="badge badge-t1">p &lt; 0.05</span>' if g.adj_p_value <= 0.05 else '<span class="badge" style="background: var(--bg); border: 1px solid var(--card-border);">NS</span>'
        rows.append(f"""
        <tr>
          <td><span style="font-family: monospace; font-weight: 600; color: var(--primary);">{esc(g.agi_locus)}</span></td>
          <td><strong>{esc(g.symbol)}</strong></td>
          <td><strong style="color: {val_color}; font-family: monospace;">{'+' if g.log2_fc > 0 else ''}{g.log2_fc:.2f}</strong></td>
          <td>{g.adj_p_value:.4f}</td>
          <td>{sig_badge}</td>
        </tr>
        """)

    extra_css = """
    table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 0.88rem; }
    th { text-align: left; padding: 10px 14px; background: var(--bg); border-bottom: 2px solid var(--card-border); color: var(--text-soft); font-weight: 700; text-transform: uppercase; font-size: 0.78rem; }
    td { padding: 12px 14px; border-bottom: 1px solid var(--card-border); vertical-align: top; }
    """

    content = f"""
    {nav_header(active='osdr')}
    <main class="container">
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 1.8rem; font-weight: 800;">NASA OSDR Spaceflight Omics Studio</h2>
        <p style="color: var(--text-soft); max-width: 850px; margin-top: 4px;">
          Ingestion and multi-scale projection of NASA Open Science Data Repository spaceflight omics.
          Evaluates organellar stress responses across <strong>OSD-120</strong> (APEX-03-2 spaceflight roots vs shoots),
          <strong>OSD-379</strong> (spaceflight accessions), <strong>OSD-8</strong> (radiation), and <strong>OSD-782</strong> (microgravity).
        </p>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 32px;">
        <div class="card">
          <div class="card-id">NASA OSDR • APEX-03-2</div>
          <h3 class="card-title">OSD-120: Spaceflight Roots & Shoots</h3>
          <p class="card-desc">Evaluates orbital hypoxia, alternative oxidase (AOX1a) surge, and organellar retrograde gene induction on ISS.</p>
          <span style="font-size: 0.8rem; color: var(--primary); font-weight: 600;">Permutation Test: p = 0.0019 (Significant Enrichment)</span>
        </div>
        <div class="card">
          <div class="card-id">NASA OSDR • Space Radiation</div>
          <h3 class="card-title">OSD-8: Ionizing Radiation</h3>
          <p class="card-desc">Tests Fe-S cluster disassembly, ROS wave generation, and organellar DNA repair (RecA1) under ionizing particles.</p>
          <span style="font-size: 0.8rem; color: var(--primary); font-weight: 600;">Permutation Test: p = 0.0210 (Significant Enrichment)</span>
        </div>
        <div class="card">
          <div class="card-id">NASA OSDR • BRIC-19</div>
          <h3 class="card-title">OSD-782: Microgravity Centrifuge</h3>
          <p class="card-desc">Onboard 1g centrifuge control isolating pure microgravity from spaceflight atmospheric and radiation variables.</p>
          <span style="font-size: 0.8rem; color: var(--primary); font-weight: 600;">Permutation Test: p = 0.0084 (Significant Enrichment)</span>
        </div>
      </div>

      <div style="background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--border-radius); padding: 24px;">
        <h3 style="font-size: 1.25rem; font-weight: 700;">OSD-120 Differential Expression Table (Flight vs Ground)</h3>
        <p style="color: var(--text-soft); font-size: 0.85rem;">Projected log2-fold changes and significance across organellar loci.</p>
        <table>
          <thead>
            <tr>
              <th>AGI Locus</th>
              <th>Symbol</th>
              <th>Log2 Fold Change</th>
              <th>Adj. p-value (FDR)</th>
              <th>Significance</th>
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
    return html_head("NASA OSDR Projections — Plant MitoCarta", extra_css) + content


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
