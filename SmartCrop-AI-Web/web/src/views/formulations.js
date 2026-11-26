/**
 * SmartCrop.AI — My Formulations View (Projects & Saved Formulations)
 */
window.SmartCrop = window.SmartCrop || {};
window.SmartCrop.Views = window.SmartCrop.Views || {};

window.SmartCrop.Views.renderFormulationCards = function renderFormulationCards(state) {
  const { Icons, Illustrations, Utils } = window.SmartCrop;
  const esc = Utils.esc;
  const projects = (state.bootstrap && state.bootstrap.projects) || [];
  const filter = state.formFilter || 'all';
  const q = (state.formQuery || '').trim().toLowerCase();

  const filtered = projects.filter((p) => {
    if (filter === 'saved' && p.latest_version <= 0) return false;
    if (filter === 'empty' && p.latest_version > 0) return false;
    if (q && !`${p.project_id} ${p.name} ${p.description} ${p.creator_name}`.toLowerCase().includes(q)) return false;
    return true;
  });

  if (!filtered.length) {
    return `
      <div class="empty-panel">
        <div class="empty-illustration">${Illustrations.emptyDossier}</div>
        <h2 class="empty-title">${projects.length ? 'No matching projects' : 'No lab projects yet'}</h2>
        <p class="empty-desc">Create a new formulation project with an end goal and let SmartCrop Co-Pilot build your starting blend.</p>
        <button class="btn btn-primary btn-sm" type="button" data-open-project-modal>
          ${Icons.plus}<span>New Project</span>
        </button>
      </div>`;
  }

  return `
    <div style="display: flex; flex-direction: column; gap: 12px;">
      ${filtered.map((p) => {
        const isCurrent = p.project_id === state.activeProjectId;
        const verBadge = p.latest_version > 0
          ? `<span class="badge-pill ok">v${p.latest_version} Saved</span>`
          : `<span class="badge-pill warn">Empty Skeleton</span>`;
        const metrics = p.metrics
          ? `<span style="font-family:var(--font-mono);font-size:12px;color:var(--text-secondary);">${p.metrics.crop_count} crops · ${p.metrics.protein_g}g protein · ${Math.round(p.metrics.energy_kcal)} kcal · ₹${p.metrics.cost_per_kg}/kg</span>`
          : `<span style="font-size:12px;color:var(--text-muted);">No formulation generated yet</span>`;
        return `
        <article class="glass-card" style="padding:18px 20px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">
          <div style="flex:1;min-width:240px;">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;">
              <strong style="font-size:16px;color:var(--forest-950);">${esc(p.name)}</strong>
              ${isCurrent ? '<span class="badge-pill ok">Active</span>' : ''}
              ${verBadge}
            </div>
            <div style="font-size:13px;color:var(--text-secondary);margin-bottom:6px;">${esc(p.description || 'No project description provided.')}</div>
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
              <span style="font-size:11.5px;color:var(--text-muted);">By ${esc(p.creator_name)} · ${esc(p.created_at.slice(0, 10))} · <code>${esc(p.project_id)}</code></span>
              ${metrics}
            </div>
          </div>
          <button class="btn ${isCurrent ? 'btn-primary' : 'btn-glass'} btn-sm" type="button" data-open-in-studio="${esc(p.project_id)}">
            ${Icons.studio}<span>Open in Studio</span>
          </button>
        </article>`;
      }).join('')}
    </div>`;
};

window.SmartCrop.Views.formulations = function renderFormulations(state) {
  const { Icons } = window.SmartCrop;
  const activeFilter = state.formFilter || 'all';
  const collections = [
    ['all', 'All Projects'],
    ['saved', 'Saved Versions'],
    ['empty', 'Empty Skeletons']
  ];

  return `
    <div class="view-container">
      <div class="page-header">
        <div>
          <div class="page-eyebrow"><span class="page-eyebrow-dot"></span><span>Researcher Library</span></div>
          <h1 class="page-title">My Formulations</h1>
          <p class="page-subtitle">Manage visible formulation projects, inspect saved version metrics, and launch any project in the Studio.</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" type="button" data-open-project-modal>${Icons.plus}<span>New Project</span></button>
        </div>
      </div>

      <section class="glass-card filter-toolbar">
        <div class="pill-tabs" role="tablist" aria-label="Formulation collections">
          ${collections.map(([id, lbl]) => `<button class="pill-tab ${activeFilter === id ? 'is-active' : ''}" type="button" data-form-filter="${id}">${lbl}</button>`).join('')}
        </div>
        <div class="search-field" style="max-width: 300px;">
          ${Icons.search}
          <input id="form-search-input" class="search-input" type="search" value="${window.SmartCrop.Utils.esc(state.formQuery || '')}" placeholder="Search projects…" aria-label="Search saved formulations" />
        </div>
      </section>

      <section id="formulations-list-host">
        ${window.SmartCrop.Views.renderFormulationCards(state)}
      </section>
    </div>`;
};
