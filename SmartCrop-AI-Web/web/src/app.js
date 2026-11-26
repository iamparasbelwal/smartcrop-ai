/**
 * SmartCrop.AI — Main Frontend Controller (Auth, Routing, Studio Chat, Modals & Live APIs)
 */
(function initSmartCropApp() {
  const { Icons, Illustrations, Views, Api, Utils, Prefs } = window.SmartCrop;
  const esc = Utils.esc;

  const ROUTES = [
    { id: 'dashboard', label: 'Dashboard', desc: 'Workspace overview & lab metrics', icon: Icons.dashboard, group: 'core' },
    { id: 'studio', label: 'Formulation Studio', desc: '4-mode workbench & AI co-pilot', icon: Icons.studio, group: 'core' },
    { id: 'ingredients', label: 'Ingredient Database', desc: 'Regional crops, fractions & verification', icon: Icons.ingredients, group: 'core' },
    { id: 'formulations', label: 'My Formulations', desc: 'Projects & saved revisions', icon: Icons.formulations, group: 'core' },
    { id: 'admin', label: 'Lab Admin', desc: 'Team, project access & audit ledger', icon: Icons.admin, group: 'system' },
    { id: 'settings', label: 'Settings', desc: 'Profile, units, router & health check', icon: Icons.settings, group: 'system' }
  ];

  const prefs = Prefs.load();
  const state = {
    bootstrap: null,
    route: 'dashboard',
    navExpanded: false,
    mobileNavOpen: false,
    activeProjectId: '',
    workspace: null,
    studioMode: 'formulation',
    studioTab: 'formulation',
    studioModel: prefs.defaultModel || '',
    studioStatus: '',
    studioMessages: {},
    studioDraftComputed: null,
    studioUnsaved: false,
    studioPending: false,
    studioPendingText: '',
    studioPrompt: '',
    studioConstraints: prefs.prioritizeLocal ? ['Clean Label', 'Local Crops'] : [],
    studioExplainBlend: '',
    studioExplainClean: '',
    studioExplaining: '',
    ingredientsData: null,
    cropQuery: '',
    cropCategory: 'All',
    cropShow: 'all',
    activeCropId: '',
    cropLayout: 'grid',
    ingQuery: '',
    ingCategory: 'All Classes',
    formFilter: 'all',
    formQuery: '',
    adminData: null,
    adminTab: 'team',
    auditArea: 'all',
    auditQuery: '',
    settingsTab: 'profile',
    healthCheck: null
  };

  const el = {
    shell: document.getElementById('app-shell'),
    navToggleBtn: document.getElementById('nav-toggle-btn'),
    mobileMenuBtn: document.getElementById('mobile-menu-btn'),
    navBackdrop: document.getElementById('nav-backdrop'),
    navList: document.getElementById('nav-list'),
    breadcrumbCurrent: document.getElementById('breadcrumb-current'),
    mainViewport: document.getElementById('main-viewport'),
    cmdTrigger: document.getElementById('cmd-trigger'),
    cmdOverlay: document.getElementById('cmd-modal-overlay'),
    cmdInput: document.getElementById('cmd-input'),
    cmdResults: document.getElementById('cmd-results'),
    cmdClose: document.getElementById('cmd-close'),
    appModalOverlay: document.getElementById('app-modal-overlay'),
    appModalTitle: document.getElementById('app-modal-title'),
    appModalBody: document.getElementById('app-modal-body'),
    appModalClose: document.getElementById('app-modal-close'),
    toastStack: document.getElementById('toast-stack'),
    navStatusText: document.getElementById('nav-status-text'),
    envBadgeText: document.getElementById('env-badge-text'),
    avatarChip: document.getElementById('avatar-chip'),
    avatarLabel: document.getElementById('avatar-label')
  };

  function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-item';
    toast.innerHTML = `<span class="toast-dot" aria-hidden="true"></span><span>${esc(message)}</span>`;
    el.toastStack.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(6px)';
      toast.style.transition = 'opacity 180ms ease, transform 180ms ease';
      setTimeout(() => toast.remove(), 200);
    }, 3200);
  }

  function openModal(title, html, wide = false) {
    const dlg = el.appModalOverlay.querySelector('.app-modal-dialog');
    if (dlg) dlg.classList.toggle('verify-modal-wide', Boolean(wide));
    el.appModalTitle.textContent = title;
    el.appModalBody.innerHTML = html;
    el.appModalOverlay.hidden = false;
  }

  function closeModal() {
    el.appModalOverlay.hidden = true;
    el.appModalBody.innerHTML = '';
  }

  function renderNav() {
    const user = state.bootstrap && state.bootstrap.user;
    if (!user) {
      el.navList.innerHTML = '';
      return;
    }
    const visibleRoutes = ROUTES.filter((r) => r.id !== 'admin' || user.role === 'lab_admin');
    const core = visibleRoutes.filter((r) => r.group === 'core');
    const sys = visibleRoutes.filter((r) => r.group === 'system');
    const item = (r) => {
      const isActive = state.route === r.id || (state.route === 'crop-detail' && r.id === 'ingredients');
      return `
      <button class="nav-item ${isActive ? 'is-active' : ''}" type="button" data-route="${r.id}" data-tooltip="${esc(r.label)}" aria-current="${isActive ? 'page' : 'false'}">
        <span class="nav-item-indicator"><span class="nav-item-icon">${r.icon}</span><span class="nav-dot-marker" aria-hidden="true"></span></span>
        <span class="nav-item-label">${esc(r.label)}</span>
      </button>`;
    };
    el.navList.innerHTML = [...core.map(item), '<div class="nav-divider" role="separator"></div>', ...sys.map(item)].join('');
  }

  function updateChrome() {
    const boot = state.bootstrap || {};
    const user = boot.user;
    const ai = boot.ai || {};
    if (el.navStatusText) el.navStatusText.textContent = ai.available ? 'Router Ready' : 'Offline Rules';
    if (el.envBadgeText) el.envBadgeText.textContent = state.studioStatus || ai.status || 'Local Backend';
    if (el.avatarLabel) el.avatarLabel.textContent = user ? `${user.name}` : 'Sign in';
  }

  function renderSignIn() {
    el.breadcrumbCurrent.textContent = 'Sign in';
    document.title = 'Sign in — SmartCrop.AI';
    document.body.removeAttribute('data-studio-mode');
    renderNav();
    updateChrome();

    el.mainViewport.innerHTML = `
      <div class="auth-split-shell">
        <section class="glass-card auth-welcome-box">
          <div class="hero-chip"><span class="page-eyebrow-dot"></span><span>SmartCrop.AI · Food R&amp;D Workbench</span></div>
          <h1 class="hero-title" style="margin:0;">Welcome back</h1>
          <p class="hero-desc" style="margin:0;">
            AI R&amp;D co-pilot for clean-label plant-based formulations. Every formulation output is computed deterministically in Python from your lab database and requires validation.
          </p>
          <div style="margin-top:8px;max-width:190px;">${Illustrations.heroLattice}</div>
        </section>

        <section class="glass-card auth-card-box">
          <div>
            <div class="page-eyebrow"><span class="page-eyebrow-dot"></span><span>Lab Credentials</span></div>
            <h2 class="card-section-title" style="font-size:18px;margin-top:4px;">Sign in to your lab</h2>
          </div>
          <form id="auth-signin-form" style="display:flex;flex-direction:column;gap:12px;">
            <div class="field-group"><label class="field-label" for="signin-email">Email</label><input id="signin-email" class="field-input" type="email" placeholder="you@lab.org" required /></div>
            <div class="field-group"><label class="field-label" for="signin-password">Password</label><input id="signin-password" class="field-input" type="password" placeholder="Password" required /></div>
            <button class="btn btn-primary" type="submit" style="width:100%;"><span>Sign in</span></button>
          </form>

          <div style="border-top:1px solid var(--border-subtle);padding-top:14px;">
            <div style="font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:8px;">Quick Demo Accounts:</div>
            <div class="demo-quick-grid">
              <button class="btn btn-glass btn-sm" type="button" data-demo-login="paras@smartcrop.ai|Admin@123">Paras (Admin)</button>
              <button class="btn btn-glass btn-sm" type="button" data-demo-login="shivam@smartcrop.ai|Worker@123">Shivam (Worker)</button>
              <button class="btn btn-glass btn-sm" type="button" data-demo-login="shreyshi@smartcrop.ai|Worker@123">Shreyshi (Worker)</button>
            </div>
          </div>
        </section>
      </div>`;
  }

  function renderView() {
    if (!state.bootstrap || !state.bootstrap.user) {
      renderSignIn();
      return;
    }
    if (state.route === 'crop-detail') {
      const allCrops = (state.ingredientsData && state.ingredientsData.ingredients) || [];
      const activeCrop = allCrops.find((c) => c.ingredient_id === state.activeCropId);
      el.breadcrumbCurrent.textContent = activeCrop ? `Ingredient Database / ${activeCrop.name}` : 'Ingredient Details';
      document.title = `${activeCrop ? activeCrop.name : 'Ingredient Details'} — SmartCrop.AI`;
      document.body.removeAttribute('data-studio-mode');
      el.mainViewport.innerHTML = Views['crop-detail'](state);
      renderNav();
      updateChrome();
      return;
    }

    const routeObj = ROUTES.find((r) => r.id === state.route) || ROUTES[0];
    el.breadcrumbCurrent.textContent = routeObj.label;
    document.title = `${routeObj.label} — SmartCrop.AI`;
    if (state.route === 'studio') document.body.setAttribute('data-studio-mode', state.studioMode);
    else document.body.removeAttribute('data-studio-mode');

    const renderer = Views[routeObj.id] || Views.dashboard;
    el.mainViewport.innerHTML = renderer(state);
    renderNav();
    updateChrome();

    const chatThread = document.getElementById('studio-chat-thread');
    if (chatThread) chatThread.scrollTop = chatThread.scrollHeight;
  }

  async function refreshBootstrap() {
    state.bootstrap = await Api.bootstrap();
    const projs = state.bootstrap.projects || [];
    if (!state.activeProjectId || !projs.some((p) => p.project_id === state.activeProjectId)) {
      state.activeProjectId = projs.length ? projs[0].project_id : '';
    }
  }

  async function loadWorkspace(pid, params = {}) {
    if (!pid) {
      state.workspace = null;
      return;
    }
    state.workspace = await Api.getWorkspace(pid, params);
    if (Array.isArray(state.workspace.messages)) {
      state.studioMessages[pid] = state.workspace.messages;
    }
    if (!params.keepDraft) {
      state.studioDraftComputed = null;
      state.studioUnsaved = false;
      state.studioExplainBlend = '';
      state.studioExplainClean = '';
    }
  }

  async function loadIngredients() {
    state.ingredientsData = await Api.listIngredients();
  }

  async function loadAdmin() {
    if (state.bootstrap && state.bootstrap.user && state.bootstrap.user.role === 'lab_admin') {
      state.adminData = await Api.getAdminOverview();
    }
  }

  async function navigateTo(routeId, updateHash = true) {
    if (!state.bootstrap || !state.bootstrap.user) {
      renderSignIn();
      return;
    }
    let target = routeId;
    let hashVal = routeId;
    if (String(routeId || '').startsWith('crop/')) {
      state.activeCropId = String(routeId).slice(5);
      target = 'crop-detail';
      hashVal = `crop/${state.activeCropId}`;
    } else if (routeId === 'crops') {
      target = 'ingredients';
      hashVal = 'ingredients';
    } else {
      const valid = ROUTES.some((r) => r.id === routeId);
      target = valid ? routeId : 'dashboard';
      if (target === 'admin' && state.bootstrap.user.role !== 'lab_admin') target = 'dashboard';
      hashVal = target;
    }
    state.route = target;
    state.mobileNavOpen = false;
    el.shell.setAttribute('data-mobile-nav', 'false');
    if (updateHash && window.location.hash !== `#${hashVal}`) window.location.hash = hashVal;

    try {
      if (target === 'studio') {
        const sameProj = state.workspace && state.workspace.project && state.workspace.project.project_id === state.activeProjectId;
        await loadWorkspace(state.activeProjectId, { keepDraft: sameProj && Boolean(state.studioDraftComputed) });
        if (!state.ingredientsData) await loadIngredients();
      } else if (target === 'crops' || target === 'ingredients' || target === 'crop-detail') {
        await loadIngredients();
      } else if (target === 'admin') {
        await loadAdmin();
      } else if (target === 'dashboard' || target === 'formulations') {
        await refreshBootstrap();
      }
    } catch (err) {
      showToast(err.message);
    }
    renderView();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function printStudioSpecPdf() {
    const computed = state.studioDraftComputed || (state.workspace && state.workspace.computed) || {};
    const rows = computed.rows || [];
    if (!rows.length) {
      showToast('Generate a formulation first before exporting PDF.');
      return;
    }

    const prefs = Prefs.load();
    const ws = state.workspace || {};
    const projects = (state.bootstrap && state.bootstrap.projects) || [];
    const proj = ws.project || projects.find((p) => p.project_id === state.activeProjectId) || {};
    const blend = computed.blend || {};
    const findings = computed.findings || [];
    const conf = computed.confidence || {};
    const deltaSign = computed.delta_pct > 0 ? '+' : '';
    const versionBadge = ws.latest_meta && !state.studioUnsaved ? `v${ws.latest_meta.version} (Saved)` : 'Draft (Unsaved)';
    const dateStr = new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
    const cleanVerdict = computed.flagged_count > 0
      ? `${computed.flagged_count} Flagged`
      : computed.review_count > 0
        ? `${computed.review_count} Review`
        : 'Clean';

    const moistureAvg = rows.reduce((acc, r) => acc + (r.moisture_g * r.share_pct) / 100, 0);
    const dmFactor = prefs.dryMatter && moistureAvg < 95 ? 100 / (100 - moistureAvg) : 1;
    const servingGrams = computed.serving_grams || 40;
    const basisLabel = prefs.dryMatter ? 'Dry-Matter Basis (per 100 g DM)' : 'As-Is (per 100 g)';
    const nutRows = [
      ['Energy', `${Math.round((blend.energy_kcal || 0) * dmFactor)} kcal`, `${Math.round(((blend.energy_kcal || 0) * servingGrams) / 100)} kcal`],
      ['Protein', `${((blend.protein_g || 0) * dmFactor).toFixed(1)} g`, `${(((blend.protein_g || 0) * servingGrams) / 100).toFixed(1)} g`],
      ['Total Fat', `${((blend.fat_g || 0) * dmFactor).toFixed(1)} g`, `${(((blend.fat_g || 0) * servingGrams) / 100).toFixed(1)} g`],
      ['Carbohydrate', `${((blend.carbs_g || 0) * dmFactor).toFixed(1)} g`, `${(((blend.carbs_g || 0) * servingGrams) / 100).toFixed(1)} g`],
      ['Dietary Fibre', `${((blend.fibre_g || 0) * dmFactor).toFixed(1)} g`, `${(((blend.fibre_g || 0) * servingGrams) / 100).toFixed(1)} g`]
    ];

    const pageHeader = (pageNum, sectionTitle) => `
      <div class="pdf-header">
        <div>
          <div class="pdf-eyebrow">SMARTCROP.AI · LAB SPECIFICATION · PAGE ${pageNum} OF 4</div>
          <h1 class="pdf-title">${esc(proj.name || 'Formulation Specification')}</h1>
          <div class="pdf-meta">${esc(proj.project_id || '')} · ${esc(versionBadge)} · ${esc(dateStr)}</div>
        </div>
        <div class="pdf-section-tag">${esc(sectionTitle)}</div>
      </div>`;

    const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>${esc(proj.project_id || 'SmartCrop')} — Lab Spec PDF</title>
  <style>
    @page { size: A4; margin: 15mm; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #0b251c;
      background: #ffffff;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .pdf-page {
      page-break-after: always;
      break-after: page;
      padding-bottom: 8px;
    }
    .pdf-page:last-child {
      page-break-after: auto;
      break-after: auto;
    }
    .pdf-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      padding-bottom: 12px;
      margin-bottom: 16px;
      border-bottom: 2px solid #0f3d2e;
    }
    .pdf-eyebrow {
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #047857;
    }
    .pdf-title {
      margin: 4px 0 3px;
      font-size: 20px;
      font-weight: 700;
      color: #072219;
    }
    .pdf-meta {
      font-size: 11.5px;
      color: #3b594e;
    }
    .pdf-section-tag {
      padding: 5px 11px;
      border-radius: 999px;
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      color: #047857;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-bottom: 18px;
    }
    .kpi-card {
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid #d1fae5;
      background: #f4f8f5;
    }
    .kpi-label {
      font-size: 9.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: #678378;
    }
    .kpi-val {
      margin-top: 4px;
      font-size: 18px;
      font-weight: 700;
      color: #072219;
    }
    .kpi-sub {
      margin-top: 2px;
      font-size: 10.5px;
      color: #3b594e;
    }
    h2 {
      margin: 0 0 8px;
      font-size: 14px;
      font-weight: 700;
      color: #072219;
    }
    .sub-note {
      margin: 0 0 12px;
      font-size: 11.5px;
      color: #678378;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 14px;
    }
    th {
      text-align: left;
      padding: 8px 10px;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #3b594e;
      background: #eff6f1;
      border-bottom: 1px solid #a7f3d0;
    }
    td {
      padding: 9px 10px;
      font-size: 12px;
      border-bottom: 1px solid #e6f0ea;
      vertical-align: top;
    }
    .mono { font-family: ui-monospace, Menlo, Consolas, monospace; }
    .pill {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 10.5px;
      font-weight: 600;
      background: #eff6f1;
      color: #3b594e;
      border: 1px solid #d1fae5;
    }
    .pill.ok { background: #ecfdf5; color: #047857; border-color: #a7f3d0; }
    .pill.warn { background: #fffbeb; color: #b45309; border-color: #fde68a; }
    .pill.flag { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }
    .bar-wrap { display: flex; align-items: center; gap: 8px; }
    .bar-track { width: 70px; height: 6px; border-radius: 999px; background: #e6f0ea; overflow: hidden; }
    .bar-fill { height: 100%; background: #059669; }
    .footer-box {
      padding: 10px 12px;
      border-radius: 8px;
      background: #f4f8f5;
      border: 1px solid #e6f0ea;
      display: flex;
      justify-content: space-between;
      font-size: 11.5px;
      color: #3b594e;
    }
    .clean-box {
      padding: 16px;
      border-radius: 10px;
      background: #ecfdf5;
      border: 1px solid #a7f3d0;
      color: #072219;
      font-size: 12.5px;
      line-height: 1.5;
    }
    .disclaimer {
      margin-top: 12px;
      font-size: 11px;
      color: #678378;
      border-left: 3px solid #059669;
      padding-left: 8px;
    }
  </style>
</head>
<body>
  <section class="pdf-page">
    ${pageHeader(1, 'Formulation Chart')}
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-label">COST / KG</div><div class="kpi-val">₹${Number(computed.cost_per_kg || 0).toFixed(2)}</div><div class="kpi-sub">${deltaSign}${computed.delta_pct}% vs wheat base</div></div>
      <div class="kpi-card"><div class="kpi-label">PROTEIN</div><div class="kpi-val">${blend.protein_g ?? 0}g</div><div class="kpi-sub">per 100g · Fibre ${blend.fibre_g ?? 0}g</div></div>
      <div class="kpi-card"><div class="kpi-label">ENERGY</div><div class="kpi-val">${Math.round(blend.energy_kcal || 0)}</div><div class="kpi-sub">kcal / 100g (${rows.length} crops)</div></div>
      <div class="kpi-card"><div class="kpi-label">CLEAN LABEL</div><div class="kpi-val">${esc(cleanVerdict)}</div><div class="kpi-sub">Watchlist screen</div></div>
    </div>
    <h2>Formulation Matrix (${rows.length} Crops)</h2>
    <p class="sub-note">${esc(proj.description || 'Plant-based formulation specification computed from private crop database.')}</p>
    <table>
      <thead><tr><th>Ingredient / Crop</th><th>Category</th><th>Share (%)</th><th>₹ / 100 g</th><th>Confidence</th></tr></thead>
      <tbody>
        ${rows.map((r) => {
          const cCls = r.nutrition_confidence === 'verified' ? 'ok' : (r.nutrition_confidence === 'unknown' ? 'flag' : 'warn');
          return `<tr>
            <td><strong>${esc(r.name)}</strong><br><span style="font-size:10.5px;color:#678378;">${esc(r.local_name || r.region)} · cap ${r.max_practical_pct}%</span></td>
            <td><span class="pill">${esc(r.category)}</span></td>
            <td><div class="bar-wrap"><div class="bar-track"><div class="bar-fill" style="width:${Math.min(100, r.share_pct)}%;"></div></div><strong class="mono">${r.share_pct}%</strong></div></td>
            <td class="mono">₹${r.cost_per_100g.toFixed(2)}</td>
            <td><span class="pill ${cCls}">${esc(r.nutrition_confidence)}</span></td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>
    <div class="footer-box"><span>Computed in Python from <code>data/ingredients.csv</code></span><strong>Total Blend: ${computed.total_pct}%</strong></div>
    <div class="disclaimer">Starting point, not a result — every figure is an estimate until the lab measures the batch.</div>
  </section>

  <section class="pdf-page">
    ${pageHeader(2, 'Nutrition Profile')}
    <h2>Nutritional Composition (${esc(basisLabel)})</h2>
    <p class="sub-note">Calculated per 100 g blend and per ${servingGrams} g serving size.</p>
    <table>
      <thead><tr><th>Nutrient</th><th>Per 100 g</th><th>Per ${servingGrams} g Serving</th></tr></thead>
      <tbody>
        ${nutRows.map(([k, v1, v2]) => `<tr><td><strong>${esc(k)}</strong></td><td class="mono">${esc(v1)}</td><td class="mono">${esc(v2)}</td></tr>`).join('')}
      </tbody>
    </table>
    <div class="footer-box">
      <span>Data confidence: ${conf.verified || 0} verified, ${conf.estimated || 0} estimated, ${conf.unknown || 0} unknown rows</span>
      <strong>Serving: ${servingGrams} g</strong>
    </div>
  </section>

  <section class="pdf-page">
    ${pageHeader(3, 'Cost Breakdown')}
    <h2>Unit Economics &amp; Mandi Pricing</h2>
    <p class="sub-note">Baseline (wheat-atta snack): ₹${Number(computed.baseline_cost || 0).toFixed(2)}/kg · Variance: <strong>${deltaSign}${computed.delta_pct}%</strong>${computed.regional && computed.regional.is_targeted ? ` · Target Market: <strong>${esc(computed.regional.target_region)}</strong> (${computed.regional.local_share_pct}% Regional)` : ''}</p>
    <table>
      <thead><tr><th>Ingredient</th><th>Share</th><th>Spot Price / kg</th><th>${computed.regional && computed.regional.is_targeted ? 'Est. Landed / kg' : 'Blend Contribution / kg'}</th></tr></thead>
      <tbody>
        ${rows.map((r) => `<tr>
          <td><strong>${esc(r.name)}</strong>${computed.regional && computed.regional.is_targeted ? `<br><span style="font-size:10px;color:#678378;">${esc(r.region)} · ${esc(r.region_tier || 'STANDARD')}</span>` : ''}</td>
          <td class="mono">${r.share_pct}%</td>
          <td class="mono">₹${r.cost_per_kg.toFixed(2)}</td>
          <td class="mono">₹${computed.regional && computed.regional.is_targeted ? Number(r.landed_cost_per_kg || r.cost_per_kg).toFixed(2) : ((r.cost_per_kg * r.share_pct) / 100).toFixed(2)}</td>
        </tr>`).join('')}
      </tbody>
    </table>
    <div class="footer-box">
      <span>${computed.regional && computed.regional.is_targeted
        ? `Est. Freight: ₹${Number(computed.regional.freight_per_kg || 0).toFixed(2)}/kg · Landed Total: <strong>₹${Number(computed.regional.landed_cost_per_kg || computed.cost_per_kg).toFixed(2)}/kg</strong> (Saved ₹${Number(computed.regional.savings_vs_distant || 0).toFixed(2)}/kg)`
        : `Cost per ${servingGrams} g serving: <strong>₹${Number(computed.cost_per_serving || 0).toFixed(2)}</strong>`}</span>
      <strong>Mandi Total / kg: ₹${Number(computed.cost_per_kg || 0).toFixed(2)}</strong>
    </div>
  </section>

  <section class="pdf-page">
    ${pageHeader(4, 'Additive Check')}
    <h2>Clean-Label &amp; Watchlist Screening</h2>
    <p class="sub-note">Deterministic screening against <code>data/additives.csv</code>.</p>
    ${!findings.length ? `
      <div class="clean-box">
        <strong>100% Clean-Label — No additives flagged</strong><br>
        All ${rows.length} ingredients passed the clean-label watchlist with zero flagged or review items.
      </div>` : `
      <table>
        <thead><tr><th>Ingredient</th><th>Status</th><th>Watchlist Note</th><th>Natural Alternative</th></tr></thead>
        <tbody>
          ${findings.map((f) => `<tr>
            <td><strong>${esc(f.name)}</strong></td>
            <td><span class="pill ${f.status === 'flagged' ? 'flag' : 'warn'}">${esc(f.status)}</span></td>
            <td>${esc(f.why)}${f.replacement_note ? `<br><em>${esc(f.replacement_note)}</em>` : ''}</td>
            <td>${f.option ? esc(f.option.name) : 'Review / Reduce'}</td>
          </tr>`).join('')}
        </tbody>
      </table>`}
  </section>
</body>
</html>`;

    const iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.right = '0';
    iframe.style.bottom = '0';
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.border = '0';
    document.body.appendChild(iframe);

    const doc = iframe.contentWindow.document;
    doc.open();
    doc.write(html);
    doc.close();

    setTimeout(() => {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
      setTimeout(() => iframe.remove(), 1500);
    }, 150);
    showToast('Opening 4-page PDF print dialog…');
  }

  function openNewProjectModal() {
    const regs = (state.bootstrap && state.bootstrap.target_regions) || ['Pan-India', 'Rajasthan', 'Karnataka', 'Maharashtra', 'Madhya Pradesh', 'Gujarat', 'Andhra Pradesh', 'Punjab', 'West Bengal', 'Uttarakhand'];
    openModal('Create New Lab Project', `
      <form id="modal-new-project-form" style="display:flex;flex-direction:column;gap:12px;">
        <div class="field-group"><label class="field-label" for="np-name">Project End Goal</label><input id="np-name" class="field-input" placeholder="e.g. High-protein clean-label millet biscuit" required /></div>
        <div class="field-group">
          <label class="field-label" for="np-region">Target Indian Market / Region (for local cost optimization)</label>
          <select id="np-region" class="field-input">
            ${regs.map((r) => `<option value="${esc(r)}">${esc(r)}</option>`).join('')}
          </select>
        </div>
        <div class="field-group"><label class="field-label" for="np-desc">Description &amp; Targets</label><textarea id="np-desc" class="field-input" style="height:88px;padding:8px 12px;" placeholder="Target nutrition, regional crops, cost ceiling, clean-label goals…"></textarea></div>
        <button class="btn btn-primary" type="submit">Create &amp; Open in Studio</button>
      </form>`);
  }

  function openAddComponentModal() {
    const ings = (state.ingredientsData && state.ingredientsData.ingredients) || [];
    openModal('Add / Adjust Formulation Component', `
      <form id="modal-add-comp-form" style="display:flex;flex-direction:column;gap:12px;">
        <div class="field-group">
          <label class="field-label" for="ac-ing">Select Crop / Ingredient</label>
          <select id="ac-ing" class="field-input">
            ${ings.map((r) => `<option value="${esc(r.ingredient_id)}">${esc(r.name)} (${esc(r.category)}, ₹${r.cost_per_kg}/kg, cap ${r.max_practical_pct}%)</option>`).join('')}
          </select>
        </div>
        <div class="field-group"><label class="field-label" for="ac-pct">Share (%)</label><input id="ac-pct" class="field-input" type="number" step="0.5" min="0.5" max="100" value="20" required /></div>
        <button class="btn btn-primary" type="submit">Add &amp; Normalize to 100%</button>
      </form>`);
  }

  function openDraftModal() {
    openModal('Draft Formulation with AI', `
      <form id="modal-ai-draft-form" style="display:flex;flex-direction:column;gap:12px;">
        <p style="margin:0;font-size:12.5px;color:var(--text-secondary);">Describe your product. SmartCrop Co-Pilot selects 4–7 database crops and Python validates every practical cap and 100% total.</p>
        <div class="field-group"><label class="field-label" for="dr-brief">Product Brief</label><textarea id="dr-brief" class="field-input" style="height:90px;padding:8px 12px;" placeholder="A high-protein baked millet snack for school kids under ₹80/kg…" required></textarea></div>
        <div class="field-group">
          <label class="field-label" for="dr-cook">Processing Method</label>
          <select id="dr-cook" class="field-input"><option>Baked snack</option><option>Extruded puff</option><option>Pan-fried flatbread</option><option>No-cook energy mix</option></select>
        </div>
        <button class="btn btn-primary" type="submit">Generate Validated Draft</button>
      </form>`);
  }

  function openRegisterCropModal() {
    openModal('Register Crop / Ingredient Source', `
      <form id="modal-reg-crop-form" style="display:flex;flex-direction:column;gap:12px;">
        <div class="form-grid">
          <div class="field-group"><label class="field-label">Crop / Ingredient Name</label><input id="rc-name" class="field-input" required placeholder="e.g. Barnyard millet" /></div>
          <div class="field-group"><label class="field-label">Local Name</label><input id="rc-local" class="field-input" placeholder="e.g. Jhangora" /></div>
          <div class="field-group"><label class="field-label">Category</label><input id="rc-cat" class="field-input" value="Millet" /></div>
          <div class="field-group"><label class="field-label">Region</label><input id="rc-region" class="field-input" value="Uttarakhand" /></div>
          <div class="field-group"><label class="field-label">Energy (kcal/100g)</label><input id="rc-kcal" class="field-input" type="number" step="1" value="342" /></div>
          <div class="field-group"><label class="field-label">Protein (g/100g)</label><input id="rc-prot" class="field-input" type="number" step="0.1" value="11.2" /></div>
          <div class="field-group"><label class="field-label">Fat (g/100g)</label><input id="rc-fat" class="field-input" type="number" step="0.1" value="3.9" /></div>
          <div class="field-group"><label class="field-label">Carbs (g/100g)</label><input id="rc-carbs" class="field-input" type="number" step="0.1" value="65.5" /></div>
          <div class="field-group"><label class="field-label">Fibre (g/100g)</label><input id="rc-fibre" class="field-input" type="number" step="0.1" value="10.1" /></div>
          <div class="field-group"><label class="field-label">Cost (₹/kg)</label><input id="rc-cost" class="field-input" type="number" step="0.5" value="85" /></div>
          <div class="field-group"><label class="field-label">Max Cap (%)</label><input id="rc-cap" class="field-input" type="number" step="1" value="50" /></div>
          <div class="field-group"><label class="field-label">Clean-Label Status</label><select id="rc-clean" class="field-input"><option value="yes">yes</option><option value="check">check</option><option value="no">no</option></select></div>
        </div>
        <button class="btn btn-primary" type="submit">Save to Crop Database</button>
      </form>`);
  }

  function openVerifyModal(iid) {
    const ing = ((state.ingredientsData && state.ingredientsData.ingredients) || []).find((r) => r.ingredient_id === iid);
    if (!ing) return;
    const stepperField = (id, label, val, step) => `
      <div class="field-group">
        <label class="field-label" for="${id}">${label}</label>
        <div class="verify-stepper">
          <input id="${id}" class="verify-stepper-input" type="number" step="${step}" min="0" value="${val}" />
          <div class="verify-stepper-btns">
            <button class="verify-stepper-btn" type="button" data-step-target="${id}" data-step-dir="-1" aria-label="Decrease ${label}">−</button>
            <button class="verify-stepper-btn" type="button" data-step-target="${id}" data-step-dir="1" aria-label="Increase ${label}">+</button>
          </div>
        </div>
      </div>`;

    openModal('Verify crop data', `
      <form id="modal-verify-form" data-verify-id="${esc(iid)}" class="verify-form">
        <div class="verify-header-meta">
          <div class="verify-crop-heading">${esc(ing.name)}${ing.local_name ? ` · ${esc(ing.local_name)}` : ''}</div>
          <div class="verify-crop-sub">${esc(ing.category)} · ${esc(ing.region)} · source ${esc(ing.source_id || 'S-001')} · last changed ${esc(ing.updated_at || '—')}</div>
        </div>

        <div class="verify-section">
          <div class="verify-section-eyebrow">VALUES ON FILE</div>
          <p class="verify-section-note">Correct a number only when your source gives you a better one. Every field you change is written to the audit log with your name and the source.</p>
          <div class="verify-stepper-grid">
            ${stepperField('vf-energy_kcal', 'Energy (kcal / 100 g)', ing.energy_kcal, '1')}
            ${stepperField('vf-protein_g', 'Protein (g / 100 g)', ing.protein_g, '0.1')}
            ${stepperField('vf-fat_g', 'Fat (g / 100 g)', ing.fat_g, '0.1')}
            ${stepperField('vf-carbs_g', 'Carbs (g / 100 g)', ing.carbs_g, '0.1')}
            ${stepperField('vf-fibre_g', 'Fibre (g / 100 g)', ing.fibre_g, '0.1')}
            ${stepperField('vf-moisture_g', 'Moisture (g / 100 g)', ing.moisture_g, '0.1')}
            ${stepperField('vf-cost_per_kg', 'Cost (₹ / kg)', Number(ing.cost_per_kg).toFixed(2), '0.5')}
          </div>
        </div>

        <div class="verify-section">
          <div class="verify-section-eyebrow">PROOF</div>
          <div class="verify-check-list">
            <label class="verify-check-row">
              <input id="vf-nconf-chk" type="checkbox" ${ing.nutrition_confidence === 'verified' ? 'checked' : ''} />
              <span>Nutrition values confirmed against a source</span>
            </label>
            <label class="verify-check-row">
              <input id="vf-cconf-chk" type="checkbox" ${ing.cost_confidence === 'verified' ? 'checked' : ''} />
              <span>Cost confirmed (mandi price dated ${esc(ing.cost_date || 'recent survey')})</span>
            </label>
          </div>
          <div class="field-group">
            <label class="field-label" for="vf-ref">What did you check it against?</label>
            <input id="vf-ref" class="field-input" placeholder="e.g. IFCT 2017 entry, supplier CoA number, invoice date" />
          </div>
          <div class="field-group">
            <label class="field-label" for="vf-file">Lab report for proof</label>
            <label class="verify-upload-box" for="vf-file">
              <span class="btn btn-glass btn-sm">Upload</span>
              <span class="verify-upload-hint" id="vf-file-label">PDF, PNG, JPG · Optional lab CoA or mandi invoice</span>
              <input id="vf-file" type="file" accept=".pdf,.png,.jpg,.jpeg,.txt" hidden />
            </label>
          </div>
        </div>

        <button class="btn btn-primary verify-submit-btn" type="submit">Save and log it</button>
      </form>`, true);
  }

  function animateAssistantReply(msgObj) {
    const bubble = document.querySelector(`.chat-msg-bubble[data-msg-id="${msgObj.id}"]`);
    const textHost = bubble && bubble.querySelector('.chat-msg-text');
    const thread = document.getElementById('studio-chat-thread');
    if (!bubble || !textHost) {
      msgObj.animateIn = false;
      return;
    }
    const fullText = String(msgObj.text || '');
    const tokens = fullText.match(/\S+\s*/g) || [fullText];
    const batchSize = tokens.length > 90 ? 3 : tokens.length > 40 ? 2 : 1;
    let idx = 0;

    const tick = () => {
      if (!document.body.contains(textHost)) {
        msgObj.animateIn = false;
        return;
      }
      const slice = tokens.slice(idx, idx + batchSize).join('');
      if (slice) {
        const span = document.createElement('span');
        span.className = 'ai-stream-chunk';
        span.textContent = slice;
        textHost.appendChild(span);
        idx += batchSize;
        if (thread) thread.scrollTop = thread.scrollHeight;
      }
      if (idx < tokens.length) {
        setTimeout(() => requestAnimationFrame(tick), 24);
      } else {
        msgObj.animateIn = false;
        bubble.classList.remove('is-streaming');
        const cursor = bubble.querySelector('.ai-stream-cursor');
        if (cursor) cursor.remove();
      }
    };
    requestAnimationFrame(tick);
  }

  async function sendStudioPrompt() {
    const prompt = (state.studioPrompt || '').trim();
    if (!prompt || state.studioPending) return;
    if (!state.activeProjectId) {
      showToast('Create or select a project first.');
      return;
    }
    const pid = state.activeProjectId;
    const msgs = state.studioMessages[pid] || [];
    msgs.push({ role: 'user', text: prompt });
    state.studioMessages[pid] = msgs;
    state.studioPrompt = '';
    state.studioPending = true;
    state.studioPendingText = 'Searching private crop database & evaluating constraints…';
    renderView();

    const currentItems = ((state.studioDraftComputed || (state.workspace && state.workspace.computed) || {}).items) || [];
    const activeReg = (state.workspace && state.workspace.project && state.workspace.project.target_region) || 'Pan-India';
    try {
      const resp = await Api.chatStudio({
        project_id: pid,
        items: currentItems,
        instruction: prompt,
        mode: state.studioMode,
        constraints: state.studioConstraints,
        target_region: activeReg,
        history: msgs.slice(0, -1),
        model: state.studioModel
      });
      state.studioPending = false;
      state.studioStatus = resp.status;
      const assistantMsg = {
        id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        role: 'assistant',
        text: resp.reply,
        engine: resp.fallback_reason
          ? `${resp.engine} (fallback from ${resp.requested_model})`
          : resp.engine,
        thought: resp.thought,
        thought_summary: resp.thought_summary,
        animateIn: true
      };
      if (resp.fallback_reason) {
        showToast(`${resp.requested_model} fell back to ${resp.engine}: ${resp.fallback_reason}`);
      }
      msgs.push(assistantMsg);
      if (resp.items_changed) {
        state.studioDraftComputed = resp.computed;
        state.studioUnsaved = true;
        state.studioExplainBlend = '';
        state.studioExplainClean = '';
      }
      renderView();
      animateAssistantReply(assistantMsg);
    } catch (err) {
      state.studioPending = false;
      showToast(err.message);
      renderView();
    }
  }

  function renderCommandResults(query = '') {
    const user = state.bootstrap && state.bootstrap.user;
    if (!user) return;
    const q = query.trim().toLowerCase();
    const allowed = ROUTES.filter((r) => r.id !== 'admin' || user.role === 'lab_admin');
    const matches = allowed.filter((r) => r.label.toLowerCase().includes(q) || r.desc.toLowerCase().includes(q));
    el.cmdResults.innerHTML = matches.length
      ? matches.map((r) => `
        <button class="cmd-result-item" type="button" data-cmd-route="${r.id}">
          <span class="cmd-result-left"><span class="slot-icon">${r.icon}</span><span><div class="cmd-result-name">${esc(r.label)}</div><div class="cmd-result-desc">${esc(r.desc)}</div></span></span>
          <span class="empty-badge">#${r.id}</span>
        </button>`).join('')
      : `<div style="padding:18px;text-align:center;color:var(--text-muted);font-size:13px;">No matching sections found.</div>`;
  }

  document.addEventListener('click', async (event) => {
    const demoBtn = event.target.closest('[data-demo-login]');
    if (demoBtn) {
      const [email, password] = demoBtn.getAttribute('data-demo-login').split('|');
      try {
        await Api.login(email, password);
        await refreshBootstrap();
        await navigateTo('dashboard');
        showToast('Signed in successfully.');
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    const routeBtn = event.target.closest('[data-route]');
    if (routeBtn) {
      await navigateTo(routeBtn.getAttribute('data-route'));
      return;
    }

    const cmdRouteBtn = event.target.closest('[data-cmd-route]');
    if (cmdRouteBtn) {
      el.cmdOverlay.hidden = true;
      await navigateTo(cmdRouteBtn.getAttribute('data-cmd-route'));
      return;
    }

    const openProjModalBtn = event.target.closest('[data-open-project-modal]');
    if (openProjModalBtn) {
      openNewProjectModal();
      return;
    }

    const openStudioBtn = event.target.closest('[data-open-in-studio]');
    if (openStudioBtn) {
      state.activeProjectId = openStudioBtn.getAttribute('data-open-in-studio');
      await navigateTo('studio');
      return;
    }

    const modelTrigger = event.target.closest('[data-model-picker-trigger]');
    if (modelTrigger) {
      const picker = modelTrigger.closest('[data-model-picker]');
      const menu = picker?.querySelector('.model-picker-menu');
      const isOpen = picker?.classList.contains('is-open');
      if (picker && menu) {
        picker.classList.toggle('is-open', !isOpen);
        menu.hidden = Boolean(isOpen);
        modelTrigger.setAttribute('aria-expanded', String(!isOpen));
      }
      return;
    }

    const modelOption = event.target.closest('[data-model-option]');
    if (modelOption) {
      state.studioModel = modelOption.getAttribute('data-model-option') || '';
      Prefs.save({ defaultModel: state.studioModel });
      state.studioStatus = '';
      const chosenName = modelOption.querySelector('.model-option-name')?.textContent || state.studioModel || 'Smart Router (Auto)';
      renderView();
      showToast(`AI Model: ${chosenName}`);
      return;
    }

    // Close open model picker when clicking outside
    const openPicker = document.querySelector('[data-model-picker].is-open');
    if (openPicker && !event.target.closest('[data-model-picker]')) {
      openPicker.classList.remove('is-open');
      const menu = openPicker.querySelector('.model-picker-menu');
      const trig = openPicker.querySelector('[data-model-picker-trigger]');
      if (menu) menu.hidden = true;
      if (trig) trig.setAttribute('aria-expanded', 'false');
    }

    const modeBtn = event.target.closest('[data-studio-mode-btn]');
    if (modeBtn) {
      state.studioMode = modeBtn.getAttribute('data-studio-mode-btn');
      renderView();
      return;
    }

    const tabBtn = event.target.closest('[data-studio-tab]');
    if (tabBtn) {
      state.studioTab = tabBtn.getAttribute('data-studio-tab');
      renderView();
      return;
    }

    const tagBtn = event.target.closest('[data-composer-tag]');
    if (tagBtn) {
      const val = tagBtn.getAttribute('data-composer-tag');
      if (state.studioConstraints.includes(val)) state.studioConstraints = state.studioConstraints.filter((x) => x !== val);
      else state.studioConstraints.push(val);
      renderView();
      return;
    }

    const quickBtn = event.target.closest('[data-quick-prompt]');
    if (quickBtn) {
      state.studioPrompt = quickBtn.getAttribute('data-quick-prompt');
      const inp = document.getElementById('studio-prompt-input');
      if (inp) {
        inp.value = state.studioPrompt;
        inp.focus();
      }
      return;
    }

    if (event.target.closest('[data-studio-reset]')) {
      if (state.activeProjectId) {
        state.studioMessages[state.activeProjectId] = [];
        try { await Api.clearProjectChats(state.activeProjectId); } catch (_) {}
      }
      state.studioDraftComputed = { items: [], rows: [], blend: {}, cost_per_kg: 0, baseline_cost: 0, delta_pct: 0, findings: [], total_pct: 0 };
      state.studioUnsaved = false;
      state.studioExplainBlend = '';
      state.studioExplainClean = '';
      renderView();
      showToast('Workspace and saved chat history reset.');
      return;
    }

    if (event.target.closest('#studio-draft-btn')) {
      openDraftModal();
      return;
    }

    if (event.target.closest('#studio-add-comp-btn')) {
      if (!state.ingredientsData) await loadIngredients();
      openAddComponentModal();
      return;
    }

    const remBtn = event.target.closest('[data-remove-ing]');
    if (remBtn) {
      const targetId = remBtn.getAttribute('data-remove-ing');
      const curr = ((state.studioDraftComputed || (state.workspace && state.workspace.computed) || {}).items) || [];
      const next = curr.filter(([k]) => k !== targetId);
      try {
        const res = await Api.computeStudio(next, true);
        state.studioDraftComputed = res.computed;
        state.studioUnsaved = next.length > 0;
        renderView();
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    const swapBtn = event.target.closest('[data-apply-swap]');
    if (swapBtn) {
      const [badId, goodId] = swapBtn.getAttribute('data-apply-swap').split('|');
      const curr = ((state.studioDraftComputed || (state.workspace && state.workspace.computed) || {}).items) || [];
      const next = curr.map(([k, v]) => [k === badId ? goodId : k, v]);
      try {
        const res = await Api.computeStudio(next, true);
        state.studioDraftComputed = res.computed;
        state.studioUnsaved = true;
        renderView();
        showToast('Applied natural substitute and recomputed.');
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    if (event.target.closest('#studio-save-btn')) {
      const curr = ((state.studioDraftComputed || (state.workspace && state.workspace.computed) || {}).items) || [];
      if (!curr.length || !state.activeProjectId) {
        showToast('Generate a formulation first before saving.');
        return;
      }
      try {
        const res = await Api.saveStudio({ project_id: state.activeProjectId, items: curr });
        await loadWorkspace(state.activeProjectId);
        await refreshBootstrap();
        renderView();
        showToast(res.message);
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    if (event.target.closest('#studio-export-btn')) {
      printStudioSpecPdf();
      return;
    }

    if (event.target.closest('#studio-explain-blend')) {
      const curr = ((state.studioDraftComputed || (state.workspace && state.workspace.computed) || {}).items) || [];
      state.studioExplaining = 'blend';
      renderView();
      try {
        const res = await Api.explainStudio({ kind: 'blend', items: curr, model: state.studioModel });
        state.studioExplainBlend = res.text;
        state.studioStatus = res.status;
      } catch (err) {
        showToast(err.message);
      }
      state.studioExplaining = '';
      renderView();
      return;
    }

    if (event.target.closest('#studio-explain-clean')) {
      const curr = ((state.studioDraftComputed || (state.workspace && state.workspace.computed) || {}).items) || [];
      state.studioExplaining = 'clean';
      renderView();
      try {
        const res = await Api.explainStudio({ kind: 'clean_label', items: curr, model: state.studioModel });
        state.studioExplainClean = res.text;
        state.studioStatus = res.status;
      } catch (err) {
        showToast(err.message);
      }
      state.studioExplaining = '';
      renderView();
      return;
    }

    const loadVerBtn = event.target.closest('[data-load-version]');
    if (loadVerBtn) {
      const fid = loadVerBtn.getAttribute('data-load-version');
      await loadWorkspace(state.activeProjectId, { version: fid });
      state.studioTab = 'formulation';
      renderView();
      showToast('Loaded selected formulation version.');
      return;
    }

    const openCropBtn = event.target.closest('[data-open-crop]');
    if (openCropBtn) {
      const cid = openCropBtn.getAttribute('data-open-crop');
      await navigateTo(`crop/${cid}`);
      return;
    }

    const formulateCropBtn = event.target.closest('[data-formulate-crop]');
    if (formulateCropBtn) {
      const cname = formulateCropBtn.getAttribute('data-formulate-crop');
      state.studioPrompt = `Create a clean-label formulation featuring ${cname} balanced with local crops.`;
      await navigateTo('studio');
      return;
    }

    const remPhotoBtn = event.target.closest('[data-remove-crop-photo]');
    if (remPhotoBtn) {
      const iid = remPhotoBtn.getAttribute('data-remove-crop-photo');
      try {
        const res = await Api.uploadIngredientPhoto(iid, { remove: true });
        await loadIngredients();
        renderView();
        showToast(res.message);
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    const cropLayoutBtn = event.target.closest('[data-crop-layout]');
    if (cropLayoutBtn) {
      state.cropLayout = cropLayoutBtn.getAttribute('data-crop-layout');
      renderView();
      return;
    }

    const cropCatBtn = event.target.closest('[data-crop-cat]');
    if (cropCatBtn) {
      state.cropCategory = cropCatBtn.getAttribute('data-crop-cat');
      renderView();
      return;
    }

    if (event.target.closest('#crops-register-btn') || event.target.closest('#ing-new-btn')) {
      openRegisterCropModal();
      return;
    }

    const ingCatBtn = event.target.closest('[data-ing-cat]');
    if (ingCatBtn) {
      state.ingCategory = ingCatBtn.getAttribute('data-ing-cat');
      renderView();
      return;
    }

    const stepBtn = event.target.closest('[data-step-target]');
    if (stepBtn) {
      const inp = document.getElementById(stepBtn.getAttribute('data-step-target'));
      if (inp) {
        const dir = Number(stepBtn.getAttribute('data-step-dir') || 1);
        const step = Number(inp.getAttribute('step') || 1);
        const decimals = String(step).includes('.') ? String(step).split('.')[1].length : 0;
        const next = Math.max(0, Number(inp.value || 0) + dir * step);
        inp.value = next.toFixed(decimals);
      }
      return;
    }

    const verifyBtn = event.target.closest('[data-verify-ing]');
    if (verifyBtn) {
      openVerifyModal(verifyBtn.getAttribute('data-verify-ing'));
      return;
    }

    const formFilterBtn = event.target.closest('[data-form-filter]');
    if (formFilterBtn) {
      state.formFilter = formFilterBtn.getAttribute('data-form-filter');
      renderView();
      return;
    }

    const adminTabBtn = event.target.closest('[data-admin-tab]');
    if (adminTabBtn) {
      const nextTab = adminTabBtn.getAttribute('data-admin-tab');
      if (nextTab === state.adminTab) return;
      state.adminTab = nextTab;
      document.querySelectorAll('[data-admin-tab]').forEach((btn) => {
        btn.classList.toggle('is-active', btn.getAttribute('data-admin-tab') === nextTab);
      });
      const host = document.getElementById('admin-tab-body');
      if (host) {
        host.innerHTML = Views.renderAdminTabBody(state);
        host.classList.remove('tab-panel-switch');
        void host.offsetWidth;
        host.classList.add('tab-panel-switch');
      } else {
        renderView();
      }
      return;
    }

    if (event.target.closest('#admin-invite-btn')) {
      openModal('Invite Lab Researcher', `
        <form id="modal-invite-form" style="display:flex;flex-direction:column;gap:12px;">
          <div class="field-group"><label class="field-label">Full Name</label><input id="iw-name" class="field-input" required placeholder="e.g. Aditi Sharma" /></div>
          <div class="field-group"><label class="field-label">Email</label><input id="iw-email" class="field-input" type="email" required placeholder="worker@lab.org" /></div>
          <div class="field-group"><label class="field-label">Temporary Password (min 8 chars)</label><input id="iw-pass" class="field-input" type="password" required minlength="8" /></div>
          <button class="btn btn-primary" type="submit">Create Worker Account</button>
        </form>`);
      return;
    }

    const toggleUserBtn = event.target.closest('[data-toggle-user]');
    if (toggleUserBtn) {
      const [uid, activeStr] = toggleUserBtn.getAttribute('data-toggle-user').split('|');
      try {
        const res = await Api.toggleUser(uid, activeStr === 'true');
        await loadAdmin();
        renderView();
        showToast(res.message);
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    const toggleAccBtn = event.target.closest('[data-toggle-access]');
    if (toggleAccBtn) {
      const [pid, uid, grantStr] = toggleAccBtn.getAttribute('data-toggle-access').split('|');
      try {
        const res = await Api.updateAccess(pid, uid, grantStr === 'true');
        await loadAdmin();
        await refreshBootstrap();
        renderView();
        showToast(res.message);
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    const auditBtn = event.target.closest('[data-open-audit]');
    if (auditBtn) {
      const eid = auditBtn.getAttribute('data-open-audit');
      const data = state.adminData || {};
      const ev = (data.audit || []).find((x) => x.event_id === eid);
      if (!ev) return;
      const actor = (data.user_names || {})[ev.actor_user_id] || ev.actor_user_id;
      openModal(`Audit Entry · ${ev.event_id}`, `
        <div style="display:flex;flex-direction:column;gap:8px;font-size:13px;">
          <div><strong>Note:</strong> ${esc(ev.note || 'Updated')}</div>
          <div><strong>Actor:</strong> ${esc(actor)} · <strong>Timestamp:</strong> <code>${esc(ev.at)}</code></div>
          <div><strong>Table / Record:</strong> ${esc(ev.table)} / <code>${esc(ev.record_id || '—')}</code></div>
          <div><strong>Field:</strong> ${esc(ev.field || '—')}</div>
          <div><strong>Change:</strong> ${esc(ev.old_value || '—')} → ${esc(ev.new_value || '—')}</div>
          ${ev.lab_report ? `<div style="margin-top:8px;"><a class="btn btn-primary btn-sm" href="/api/audit/${esc(ev.event_id)}/report" download>Download Attached Lab Report</a></div>` : '<div style="color:var(--text-muted);">No lab report attached.</div>'}
        </div>`);
      return;
    }

    const settingsTabBtn = event.target.closest('[data-settings-tab]');
    if (settingsTabBtn) {
      state.settingsTab = settingsTabBtn.getAttribute('data-settings-tab');
      renderView();
      return;
    }

    const prefSwitch = event.target.closest('[data-pref-switch]');
    if (prefSwitch) {
      const key = prefSwitch.getAttribute('data-pref-switch');
      const current = prefSwitch.getAttribute('aria-checked') === 'true';
      Prefs.save({ [key]: !current });
      renderView();
      return;
    }

    if (event.target.closest('#settings-test-conn')) {
      try {
        state.healthCheck = await Api.health();
        renderView();
        showToast('Tested backend, skill loader, and FreeLLMAPI router.');
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    if (event.target.closest('#settings-signout-btn') || event.target.closest('#modal-signout-btn')) {
      closeModal();
      await Api.logout();
      await refreshBootstrap();
      renderView();
      showToast('Signed out.');
    }
  });

  document.addEventListener('submit', async (event) => {
    const form = event.target;
    if (form.id === 'auth-signin-form') {
      event.preventDefault();
      try {
        await Api.login(document.getElementById('signin-email').value, document.getElementById('signin-password').value);
        await refreshBootstrap();
        await navigateTo('dashboard');
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    if (form.id === 'studio-composer-form') {
      event.preventDefault();
      await sendStudioPrompt();
      return;
    }

    if (form.id === 'modal-new-project-form') {
      event.preventDefault();
      try {
        const regEl = document.getElementById('np-region');
        const res = await Api.createProject(
          document.getElementById('np-name').value,
          document.getElementById('np-desc').value,
          regEl ? regEl.value : 'Pan-India'
        );
        closeModal();
        await refreshBootstrap();
        state.activeProjectId = res.project_id;
        await navigateTo('studio');
        showToast(res.message);
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    if (form.id === 'modal-add-comp-form') {
      event.preventDefault();
      const iid = document.getElementById('ac-ing').value;
      const pct = parseFloat(document.getElementById('ac-pct').value || '0');
      const curr = ((state.studioDraftComputed || (state.workspace && state.workspace.computed) || {}).items) || [];
      const next = [...curr.filter(([k]) => k !== iid), [iid, pct]];
      try {
        const res = await Api.computeStudio(next, true);
        closeModal();
        state.studioDraftComputed = res.computed;
        state.studioUnsaved = true;
        renderView();
        showToast(res.notes && res.notes.length ? res.notes.join('; ') : 'Updated formulation shares.');
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    if (form.id === 'modal-ai-draft-form') {
      event.preventDefault();
      const brief = document.getElementById('dr-brief').value;
      const cook = document.getElementById('dr-cook').value;
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Formulating from DB…';
      }
      try {
        const res = await Api.draftStudio({
          brief,
          cook,
          project_name: state.workspace ? state.workspace.project.name : '',
          model: state.studioModel
        });
        closeModal();
        state.studioDraftComputed = res.computed;
        state.studioUnsaved = true;
        state.studioStatus = res.status;
        if (state.activeProjectId) {
          state.studioMessages[state.activeProjectId] = state.studioMessages[state.activeProjectId] || [];
          state.studioMessages[state.activeProjectId].push({
            role: 'assistant',
            text: `AI Draft “${res.name}”: ${res.rationale}`,
            engine: res.engine
          });
        }
        renderView();
        showToast(`Loaded AI draft: ${res.name}`);
      } catch (err) {
        if (btn) {
          btn.disabled = false;
          btn.textContent = 'Generate Validated Draft';
        }
        showToast(err.message);
      }
      return;
    }

    if (form.id === 'modal-reg-crop-form') {
      event.preventDefault();
      try {
        const res = await Api.createIngredient({
          name: document.getElementById('rc-name').value,
          local_name: document.getElementById('rc-local').value,
          category: document.getElementById('rc-cat').value,
          region: document.getElementById('rc-region').value,
          energy_kcal: document.getElementById('rc-kcal').value,
          protein_g: document.getElementById('rc-prot').value,
          fat_g: document.getElementById('rc-fat').value,
          carbs_g: document.getElementById('rc-carbs').value,
          fibre_g: document.getElementById('rc-fibre').value,
          cost_per_kg: document.getElementById('rc-cost').value,
          max_practical_pct: document.getElementById('rc-cap').value,
          is_clean_label: document.getElementById('rc-clean').value
        });
        closeModal();
        await loadIngredients();
        await refreshBootstrap();
        renderView();
        showToast(res.message);
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    if (form.id === 'modal-verify-form') {
      event.preventDefault();
      const iid = form.getAttribute('data-verify-id');
      const fileInp = document.getElementById('vf-file');
      const readReport = () => new Promise((resolve) => {
        if (!fileInp || !fileInp.files || !fileInp.files[0]) return resolve({});
        const f = fileInp.files[0];
        const reader = new FileReader();
        reader.onload = () => {
          const b64 = String(reader.result || '').split(',')[1] || '';
          resolve({ report_name: f.name, report_b64: b64 });
        };
        reader.readAsDataURL(f);
      });
      try {
        const rep = await readReport();
        const ing = ((state.ingredientsData && state.ingredientsData.ingredients) || []).find((r) => r.ingredient_id === iid) || {};
        const nChecked = Boolean(document.getElementById('vf-nconf-chk')?.checked);
        const cChecked = Boolean(document.getElementById('vf-cconf-chk')?.checked);
        const nConf = nChecked ? 'verified' : (ing.nutrition_confidence === 'verified' ? 'estimated' : (ing.nutrition_confidence || 'estimated'));
        const cConf = cChecked ? 'verified' : (ing.cost_confidence === 'verified' ? 'estimated' : (ing.cost_confidence || 'estimated'));
        const res = await Api.verifyIngredient(iid, Object.assign({
          values: {
            energy_kcal: Number(document.getElementById('vf-energy_kcal').value),
            protein_g: Number(document.getElementById('vf-protein_g').value),
            fat_g: Number(document.getElementById('vf-fat_g').value),
            carbs_g: Number(document.getElementById('vf-carbs_g').value),
            fibre_g: Number(document.getElementById('vf-fibre_g').value),
            moisture_g: Number(document.getElementById('vf-moisture_g').value),
            cost_per_kg: Number(document.getElementById('vf-cost_per_kg').value)
          },
          nutrition_confidence: nConf,
          cost_confidence: cConf,
          reference: document.getElementById('vf-ref').value
        }, rep));
        closeModal();
        await loadIngredients();
        await refreshBootstrap();
        renderView();
        showToast(res.message);
      } catch (err) {
        showToast(err.message);
      }
      return;
    }

    if (form.id === 'modal-invite-form') {
      event.preventDefault();
      try {
        const res = await Api.createWorker({
          name: document.getElementById('iw-name').value,
          email: document.getElementById('iw-email').value,
          password: document.getElementById('iw-pass').value
        });
        closeModal();
        await loadAdmin();
        renderView();
        showToast(res.message);
      } catch (err) {
        showToast(err.message);
      }
    }
  });

  document.addEventListener('change', async (event) => {
    if (event.target.id === 'studio-project-select') {
      state.activeProjectId = event.target.value;
      await loadWorkspace(state.activeProjectId);
      renderView();
    } else if (event.target.id === 'studio-region-select') {
      const newReg = event.target.value;
      if (state.activeProjectId) {
        const curr = ((state.studioDraftComputed || (state.workspace && state.workspace.computed) || {}).items) || [];
        try {
          const res = await Api.updateProjectRegion(state.activeProjectId, newReg, curr);
          if (state.workspace && state.workspace.project) state.workspace.project.target_region = res.target_region;
          if (curr.length) state.studioDraftComputed = res.computed;
          else if (state.workspace) state.workspace.computed = res.computed;
          await refreshBootstrap();
          renderView();
          showToast(res.message);
        } catch (err) {
          showToast(err.message);
        }
      }
    } else if (event.target.id === 'studio-model-select') {
      state.studioModel = event.target.value;
      Prefs.save({ defaultModel: state.studioModel });
      state.studioStatus = '';
      renderView();
    } else if (event.target.id === 'settings-default-model') {
      state.studioModel = event.target.value;
      Prefs.save({ defaultModel: state.studioModel });
      renderView();
      showToast('Updated default AI router model.');
    } else if (event.target.id === 'vf-file') {
      const lbl = document.getElementById('vf-file-label');
      const f = event.target.files && event.target.files[0];
      if (lbl) lbl.textContent = f ? f.name : 'PDF, PNG, JPG · Optional lab CoA or mandi invoice';
    } else if (event.target.id === 'crop-photo-input') {
      const file = event.target.files && event.target.files[0];
      const iid = event.target.getAttribute('data-photo-target');
      if (!file || !iid) return;
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const b64 = String(reader.result || '').split(',')[1] || '';
          const res = await Api.uploadIngredientPhoto(iid, { filename: file.name, image_b64: b64 });
          await loadIngredients();
          renderView();
          showToast(res.message);
        } catch (err) {
          showToast(err.message);
        }
      };
      reader.readAsDataURL(file);
    } else if (event.target.id === 'crops-cat-select') {
      state.cropCategory = event.target.value;
      const host = document.getElementById('crops-results-host');
      if (host) host.innerHTML = Views.renderCropCards(state);
    } else if (event.target.id === 'crops-show-select') {
      state.cropShow = event.target.value;
      const host = document.getElementById('crops-results-host');
      if (host) host.innerHTML = Views.renderCropCards(state);
    } else if (event.target.id === 'studio-cmp-a' || event.target.id === 'studio-cmp-b') {
      const a = document.getElementById('studio-cmp-a')?.value;
      const b = document.getElementById('studio-cmp-b')?.value;
      await loadWorkspace(state.activeProjectId, { cmp_a: a, cmp_b: b, keepDraft: true });
      renderView();
    } else if (event.target.id === 'audit-area-select') {
      state.auditArea = event.target.value;
      const host = document.getElementById('audit-rows-host');
      if (host) host.innerHTML = Views.renderAuditRows(state);
    }
  });

  document.addEventListener('input', (event) => {
    if (event.target.id === 'studio-prompt-input') {
      state.studioPrompt = event.target.value;
    } else if (event.target.id === 'crops-search-input') {
      state.cropQuery = event.target.value;
      const host = document.getElementById('crops-results-host');
      if (host) host.innerHTML = Views.renderCropCards(state);
    } else if (event.target.id === 'ing-search-input') {
      state.ingQuery = event.target.value;
      const host = document.getElementById('ingredients-table-host');
      if (host) host.innerHTML = Views.renderIngredientsRows(state);
    } else if (event.target.id === 'form-search-input') {
      state.formQuery = event.target.value;
      const host = document.getElementById('formulations-list-host');
      if (host) host.innerHTML = Views.renderFormulationCards(state);
    } else if (event.target.id === 'audit-search-input') {
      state.auditQuery = event.target.value;
      const host = document.getElementById('audit-rows-host');
      if (host) host.innerHTML = Views.renderAuditRows(state);
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.target.id === 'studio-prompt-input' && event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendStudioPrompt();
      return;
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      if (el.cmdOverlay.hidden) {
        el.cmdOverlay.hidden = false;
        el.cmdInput.value = '';
        renderCommandResults('');
        setTimeout(() => el.cmdInput.focus(), 20);
      } else {
        el.cmdOverlay.hidden = true;
      }
    } else if (event.key === 'Escape') {
      el.cmdOverlay.hidden = true;
      closeModal();
      const openPicker = document.querySelector('[data-model-picker].is-open');
      if (openPicker) {
        openPicker.classList.remove('is-open');
        const menu = openPicker.querySelector('.model-picker-menu');
        const trig = openPicker.querySelector('[data-model-picker-trigger]');
        if (menu) menu.hidden = true;
        if (trig) trig.setAttribute('aria-expanded', 'false');
      }
      state.mobileNavOpen = false;
      el.shell.setAttribute('data-mobile-nav', 'false');
    }
  });

  el.navToggleBtn.addEventListener('click', () => {
    if (window.innerWidth <= 860) {
      state.mobileNavOpen = false;
      el.shell.setAttribute('data-mobile-nav', 'false');
    } else {
      state.navExpanded = !state.navExpanded;
      el.shell.setAttribute('data-nav-expanded', String(state.navExpanded));
      el.navToggleBtn.setAttribute('aria-expanded', String(state.navExpanded));
    }
  });

  el.mobileMenuBtn.addEventListener('click', () => {
    state.mobileNavOpen = true;
    el.shell.setAttribute('data-mobile-nav', 'true');
  });
  el.navBackdrop.addEventListener('click', () => {
    state.mobileNavOpen = false;
    el.shell.setAttribute('data-mobile-nav', 'false');
  });

  el.avatarChip.addEventListener('click', () => {
    const user = state.bootstrap && state.bootstrap.user;
    if (!user) return;
    openModal('Lab Profile', `
      <div style="display:flex;flex-direction:column;gap:10px;font-size:13.5px;">
        <div><strong>${esc(user.name)}</strong> (${esc(user.role === 'lab_admin' ? 'Lab Admin' : 'Lab Worker')})</div>
        <div style="color:var(--text-secondary);">${esc(user.email)} · ${esc(user.lab_id)}</div>
        <div style="display:flex;gap:10px;margin-top:8px;">
          <button class="btn btn-glass btn-sm" type="button" data-route="settings" onclick="document.getElementById('app-modal-overlay').hidden=true;">Open Settings</button>
          <button class="btn btn-primary btn-sm" type="button" id="modal-signout-btn">Sign Out</button>
        </div>
      </div>`);
  });

  el.cmdTrigger.addEventListener('click', () => {
    el.cmdOverlay.hidden = false;
    el.cmdInput.value = '';
    renderCommandResults('');
    setTimeout(() => el.cmdInput.focus(), 20);
  });
  el.cmdClose.addEventListener('click', () => { el.cmdOverlay.hidden = true; });
  el.cmdOverlay.addEventListener('click', (e) => { if (e.target === el.cmdOverlay) el.cmdOverlay.hidden = true; });
  el.cmdInput.addEventListener('input', (e) => renderCommandResults(e.target.value));
  el.appModalClose.addEventListener('click', closeModal);
  el.appModalOverlay.addEventListener('click', (e) => { if (e.target === el.appModalOverlay) closeModal(); });

  window.addEventListener('hashchange', () => {
    const h = window.location.hash.replace(/^#/, '');
    if (h && h !== state.route) navigateTo(h, false);
  });

  (async function boot() {
    try {
      await refreshBootstrap();
      const hashRoute = window.location.hash.replace(/^#/, '');
      await navigateTo(hashRoute || 'dashboard', false);
    } catch (err) {
      el.mainViewport.innerHTML = `<div class="empty-panel"><h2>Could not connect to SmartCrop.AI Server</h2><p>${esc(err.message)}</p></div>`;
    }
  })();
})();
