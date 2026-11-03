"""
Global Omnibox Modal UI and Canvas Pan/Zoom/Fullscreen Controller for Plant MitoCarta.
Provides:
- OMNIBOX_AND_CANVAS_CSS: styles for Omnibox modal and pan/zoom overlay toolbar.
- get_omnibox_modal_html(): HTML markup for the modal dialog.
- get_omnibox_and_canvas_js(prefix): client-side JavaScript engine.
"""

OMNIBOX_AND_CANVAS_CSS = """
    /* CoSE Global Omnibox Modal & Search Button (Decision 1.1) */
    .cose-omnibox-backdrop {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 20, 27, 0.65);
      backdrop-filter: blur(5px);
      -webkit-backdrop-filter: blur(5px);
      z-index: 99999;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding: 50px 16px 20px;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.15s ease;
    }
    .cose-omnibox-backdrop.open {
      opacity: 1;
      pointer-events: auto;
    }
    .cose-omnibox-dialog {
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 12px;
      box-shadow: 0 24px 48px rgba(0,0,0,0.3);
      width: 100%;
      max-width: 860px;
      max-height: 84vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transform: scale(0.97);
      transition: transform 0.15s ease;
    }
    .cose-omnibox-backdrop.open .cose-omnibox-dialog {
      transform: scale(1.0);
    }
    .cose-omnibox-header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 18px;
      border-bottom: 1px solid var(--line);
      background: var(--surface);
    }
    .cose-omnibox-header input {
      flex: 1;
      border: none;
      background: transparent;
      font-size: 1.05rem;
      font-family: var(--font-sans);
      color: var(--ink);
      outline: none;
    }
    .cose-omnibox-header input::placeholder {
      color: var(--muted);
      font-size: 0.95rem;
    }
    .omnibox-badge-esc {
      font-size: 0.72rem;
      font-weight: 700;
      padding: 3px 7px;
      border-radius: 5px;
      background: var(--surface-2);
      border: 1px solid var(--line);
      color: var(--muted);
      font-family: var(--font-mono);
      cursor: pointer;
    }
    .cose-omnibox-filter-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 10px 18px;
      border-bottom: 1px solid var(--line);
      background: var(--bg);
    }
    .omnibox-filter-chip {
      padding: 4px 10px;
      font-size: 0.76rem;
      font-weight: 600;
      border-radius: 6px;
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--muted);
      cursor: pointer;
      transition: all 0.12s ease;
    }
    .omnibox-filter-chip:hover {
      border-color: var(--accent);
      color: var(--ink);
    }
    .omnibox-filter-chip.active {
      background: var(--primary-light);
      border-color: var(--primary);
      color: var(--primary);
      font-weight: 700;
    }
    .cose-omnibox-body {
      display: grid;
      grid-template-columns: 320px 1fr;
      flex: 1;
      min-height: 380px;
      max-height: 58vh;
      overflow: hidden;
      border-bottom: 1px solid var(--line);
    }
    @media (max-width: 768px) {
      .cose-omnibox-body {
        grid-template-columns: 1fr;
        max-height: 65vh;
      }
      .cose-omnibox-detail { display: none; }
    }
    .cose-omnibox-list {
      overflow-y: auto;
      border-right: 1px solid var(--line);
      padding: 6px 0;
    }
    .omnibox-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 9px 16px;
      cursor: pointer;
      border-left: 3px solid transparent;
      transition: background 0.1s ease, border-color 0.1s ease;
    }
    .omnibox-item:hover, .omnibox-item.active {
      background: var(--surface-2);
      border-left-color: var(--primary);
    }
    .omnibox-item-locus {
      font-family: var(--font-mono);
      font-weight: 700;
      font-size: 0.82rem;
      color: var(--primary);
    }
    .omnibox-item-symbol {
      font-weight: 700;
      font-size: 0.9rem;
      color: var(--ink);
      margin-left: 6px;
    }
    .omnibox-item-comp {
      font-size: 0.74rem;
      color: var(--muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 130px;
    }
    .cose-omnibox-detail {
      overflow-y: auto;
      padding: 18px 22px;
      background: var(--surface);
    }
    .cose-omnibox-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 9px 18px;
      background: var(--surface-2);
      font-size: 0.76rem;
      color: var(--muted);
    }
    .omnibox-hints {
      display: flex;
      gap: 12px;
    }
    .omnibox-hints kbd {
      font-family: var(--font-mono);
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 3px;
      padding: 1px 4px;
      font-size: 0.72rem;
    }

    /* Canvas Pan, Zoom, and Fullscreen Controls (Decision 1.2) */
    .canvas-viewport-wrapper {
      position: relative;
    }
    .canvas-pan-zoom-toolbar {
      position: absolute;
      top: 10px;
      right: 10px;
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 3px 5px;
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      z-index: 25;
      opacity: 0.88;
      transition: opacity 0.15s ease;
    }
    .canvas-pan-zoom-toolbar:hover {
      opacity: 1.0;
    }
    .canvas-toolbar-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 26px;
      height: 26px;
      border-radius: 5px;
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--ink);
      font-size: 0.85rem;
      font-weight: 700;
      cursor: pointer;
      line-height: 1;
      padding: 0;
      transition: all 0.1s ease;
    }
    .canvas-toolbar-btn:hover {
      border-color: var(--accent);
      background: var(--surface-2);
      color: var(--accent);
    }
    .canvas-viewport-wrapper:fullscreen,
    .canvas-viewport-wrapper:-webkit-full-screen {
      width: 100vw !important;
      height: 100vh !important;
      padding: 24px !important;
      background: #ffffff !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      overflow: hidden !important;
    }
    .canvas-viewport-wrapper:fullscreen svg,
    .canvas-viewport-wrapper:-webkit-full-screen svg {
      max-height: 94vh !important;
      max-width: 96vw !important;
    }
"""


