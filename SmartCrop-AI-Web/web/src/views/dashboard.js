/**
 * SmartCrop.AI — Dashboard View (Connected to Live Backend Metrics & Projects)
 */
window.SmartCrop = window.SmartCrop || {};
window.SmartCrop.Views = window.SmartCrop.Views || {};

window.SmartCrop.Views.dashboard = function renderDashboard(state) {
  const { Icons, Illustrations, Utils } = window.SmartCrop;
  const esc = Utils.esc;
  const boot = state.bootstrap || {};
  const user = boot.user || {};
  const stats = boot.stats || {};
  const projects = boot.projects || [];
  const firstName = (user.name || 'Researcher').split(' ')[0];

  const summarySlots = [
    {
      label: 'Active Projects',
      value: String(stats.projects_count ?? 0),
      status: `${stats.formulations_count ?? 0} saved formulation version(s)`,
      icon: Icons.formulations
    },
    {
      label: 'Verified Ingredients',
      value: `${stats.nutrition_verified ?? 0} / ${stats.ingredients_count ?? 0}`,
      status: `${stats.cost_verified ?? 0} cost rows verified`,
      icon: Icons.ingredients
    }
  ];

  const activityBody = projects.length
    ? `<div class="module-list">
        ${projects
          .slice(0, 6)
          .map((p) => {
            const metaText = p.metrics
              ? `v${p.latest_version} · Protein ${p.metrics.protein_g}g · ₹${p.metrics.cost_per_kg}/kg`
              : 'No formulation yet — open Studio to formulate';
            return `
            <div class="module-row" style="cursor: pointer;" data-open-in-studio="${esc(p.project_id)}">
              <div class="module-row-left">
                <span class="module-dot" aria-hidden="true"></span>
                <div>
                  <div class="module-title">${esc(p.name)}</div>
                  <div class="module-sub">${esc(p.description || 'No description')} · ${esc(metaText)}</div>
                </div>
              </div>
              <span class="badge-pill ${p.latest_version > 0 ? 'ok' : ''}">${p.latest_version > 0 ? `v${p.latest_version}` : 'Skeleton'}</span>
            </div>`;
          })
          .join('')}
      </div>`
    : `<div class="empty-panel">
        <div class="empty-illustration">${Illustrations.emptyBeaker}</div>
        <h3 class="empty-title">No lab projects yet</h3>
        <p class="empty-desc">
          Create a project with an end goal, then open Formulation Studio so SmartCrop Co-Pilot can extract local crops and formulate a blend.
        </p>
        <button class="btn btn-primary btn-sm" type="button" data-open-project-modal>
          ${Icons.plus}
          <span>New Project</span>
        </button>
      </div>`;

  return `
    <div class="view-container">
      <section class="hero-banner">
        <div class="hero-copy">
          <div class="hero-chip">
            <span class="page-eyebrow-dot"></span>
            <span>${esc(boot.lab_name || 'SmartCrop Demo Lab')} · ${esc(user.role === 'lab_admin' ? 'Lab Admin' : 'Lab Worker')}</span>
          </div>
          <h1 class="hero-title">Welcome, ${esc(firstName)}</h1>
          <p class="hero-desc">
            Explore indexed regional crops, verify nutrition and mandi pricing, and formulate clean-label plant-based recipes with AI reasoning backed by Python calculations.
          </p>
          <div class="hero-actions">
            <button class="btn btn-primary" type="button" data-route="studio">
              ${Icons.studio}
              <span>Open Formulation Studio</span>
            </button>
            <button class="btn btn-glass" type="button" data-open-project-modal>
              ${Icons.plus}
              <span>New Project</span>
            </button>
          </div>
        </div>
        <div class="hero-visual" aria-hidden="true">
          ${Illustrations.heroLattice}
        </div>
      </section>

      <section class="grid-2" aria-label="Workspace metrics">
        ${summarySlots
          .map(
            (slot) => `
          <article class="glass-card slot-card">
            <div class="slot-card-top">
              <span class="slot-label">${esc(slot.label)}</span>
              <span class="slot-icon">${slot.icon}</span>
            </div>
            <div class="slot-placeholder-box">
              <span class="slot-dash" style="color: var(--forest-900); font-size: 20px;">${esc(slot.value)}</span>
              <span class="slot-status">${esc(slot.status)}</span>
            </div>
          </article>
        `
          )
          .join('')}
      </section>

      <section>
        <article class="glass-card card-section">
          <div class="card-section-header">
            <h2 class="card-section-title">Lab Projects &amp; Recent Trials</h2>
            <span class="card-section-meta">${projects.length} accessible</span>
          </div>
          ${activityBody}
        </article>
      </section>
    </div>
  `;
};
