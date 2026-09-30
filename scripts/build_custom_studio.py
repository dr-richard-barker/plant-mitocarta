"""
Builder functions for Custom Multi-Omics Data Projection Studio
and dedicated NASA OSDR Study Showcase Pages.
"""
import html
import json
from typing import Dict, Any, List

from plant_mitocarta.studio import STUDY_PROFILES
from plant_mitocarta.osdr import CURATED_MULTIOMICS_ENTRIES
from plant_mitocarta.render import render_map_svg


def esc(s):
    return html.escape(str(s), quote=True)


def build_study_showcase_page(study_id, profile, ont, maps, html_head_fn, nav_header_fn, html_footer_fn, build_map_omics_fn):
    rel_map_ids = profile.get("relevant_maps", ["PMM-01", "PMM-02", "PMM-05"])
    maps_by_id = {m.id: m for m in maps}
    default_contrast = profile.get("default_contrast", profile["contrasts"][0]["id"])
    default_map = rel_map_ids[0]

    map_svgs = {}
    map_titles = {}
    for mid in rel_map_ids:
        m = maps_by_id.get(mid)
        if m:
            map_svgs[mid] = render_map_svg(m, theme="light")
            map_titles[mid] = m.title

    contrast_ids = {c["id"] for c in profile["contrasts"]}
    study_entries = []
    for entry in CURATED_MULTIOMICS_ENTRIES:
        matched_contrasts = {cid: entry["contrasts"][cid] for cid in contrast_ids if cid in entry["contrasts"]}
        if matched_contrasts:
            study_entries.append({
                "locus": entry["locus"],
                "symbol": entry["symbol"],
                "compartment": entry["subcompartment_label"],
                "pathway": entry["pathway"],
                "desc": entry["desc"],
                "contrasts": matched_contrasts,
            })

    ranked_by_contrast = {}
    for c in profile["contrasts"]:
        cid = c["id"]
        c_list = []
        for e in study_entries:
            if cid in e["contrasts"]:
                stat = e["contrasts"][cid]
                c_list.append({
                    "locus": e["locus"],
                    "symbol": e["symbol"],
                    "compartment": e["compartment"],
                    "pathway": e["pathway"],
                    "desc": e["desc"],
                    "fc": stat["fc"],
                    "pval": stat["pval"],
                    "sig": stat["sig"],
                })
        c_list.sort(key=lambda x: abs(x["fc"]), reverse=True)
        ranked_by_contrast[cid] = c_list

    map_omics_data = build_map_omics_fn(ont, maps)

    extra_css = """
    .study-hero {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 28px 32px;
      margin-bottom: 28px;
    }
    .study-title {
      font-size: 1.85rem;
      font-weight: 800;
      margin: 8px 0 16px;
      color: var(--text);
      line-height: 1.25;
    }
    .study-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-bottom: 12px;
    }
    .section-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 24px;
      margin-bottom: 28px;
    }
    .finding-card {
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-left: 3px solid var(--accent);
      border-radius: 8px;
      padding: 14px 18px;
      margin-bottom: 12px;
      font-size: 0.9rem;
      line-height: 1.5;
    }
    .map-tab-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
    }
    .contrast-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--card-border);
    }
    .contrast-pill-btn {
      padding: 6px 14px;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 6px;
      border: 1px solid var(--card-border);
      background: var(--bg);
      color: var(--ink);
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .contrast-pill-btn.active {
      background: var(--primary-light);
      border-color: var(--primary);
      color: var(--primary);
    }
    .map-svg-viewport {
      background: #ffffff;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      text-align: center;
    }
    .map-svg-viewport svg {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
    }
    .inspector-box {
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      margin-top: 14px;
      min-height: 72px;
    }
    .study-table-container {
      overflow-x: auto;
      margin-top: 16px;
    }
    table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
    th { text-align: left; padding: 10px 12px; background: var(--surface); border-bottom: 2px solid var(--card-border); color: var(--text-soft); font-weight: 700; text-transform: uppercase; font-size: 0.76rem; }
    td { padding: 10px 12px; border-bottom: 1px solid var(--card-border); vertical-align: middle; }
    tr:hover td { background: var(--surface-2); }
    """

    # Generate Findings HTML
    findings_html = "".join([
        f'<div class="finding-card"><strong>Key Discovery:</strong> {esc(f)}</div>'
        for f in profile.get("key_findings", [])
    ])

    # Generate Citations HTML
    citations_html = "".join([
        f'<li><a href="{esc(url)}" target="_blank" rel="noopener">{esc(title)} &nearr;</a></li>'
        for title, url in profile.get("citations", [])
    ])

    # Generate Map buttons HTML
    map_btns_html = "".join([
        f'<button class="btn btn-sm map-tab-btn {"active" if mid == default_map else ""}" data-map="{mid}" onclick="switchStudyMap(\'{mid}\')">{mid}: {esc(map_titles.get(mid, mid))}</button>'
        for mid in rel_map_ids
    ])

    # Generate Contrast buttons HTML
    contrast_btns_html = "".join([
        f'<button class="contrast-pill-btn {"active" if c["id"] == default_contrast else ""}" data-contrast="{c["id"]}" onclick="switchStudyContrast(\'{c["id"]}\')">{esc(c["name"])} ({esc(c.get("tissue", ""))})</button>'
        for c in profile["contrasts"]
    ])

    # Initial SVG for default map
    initial_svg = map_svgs.get(default_map, "<p>Map not found</p>")

    template = """
    __NAV_HEADER__
    <main class="container">
      <div style="font-size: 0.82rem; color: var(--text-soft); margin-bottom: 12px;">
        <a href="../index.html">Plant MitoCarta</a> &rsaquo;
        <a href="../osdr_projections.html">NASA OSDR Studio</a> &rsaquo;
        <span style="color: var(--ink); font-weight: 600;">__STUDY_ID__</span>
      </div>

      <header class="study-hero">
        <div class="study-badges">
          <span class="badge" style="background: var(--primary-light); color: var(--primary); font-family: var(--font-mono); font-weight: 700; font-size: 0.9rem;">__STUDY_ID__</span>
          <span class="badge" style="background: rgba(16, 110, 84, 0.12); color: #106e54; font-weight: 600;">NASA Open Science Data Repository</span>
          <span class="badge" style="background: var(--surface-2);">__MISSION__</span>
          <span class="badge" style="background: var(--surface-2);">__HARDWARE__</span>
          <span class="badge" style="background: var(--surface-2);">__DURATION__</span>
          <span class="badge" style="background: var(--surface-2);">__ORGANISM__</span>
        </div>
        <h1 class="study-title">__TITLE__</h1>
        <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-top: 16px;">
          <a href="__OSDR_URL__" target="_blank" rel="noopener" class="btn">NASA OSDR Repository &nearr;</a>
          <a id="btn-open-custom-studio" href="../custom_projection.html?study=__STUDY_ID__&contrast=__DEFAULT_CONTRAST__&map=__DEFAULT_MAP__" class="btn primary">Project in Custom Omics Studio &nearr;</a>
        </div>
      </header>

      <!-- SECTION 1: BIOLOGICAL SYNOPSIS & KEY FINDINGS -->
      <section class="section-card">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
          <span style="font-size: 1.25rem;">🔬</span>
          <h2 style="font-size: 1.35rem; font-weight: 800; margin: 0;">Biological Synopsis &amp; Spaceflight Discoveries</h2>
        </div>
        <p style="font-size: 0.96rem; line-height: 1.65; color: var(--ink); margin-bottom: 20px;">
          __SYNOPSIS__
        </p>

        <h3 style="font-size: 1.05rem; font-weight: 700; margin: 18px 0 10px;">Key Biological Insights:</h3>
        <div style="margin-bottom: 20px;">
          __FINDINGS_HTML__
        </div>

        <h3 style="font-size: 1.05rem; font-weight: 700; margin: 18px 0 10px;">Primary Literature &amp; Mission Reports:</h3>
        <ul style="font-size: 0.88rem; line-height: 1.6; margin: 0; padding-left: 20px; color: var(--text-soft);">
          __CITATIONS_HTML__
        </ul>
      </section>

      <!-- SECTION 2: INTERACTIVE PRE-PROJECTED PATHWAY MAPS -->
      <section class="section-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; margin-bottom: 16px;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.25rem;">🗺️</span>
              <h2 style="font-size: 1.35rem; font-weight: 800; margin: 0;">Pre-Projected Organellar Pathway Maps</h2>
            </div>
            <p style="color: var(--text-soft); font-size: 0.88rem; margin: 4px 0 0;">
              High-resolution vector maps showing spaceflight log2 fold-changes dynamically color-coded with WCAG AAA luminance-adaptive text contrast.
            </p>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-sm" onclick="exportStudySvg()"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" style="display:inline-block; vertical-align:middle; margin-right:4px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>Download Recolored SVG</button>
          </div>
        </div>

        <div class="map-tab-bar">
          __MAP_BTNS_HTML__
        </div>

        <div class="contrast-bar">
          <span style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--text-soft); margin-right: 4px;">Contrasts:</span>
          __CONTRAST_BTNS_HTML__
        </div>

        <!-- SVG Map Container -->
        <div class="map-svg-viewport" id="study-svg-container">
          __INITIAL_SVG__
        </div>

        <!-- Node Inspector Drawer -->
        <div class="inspector-box" id="study-node-inspector">
          <div style="color: var(--text-soft); font-size: 0.86rem; text-align: center; padding: 12px 0;">
            Hover over or click any pathway node in the map above to inspect locus ID, fold-change, significance, and biological role.
          </div>
        </div>
      </section>

      <!-- SECTION 3: RANKED ORGANELLAR RESPONDERS -->
      <section class="section-card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; margin-bottom: 16px;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.25rem;">📊</span>
              <h2 style="font-size: 1.35rem; font-weight: 800; margin: 0;">Ranked Organellar Responders</h2>
            </div>
            <p style="color: var(--text-soft); font-size: 0.88rem; margin: 4px 0 0;">
              All assayed mitochondrial, chloroplast, and peroxisomal loci in __STUDY_ID__, ranked by absolute fold-change.
            </p>
          </div>
          <div style="display: flex; align-items: center; gap: 12px;">
            <input type="text" id="study-table-search" placeholder="Search locus, symbol, role..." oninput="renderStudyTable()" style="padding: 6px 12px; font-size: 0.84rem; border: 1px solid var(--card-border); border-radius: 6px; background: var(--bg); color: var(--ink); width: 220px;">
            <span class="badge" id="study-table-count" style="background: var(--surface-2); font-weight: 700;"></span>
          </div>
        </div>

        <div style="display: flex; gap: 6px; margin-bottom: 14px;">
          <button class="btn btn-sm study-comp-filter active" data-comp="all" onclick="filterStudyComp('all')">All Responders</button>
          <button class="btn btn-sm study-comp-filter" data-comp="mito" onclick="filterStudyComp('mito')">Mitochondrion</button>
          <button class="btn btn-sm study-comp-filter" data-comp="chloro" onclick="filterStudyComp('chloro')">Chloroplast</button>
          <button class="btn btn-sm study-comp-filter" data-comp="perox" onclick="filterStudyComp('perox')">Peroxisome</button>
        </div>

        <div class="study-table-container">
          <table>
            <thead>
              <tr>
                <th style="width: 40px;">Rank</th>
                <th>AGI Locus</th>
                <th>Symbol</th>
                <th>Subcompartment</th>
                <th style="width: 140px;">Log2 Fold-Change</th>
                <th>p-value</th>
                <th>Pathway / Biological Role</th>
                <th style="text-align: right;">Action</th>
              </tr>
            </thead>
            <tbody id="study-table-body">
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <script>
    const studyMapSvgs = __STUDY_MAP_SVGS_JSON__;
    const studyRankedData = __STUDY_RANKED_JSON__;
    const studyContrasts = __STUDY_CONTRASTS_JSON__;
    const studyProfile = __STUDY_PROFILE_JSON__;
    const mapOmicsData = __MAP_OMICS_JSON__;

    let activeMapId = '__DEFAULT_MAP__';
    let activeContrastId = '__DEFAULT_CONTRAST__';
    let activeCompFilter = 'all';

    function switchStudyMap(mapId) {
      activeMapId = mapId;
      document.querySelectorAll('.map-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-map') === mapId);
      });
      const container = document.getElementById('study-svg-container');
      if (container && studyMapSvgs[mapId]) {
        container.innerHTML = studyMapSvgs[mapId];
        applyStudyProjection();
        attachStudyNodeEvents();
      }
      updateCtaLink();
    }

    function switchStudyContrast(contrastId) {
      activeContrastId = contrastId;
      document.querySelectorAll('.contrast-pill-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-contrast') === contrastId);
      });
      applyStudyProjection();
      renderStudyTable();
      updateCtaLink();
    }

    function updateCtaLink() {
      const ctaBtn = document.getElementById('btn-open-custom-studio');
      if (ctaBtn) {
        ctaBtn.href = '../custom_projection.html?study=' + studyProfile.id + '&contrast=' + activeContrastId + '&map=' + activeMapId;
      }
    }

    function filterStudyComp(comp) {
      activeCompFilter = comp;
      document.querySelectorAll('.study-comp-filter').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-comp') === comp);
      });
      renderStudyTable();
    }

    function applyStudyProjection() {
      const container = document.getElementById('study-svg-container');
      if (!container) return;
      const currentRanked = studyRankedData[activeContrastId] || [];
      const locusMap = {};
      const symbolMap = {};
      currentRanked.forEach(r => {
        locusMap[r.locus] = r;
        if (r.symbol) symbolMap[r.symbol.toUpperCase()] = r;
      });

      const nodeGroups = container.querySelectorAll('.pmc-node-group');
      nodeGroups.forEach(group => {
        const nodeId = group.getAttribute('data-node-id') || group.id.replace(/^node-/, '');
        const rect = group.querySelector('.pmc-node');
        const labels = group.querySelectorAll('.pmc-label, .pmc-sub');
        let statPill = group.querySelector('.pmc-omics-stat-pill');

        const mData = mapOmicsData[activeMapId] || {};
        const nInfo = mData[nodeId];
        let match = null;
        if (nInfo) {
          if (locusMap[nInfo.locus]) match = locusMap[nInfo.locus];
          else if (nInfo.all_loci) {
            for (let l of nInfo.all_loci) {
              if (locusMap[l]) { match = locusMap[l]; break; }
            }
          }
          if (!match && nInfo.symbol && symbolMap[nInfo.symbol.toUpperCase()]) {
            match = symbolMap[nInfo.symbol.toUpperCase()];
          }
        }
        if (!match && symbolMap[nodeId.toUpperCase()]) {
          match = symbolMap[nodeId.toUpperCase()];
        }

        if (match) {
          const maxFC = 2.0;
          const clamped = Math.max(-maxFC, Math.min(maxFC, match.fc));
          const norm = (clamped + maxFC) / (2 * maxFC);
          let r, g, b;
          if (norm < 0.5) {
            const t = norm / 0.5;
            r = Math.round(37 + (255 - 37) * t);
            g = Math.round(99 + (255 - 99) * t);
            b = Math.round(235 + (255 - 235) * t);
          } else {
            const t = (norm - 0.5) / 0.5;
            r = Math.round(255 + (220 - 255) * t);
            g = Math.round(255 + (38 - 255) * t);
            b = Math.round(255 + (38 - 255) * t);
          }
          const hex = '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
          if (rect) rect.style.fill = hex;

          const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
          const textFill = lum < 0.48 ? '#f8fafc' : '#111827';
          labels.forEach(l => l.style.fill = textFill);

          const rx = parseFloat(rect ? rect.getAttribute('x') : 0) + 6;
          const ry = parseFloat(rect ? rect.getAttribute('y') : 0) + 6;
          if (!statPill && rect) {
            statPill = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            statPill.setAttribute('class', 'pmc-omics-stat-pill');
            statPill.innerHTML = `
              <rect x="${rx}" y="${ry}" width="42" height="13" rx="3" fill="#0f172a" opacity="0.88" />
              <text x="${rx + 21}" y="${ry + 9.5}" font-size="9px" font-weight="700" fill="#38bdf8" text-anchor="middle">
                ${match.fc >= 0 ? '+' : ''}${match.fc.toFixed(2)}${match.sig ? '*' : ''}
              </text>
            `;
            group.appendChild(statPill);
          } else if (statPill) {
            statPill.innerHTML = `
              <rect x="${rx}" y="${ry}" width="42" height="13" rx="3" fill="#0f172a" opacity="0.88" />
              <text x="${rx + 21}" y="${ry + 9.5}" font-size="9px" font-weight="700" fill="#38bdf8" text-anchor="middle">
                ${match.fc >= 0 ? '+' : ''}${match.fc.toFixed(2)}${match.sig ? '*' : ''}
              </text>
            `;
          }
          group.style.opacity = '1.0';
          group.style.filter = 'none';
        } else {
          if (rect) rect.style.fill = '';
          labels.forEach(l => l.style.fill = '');
          if (statPill) statPill.remove();
          group.style.opacity = '0.9';
        }
      });
    }

    function attachStudyNodeEvents() {
      const container = document.getElementById('study-svg-container');
      if (!container) return;
      const nodeGroups = container.querySelectorAll('.pmc-node-group');
      nodeGroups.forEach(group => {
        group.style.cursor = 'pointer';
        group.addEventListener('mouseenter', () => inspectStudyNode(group));
        group.addEventListener('click', () => inspectStudyNode(group));
      });
    }

    function inspectStudyNode(group) {
      const nodeId = group.getAttribute('data-node-id') || group.id.replace(/^node-/, '');
      const mData = mapOmicsData[activeMapId] || {};
      const nInfo = mData[nodeId];
      const currentRanked = studyRankedData[activeContrastId] || [];
      const locusMap = {};
      currentRanked.forEach(r => locusMap[r.locus] = r);

      let match = nInfo && locusMap[nInfo.locus] ? locusMap[nInfo.locus] : null;
      const drawer = document.getElementById('study-node-inspector');
      if (!drawer) return;

      const title = nInfo ? nInfo.title : nodeId;
      const locus = match ? match.locus : (nInfo ? nInfo.locus : 'N/A');
      const symbol = match ? match.symbol : (nInfo ? nInfo.symbol : nodeId);
      const comp = match ? match.compartment : (nInfo ? nInfo.compartment : 'Organellar');
      const fcText = match ? (match.fc >= 0 ? '+' : '') + match.fc.toFixed(2) + ' log2FC' : 'Baseline / Unassayed';
      const pvalText = match ? 'p = ' + match.pval.toExponential(2) + (match.sig ? ' (Significant)' : '') : 'N/A';
      const desc = match ? match.desc : (nInfo ? nInfo.desc : 'Constituent pathway node.');

      const fcColor = match ? (match.fc > 0 ? '#dc2626' : (match.fc < 0 ? '#2563eb' : 'var(--text)')) : 'var(--text-soft)';

      drawer.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
          <div>
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
              <h4 style="font-size:1.1rem; font-weight:800; margin:0;">${title}</h4>
              <span class="badge" style="background:var(--primary-light); color:var(--primary); font-family:var(--font-mono); font-weight:700;">${symbol}</span>
              <span class="badge" style="background:var(--surface-2); font-family:var(--font-mono); font-size:0.75rem;">${locus}</span>
            </div>
            <p style="margin:2px 0 6px; font-size:0.84rem; color:var(--text-soft);">${comp}</p>
            <p style="margin:0; font-size:0.86rem; line-height:1.4; max-width:800px;">${desc}</p>
          </div>
          <div style="text-align:right; min-width:180px;">
            <div style="font-size:1.25rem; font-weight:800; color:${fcColor}; font-family:var(--font-mono);">${fcText}</div>
            <div style="font-size:0.78rem; color:var(--text-soft); margin-top:2px;">${pvalText}</div>
            ${match ? `<a href="../custom_projection.html?study=${studyProfile.id}&contrast=${activeContrastId}&locus=${locus}&map=${activeMapId}" class="btn btn-sm primary" style="margin-top:8px; font-size:0.76rem; padding:4px 10px;">Project in Studio &nearr;</a>` : ''}
          </div>
        </div>
      `;
    }

    function renderStudyTable() {
      const tbody = document.getElementById('study-table-body');
      if (!tbody) return;
      const currentRanked = studyRankedData[activeContrastId] || [];
      const query = (document.getElementById('study-table-search')?.value || '').toLowerCase().trim();

      let filtered = currentRanked.filter(r => {
        if (query) {
          const txt = (r.locus + ' ' + r.symbol + ' ' + r.compartment + ' ' + r.pathway + ' ' + r.desc).toLowerCase();
          if (!txt.includes(query)) return false;
        }
        if (activeCompFilter !== 'all') {
          const c = r.compartment.toLowerCase();
          if (activeCompFilter === 'mito' && !c.includes('mito')) return false;
          if (activeCompFilter === 'chloro' && !c.includes('chloro') && !c.includes('thylakoid') && !c.includes('plastid')) return false;
          if (activeCompFilter === 'perox' && !c.includes('perox')) return false;
        }
        return true;
      });

      const countEl = document.getElementById('study-table-count');
      if (countEl) countEl.textContent = filtered.length + ' Loci';

      tbody.innerHTML = filtered.map((r, i) => {
        const isUp = r.fc > 0;
        const barWidth = Math.min(100, Math.round(Math.abs(r.fc) / 3.0 * 100));
        const barColor = isUp ? '#dc2626' : '#2563eb';
        const sign = isUp ? '+' : '';
        return `
          <tr>
            <td style="font-weight:700; color:var(--text-soft); font-size:0.8rem; width:40px;">#${i + 1}</td>
            <td>
              <span style="font-family:var(--font-mono); font-weight:700; color:var(--primary);">${r.locus}</span>
            </td>
            <td><strong>${r.symbol}</strong></td>
            <td><span class="badge" style="background:var(--surface-2); font-size:0.75rem;">${r.compartment}</span></td>
            <td style="width:140px;">
              <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-family:var(--font-mono); font-weight:700; font-size:0.82rem; color:${barColor}; min-width:44px;">${sign}${r.fc.toFixed(2)}</span>
                <div style="flex:1; height:6px; background:var(--surface-2); border-radius:3px; overflow:hidden;">
                  <div style="width:${barWidth}%; height:100%; background:${barColor}; border-radius:3px;"></div>
                </div>
              </div>
            </td>
            <td style="font-family:var(--font-mono); font-size:0.78rem;">${r.pval.toExponential(2)}${r.sig ? ' *' : ''}</td>
            <td style="font-size:0.82rem; color:var(--text-soft); max-width:240px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${r.desc}">${r.pathway || r.desc}</td>
            <td style="text-align:right;">
              <a href="../custom_projection.html?study=${studyProfile.id}&contrast=${activeContrastId}&locus=${r.locus}&map=${activeMapId}" class="btn btn-sm" style="font-size:0.75rem; padding:3px 8px;">Project &nearr;</a>
            </td>
          </tr>
        `;
      }).join('');
    }

    function exportStudySvg() {
      const container = document.getElementById('study-svg-container');
      const svg = container?.querySelector('svg');
      if (!svg) return;
      const clone = svg.cloneNode(true);
      const serializer = new XMLSerializer();
      const source = '<?xml version="1.0" standalone="no"?>\\r\\n' + serializer.serializeToString(clone);
      const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = studyProfile.id + '_' + activeMapId + '_' + activeContrastId + '.svg';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    // Initialize study showcase
    applyStudyProjection();
    attachStudyNodeEvents();
    renderStudyTable();
    </script>
    __HTML_FOOTER__
    """

    content = (
        template.replace("__NAV_HEADER__", nav_header_fn(active="osdr", depth=1))
        .replace("__HTML_FOOTER__", html_footer_fn())
        .replace("__STUDY_ID__", esc(study_id))
        .replace("__TITLE__", esc(profile["title"]))
        .replace("__MISSION__", esc(profile.get("mission", "")))
        .replace("__HARDWARE__", esc(profile.get("hardware", "")))
        .replace("__DURATION__", esc(profile.get("duration", "")))
        .replace("__ORGANISM__", esc(profile.get("organism", "")))
        .replace("__OSDR_URL__", esc(profile.get("osdr_url", "https://osdr.nasa.gov")))
        .replace("__DEFAULT_CONTRAST__", esc(default_contrast))
        .replace("__DEFAULT_MAP__", esc(default_map))
        .replace("__SYNOPSIS__", esc(profile.get("synopsis", "")))
        .replace("__FINDINGS_HTML__", findings_html)
        .replace("__CITATIONS_HTML__", citations_html)
        .replace("__MAP_BTNS_HTML__", map_btns_html)
        .replace("__CONTRAST_BTNS_HTML__", contrast_btns_html)
        .replace("__INITIAL_SVG__", initial_svg)
        .replace("__STUDY_MAP_SVGS_JSON__", json.dumps(map_svgs))
        .replace("__STUDY_RANKED_JSON__", json.dumps(ranked_by_contrast))
        .replace("__STUDY_CONTRASTS_JSON__", json.dumps(profile["contrasts"]))
        .replace("__STUDY_PROFILE_JSON__", json.dumps(profile))
        .replace("__MAP_OMICS_JSON__", json.dumps(map_omics_data))
    )

    return html_head_fn(f"{study_id}: {profile['title']} — Plant MitoCarta", extra_css) + content