def get_omnibox_modal_html():
    return """
  <!-- GLOBAL GENE OMNIBOX MODAL (Decision 1.1) -->
  <div id="cose-omnibox-backdrop" class="cose-omnibox-backdrop" aria-hidden="true" role="dialog" aria-modal="true" style="display: none;">
    <div class="cose-omnibox-dialog">
      <div class="cose-omnibox-header">
        <svg class="omnibox-search-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--muted); flex-shrink: 0;">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input type="text" id="cose-omnibox-input" placeholder="Search locus (e.g. AT3G22370), gene symbol (e.g. AOX1a), enzyme, pathway, or organelle..." autocomplete="off" spellcheck="false">
        <span class="omnibox-badge-esc" onclick="closeOmnibox()">ESC</span>
      </div>

      <div class="cose-omnibox-filter-bar">
        <button type="button" class="omnibox-filter-chip active" data-filter="all" onclick="setOmniboxFilter('all')">All (96)</button>
        <button type="button" class="omnibox-filter-chip" data-filter="mito" onclick="setOmniboxFilter('mito')">Mitochondria</button>
        <button type="button" class="omnibox-filter-chip" data-filter="chloro" onclick="setOmniboxFilter('chloro')">Chloroplast</button>
        <button type="button" class="omnibox-filter-chip" data-filter="nuc" onclick="setOmniboxFilter('nuc')">Nucleus</button>
        <button type="button" class="omnibox-filter-chip" data-filter="retro" onclick="setOmniboxFilter('retro')">Retrograde Circuits</button>
        <button type="button" class="omnibox-filter-chip" data-filter="spaceflight" onclick="setOmniboxFilter('spaceflight')">Spaceflight Responders</button>
        <button type="button" class="omnibox-filter-chip" data-filter="ortho" onclick="setOmniboxFilter('ortho')">MitoCarta 3.0</button>
      </div>

      <div class="cose-omnibox-body">
        <div class="cose-omnibox-list" id="cose-omnibox-list" role="listbox">
          <!-- Populated by JS -->
        </div>
        <div class="cose-omnibox-detail" id="cose-omnibox-detail">
          <!-- Populated on hover/select -->
        </div>
      </div>

      <div class="cose-omnibox-footer">
        <div class="omnibox-hints">
          <span><kbd>&uarr;</kbd> <kbd>&darr;</kbd> Navigate</span>
          <span><kbd>&crarr;</kbd> Select</span>
          <span><kbd>Esc</kbd> Close</span>
        </div>
        <div class="omnibox-powered">
          Plant MitoCarta Cross-Portal Search &bull; 96 Loci Indexed
        </div>
      </div>
    </div>
  </div>
"""


