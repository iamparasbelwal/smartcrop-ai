/**
 * SmartCrop.AI — Formulation Studio View (Clean Split Workbench + Live Co-Pilot)
 */
window.SmartCrop = window.SmartCrop || {};
window.SmartCrop.Views = window.SmartCrop.Views || {};

window.SmartCrop.Views.studio = function renderStudio(state) {
  const { Icons, Utils, Prefs } = window.SmartCrop;
  const esc = Utils.esc;
  const prefs = Prefs.load();
  const activeTab = state.studioTab || 'formulation';
  const boot = state.bootstrap || {};
  const ai = boot.ai || {};
  const projects = boot.projects || [];
  const ws = state.workspace || {};
  const activeProject = ws.project || projects.find((p) => p.project_id === state.activeProjectId) || projects[0] || null;
  const pid = activeProject ? activeProject.project_id : '';
  const computed = state.studioDraftComputed || ws.computed || { items: [], rows: [], blend: {}, cost_per_kg: 0, baseline_cost: 0, delta_pct: 0, findings: [], total_pct: 0 };
  const rows = computed.rows || [];
  const blend = computed.blend || {};
  const findings = computed.findings || [];
  const versions = ws.versions || [];
  const regional = computed.regional || {};
  const targetRegions = boot.target_regions || ['Pan-India', 'Rajasthan', 'Karnataka', 'Maharashtra', 'Madhya Pradesh', 'Gujarat', 'Andhra Pradesh', 'Punjab', 'West Bengal', 'Uttarakhand'];
  const activeRegion = (activeProject && activeProject.target_region) || regional.target_region || 'Pan-India';
  const hasItems = rows.length > 0;
  const messages = (pid && state.studioMessages[pid]) || [];
  const selectedModel = state.studioModel != null ? state.studioModel : (prefs.defaultModel || '');
  const modelChoices = ai.choices || [{ label: 'Smart Router (Auto)', value: '' }];
  const engineLabel = ai.model || 'ROUTER · LLAMA-3.3-70B-FP8-FAST';
  const activeChoice = modelChoices.find((c) => c.value === selectedModel) || modelChoices[0];
  const parseChoice = (label) => {
    const parts = String(label || '').split('·');
    return {
      name: (parts[0] || '').trim(),
      tag: parts.length > 1 ? parts.slice(1).join('·').trim() : ''
    };
  };

  const quickPrompts = hasItems
    ? [
        { icon: Icons.bolt, label: 'More protein', prompt: 'Boost protein while keeping shares practical' },
        { icon: Icons.trendingDown, label: 'Lower cost', prompt: 'Reduce ingredient cost per kg cleanly' },
        { icon: Icons.grass, label: 'Millet base', prompt: 'Replace wheat with regional millet base' },
        { icon: Icons.waterDrop, label: 'Less sugar', prompt: 'Lower jaggery or sugar share for a low-sugar blend' }
      ]
    : [
        { icon: Icons.bolt, label: 'High protein', prompt: 'Create a high-protein formulation from the private crop database for this project goal.' },
        { icon: Icons.trendingDown, label: 'Low cost', prompt: 'Create an affordable, cost-optimized formulation using local crops from the database.' },
        { icon: Icons.grass, label: 'Millet base', prompt: 'Build a millet-rich clean-label formulation using local crops from the database.' },
        { icon: Icons.waterDrop, label: 'Low sugar', prompt: 'Build a low-sugar clean-label plant formulation using ingredients from the database.' }
      ];

  const cleanVerdict = !hasItems
    ? { val: '—', sub: 'Not screened' }
    : computed.flagged_count > 0
      ? { val: `${computed.flagged_count} Flagged`, sub: 'Watchlist hit' }
      : computed.review_count > 0
        ? { val: `${computed.review_count} Review`, sub: 'Check supplier spec' }
        : { val: 'Clean', sub: 'Zero flags found' };

  const deltaSign = computed.delta_pct > 0 ? '+' : '';
  const summaryCards = [
    {
      label: 'COST / KG',
      value: hasItems ? `₹${Number(computed.cost_per_kg || 0).toFixed(2)}` : '',
      status: hasItems ? `${deltaSign}${computed.delta_pct}% vs wheat base` : '',
      filled: hasItems
    },
    {
      label: 'PROTEIN',
      value: hasItems ? `${blend.protein_g ?? 0}g` : '',
      status: hasItems ? `per 100g · Fibre ${blend.fibre_g ?? 0}g` : '',
      filled: hasItems
    },
    {
      label: 'ENERGY',
      value: hasItems ? `${Math.round(blend.energy_kcal || 0)}` : '',
      status: hasItems ? `kcal / 100g (${rows.length} crops)` : '',
      filled: hasItems
    },
    {
      label: 'CLEAN LABEL',
      value: hasItems ? cleanVerdict.val : '',
      status: hasItems ? cleanVerdict.sub : '',
      filled: hasItems
    }
  ];

  const tabs = [
    { id: 'formulation', label: 'Formulation' },
    { id: 'nutrition', label: 'Nutrition' },
    { id: 'cost', label: 'Cost' },
    { id: 'additive', label: 'Additive Check' },
    { id: 'versions', label: 'Versions' }
  ];

  const renderFormulationTab = () => {
    if (!hasItems) {
      const skelWidths = [
        ['138px', '72px', '56px', '76px', '38px'],
        ['116px', '58px', '56px', '54px', '38px'],
        ['132px', '64px', '56px', '68px', '38px'],
        ['96px', '48px', '56px', '44px', '38px'],
        ['108px', '54px', '56px', '60px', '38px']
      ];
      return `
        <div class="studio-table-scroll">
          <table class="spec-table spec-table-clean">
            <thead>
              <tr><th>INGREDIENT / CROP</th><th>CATEGORY</th><th>SHARE (%)</th><th>₹ / 100 G</th></tr>
            </thead>
            <tbody>
              ${skelWidths.map(([w1, w2, wCat, wShare, wCost]) => `
                <tr class="spec-skeleton-row" aria-hidden="true">
                  <td>
                    <span class="spec-ghost-bar" style="width:${w1};"></span>
                    <span class="spec-ghost-bar sub" style="width:${w2};"></span>
                  </td>
                  <td><span class="spec-ghost-pill" style="width:${wCat};"></span></td>
                  <td><span class="spec-ghost-bar" style="width:${wShare}; height:6px;"></span></td>
                  <td><span class="spec-ghost-pill" style="width:${wCost};"></span></td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
        <div class="spec-empty-callout">
          <div class="spec-empty-title">No formulation yet</div>
          <div class="spec-empty-desc">Send us your requirements in the chat, the AI models will do the rest for you.</div>
        </div>`;
    }

    return `
      <div class="studio-table-scroll">
        <table class="spec-table spec-table-clean">
          <thead>
            <tr><th>Ingredient / Crop</th><th>Category</th><th>Share (%)</th><th>₹ / 100 g</th><th></th></tr>
          </thead>
          <tbody>
            ${rows.map((r) => {
              const tierCls = r.region_tier === 'LOCAL' ? 'ok' : (r.region_tier === 'NEARBY' ? 'warn' : '');
              const tierTag = (regional.is_targeted && r.region_tier && r.region_tier !== 'STANDARD')
                ? `<span class="badge-pill ${tierCls}" style="font-size:10px;padding:1px 6px;margin-left:5px;">${esc(r.region_tier)}</span>`
                : '';
              return `
              <tr>
                <td>
                  <div style="font-weight: 600; color: var(--forest-950);">${esc(r.name)}${tierTag}</div>
                  <div style="font-size: 11px; color: var(--text-muted);">${esc(r.local_name || '')}${r.local_name ? ' · ' : ''}${esc(r.region)} · cap ${r.max_practical_pct}%</div>
                </td>
                <td><span class="badge-pill">${esc(r.category)}</span></td>
                <td>
                  <div class="share-meter">
                    <div class="share-meter-track"><div class="share-meter-fill" style="width:${Math.min(100, r.share_pct)}%"></div></div>
                    <strong style="font-family: var(--font-mono); font-size: 12.5px;">${r.share_pct}%</strong>
                  </div>
                </td>
                <td style="font-family: var(--font-mono); font-size: 12.5px;">₹${r.cost_per_100g.toFixed(2)}</td>
                <td style="text-align:right;">
                  <button class="btn-icon-remove" type="button" data-remove-ing="${esc(r.ingredient_id)}" title="Remove ingredient">×</button>
                </td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>
      <div class="studio-tab-footer-bar">
        <span style="font-size: 11.5px; color: var(--text-muted);">Computed in Python from <code>data/ingredients.csv</code>.</span>
        <div class="spec-table-footer-meta"><span>Total:</span><strong>${computed.total_pct}%</strong></div>
      </div>`;
  };

  const renderNutritionTab = () => {
    if (!hasItems) return renderFormulationTab();
    const moistureAvg = rows.reduce((acc, r) => acc + (r.moisture_g * r.share_pct) / 100, 0);
    const dmFactor = prefs.dryMatter && moistureAvg < 95 ? 100 / (100 - moistureAvg) : 1;
    const nutRows = [
      ['Energy', `${Math.round((blend.energy_kcal || 0) * dmFactor)} kcal`, `${Math.round(((blend.energy_kcal || 0) * (computed.serving_grams || 40)) / 100)} kcal`],
      ['Protein', `${((blend.protein_g || 0) * dmFactor).toFixed(1)} g`, `${(((blend.protein_g || 0) * (computed.serving_grams || 40)) / 100).toFixed(1)} g`],
      ['Fat', `${((blend.fat_g || 0) * dmFactor).toFixed(1)} g`, `${(((blend.fat_g || 0) * (computed.serving_grams || 40)) / 100).toFixed(1)} g`],
      ['Carbohydrate', `${((blend.carbs_g || 0) * dmFactor).toFixed(1)} g`, `${(((blend.carbs_g || 0) * (computed.serving_grams || 40)) / 100).toFixed(1)} g`],
      ['Dietary fibre', `${((blend.fibre_g || 0) * dmFactor).toFixed(1)} g`, `${(((blend.fibre_g || 0) * (computed.serving_grams || 40)) / 100).toFixed(1)} g`]
    ];
    const basisLabel = prefs.dryMatter ? 'Dry-Matter Basis (per 100 g DM)' : 'As-Is (per 100 g)';
    const conf = computed.confidence || {};
    return `
      <div class="studio-table-top">
        <h3 class="card-section-title">${esc(basisLabel)}</h3>
        <button class="btn btn-glass btn-sm" type="button" id="studio-explain-blend">
          ${Icons.spark}<span>${state.studioExplaining === 'blend' ? 'Reading…' : 'Explain blend'}</span>
        </button>
      </div>
      <div class="studio-table-scroll">
        <table class="spec-table spec-table-clean">
          <thead><tr><th>Nutrient</th><th>Per 100 g</th><th>Per ${computed.serving_grams || 40} g Serving</th></tr></thead>
          <tbody>
            ${nutRows.map(([k, v1, v2]) => `<tr><td><strong>${esc(k)}</strong></td><td style="font-family:var(--font-mono);">${esc(v1)}</td><td style="font-family:var(--font-mono);">${esc(v2)}</td></tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${state.studioExplainBlend ? `<div class="studio-explain-callout"><strong>AI Nutrition Read:</strong> ${esc(state.studioExplainBlend)}</div>` : ''}
      <div class="studio-tab-footer-bar">
        <span style="font-size:11.5px;color:var(--text-muted);">${conf.estimated || 0} estimated, ${conf.verified || 0} verified, ${conf.unknown || 0} unknown</span>
        <span class="badge-pill">Serving: ${computed.serving_grams || 40} g</span>
      </div>`;
  };

  const renderCostTab = () => {
    if (!hasItems) return renderFormulationTab();
    const isTargeted = Boolean(regional.is_targeted);
    return `
      <div class="studio-table-top">
        <h3 class="card-section-title">Unit Economics</h3>
        <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
          ${isTargeted ? `<span class="badge-pill ${regional.local_share_pct >= 60 ? 'ok' : 'warn'}">${regional.local_share_pct}% Regional (${esc(regional.target_region)})</span>` : ''}
          <span class="badge-pill ${computed.delta_pct <= 0 ? 'ok' : 'warn'}">${deltaSign}${computed.delta_pct}% vs wheat baseline</span>
        </div>
      </div>
      <div class="studio-table-scroll">
        <table class="spec-table spec-table-clean">
          <thead><tr><th>Ingredient</th><th>Share</th><th>Mandi / kg</th><th>${isTargeted ? 'Landed / kg' : 'Contribution'}</th></tr></thead>
          <tbody>
            ${rows.map((r) => `
              <tr>
                <td>
                  <strong>${esc(r.name)}</strong>
                  ${isTargeted ? `<div style="font-size:10.5px;color:var(--text-muted);">${esc(r.region)} · ${esc(r.region_tier || 'STANDARD')} (+₹${Number(r.freight_per_kg || 0).toFixed(1)})</div>` : ''}
                </td>
                <td style="font-family:var(--font-mono);">${r.share_pct}%</td>
                <td style="font-family:var(--font-mono);">₹${r.cost_per_kg.toFixed(2)}</td>
                <td style="font-family:var(--font-mono);">₹${isTargeted ? Number(r.landed_cost_per_kg || r.cost_per_kg).toFixed(2) : ((r.cost_per_kg * r.share_pct) / 100).toFixed(2)}</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>
      <div class="studio-tab-footer-bar">
        <span style="font-size:11.5px;color:var(--text-muted);">
          ${isTargeted
            ? `Est. Freight: ₹${Number(regional.freight_per_kg || 0).toFixed(2)}/kg · Landed: ₹${Number(regional.landed_cost_per_kg || computed.cost_per_kg).toFixed(2)}/kg (Saved ₹${Number(regional.savings_vs_distant || 0).toFixed(2)}/kg vs distant)`
            : `Baseline: ₹${Number(computed.baseline_cost || 0).toFixed(2)}/kg · Per serving: ₹${Number(computed.cost_per_serving || 0).toFixed(2)}`}
        </span>
        <div class="spec-table-footer-meta"><span>Total Cost / kg:</span><strong>₹${Number(computed.cost_per_kg || 0).toFixed(2)}</strong></div>
      </div>`;
  };

  const renderAdditiveTab = () => {
    if (!hasItems) return renderFormulationTab();
    return `
      <div class="studio-table-top">
        <h3 class="card-section-title">Watchlist Screening</h3>
        ${findings.length ? `<button class="btn btn-glass btn-sm" type="button" id="studio-explain-clean">${Icons.spark}<span>${state.studioExplaining === 'clean' ? 'Analyzing…' : 'What do these do?'}</span></button>` : '<span class="badge-pill ok">100% Clean-Label</span>'}
      </div>
      ${!findings.length ? `
        <div class="spec-empty-callout" style="margin: 16px;">
          <div class="spec-empty-title">No additives flagged</div>
          <div class="spec-empty-desc">All ${rows.length} ingredients passed the watchlist with zero synthetic flags.</div>
        </div>` : `
        <div class="studio-table-scroll">
          <table class="spec-table spec-table-clean">
            <thead><tr><th>Ingredient</th><th>Flag</th><th>Note</th><th>Alternative</th></tr></thead>
            <tbody>
              ${findings.map((f) => `
                <tr>
                  <td><strong>${esc(f.name)}</strong></td>
                  <td><span class="badge-pill ${f.status === 'flagged' ? 'flag' : 'warn'}">${esc(f.status)}</span></td>
                  <td style="font-size:12px;color:var(--text-secondary);">${esc(f.why)}${f.replacement_note ? `<br><em>${esc(f.replacement_note)}</em>` : ''}</td>
                  <td>${f.option ? `<button class="btn btn-primary btn-sm" type="button" data-apply-swap="${esc(f.ingredient_id)}|${esc(f.option.ingredient_id)}">Swap → ${esc(f.option.name)}</button>` : '<span style="font-size:12px;color:var(--text-muted);">Review / Reduce</span>'}</td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>`}
      ${state.studioExplainClean ? `<div class="studio-explain-callout"><strong>AI Watchlist Notes:</strong> ${esc(state.studioExplainClean)}</div>` : ''}`;
  };

  const renderVersionsTab = () => {
    const cmp = ws.compare || {};
    const cmpRows = cmp.rows || [];
    if (!versions.length) {
      return `
        <div class="spec-empty-callout" style="margin:16px;">
          <div class="spec-empty-title">No saved versions yet</div>
          <div class="spec-empty-desc">Formulate a blend and click <strong>Save</strong> to record v1 and compare revisions.</div>
        </div>`;
    }
    return `
      <div class="studio-table-top">
        <h3 class="card-section-title">Saved Revisions (${versions.length})</h3>
        ${versions.length >= 2 ? `
          <div style="display:flex;align-items:center;gap:6px;">
            <select id="studio-cmp-a" class="studio-select compact" aria-label="Compare Version A">
              ${versions.map((v) => `<option value="${esc(v.formulation_id)}" ${cmp.cmp_a === v.formulation_id ? 'selected' : ''}>v${v.version}</option>`).join('')}
            </select>
            <span style="font-size:11px;color:var(--text-muted);">vs</span>
            <select id="studio-cmp-b" class="studio-select compact" aria-label="Compare Version B">
              ${versions.map((v) => `<option value="${esc(v.formulation_id)}" ${cmp.cmp_b === v.formulation_id ? 'selected' : ''}>v${v.version}</option>`).join('')}
            </select>
          </div>` : ''}
      </div>
      <div class="studio-table-scroll">
        <table class="spec-table spec-table-clean">
          <thead><tr><th>Version</th><th>Saved</th><th>By</th><th>Items</th><th></th></tr></thead>
          <tbody>
            ${versions.map((v) => `
              <tr>
                <td><span class="badge-pill ok">v${v.version}</span> ${esc(v.name)}</td>
                <td style="font-family:var(--font-mono);font-size:11.5px;">${esc(v.created_at)}</td>
                <td>${esc(v.creator_name)}</td>
                <td>${v.item_count}</td>
                <td><button class="btn btn-glass btn-sm" type="button" data-load-version="${esc(v.formulation_id)}">Load</button></td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${cmpRows.length ? `
        <div style="padding:12px 16px;border-top:1px solid var(--mode-border-subtle);">
          <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--text-muted);margin-bottom:6px;">Version Delta (A → B)</div>
          <div style="display:flex;flex-wrap:wrap;gap:6px;">
            ${cmpRows.map((d) => `<span class="badge-pill ${d.delta > 0 ? 'ok' : (d.delta < 0 ? 'warn' : '')}">${esc(d.name)}: ${d.share_a}% → ${d.share_b}% (${d.delta > 0 ? '+' : ''}${d.delta}%)</span>`).join('')}
          </div>
        </div>` : ''}`;
  };

  const tabBodyHtml = activeTab === 'nutrition'
    ? renderNutritionTab()
    : activeTab === 'cost'
      ? renderCostTab()
      : activeTab === 'additive'
        ? renderAdditiveTab()
        : activeTab === 'versions'
          ? renderVersionsTab()
          : renderFormulationTab();

  const renderChatBody = () => {
    const hasMessages = messages.length > 0 || state.studioPending;
    if (!hasMessages) {
      return `
        <div class="assistant-thread assistant-thread-clean">
          <div class="assistant-welcome-top">
            <div class="welcome-speech-bubble">How can I help you?</div>
          </div>
        </div>`;
    }

    const msgHtml = messages.map((m) => {
      if (m.role === 'user') {
        return `<div class="chat-msg-row user"><div class="chat-msg-bubble">${esc(m.text)}</div></div>`;
      }
      const thoughtBlock = prefs.showReasoning && m.thought
        ? `<details class="assistant-thought"><summary><span>${esc(m.thought_summary || 'Analyzed database & constraints')}</span></summary><div class="assistant-thought-body">${esc(m.thought)}</div></details>`
        : '';
      const meta = m.engine ? `<div class="chat-msg-meta">${esc(m.engine)}</div>` : '';
      return `<div class="chat-msg-row assistant">${thoughtBlock}<div class="chat-msg-bubble ${m.animateIn ? 'is-streaming' : ''}" data-msg-id="${esc(m.id || '')}"><span class="chat-msg-text">${m.animateIn ? '' : esc(m.text)}</span>${m.animateIn ? '<span class="ai-stream-cursor" aria-hidden="true"></span>' : ''}${meta}</div></div>`;
    }).join('');

    const pendingRow = state.studioPending
      ? `<div class="ai-progress-inline"><img src="assets/loading_biscuit_flask.gif" class="ai-progress-gif" alt="" /><span>${esc(state.studioPendingText || 'Inspecting private crop database & formulating blend…')}</span></div>`
      : '';

    return `<div class="assistant-thread has-messages" id="studio-chat-thread">${msgHtml}${pendingRow}</div>`;
  };

  return `
    <div class="view-container studio-view workbench-clean">
      <div class="workbench-header">
        <div class="workbench-eyebrow-row">
          <span class="workbench-eyebrow">${activeProject ? `${esc(activeProject.project_id)} · SMARTCROP DEMO LAB` : 'SMARTCROP DEMO LAB'}</span>
          ${projects.length > 1 ? `
            <select id="studio-project-select" class="studio-project-inline-select" aria-label="Switch project">
              ${projects.map((p) => `<option value="${esc(p.project_id)}" ${p.project_id === pid ? 'selected' : ''}>${esc(p.project_id)} · ${esc(p.name)}</option>`).join('')}
            </select>` : ''}
          ${activeProject ? `
            <select id="studio-region-select" class="studio-project-inline-select" aria-label="Target market region" title="Target Indian region for cost optimization">
              ${targetRegions.map((reg) => `<option value="${esc(reg)}" ${activeRegion === reg ? 'selected' : ''}>Target: ${esc(reg)}</option>`).join('')}
            </select>` : ''}
        </div>
        <h1 class="workbench-title">${activeProject ? esc(activeProject.name) : 'High-protein clean-label millet snack'}</h1>
        <p class="workbench-subtitle">
          ${activeProject && activeProject.description ? esc(activeProject.description) : 'Extruded plant-based snack targeting high protein, affordable local crops, and zero synthetic additives.'}
        </p>
        <div class="project-spec-notice">
          <span class="notice-bar" aria-hidden="true"></span>
          <span>Starting point, not a result — every figure is an estimate until the lab measures the batch.</span>
        </div>
      </div>

      <section class="studio-split workbench-split">
        <aside class="glass-card studio-assistant-pane workbench-left" aria-label="AI Formulation Assistant">
          <div class="assistant-header workbench-chat-header">
            <div class="assistant-identity">
              <div class="panel-eyebrow">SMARTCROP CO-PILOT</div>
              <h2 class="assistant-title">Formulation assistant</h2>
            </div>
            <div class="assistant-router-col">
              <div class="model-picker" id="studio-model-picker" data-model-picker>
                <button class="model-picker-trigger" type="button" id="studio-model-select" data-model-picker-trigger aria-haspopup="listbox" aria-expanded="false" aria-label="AI model router selector">
                  <span class="model-picker-dot" aria-hidden="true"></span>
                  <span class="model-picker-current">${esc(activeChoice.label)}</span>
                  <svg class="model-picker-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>
                </button>
                <div class="model-picker-menu" role="listbox" aria-label="Select AI router model" hidden>
                  <div class="model-picker-menu-header">AI Router Model</div>
                  ${modelChoices.map((c) => {
                    const isSelected = selectedModel === c.value;
                    const parsed = parseChoice(c.label);
                    return `
                      <button class="model-picker-option ${isSelected ? 'is-selected' : ''}" type="button" role="option" aria-selected="${isSelected ? 'true' : 'false'}" data-model-option="${esc(c.value)}">
                        <span class="model-option-main">
                          <span class="model-option-name">${esc(parsed.name)}</span>
                          ${parsed.tag ? `<span class="model-option-tag">${esc(parsed.tag)}</span>` : ''}
                        </span>
                        <span class="model-option-check" aria-hidden="true">
                          ${isSelected ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
                        </span>
                      </button>`;
                  }).join('')}
                </div>
              </div>
            </div>
          </div>

          ${renderChatBody()}

          <div class="assistant-bottom-group">
            <div class="quick-prompts-section">
              <div class="quick-prompts-label">QUICK PROMPTS</div>
              <div class="quick-prompts-row" role="group" aria-label="Quick formulation prompts">
                ${quickPrompts.map((p) => `
                  <button class="quick-prompt-pill" type="button" data-quick-prompt="${esc(p.prompt)}" title="${esc(p.prompt)}">
                    <span class="qp-icon" aria-hidden="true">${p.icon}</span>
                    <span class="qp-text">${esc(p.label)}</span>
                  </button>`).join('')}
              </div>
            </div>

            <form class="workbench-composer" id="studio-composer-form">
              <input id="studio-prompt-input" type="text" class="workbench-input" placeholder="Describe your formulation goals" aria-label="Prompt SmartCrop Co-Pilot" value="${esc(state.studioPrompt || '')}" />
              <button class="composer-send-btn" type="submit" title="Send prompt" ${state.studioPending ? 'disabled' : ''}>
                <span>Send</span>
                <span class="btn-icon-end" aria-hidden="true">↵</span>
              </button>
            </form>
          </div>
        </aside>

        <section class="glass-card studio-spec-pane workbench-right" aria-label="Formulation Specification Workspace">
          <div class="spec-workspace-header workbench-spec-header">
            <div class="spec-title-group">
              <div class="spec-eyebrow">FORMULATION SPEC</div>
              <span class="badge-pill ${ws.latest_meta && !state.studioUnsaved ? 'ok' : 'warn'}">
                ${ws.latest_meta && !state.studioUnsaved ? `v${ws.latest_meta.version} · Saved` : (hasItems ? 'Draft · Unsaved' : 'Awaiting goals')}
              </span>
            </div>
            ${hasItems ? `
              <div class="spec-header-actions">
                <button class="btn btn-primary btn-sm" type="button" id="studio-save-btn">Save</button>
                <button class="btn btn-glass btn-sm" type="button" id="studio-export-btn">Export Spec</button>
                <button class="btn btn-glass btn-sm" type="button" data-studio-reset>Reset</button>
              </div>
            ` : `
              <div class="spec-header-skeleton-actions" aria-hidden="true">
                <span class="spec-skel-btn short"></span>
                <span class="spec-skel-btn"></span>
              </div>
            `}
          </div>

          <div class="studio-summary-grid workbench-kpi-grid" aria-label="Formulation summary metrics">
            ${summaryCards.map((card) => `
              <article class="studio-summary-card workbench-kpi-card ${card.filled ? 'is-filled' : ''}">
                <div class="summary-card-label">${esc(card.label)}</div>
                ${card.filled ? `
                  <div class="summary-card-value">${esc(card.value)}</div>
                  <div class="summary-card-status">${esc(card.status)}</div>
                ` : `
                  <span class="spec-ghost-bar kpi-val" aria-hidden="true"></span>
                  <span class="spec-ghost-bar kpi-sub" aria-hidden="true"></span>
                `}
              </article>`).join('')}
          </div>

          <div class="workbench-tabs-bar">
            <div class="workbench-tabs" role="tablist" aria-label="Specification views">
              ${tabs.map((tab) => `
                <button class="workbench-tab-btn ${activeTab === tab.id ? 'is-active' : ''}" type="button" role="tab" aria-selected="${activeTab === tab.id ? 'true' : 'false'}" data-studio-tab="${tab.id}">
                  <span>${esc(tab.label)}</span>
                </button>`).join('')}
            </div>
          </div>

          <div class="workbench-table-wrap" role="tabpanel">${tabBodyHtml}</div>
        </section>
      </section>
    </div>
  `;
};