def build_custom_projection_page(ont, maps, html_head_fn, nav_header_fn, html_footer_fn, build_map_omics_fn):
    catalog = {}
    for ent in ont.all_entities():
        for locus in ent.agi_loci:
            catalog[locus] = {
                "locus": locus,
                "symbol": ent.label,
                "compartment": ent.compartment,
                "pmco_id": ent.id,
                "desc": ent.description,
            }

    osdr_presets = {}
    contrasts = ["osd120_root", "osd120_shoot", "osd427_protein", "osd37", "osd782", "osd8"]
    for c in contrasts:
        lines = ["locus,log2fc,pvalue,symbol,compartment"]
        for entry in CURATED_MULTIOMICS_ENTRIES:
            if c in entry["contrasts"]:
                stat = entry["contrasts"][c]
                lines.append(f"{entry['locus']},{stat['fc']},{stat['pval']},{entry['symbol']},{entry['subcompartment_label']}")
        osdr_presets[c] = "\n".join(lines)

    map_svgs = {}
    map_metadata = {}
    for m in maps:
        map_svgs[m.id] = render_map_svg(m, theme="light")
        map_metadata[m.id] = {
            "id": m.id,
            "title": m.title,
            "description": getattr(m, "caption", m.title),
            "node_count": len(m.nodes),
        }

    map_omics_data = build_map_omics_fn(ont, maps)

    extra_css = """
    .studio-header {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 28px 32px;
      margin-bottom: 24px;
    }
    .studio-grid-2col {
      display: grid;
      grid-template-columns: 440px 1fr;
      gap: 24px;
      margin-bottom: 32px;
    }
    @media (max-width: 1024px) {
      .studio-grid-2col { grid-template-columns: 1fr; }
    }
    .panel-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 20px;
      margin-bottom: 20px;
    }
    .panel-title {
      font-size: 1.05rem;
      font-weight: 700;
      margin: 0 0 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .dropzone {
      border: 2px dashed var(--line);
      border-radius: 8px;
      padding: 16px;
      text-align: center;
      cursor: pointer;
      background: var(--surface);
      transition: all 0.15s ease;
      margin-bottom: 12px;
    }
    .dropzone:hover, .dropzone.dragover {
      border-color: var(--primary);
      background: var(--primary-light);
    }
    .telemetry-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-bottom: 16px;
    }
    .telemetry-card {
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 10px;
      text-align: center;
    }
    .telemetry-val {
      font-size: 1.35rem;
      font-weight: 800;
      font-family: var(--font-mono);
      color: var(--text);
    }
    .telemetry-lbl {
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--text-soft);
      text-transform: uppercase;
      margin-top: 2px;
    }
    .canvas-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--border-radius);
      padding: 20px;
    }
    .canvas-viewport {
      background: #ffffff;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      text-align: center;
      min-height: 520px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .canvas-viewport svg {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
    }
    .gradient-legend {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-radius: 6px;
      margin-top: 14px;
      font-size: 0.8rem;
    }
    .legend-bar {
      flex: 1;
      height: 12px;
      border-radius: 3px;
      background: linear-gradient(90deg, #2563eb, #ffffff, #dc2626);
    }
    .preset-chip-btn {
      padding: 5px 10px;
      font-size: 0.78rem;
      font-weight: 600;
      border-radius: 6px;
      border: 1px solid var(--card-border);
      background: var(--surface);
      color: var(--ink);
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .preset-chip-btn:hover {
      background: var(--surface-2);
      border-color: var(--accent);
    }
    .preset-chip-btn.active {
      background: var(--primary-light);
      border-color: var(--primary);
      color: var(--primary);
    }
    .inspector-box {
      background: var(--surface);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 16px;
      margin-top: 14px;
      min-height: 72px;
    }
    table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
    th { text-align: left; padding: 10px 12px; background: var(--surface); border-bottom: 2px solid var(--card-border); color: var(--text-soft); font-weight: 700; text-transform: uppercase; font-size: 0.76rem; }
    td { padding: 10px 12px; border-bottom: 1px solid var(--card-border); vertical-align: middle; }
    tr:hover td { background: var(--surface-2); }
    """

    map_options_html = "".join([
        f'<option value="{m.id}">{m.id}: {esc(m.title)}</option>'
        for m in maps
    ])

    template = """
    __NAV_HEADER__
    <main class="container">
      <header class="studio-header">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
          <span style="display: inline-flex; align-items: center; justify-content: center; width: 34px; height: 34px; border-radius: 8px; background: var(--primary-light); color: var(--primary); font-size: 1.25rem;">🧪</span>
          <h1 style="font-size: 1.85rem; font-weight: 800; margin: 0;">Custom Multi-Omics Data Projection Studio</h1>
        </div>
        <p style="color: var(--text-soft); max-width: 960px; margin: 0; line-height: 1.55;">
          Upload, paste, or query <strong>NASA Open Science Data Repository (OSDR)</strong> spaceflight datasets or your own experimental multi-omics tables.
          Dynamically projects RNA-Seq, microarray, or proteomics log2 fold-changes onto all 10 plant organellar pathway maps with automatic WCAG AAA luminance-adaptive text contrast, significance filtering, and vector SVG/PNG export.
        </p>
      </header>

      <div class="studio-grid-2col">
        <!-- LEFT COLUMN: CONTROLS & INPUT -->
        <div>
          <!-- PANEL 1: DATA INGESTION & PRESETS -->
          <div class="panel-card">
            <h3 class="panel-title">
              <span>📂</span> 1. Ingest Multi-Omics Data
            </h3>

            <!-- 1-Click NASA OSDR Presets -->
            <div style="margin-bottom: 14px;">
              <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--text-soft); margin-bottom: 6px;">1-Click Spaceflight Presets:</div>
              <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                <button class="preset-chip-btn active" onclick="loadPreset('osd120_root')">OSD-120 Roots (ISS)</button>
                <button class="preset-chip-btn" onclick="loadPreset('osd120_shoot')">OSD-120 Shoots (ISS)</button>
                <button class="preset-chip-btn" onclick="loadPreset('osd427_protein')">OSD-427 Proteomics</button>
                <button class="preset-chip-btn" onclick="loadPreset('osd37')">OSD-37 Seedlings</button>
                <button class="preset-chip-btn" onclick="loadPreset('osd782')">OSD-782 Centrifuge</button>
                <button class="preset-chip-btn" onclick="loadPreset('osd8')">OSD-8 Cosmic Radiation</button>
                <button class="preset-chip-btn" onclick="loadSyntheticData()">Synthetic Random</button>
                <button class="preset-chip-btn" onclick="clearData()">Clear</button>
              </div>
            </div>

            <!-- NASA OSDR API Query -->
            <div style="margin-bottom: 14px; padding: 12px; background: var(--surface); border: 1px solid var(--card-border); border-radius: 6px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--text-soft);">NASA OSDR API Live Query:</span>
                <span id="osdr-api-status" style="font-size: 0.74rem; font-weight: 600; color: var(--primary);">Ready</span>
              </div>
              <div style="display: flex; gap: 8px;">
                <input type="text" id="osdr-api-input" placeholder="e.g. OSD-120, OSD-427, OSD-37" style="flex: 1; padding: 6px 10px; font-size: 0.84rem; border: 1px solid var(--card-border); border-radius: 6px; background: var(--bg); color: var(--ink);">
                <button class="btn btn-sm primary" id="btn-query-osdr" onclick="queryOsdrApi()">Query OSDR</button>
              </div>
            </div>

            <!-- File Drag and Drop -->
            <div class="dropzone" id="file-drop-zone" onclick="document.getElementById('file-upload-input').click()">
              <input type="file" id="file-upload-input" accept=".csv,.tsv,.txt,.json" style="display: none;" onchange="handleFileUpload(event)">
              <div style="font-size: 1.2rem; margin-bottom: 4px;">📥</div>
              <div style="font-size: 0.84rem; font-weight: 600; color: var(--ink);">Drag &amp; drop CSV/TSV/JSON file or click to browse</div>
              <div style="font-size: 0.74rem; color: var(--text-soft); margin-top: 2px;">Accepts AGI locus, log2fc, and p-value columns</div>
            </div>

            <!-- Textarea -->
            <div style="margin-bottom: 12px;">
              <label for="custom-data-input" style="display: flex; justify-content: space-between; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--text-soft); margin-bottom: 4px;">
                <span>Or Paste Tabular Data:</span>
                <span style="font-family: var(--font-mono); font-size: 0.72rem;">CSV / TSV format</span>
              </label>
              <textarea id="custom-data-input" rows="8" style="width: 100%; box-sizing: border-box; font-family: var(--font-mono); font-size: 0.8rem; padding: 10px; border: 1px solid var(--card-border); border-radius: 6px; background: var(--bg); color: var(--ink); line-height: 1.4; resize: vertical;" placeholder="locus,log2fc,pvalue,symbol&#10;AT3G22370,2.42,0.0001,AOX1a&#10;AT1G07180,1.88,0.002,NDA1&#10;AT5G08530,-1.25,0.004,NDUFS4&#10;AT1G47260,-0.85,0.03,CAL1"></textarea>
            </div>

            <button id="btn-project-data" class="btn primary" style="width: 100%; justify-content: center; padding: 10px; font-weight: 700;" onclick="projectData()">⚡ Parse &amp; Project Data onto Map</button>
          </div>

          <!-- PANEL 2: TELEMETRY & INGESTION STATS -->
          <div class="panel-card">
            <h3 class="panel-title">
              <span>📈</span> 2. Ingestion Telemetry HUD
            </h3>
            <div class="telemetry-grid">
              <div class="telemetry-card">
                <div class="telemetry-val" id="hud-total-rows">0</div>
                <div class="telemetry-lbl">Input Rows</div>
              </div>
              <div class="telemetry-card">
                <div class="telemetry-val" id="hud-matched-loci" style="color: var(--primary);">0</div>
                <div class="telemetry-lbl">Catalog Loci</div>
              </div>
              <div class="telemetry-card">
                <div class="telemetry-val" id="hud-active-nodes" style="color: #106e54;">0</div>
                <div class="telemetry-lbl">Map Nodes</div>
              </div>
              <div class="telemetry-card">
                <div class="telemetry-val" id="hud-up-count" style="color: #dc2626;">0</div>
                <div class="telemetry-lbl">Induced (&gt;0.5)</div>
              </div>
              <div class="telemetry-card">
                <div class="telemetry-val" id="hud-down-count" style="color: #2563eb;">0</div>
                <div class="telemetry-lbl">Repressed (&lt;-0.5)</div>
              </div>
              <div class="telemetry-card">
                <div class="telemetry-val" id="hud-sig-count" style="color: #d97706;">0</div>
                <div class="telemetry-lbl">Sig (p&lt;0.05)</div>
              </div>
            </div>

            <!-- Visualization Settings -->
            <div style="padding-top: 14px; border-top: 1px solid var(--card-border);">
              <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px;">
                  <span>Dynamic Fold-Change Scale:</span>
                  <span id="val-fc-range" style="font-family: var(--font-mono); color: var(--primary);">&plusmn;2.00 log2FC</span>
                </div>
                <input type="range" id="slider-fc-range" min="0.5" max="5.0" step="0.1" value="2.0" style="width: 100%;" oninput="updateFcSlider(this.value)">
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                <div>
                  <label for="select-sig-filter" style="display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 4px;">Significance Filter:</label>
                  <select id="select-sig-filter" onchange="applyProjection()" style="width: 100%; padding: 6px; font-size: 0.8rem; border: 1px solid var(--card-border); border-radius: 6px; background: var(--bg); color: var(--ink);">
                    <option value="none">Show All</option>
                    <option value="p005">Filter p &lt; 0.05</option>
                    <option value="p001">Filter p &lt; 0.01</option>
                  </select>
                </div>
                <div>
                  <label for="select-palette" style="display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 4px;">Color Palette:</label>
                  <select id="select-palette" onchange="applyProjection()" style="width: 100%; padding: 6px; font-size: 0.8rem; border: 1px solid var(--card-border); border-radius: 6px; background: var(--bg); color: var(--ink);">
                    <option value="red-blue">Blue &bull; White &bull; Red</option>
                    <option value="orange-blue">Blue &bull; White &bull; Orange (Safe)</option>
                  </select>
                </div>
              </div>

              <div>
                <label for="select-contrast-mode" style="display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 4px;">Text Contrast Mode:</label>
                <select id="select-contrast-mode" onchange="applyProjection()" style="width: 100%; padding: 6px; font-size: 0.8rem; border: 1px solid var(--card-border); border-radius: 6px; background: var(--bg); color: var(--ink);">
                  <option value="adaptive">Auto WCAG AAA Luminance-Adaptive</option>
                  <option value="white">Crisp White Only</option>
                  <option value="dark">Charcoal Black Only</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT COLUMN: INTERACTIVE MAP CANVAS -->
        <div>
          <div class="canvas-card">
            <!-- Map Toolbar -->
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 14px;">
              <div style="display: flex; align-items: center; gap: 8px; flex: 1; min-width: 260px;">
                <label for="select-active-map" style="font-size: 0.84rem; font-weight: 700; white-space: nowrap;">Active Map:</label>
                <select id="select-active-map" onchange="switchStudioMap(this.value)" style="padding: 6px 10px; font-size: 0.84rem; font-weight: 600; border: 1px solid var(--card-border); border-radius: 6px; background: var(--bg); color: var(--ink); flex: 1;">
                  __MAP_OPTIONS_HTML__
                </select>
              </div>

              <div style="display: flex; gap: 8px;">
                <button class="btn btn-sm" id="btn-export-svg" onclick="exportStudioSvg()"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" style="display:inline-block; vertical-align:middle; margin-right:4px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>Export SVG</button>
                <button class="btn btn-sm" id="btn-export-png" onclick="exportStudioPng()"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" style="display:inline-block; vertical-align:middle; margin-right:4px;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>Export PNG</button>
                <button class="btn btn-sm" id="btn-export-csv" onclick="exportStudioCsv()"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" style="display:inline-block; vertical-align:middle; margin-right:4px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>Export CSV</button>
              </div>
            </div>

            <!-- SVG Canvas Viewport -->
            <div class="canvas-viewport" id="studio-canvas-container">
            </div>

            <!-- Gradient Legend -->
            <div class="gradient-legend">
              <span id="legend-min-lbl" style="font-family: var(--font-mono); font-weight: 700; color: #2563eb;">-2.00</span>
              <div class="legend-bar" id="legend-gradient-bar"></div>
              <span id="legend-max-lbl" style="font-family: var(--font-mono); font-weight: 700; color: #dc2626;">+2.00</span>
              <span style="font-size: 0.76rem; color: var(--text-soft); margin-left: 8px;">* indicates p &lt; 0.05</span>
            </div>

            <!-- Interactive Inspector Drawer -->
            <div class="inspector-box" id="node-inspector-drawer">
              <div style="color: var(--text-soft); font-size: 0.86rem; text-align: center; padding: 12px 0;">
                Hover over or click any pathway node in the map above to inspect locus ID, fold-change, significance, and biological role.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- SECTION 3: MATCHED LOCI TABLE -->
      <section class="panel-card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; margin-bottom: 16px;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.2rem;">📋</span>
              <h3 style="font-size: 1.25rem; font-weight: 800; margin: 0;">Matched Loci &amp; Data Inspection Table</h3>
            </div>
            <p style="color: var(--text-soft); font-size: 0.88rem; margin: 4px 0 0;">
              Examine parsed records, match status against the Plant MitoCarta catalog, and corresponding active map nodes.
            </p>
          </div>
          <div style="display: flex; align-items: center; gap: 12px;">
            <input type="text" id="table-search-input" placeholder="Filter locus, symbol, map..." oninput="renderTable()" style="padding: 6px 12px; font-size: 0.84rem; border: 1px solid var(--card-border); border-radius: 6px; background: var(--bg); color: var(--ink); width: 220px;">
            <span class="badge" id="table-row-count" style="background: var(--surface-2); font-weight: 700;">0 Rows</span>
          </div>
        </div>

        <div style="overflow-x: auto;">
          <table>
            <thead>
              <tr>
                <th>AGI Locus</th>
                <th>Symbol</th>
                <th>Subcompartment</th>
                <th style="width: 140px;">Log2 Fold-Change</th>
                <th>p-value</th>
                <th>Significance</th>
                <th>Active Map Match</th>
                <th style="text-align: right;">Action</th>
              </tr>
            </thead>
            <tbody id="matched-loci-tbody">
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <script>
    const catalogData = __CATALOG_JSON__;
    const osdrPresets = __PRESETS_JSON__;
    const mapSvgs = __MAP_SVGS_JSON__;
    const mapMetadata = __MAP_METADATA_JSON__;
    const mapOmicsData = __MAP_OMICS_JSON__;

    let currentMapId = 'PMM-01';
    let currentParsedRecords = [];
    let maxFcScale = 2.0;

    function initStudio() {
      // Check URL parameters
      const urlParams = new URLSearchParams(window.location.search);
      const studyParam = urlParams.get('study');
      const contrastParam = urlParams.get('contrast');
      const mapParam = urlParams.get('map');
      const locusParam = urlParams.get('locus');

      if (mapParam && mapSvgs[mapParam]) {
        currentMapId = mapParam;
        document.getElementById('select-active-map').value = currentMapId;
      }

      if (studyParam) {
        let presetKey = contrastParam;
        if (!presetKey) {
          const s = studyParam.toUpperCase();
          if (s === 'OSD-120') presetKey = 'osd120_root';
          else if (s === 'OSD-427') presetKey = 'osd427_protein';
          else if (s === 'OSD-37') presetKey = 'osd37';
          else if (s === 'OSD-782') presetKey = 'osd782';
          else if (s === 'OSD-8') presetKey = 'osd8';
          else presetKey = studyParam.toLowerCase().replace('-', '_');
        }
        if (osdrPresets[presetKey]) {
          loadPreset(presetKey);
        } else {
          loadPreset('osd120_root');
        }
      } else {
        loadPreset('osd120_root');
      }

      if (locusParam) {
        setTimeout(() => highlightLocus(locusParam), 300);
      }
    }

    function switchStudioMap(mapId) {
      currentMapId = mapId;
      renderCurrentMap();
      applyProjection();
    }

    function renderCurrentMap() {
      const container = document.getElementById('studio-canvas-container');
      if (container && mapSvgs[currentMapId]) {
        container.innerHTML = mapSvgs[currentMapId];
        attachCanvasEvents();
      }
    }

    function loadPreset(presetKey) {
      document.querySelectorAll('.preset-chip-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('onclick')?.includes(presetKey));
      });
      const textarea = document.getElementById('custom-data-input');
      if (textarea && osdrPresets[presetKey]) {
        textarea.value = osdrPresets[presetKey];
        projectData();
      }
    }

    function loadSyntheticData() {
      const loci = Object.keys(catalogData);
      const lines = ['locus,log2fc,pvalue,symbol,compartment'];
      loci.forEach(l => {
        const ent = catalogData[l];
        const fc = (Math.random() * 4.0 - 2.0).toFixed(2);
        const pval = Math.random() < 0.65 ? (Math.random() * 0.045).toExponential(3) : (Math.random() * 0.4 + 0.05).toExponential(3);
        lines.append ? lines.push(`${l},${fc},${pval},${ent.symbol},${ent.compartment}`) : lines.push(l + ',' + fc + ',' + pval + ',' + ent.symbol + ',' + ent.compartment);
      });
      document.getElementById('custom-data-input').value = lines.join('\\n');
      projectData();
    }

    function clearData() {
      document.getElementById('custom-data-input').value = '';
      currentParsedRecords = [];
      updateTelemetry([]);
      applyProjection();
      renderTable();
    }

    function handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(e) {
        document.getElementById('custom-data-input').value = e.target.result;
        projectData();
      };
      reader.readAsText(file);
    }

    // Drag and drop events
    const dropZone = document.getElementById('file-drop-zone');
    if (dropZone) {
      ['dragenter', 'dragover'].forEach(name => {
        dropZone.addEventListener(name, e => { e.preventDefault(); dropZone.classList.add('dragover'); });
      });
      ['dragleave', 'drop'].forEach(name => {
        dropZone.addEventListener(name, e => { e.preventDefault(); dropZone.classList.remove('dragover'); });
      });
      dropZone.addEventListener('drop', e => {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = ev => {
            document.getElementById('custom-data-input').value = ev.target.result;
            projectData();
          };
          reader.readAsText(file);
        }
      });
    }

    function queryOsdrApi() {
      const input = document.getElementById('osdr-api-input');
      const statusEl = document.getElementById('osdr-api-status');
      const studyId = (input?.value || '').trim().toUpperCase();
      if (!studyId) {
        alert('Please enter a NASA OSDR Study ID (e.g. OSD-120, OSD-427, OSD-37, OSD-782, OSD-8)');
        return;
      }

      statusEl.innerHTML = '<span style="color:var(--primary);">Querying NASA OSDR...</span>';

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      fetch('https://osdr.nasa.gov/osdr/data/osd/meta/' + studyId, { signal: controller.signal })
        .then(res => {
          clearTimeout(timeoutId);
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.json();
        })
        .then(data => {
          statusEl.innerHTML = '<span style="color:#106e54; font-weight:700;">Live OSDR Connected</span>';
          let presetKey = studyId.toLowerCase().replace('-', '_');
          if (presetKey === 'osd_120') presetKey = 'osd120_root';
          if (presetKey === 'osd_427') presetKey = 'osd427_protein';
          if (presetKey === 'osd_37') presetKey = 'osd37';
          if (presetKey === 'osd_782') presetKey = 'osd782';
          if (presetKey === 'osd_8') presetKey = 'osd8';
          if (osdrPresets[presetKey]) {
            loadPreset(presetKey);
          }
        })
        .catch(err => {
          clearTimeout(timeoutId);
          // Fallback to local spaceflight cache
          let presetKey = studyId.toLowerCase().replace('-', '_');
          if (presetKey === 'osd_120') presetKey = 'osd120_root';
          if (presetKey === 'osd_427') presetKey = 'osd427_protein';
          if (presetKey === 'osd_37') presetKey = 'osd37';
          if (presetKey === 'osd_782') presetKey = 'osd782';
          if (presetKey === 'osd_8') presetKey = 'osd8';
          if (osdrPresets[presetKey]) {
            statusEl.innerHTML = '<span style="color:#106e54; font-weight:700;">Loaded Spaceflight Cache</span>';
            loadPreset(presetKey);
          } else {
            statusEl.innerHTML = '<span style="color:#dc2626;">Study Not Found in Cache</span>';
          }
        });
    }

    function parseData() {
      const raw = document.getElementById('custom-data-input')?.value || '';
      const lines = raw.split(/\\r?\\n/).map(l => l.trim()).filter(l => l && !l.startsWith('#') && !l.startsWith('//'));
      if (!lines.length) return [];

      let delimiter = ',';
      if (lines[0].includes('\\t')) delimiter = '\\t';
      else if (lines[0].includes(';')) delimiter = ';';

      let locusIdx = 0, fcIdx = 1, pvalIdx = 2, symIdx = -1, compIdx = -1;
      const headerTokens = lines[0].toLowerCase().split(delimiter).map(t => t.replace(/["']/g, '').trim());

      let hasHeader = false;
      headerTokens.forEach((tok, idx) => {
        if (tok.includes('locus') || tok.includes('agi') || tok.includes('gene_id') || tok === 'id') { locusIdx = idx; hasHeader = true; }
        else if (tok.includes('log') || tok.includes('fc') || tok.includes('fold') || tok === 'lfc') { fcIdx = idx; hasHeader = true; }
        else if (tok.includes('pval') || tok.includes('p_val') || tok.includes('padj') || tok === 'p' || tok === 'fdr') { pvalIdx = idx; hasHeader = true; }
        else if (tok.includes('symbol') || tok.includes('name')) { symIdx = idx; hasHeader = true; }
        else if (tok.includes('comp') || tok.includes('compartment')) { compIdx = idx; hasHeader = true; }
      });

      const startRow = hasHeader ? 1 : 0;
      const records = [];

      for (let i = startRow; i < lines.length; i++) {
        const parts = lines[i].split(delimiter).map(t => t.replace(/["']/g, '').trim());
        if (!parts[locusIdx]) continue;
        const locus = parts[locusIdx].toUpperCase();
        const fc = parseFloat(parts[fcIdx]);
        if (isNaN(fc)) continue;

        let pval = 0.01;
        if (pvalIdx >= 0 && parts[pvalIdx]) {
          const p = parseFloat(parts[pvalIdx]);
          if (!isNaN(p)) pval = p;
        }

        const cat = catalogData[locus];
        const symbol = (symIdx >= 0 && parts[symIdx]) ? parts[symIdx] : (cat ? cat.symbol : locus);
        const comp = (compIdx >= 0 && parts[compIdx]) ? parts[compIdx] : (cat ? cat.compartment : 'Organellar');

        records.push({
          locus: locus,
          fc: fc,
          pval: pval,
          sig: pval < 0.05,
          symbol: symbol,
          compartment: comp,
          desc: cat ? cat.desc : 'User-supplied entity.'
        });
      }

      return records;
    }

    function projectData() {
      currentParsedRecords = parseData();
      renderCurrentMap();
      applyProjection();
      updateTelemetry(currentParsedRecords);
      renderTable();
    }

    function updateFcSlider(val) {
      maxFcScale = parseFloat(val);
      document.getElementById('val-fc-range').textContent = '&plusmn;' + maxFcScale.toFixed(2) + ' log2FC';
      document.getElementById('legend-min-lbl').textContent = '-' + maxFcScale.toFixed(2);
      document.getElementById('legend-max-lbl').textContent = '+' + maxFcScale.toFixed(2);
      applyProjection();
    }

    function applyProjection() {
      const container = document.getElementById('studio-canvas-container');
      if (!container) return;

      const palette = document.getElementById('select-palette')?.value || 'red-blue';
      const contrastMode = document.getElementById('select-contrast-mode')?.value || 'adaptive';
      const sigFilter = document.getElementById('select-sig-filter')?.value || 'none';

      const locusMap = {};
      const symbolMap = {};
      currentParsedRecords.forEach(r => {
        locusMap[r.locus] = r;
        if (r.symbol) symbolMap[r.symbol.toUpperCase()] = r;
      });

      let matchedNodes = 0;
      const nodeGroups = container.querySelectorAll('.pmc-node-group');

      nodeGroups.forEach(group => {
        const nodeId = group.getAttribute('data-node-id') || group.id.replace(/^node-/, '');
        const rect = group.querySelector('.pmc-node');
        const labels = group.querySelectorAll('.pmc-label, .pmc-sub');
        let statPill = group.querySelector('.pmc-omics-stat-pill');

        const mData = mapOmicsData[currentMapId] || {};
        const nInfo = mData[nodeId];
        let match = null;
        if (nInfo) {
          if (locusMap[nInfo.locus]) match = locusMap[nInfo.locus];
          else if (nInfo.all_loci) {
            for (let l of nInfo.all_loci) {
              if (locusMap[l]) { match = locusMap[l]; break; }
            }
          }
          if (!match && nInfo.symbol && symbolMap[nInfo.symbol.toUpperCase()]) {
            match = symbolMap[nInfo.symbol.toUpperCase()];
          }
        }
        if (!match && symbolMap[nodeId.toUpperCase()]) {
          match = symbolMap[nodeId.toUpperCase()];
        }

        if (match) {
          matchedNodes++;
          const clamped = Math.max(-maxFcScale, Math.min(maxFcScale, match.fc));
          const norm = (clamped + maxFcScale) / (2 * maxFcScale);
          let r, g, b;
          if (palette === 'orange-blue') {
            if (norm < 0.5) {
              const t = norm / 0.5;
              r = Math.round(2 + (255 - 2) * t);
              g = Math.round(132 + (255 - 132) * t);
              b = Math.round(199 + (255 - 199) * t);
            } else {
              const t = (norm - 0.5) / 0.5;
              r = Math.round(255 + (217 - 255) * t);
              g = Math.round(255 + (119 - 255) * t);
              b = Math.round(255 + (6 - 255) * t);
            }
          } else {
            if (norm < 0.5) {
              const t = norm / 0.5;
              r = Math.round(37 + (255 - 37) * t);
              g = Math.round(99 + (255 - 99) * t);
              b = Math.round(235 + (255 - 235) * t);
            } else {
              const t = (norm - 0.5) / 0.5;
              r = Math.round(255 + (220 - 255) * t);
              g = Math.round(255 + (38 - 255) * t);
              b = Math.round(255 + (38 - 255) * t);
            }
          }

          const hex = '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
          if (rect) rect.style.fill = hex;

          const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
          let textFill = '#111827';
          if (contrastMode === 'white') textFill = '#ffffff';
          else if (contrastMode === 'dark') textFill = '#111827';
          else textFill = lum < 0.48 ? '#f8fafc' : '#111827';

          labels.forEach(l => l.style.fill = textFill);

          const rx = parseFloat(rect ? rect.getAttribute('x') : 0) + 6;
          const ry = parseFloat(rect ? rect.getAttribute('y') : 0) + 6;
          if (!statPill && rect) {
            statPill = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            statPill.setAttribute('class', 'pmc-omics-stat-pill');
            statPill.innerHTML = `
              <rect x="${rx}" y="${ry}" width="42" height="13" rx="3" fill="#0f172a" opacity="0.88" />
              <text x="${rx + 21}" y="${ry + 9.5}" font-size="9px" font-weight="700" fill="#38bdf8" text-anchor="middle">
                ${match.fc >= 0 ? '+' : ''}${match.fc.toFixed(2)}${match.sig ? '*' : ''}
              </text>
            `;
            group.appendChild(statPill);
          } else if (statPill) {
            statPill.innerHTML = `
              <rect x="${rx}" y="${ry}" width="42" height="13" rx="3" fill="#0f172a" opacity="0.88" />
              <text x="${rx + 21}" y="${ry + 9.5}" font-size="9px" font-weight="700" fill="#38bdf8" text-anchor="middle">
                ${match.fc >= 0 ? '+' : ''}${match.fc.toFixed(2)}${match.sig ? '*' : ''}
              </text>
            `;
          }

          if (sigFilter === 'p005' && match.pval >= 0.05) {
            group.style.opacity = '0.35';
            group.style.filter = 'grayscale(70%)';
          } else if (sigFilter === 'p001' && match.pval >= 0.01) {
            group.style.opacity = '0.35';
            group.style.filter = 'grayscale(70%)';
          } else {
            group.style.opacity = '1.0';
            group.style.filter = 'none';
          }
        } else {
          if (rect) rect.style.fill = '';
          labels.forEach(l => l.style.fill = '');
          if (statPill) statPill.remove();
          group.style.opacity = '0.88';
          group.style.filter = 'none';
        }
      });

      document.getElementById('hud-active-nodes').textContent = matchedNodes;
    }

    function attachCanvasEvents() {
      const container = document.getElementById('studio-canvas-container');
      if (!container) return;
      const nodeGroups = container.querySelectorAll('.pmc-node-group');
      nodeGroups.forEach(group => {
        group.style.cursor = 'pointer';
        group.addEventListener('mouseenter', () => inspectCanvasNode(group));
        group.addEventListener('click', () => inspectCanvasNode(group));
      });
    }

    function inspectCanvasNode(group) {
      const nodeId = group.getAttribute('data-node-id') || group.id.replace(/^node-/, '');
      const mData = mapOmicsData[currentMapId] || {};
      const nInfo = mData[nodeId];
      const locusMap = {};
      currentParsedRecords.forEach(r => locusMap[r.locus] = r);

      let match = nInfo && locusMap[nInfo.locus] ? locusMap[nInfo.locus] : null;
      const drawer = document.getElementById('node-inspector-drawer');
      if (!drawer) return;

      const title = nInfo ? nInfo.title : nodeId;
      const locus = match ? match.locus : (nInfo ? nInfo.locus : 'N/A');
      const symbol = match ? match.symbol : (nInfo ? nInfo.symbol : nodeId);
      const comp = match ? match.compartment : (nInfo ? nInfo.compartment : 'Organellar');
      const fcText = match ? (match.fc >= 0 ? '+' : '') + match.fc.toFixed(2) + ' log2FC' : 'Unmapped / Baseline';
      const pvalText = match ? 'p = ' + match.pval.toExponential(2) + (match.sig ? ' (Significant)' : '') : 'N/A';
      const desc = match ? match.desc : (nInfo ? nInfo.desc : 'Constituent pathway node.');

      const fcColor = match ? (match.fc > 0 ? '#dc2626' : (match.fc < 0 ? '#2563eb' : 'var(--text)')) : 'var(--text-soft)';

      drawer.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
          <div>
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
              <h4 style="font-size:1.1rem; font-weight:800; margin:0;">${title}</h4>
              <span class="badge" style="background:var(--primary-light); color:var(--primary); font-family:var(--font-mono); font-weight:700;">${symbol}</span>
              <span class="badge" style="background:var(--surface-2); font-family:var(--font-mono); font-size:0.75rem;">${locus}</span>
            </div>
            <p style="margin:2px 0 6px; font-size:0.84rem; color:var(--text-soft);">${comp}</p>
            <p style="margin:0; font-size:0.86rem; line-height:1.4; max-width:800px;">${desc}</p>
          </div>
          <div style="text-align:right; min-width:180px;">
            <div style="font-size:1.25rem; font-weight:800; color:${fcColor}; font-family:var(--font-mono);">${fcText}</div>
            <div style="font-size:0.78rem; color:var(--text-soft); margin-top:2px;">${pvalText}</div>
          </div>
        </div>
      `;
    }

    function updateTelemetry(records) {
      document.getElementById('hud-total-rows').textContent = records.length;
      let matchedLoci = 0;
      let up = 0;
      let down = 0;
      let sig = 0;

      records.forEach(r => {
        if (catalogData[r.locus]) matchedLoci++;
        if (r.fc > 0.5) up++;
        if (r.fc < -0.5) down++;
        if (r.sig) sig++;
      });

      document.getElementById('hud-matched-loci').textContent = matchedLoci;
      document.getElementById('hud-up-count').textContent = up;
      document.getElementById('hud-down-count').textContent = down;
      document.getElementById('hud-sig-count').textContent = sig;
    }

    function renderTable() {
      const tbody = document.getElementById('matched-loci-tbody');
      if (!tbody) return;
      const query = (document.getElementById('table-search-input')?.value || '').toLowerCase().trim();

      const mData = mapOmicsData[currentMapId] || {};
      const nodeLociMap = {};
      Object.keys(mData).forEach(nodeId => {
        const info = mData[nodeId];
        if (info.locus) nodeLociMap[info.locus] = nodeId;
        if (info.all_loci) info.all_loci.forEach(l => nodeLociMap[l] = nodeId);
      });

      const filtered = currentParsedRecords.filter(r => {
        if (!query) return true;
        const txt = (r.locus + ' ' + r.symbol + ' ' + r.compartment + ' ' + (nodeLociMap[r.locus] || '')).toLowerCase();
        return txt.includes(query);
      });

      document.getElementById('table-row-count').textContent = filtered.length + ' Rows';

      tbody.innerHTML = filtered.map(r => {
        const isUp = r.fc > 0;
        const barWidth = Math.min(100, Math.round(Math.abs(r.fc) / 3.0 * 100));
        const barColor = isUp ? '#dc2626' : '#2563eb';
        const sign = isUp ? '+' : '';
        const mapNodeId = nodeLociMap[r.locus] || '';

        return `
          <tr>
            <td><span style="font-family:var(--font-mono); font-weight:700; color:var(--primary);">${r.locus}</span></td>
            <td><strong>${r.symbol}</strong></td>
            <td><span class="badge" style="background:var(--surface-2); font-size:0.75rem;">${r.compartment}</span></td>
            <td style="width:140px;">
              <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-family:var(--font-mono); font-weight:700; font-size:0.82rem; color:${barColor}; min-width:44px;">${sign}${r.fc.toFixed(2)}</span>
                <div style="flex:1; height:6px; background:var(--surface-2); border-radius:3px; overflow:hidden;">
                  <div style="width:${barWidth}%; height:100%; background:${barColor}; border-radius:3px;"></div>
                </div>
              </div>
            </td>
            <td style="font-family:var(--font-mono); font-size:0.78rem;">${r.pval.toExponential(2)}</td>
            <td><span class="badge" style="background:${r.sig ? 'rgba(16,110,84,0.12)' : 'var(--surface-2)'}; color:${r.sig ? '#106e54' : 'var(--text-soft)'}; font-weight:700;">${r.sig ? 'p < 0.05' : 'NS'}</span></td>
            <td>${mapNodeId ? `<span class="badge" style="background:var(--primary-light); color:var(--primary); font-family:var(--font-mono);">${mapNodeId}</span>` : '<span style="color:var(--text-soft); font-size:0.75rem;">None on active map</span>'}</td>
            <td style="text-align:right;">
              ${mapNodeId ? `<button class="btn btn-sm" onclick="highlightLocus('${r.locus}')" style="font-size:0.75rem; padding:3px 8px;">Highlight</button>` : ''}
            </td>
          </tr>
        `;
      }).join('');
    }

    function highlightLocus(locus) {
      const container = document.getElementById('studio-canvas-container');
      if (!container) return;
      const mData = mapOmicsData[currentMapId] || {};
      let targetNodeId = null;
      Object.keys(mData).forEach(nodeId => {
        const info = mData[nodeId];
        if (info.locus === locus || (info.all_loci && info.all_loci.includes(locus))) {
          targetNodeId = nodeId;
        }
      });

      if (targetNodeId) {
        const nodeEl = container.querySelector('#node-' + targetNodeId + ', [data-node-id="' + targetNodeId + '"]');
        if (nodeEl) {
          inspectCanvasNode(nodeEl);
          nodeEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
          nodeEl.style.transition = 'transform 0.2s ease';
          nodeEl.style.transform = 'scale(1.05)';
          setTimeout(() => { nodeEl.style.transform = ''; }, 600);
        }
      }
    }

    function exportStudioSvg() {
      const container = document.getElementById('studio-canvas-container');
      const svg = container?.querySelector('svg');
      if (!svg) return;
      const clone = svg.cloneNode(true);
      const serializer = new XMLSerializer();
      const source = '<?xml version="1.0" standalone="no"?>\\r\\n' + serializer.serializeToString(clone);
      const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'plant_mitocarta_' + currentMapId + '_custom_projection.svg';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    function exportStudioPng() {
      const container = document.getElementById('studio-canvas-container');
      const svg = container?.querySelector('svg');
      if (!svg) return;
      const clone = svg.cloneNode(true);
      const svgString = new XMLSerializer().serializeToString(clone);
      const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
      const URLObj = window.URL || window.webkitURL || window;
      const blobURL = URLObj.createObjectURL(svgBlob);
      const image = new Image();
      image.onload = function() {
        const canvas = document.createElement('canvas');
        canvas.width = image.width || 1200;
        canvas.height = image.height || 800;
        const context = canvas.getContext('2d');
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.drawImage(image, 0, 0);
        const png = canvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = png;
        a.download = 'plant_mitocarta_' + currentMapId + '_custom_projection.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URLObj.revokeObjectURL(blobURL);
      };
      image.src = blobURL;
    }

    function exportStudioCsv() {
      if (!currentParsedRecords.length) return;
      const mData = mapOmicsData[currentMapId] || {};
      const nodeLociMap = {};
      Object.keys(mData).forEach(nodeId => {
        const info = mData[nodeId];
        if (info.locus) nodeLociMap[info.locus] = nodeId;
        if (info.all_loci) info.all_loci.forEach(l => nodeLociMap[l] = nodeId);
      });

      const lines = ['locus,symbol,log2fc,pvalue,significant,compartment,active_map_node'];
      currentParsedRecords.forEach(r => {
        lines.push(`${r.locus},${r.symbol},${r.fc},${r.pval},${r.sig},${r.compartment},${nodeLociMap[r.locus] || ''}`);
      });

      const blob = new Blob([lines.join('\\n')], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'plant_mitocarta_' + currentMapId + '_projected_records.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    // Initialize Studio on DOM Load
    initStudio();
    </script>
    __HTML_FOOTER__
    """

    content = (
        template.replace("__NAV_HEADER__", nav_header_fn(active="custom"))
        .replace("__HTML_FOOTER__", html_footer_fn())
        .replace("__MAP_OPTIONS_HTML__", map_options_html)
        .replace("__CATALOG_JSON__", json.dumps(catalog))
        .replace("__PRESETS_JSON__", json.dumps(osdr_presets))
        .replace("__MAP_SVGS_JSON__", json.dumps(map_svgs))
        .replace("__MAP_METADATA_JSON__", json.dumps(map_metadata))
        .replace("__MAP_OMICS_JSON__", json.dumps(map_omics_data))
    )

    return html_head_fn("Custom Multi-Omics Data Projection Studio — Plant MitoCarta", extra_css) + content