def get_omnibox_and_canvas_js(prefix=""):
    return f"""
(function() {{
  const prefix = '{prefix}';

  // ==========================================
  // 1. GLOBAL GENE OMNIBOX (Decision 1.1)
  // ==========================================
  let omniboxIndex = window.PLANT_MITOCARTA_OMNIBOX_INDEX || [];
  let filteredResults = [];
  let activeIndex = 0;
  let activeCategory = 'all';

  function ensureIndex(cb) {{
    if (omniboxIndex && omniboxIndex.length > 0) {{
      if (cb) cb();
      return;
    }}
    fetch(prefix + 'assets/omnibox_index.json')
      .then(res => res.json())
      .then(data => {{
        omniboxIndex = data;
        window.PLANT_MITOCARTA_OMNIBOX_INDEX = data;
        if (cb) cb();
      }})
      .catch(err => {{
        console.warn('Could not fetch omnibox_index.json', err);
        if (cb) cb();
      }});
  }}

  function openOmnibox() {{
    const backdrop = document.getElementById('cose-omnibox-backdrop');
    if (!backdrop) return;
    backdrop.style.display = 'flex';
    setTimeout(() => backdrop.classList.add('open'), 10);
    backdrop.setAttribute('aria-hidden', 'false');
    const input = document.getElementById('cose-omnibox-input');
    if (input) {{
      input.focus();
      input.select();
    }}
    ensureIndex(() => {{
      runSearch();
    }});
  }}

  function closeOmnibox() {{
    const backdrop = document.getElementById('cose-omnibox-backdrop');
    if (!backdrop) return;
    backdrop.classList.remove('open');
    backdrop.setAttribute('aria-hidden', 'true');
    setTimeout(() => {{ backdrop.style.display = 'none'; }}, 150);
  }}

  function runSearch() {{
    const query = (document.getElementById('cose-omnibox-input')?.value || '').toLowerCase().trim();
    if (!omniboxIndex || omniboxIndex.length === 0) return;

    filteredResults = omniboxIndex.filter(item => {{
      // Category filter
      if (activeCategory === 'mito') {{
        const c = (item.comp + ' ' + item.comp_label).toLowerCase();
        if (!c.includes('mito') && !c.includes('cristae')) return false;
      }} else if (activeCategory === 'chloro') {{
        const c = (item.comp + ' ' + item.comp_label).toLowerCase();
        if (!c.includes('chloro') && !c.includes('thylakoid') && !c.includes('plastid') && !c.includes('stroma')) return false;
      }} else if (activeCategory === 'nuc') {{
        const c = (item.comp + ' ' + item.comp_label).toLowerCase();
        if (!c.includes('nucle') && !c.includes('chromatin')) return false;
      }} else if (activeCategory === 'retro') {{
        if (!item.retro || item.retro.length === 0) return false;
      }} else if (activeCategory === 'spaceflight') {{
        if (!item.contrasts || Object.keys(item.contrasts).length === 0) return false;
      }} else if (activeCategory === 'ortho') {{
        if (!item.ortho || !item.ortho.cat) return false;
      }}

      if (!query) return true;

      const mapStr = (item.maps || []).map(m => m.map_id + ' ' + m.map_title + ' ' + m.node_label).join(' ');
      const searchBlob = (item.locus + ' ' + item.symbol + ' ' + item.name + ' ' + item.comp_label + ' ' + (item.pmco_id || '') + ' ' + mapStr + ' ' + (item.ortho ? item.ortho.human_symbol + ' ' + item.ortho.clin : '')).toLowerCase();

      return searchBlob.includes(query);
    }});

    activeIndex = 0;
    renderResultsList();
    renderActiveDetail();
  }}

  function renderResultsList() {{
    const listEl = document.getElementById('cose-omnibox-list');
    if (!listEl) return;
    if (filteredResults.length === 0) {{
      listEl.innerHTML = '<div style="padding: 24px 16px; text-align: center; color: var(--muted); font-size: 0.88rem;">No loci matching search criteria.</div>';
      return;
    }}

    listEl.innerHTML = filteredResults.slice(0, 40).map((r, idx) => {{
      const isAct = idx === activeIndex ? ' active' : '';
      return `
        <div class="omnibox-item${{isAct}}" data-index="${{idx}}" onclick="selectOmniboxIndex(${{idx}})">
          <div style="display: flex; align-items: center; min-width: 0; overflow: hidden;">
            <span class="omnibox-item-locus">${{r.locus}}</span>
            <span class="omnibox-item-symbol">${{r.symbol}}</span>
          </div>
          <span class="omnibox-item-comp">${{r.comp_label}}</span>
        </div>
      `;
    }}).join('');
  }}

  function renderActiveDetail() {{
    const detailEl = document.getElementById('cose-omnibox-detail');
    if (!detailEl) return;
    const item = filteredResults[activeIndex];
    if (!item) {{
      detailEl.innerHTML = '<div style="padding: 30px; text-align: center; color: var(--muted);">Select a locus from the list to preview details.</div>';
      return;
    }}

    // Maps HTML
    const mapsHtml = (item.maps && item.maps.length > 0)
      ? item.maps.map(m => `<a href="${{prefix}}index.html?map=${{m.map_id}}&locus=${{item.locus}}" class="badge" style="background: var(--primary-light); color: var(--primary); text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px;" title="${{m.map_title}}: ${{m.node_label}}">${{m.map_id}} &bull; ${{m.node_label}} &nearr;</a>`).join(' ')
      : '<span style="font-size: 0.8rem; color: var(--muted);">Not directly mapped in 10 pathway diagrams</span>';

    // Retrograde HTML
    const retroHtml = (item.retro && item.retro.length > 0)
      ? item.retro.map(r => `
          <div style="background: var(--bg); border: 1px solid var(--line); border-left: 3px solid var(--accent); border-radius: 6px; padding: 6px 10px; margin-top: 4px; font-size: 0.8rem;">
            <strong>${{r.circuit_title}}</strong> (Step ${{r.step_idx}}: ${{r.step_label}})
            <div style="margin-top: 3px;"><a href="${{prefix}}retrograde.html?circuit=${{r.circuit_id}}&step=${{r.step_idx - 1}}" style="font-size: 0.74rem; font-weight: 700; color: var(--primary);">View in Circuit &rarr;</a></div>
          </div>
        `).join('')
      : '<span style="font-size: 0.8rem; color: var(--muted);">Not in retrograde signaling pathway core</span>';

    // Spaceflight Telemetry HTML
    let omicsBadges = '';
    if (item.contrasts && Object.keys(item.contrasts).length > 0) {{
      const keys = ['osd120_root', 'osd120_shoot', 'osd427_protein', 'osd37', 'osd782', 'osd8'];
      const labels = {{'osd120_root': 'OSD-120 Root', 'osd120_shoot': 'OSD-120 Shoot', 'osd427_protein': 'OSD-427 Prot', 'osd37': 'OSD-37 Seed', 'osd782': 'OSD-782 Cent', 'osd8': 'OSD-8 Rad'}};
      omicsBadges = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(105px, 1fr)); gap: 6px; margin-top: 6px;">' +
        keys.filter(k => item.contrasts[k]).map(k => {{
          const c = item.contrasts[k];
          const isUp = c.fc > 0;
          const col = isUp ? '#dc2626' : '#2563eb';
          const sign = isUp ? '+' : '';
          return `
            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 6px; padding: 5px 7px; text-align: center;">
              <div style="font-size: 0.68rem; color: var(--muted);">${{labels[k]}}</div>
              <div style="font-family: var(--font-mono); font-weight: 700; font-size: 0.82rem; color: ${{col}};">${{sign}}${{c.fc.toFixed(2)}}${{c.sig ? '*' : ''}}</div>
            </div>
          `;
        }}).join('') + '</div>';
    }} else {{
      omicsBadges = '<span style="font-size: 0.8rem; color: var(--muted);">No spaceflight microgravity differential expression recorded</span>';
    }}

    // MitoCarta 3.0 Orthology HTML
    let orthoHtml = '';
    if (item.ortho && item.ortho.cat) {{
      orthoHtml = `
        <div style="font-size: 0.82rem; line-height: 1.45;">
          <div><strong>Human Ortholog:</strong> <span style="font-family: var(--font-mono); color: var(--primary); font-weight: 700;">${{item.ortho.human_symbol || 'None (Plant Innovation)'}}</span></div>
          <div><strong>Evolutionary Status:</strong> ${{item.ortho.cat.replace(/_/g, ' ').toUpperCase()}}</div>
          ${{item.ortho.mitopathway ? `<div><strong>MitoPathway:</strong> ${{item.ortho.mitopathway}}</div>` : ''}}
          ${{item.ortho.clin ? `<div style="margin-top: 4px; font-size: 0.76rem; color: var(--muted);">${{item.ortho.clin}}</div>` : ''}}
        </div>
      `;
    }} else {{
      orthoHtml = '<span style="font-size: 0.8rem; color: var(--muted);">Absent in mammalian MitoCarta 3.0 / Plant-specific</span>';
    }}

    // SUBA5 HTML
    let subaHtml = '';
    if (item.suba && item.suba.comp) {{
      subaHtml = `
        <div style="font-size: 0.82rem;">
          <strong>SUBAcon Consensus:</strong> <span class="badge" style="background: var(--surface-2);">${{item.suba.comp}}</span> (Score: ${{item.suba.score}})
          <div style="margin-top: 3px; font-size: 0.76rem; color: var(--muted);">
            ${{item.suba.ms ? '✓ MS Verified' : 'No MS'}} &bull; ${{item.suba.gfp ? '✓ GFP Imaged' : 'No GFP'}} ${{item.suba.dual ? '&bull; <strong>Dual-Targeted</strong>' : ''}}
          </div>
        </div>
      `;
    }} else {{
      subaHtml = '<span style="font-size: 0.8rem; color: var(--muted);">No SUBA5 localization record</span>';
    }}

    // Anchor HTML
    const anchorHtml = item.anchor
      ? `<div style="font-size: 0.8rem; margin-top: 4px;"><span class="badge" style="background: rgba(16,185,129,0.12); color: #059669; font-weight: 700;">⚓ Empirical Landmark Pin: ${{item.anchor.anchor}}</span> &bull; <a href="${{prefix}}digital_doubles.html?double=${{item.anchor.double_id}}&locus=${{item.locus}}" style="color: var(--primary); font-weight: 600;">View on ${{item.anchor.double_name}} Double &rarr;</a></div>`
      : '';

    detailEl.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--line);">
        <div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <h4 style="font-size: 1.2rem; font-weight: 800; margin: 0; color: var(--ink);">${{item.symbol}}</h4>
            <span class="badge" style="background: var(--surface-2); font-family: var(--font-mono); font-weight: 700; color: var(--primary); font-size: 0.84rem;">${{item.locus}}</span>
            ${{item.pmco_id ? `<span class="badge" style="background: var(--surface-2); font-family: var(--font-mono); font-size: 0.74rem;">${{item.pmco_id}}</span>` : ''}}
          </div>
          <div style="font-size: 0.86rem; color: var(--muted); margin-top: 3px;">${{item.comp_label}}</div>
          <div style="font-size: 0.88rem; color: var(--ink); margin-top: 6px; line-height: 1.4;">${{item.name}}</div>
          ${{anchorHtml}}
        </div>
        <div style="display: flex; flex-direction: column; gap: 6px; align-items: flex-end;">
          <a href="${{prefix}}custom_projection.html?locus=${{item.locus}}" class="btn btn-sm primary" style="font-size: 0.76rem; white-space: nowrap;">Project in Studio &nearr;</a>
          ${{(item.maps && item.maps.length > 0) ? `<a href="${{prefix}}index.html?map=${{item.maps[0].map_id}}&locus=${{item.locus}}" class="btn btn-sm" style="font-size: 0.76rem; white-space: nowrap;">View in Map &nearr;</a>` : ''}}
        </div>
      </div>

      <div style="margin-bottom: 14px;">
        <div style="font-size: 0.74rem; font-weight: 700; text-transform: uppercase; color: var(--muted); margin-bottom: 4px;">Pathway Map Occurrences:</div>
        <div style="display: flex; flex-wrap: wrap; gap: 6px;">${{mapsHtml}}</div>
      </div>

      <div style="margin-bottom: 14px;">
        <div style="font-size: 0.74rem; font-weight: 700; text-transform: uppercase; color: var(--muted); margin-bottom: 4px;">Retrograde Signaling Circuits:</div>
        <div>${{retroHtml}}</div>
      </div>

      <div style="margin-bottom: 14px;">
        <div style="font-size: 0.74rem; font-weight: 700; text-transform: uppercase; color: var(--muted); margin-bottom: 4px;">NASA OSDR Spaceflight Telemetry:</div>
        ${{omicsBadges}}
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line);">
        <div>
          <div style="font-size: 0.74rem; font-weight: 700; text-transform: uppercase; color: var(--muted); margin-bottom: 4px;">MitoCarta 3.0 Orthology:</div>
          ${{orthoHtml}}
        </div>
        <div>
          <div style="font-size: 0.74rem; font-weight: 700; text-transform: uppercase; color: var(--muted); margin-bottom: 4px;">SUBA5 Proteomics:</div>
          ${{subaHtml}}
        </div>
      </div>
    `;
  }}

  window.selectOmniboxIndex = function(idx) {{
    activeIndex = idx;
    document.querySelectorAll('.omnibox-item').forEach((el, i) => {{
      el.classList.toggle('active', i === idx);
    }});
    renderActiveDetail();
  }};

  window.setOmniboxFilter = function(filter) {{
    activeCategory = filter;
    document.querySelectorAll('.omnibox-filter-chip').forEach(btn => {{
      btn.classList.toggle('active', btn.getAttribute('data-filter') === filter);
    }});
    runSearch();
  }};

  window.openOmnibox = openOmnibox;
  window.closeOmnibox = closeOmnibox;

  // Global Keyboard Shortcuts
  window.addEventListener('keydown', function(e) {{
    const isCmdK = (e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K');
    const isSlash = e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName);
    if (isCmdK || isSlash) {{
      e.preventDefault();
      const backdrop = document.getElementById('cose-omnibox-backdrop');
      if (backdrop && backdrop.classList.contains('open')) {{
        closeOmnibox();
      }} else {{
        openOmnibox();
      }}
      return;
    }}

    const backdrop = document.getElementById('cose-omnibox-backdrop');
    if (!backdrop || !backdrop.classList.contains('open')) return;

    if (e.key === 'Escape') {{
      e.preventDefault();
      closeOmnibox();
    }} else if (e.key === 'ArrowDown') {{
      e.preventDefault();
      if (filteredResults.length > 0) {{
        activeIndex = (activeIndex + 1) % Math.min(filteredResults.length, 40);
        renderResultsList();
        renderActiveDetail();
        const activeEl = document.querySelector('.omnibox-item.active');
        if (activeEl) activeEl.scrollIntoView({{ block: 'nearest' }});
      }}
    }} else if (e.key === 'ArrowUp') {{
      e.preventDefault();
      if (filteredResults.length > 0) {{
        activeIndex = (activeIndex - 1 + Math.min(filteredResults.length, 40)) % Math.min(filteredResults.length, 40);
        renderResultsList();
        renderActiveDetail();
        const activeEl = document.querySelector('.omnibox-item.active');
        if (activeEl) activeEl.scrollIntoView({{ block: 'nearest' }});
      }}
    }} else if (e.key === 'Enter') {{
      e.preventDefault();
      const item = filteredResults[activeIndex];
      if (item) {{
        if (item.maps && item.maps.length > 0) {{
          window.location.href = prefix + 'index.html?map=' + item.maps[0].map_id + '&locus=' + item.locus;
        }} else {{
          window.location.href = prefix + 'custom_projection.html?locus=' + item.locus;
        }}
      }}
    }}
  }});

  // Attach search button
  const searchBtn = document.getElementById('cose-omnibox-btn');
  if (searchBtn) {{
    searchBtn.addEventListener('click', openOmnibox);
  }}

  const inputEl = document.getElementById('cose-omnibox-input');
  if (inputEl) {{
    inputEl.addEventListener('input', runSearch);
  }}

  // Backdrop click close
  const backdrop = document.getElementById('cose-omnibox-backdrop');
  if (backdrop) {{
    backdrop.addEventListener('click', function(e) {{
      if (e.target === backdrop) closeOmnibox();
    }});
  }}

  // ==========================================
  // 2. CANVAS PAN, ZOOM & FULLSCREEN (Decision 1.2)
  // ==========================================
  function initCanvasControls(container) {{
    if (!container) return;
    const svg = container.querySelector('svg');
    if (!svg) return;
    if (container.querySelector('.canvas-pan-zoom-toolbar')) return;

    container.classList.add('canvas-viewport-wrapper');

    // Create toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'canvas-pan-zoom-toolbar';
    toolbar.innerHTML = `
      <button type="button" class="canvas-toolbar-btn" data-action="zoom-in" title="Zoom In (+)">+</button>
      <button type="button" class="canvas-toolbar-btn" data-action="zoom-out" title="Zoom Out (−)">−</button>
      <button type="button" class="canvas-toolbar-btn" data-action="reset" title="Reset Zoom (100%)">↺</button>
      <button type="button" class="canvas-toolbar-btn" data-action="fullscreen" title="Toggle Fullscreen">⛶</button>
    `;
    container.appendChild(toolbar);

    let scale = 1.0;
    let translateX = 0;
    let translateY = 0;
    let isDragging = false;
    let startX = 0;
    let startY = 0;

    function applyTransform() {{
      svg.style.transformOrigin = 'center center';
      svg.style.transition = isDragging ? 'none' : 'transform 0.15s ease-out';
      svg.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{scale}})`;
      if (scale > 1.05) {{
        container.style.cursor = isDragging ? 'grabbing' : 'grab';
      }} else {{
        container.style.cursor = '';
      }}
    }}

    toolbar.querySelector('[data-action="zoom-in"]').addEventListener('click', (e) => {{
      e.stopPropagation();
      scale = Math.min(3.5, scale * 1.25);
      applyTransform();
    }});

    toolbar.querySelector('[data-action="zoom-out"]').addEventListener('click', (e) => {{
      e.stopPropagation();
      scale = Math.max(0.6, scale / 1.25);
      if (scale <= 1.05) {{ translateX = 0; translateY = 0; }}
      applyTransform();
    }});

    toolbar.querySelector('[data-action="reset"]').addEventListener('click', (e) => {{
      e.stopPropagation();
      scale = 1.0;
      translateX = 0;
      translateY = 0;
      applyTransform();
    }});

    toolbar.querySelector('[data-action="fullscreen"]').addEventListener('click', (e) => {{
      e.stopPropagation();
      if (!document.fullscreenElement) {{
        if (container.requestFullscreen) container.requestFullscreen();
        else if (container.webkitRequestFullscreen) container.webkitRequestFullscreen();
      }} else {{
        if (document.exitFullscreen) document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
      }}
    }});

    container.addEventListener('mousedown', (e) => {{
      if (e.target.closest('.canvas-pan-zoom-toolbar') || e.target.closest('button') || e.target.closest('a')) return;
      if (scale > 1.05) {{
        isDragging = true;
        startX = e.clientX - translateX;
        startY = e.clientY - translateY;
      }}
    }});

    window.addEventListener('mousemove', (e) => {{
      if (!isDragging) return;
      translateX = e.clientX - startX;
      translateY = e.clientY - startY;
      applyTransform();
    }});

    window.addEventListener('mouseup', () => {{
      if (isDragging) {{
        isDragging = false;
        applyTransform();
      }}
    }});
  }}

  function initAllCanvasControls() {{
    const targets = document.querySelectorAll('#studio-svg-container, #studio-canvas-container, #study-svg-container, .map-svg-viewport');
    targets.forEach(t => initCanvasControls(t));
  }}

  setTimeout(initAllCanvasControls, 250);
  window.initCanvasControls = initCanvasControls;
  window.initAllCanvasControls = initAllCanvasControls;
}})();
"""
