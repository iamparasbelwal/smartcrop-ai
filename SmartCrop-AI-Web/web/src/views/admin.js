/**
 * SmartCrop.AI — Lab Admin View (Team Roster, Project Access, Data Integrity & Audit Ledger)
 */
window.SmartCrop = window.SmartCrop || {};
window.SmartCrop.Views = window.SmartCrop.Views || {};

window.SmartCrop.Views.renderAuditRows = function renderAuditRows(state) {
  const { Utils } = window.SmartCrop;
  const esc = Utils.esc;
  const data = state.adminData || {};
  const names = data.user_names || {};
  const audit = data.audit || [];
  const area = state.auditArea || 'all';
  const q = (state.auditQuery || '').trim().toLowerCase();

  const filtered = audit.filter((ev) => {
    if (area !== 'all' && ev.table !== area) return false;
    if (q) {
      const hay = `${ev.event_id} ${ev.note} ${ev.record_id} ${ev.field} ${names[ev.actor_user_id] || ''}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  if (!filtered.length) {
    return `<div class="table-empty-body"><div class="empty-panel" style="border:none;background:transparent;"><h2 class="empty-title">No matching audit events</h2><p class="empty-desc">Try adjusting the table filter or search term.</p></div></div>`;
  }

  return filtered.slice(0, 120).map((ev) => `
    <div class="data-row-grid-audit">
      <div style="font-family:var(--font-mono);font-size:11.5px;">${esc(ev.at)}</div>
      <div style="font-weight:600;">${esc(names[ev.actor_user_id] || ev.actor_user_id)}</div>
      <div>
        <div>${esc(ev.note || 'Updated')}</div>
        <div style="font-size:11px;color:var(--text-muted);">${esc(ev.table)}</div>
      </div>
      <div><code>${esc(ev.record_id || '—')}</code></div>
      <div style="font-size:12px;">${ev.field ? `<strong>${esc(ev.field)}</strong>: ` : ''}${esc(ev.old_value ? `${ev.old_value} → ` : '')}${esc(ev.new_value || '—')}${ev.lab_report ? ' <span class="badge-pill ok">report</span>' : ''}</div>
      <div><button class="btn btn-glass btn-sm" type="button" data-open-audit="${esc(ev.event_id)}">Open</button></div>
    </div>`).join('');
};

window.SmartCrop.Views.renderAdminTabBody = function renderAdminTabBody(state) {
  const { Icons, Utils } = window.SmartCrop;
  const esc = Utils.esc;
  const boot = state.bootstrap || {};
  const user = boot.user || {};
  const activeTab = state.adminTab || 'team';
  const data = state.adminData || {};
  const users = data.users || [];
  const accessMatrix = data.access_matrix || [];
  const vcounts = data.verified_counts || {};

  if (activeTab === 'workspaces') {
    if (!accessMatrix.length) {
      return `<section class="glass-card card-section"><div class="empty-panel"><h2 class="empty-title">No projects created yet</h2><p class="empty-desc">Create a project first to manage worker access permissions.</p></div></section>`;
    }
    return `
      <div style="display:flex;flex-direction:column;gap:14px;">
        ${accessMatrix.map((entry) => {
          const p = entry.project;
          return `
          <section class="glass-card card-section">
            <div class="card-section-header">
              <h2 class="card-section-title">${esc(p.name)} <code style="font-size:12px;">(${esc(p.project_id)})</code></h2>
              <span class="badge-pill">${entry.visible_count} of ${entry.members.length} can open</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:8px;">
              ${entry.members.map((m) => `
                <div class="data-row-grid-admin" style="padding:8px 0;">
                  <div><strong>${esc(m.name)}</strong></div>
                  <div style="color:var(--text-muted);">${esc(m.email)}</div>
                  <div><span class="badge-pill">${m.always ? esc(m.always_reason) : (m.has_access ? 'Can open' : 'No access')}</span></div>
                  <div></div>
                  <div style="text-align:right;">
                    ${m.always ? '<span style="font-size:12px;color:var(--text-muted);">Always</span>' : `<button class="btn ${m.has_access ? 'btn-glass' : 'btn-primary'} btn-sm" type="button" data-toggle-access="${esc(p.project_id)}|${esc(m.user_id)}|${!m.has_access}">${m.has_access ? 'Revoke' : 'Grant'}</button>`}
                  </div>
                </div>`).join('')}
            </div>
          </section>`;
        }).join('')}
      </div>`;
  }

  if (activeTab === 'pipelines') {
    return `
      <section class="glass-card card-section">
        <div class="card-section-header">
          <h2 class="card-section-title">Database Integrity &amp; Verification</h2>
          <button class="btn btn-primary btn-sm" type="button" data-route="ingredients">Open Ingredient Verification</button>
        </div>
        <p class="empty-desc" style="margin:0 0 12px;">${vcounts.ingredients || 0} seeded crops in <code>data/ingredients.csv</code>. Currently ${vcounts.nutrition_verified || 0} have lab-verified nutrition profiles and ${vcounts.cost_verified || 0} have verified mandi prices.</p>
      </section>`;
  }

  if (activeTab === 'audit') {
    return `
      <section class="glass-card filter-toolbar">
        <div class="search-field">
          ${Icons.search}
          <input id="audit-search-input" class="search-input" type="search" value="${esc(state.auditQuery || '')}" placeholder="Search audit event, note, record ID, or actor…" />
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <select id="audit-area-select" class="studio-select">
            <option value="all" ${state.auditArea === 'all' ? 'selected' : ''}>All Areas</option>
            <option value="users" ${state.auditArea === 'users' ? 'selected' : ''}>People</option>
            <option value="projects" ${state.auditArea === 'projects' ? 'selected' : ''}>Projects</option>
            <option value="formulations" ${state.auditArea === 'formulations' ? 'selected' : ''}>Formulations</option>
            <option value="ingredients" ${state.auditArea === 'ingredients' ? 'selected' : ''}>Ingredients</option>
            <option value="project_access" ${state.auditArea === 'project_access' ? 'selected' : ''}>Project Access</option>
          </select>
          <a class="btn btn-glass btn-sm" href="/api/audit/csv" download="smartcrop_audit_log.csv">Download CSV</a>
        </div>
      </section>
      <section class="glass-card table-shell">
        <div class="data-row-grid-audit data-row-header">
          <span>Timestamp</span><span>Actor</span><span>Event</span><span>Record</span><span>Change</span><span>Open</span>
        </div>
        <div id="audit-rows-host">${window.SmartCrop.Views.renderAuditRows(state)}</div>
      </section>`;
  }

  return `
    <section class="glass-card table-shell">
      <div class="data-row-grid-admin data-row-header">
        <span>Name</span><span>Email</span><span>Role</span><span>Status</span><span>Action</span>
      </div>
      ${users.map((u) => {
        const isActive = u.active === 'yes';
        return `
        <div class="data-row-grid-admin">
          <div><strong>${esc(u.name)}</strong></div>
          <div style="color:var(--text-muted);">${esc(u.email)}</div>
          <div><span class="badge-pill">${esc(u.role === 'lab_admin' ? 'Lab admin' : 'Lab worker')}</span></div>
          <div><span class="badge-pill ${isActive ? 'ok' : 'flag'}">${isActive ? 'Active' : 'Deactivated'}</span></div>
          <div>
            ${u.user_id === user.user_id ? '<span style="font-size:12px;color:var(--text-muted);">You (Current)</span>' : `<button class="btn btn-glass btn-sm" type="button" data-toggle-user="${esc(u.user_id)}|${!isActive}">${isActive ? 'Deactivate' : 'Reactivate'}</button>`}
          </div>
        </div>`;
      }).join('')}
    </section>`;
};

window.SmartCrop.Views.admin = function renderAdmin(state) {
  const { Icons, Illustrations, Utils } = window.SmartCrop;
  const esc = Utils.esc;
  const boot = state.bootstrap || {};
  const user = boot.user || {};

  if (user.role !== 'lab_admin') {
    return `
      <div class="view-container">
        <div class="page-header">
          <div>
            <div class="page-eyebrow"><span class="page-eyebrow-dot"></span><span>Organization &amp; Governance</span></div>
            <h1 class="page-title">Lab Admin</h1>
          </div>
        </div>
        <section class="glass-card card-section">
          <div class="empty-panel">
            <div class="empty-illustration">${Illustrations.emptyMolecular}</div>
            <h2 class="empty-title">Lab Administrator Access Required</h2>
            <p class="empty-desc">You are signed in as <strong>${esc(user.name)}</strong> (${esc(user.role)}). Switch to a Lab Admin account (for example Paras Belwal) to manage researchers, project grants, and audit logs.</p>
          </div>
        </section>
      </div>`;
  }

  const activeTab = state.adminTab || 'team';
  const data = state.adminData || {};
  const users = data.users || [];
  const vcounts = data.verified_counts || {};
  const activeCount = users.filter((u) => u.active === 'yes').length;

  const tabs = [
    { id: 'team', label: 'Team & Researchers' },
    { id: 'workspaces', label: 'Project Access' },
    { id: 'pipelines', label: 'Data Integrity' },
    { id: 'audit', label: 'Audit & Compliance' }
  ];

  return `
    <div class="view-container">
      <div class="page-header">
        <div>
          <div class="page-eyebrow"><span class="page-eyebrow-dot"></span><span>${esc(user.lab_id)} · Administration</span></div>
          <h1 class="page-title">Lab Admin</h1>
          <p class="page-subtitle">Manage researchers, per-project access permissions, verified crop integrity, and the immutable audit log.</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" type="button" id="admin-invite-btn">${Icons.plus}<span>Invite Researcher</span></button>
        </div>
      </div>

      <section class="glass-card filter-toolbar">
        <div class="pill-tabs admin-tabs-bar" role="tablist" aria-label="Lab Admin sections">
          ${tabs.map((tab) => `<button class="pill-tab ${activeTab === tab.id ? 'is-active' : ''}" type="button" data-admin-tab="${tab.id}">${tab.label}</button>`).join('')}
        </div>
        <span class="badge-pill ok">${activeCount} active accounts · ${data.total_audit || 0} audit events</span>
      </section>

      <section class="grid-3">
        <article class="glass-card slot-card">
          <div class="slot-card-top"><span class="slot-label">Lab Members</span><span class="slot-icon">${Icons.admin}</span></div>
          <div class="slot-placeholder-box"><span class="slot-dash" style="color:var(--forest-900);">${users.length}</span><span class="slot-status">${activeCount} active accounts</span></div>
        </article>
        <article class="glass-card slot-card">
          <div class="slot-card-top"><span class="slot-label">Verified Crops</span><span class="slot-icon">${Icons.ingredients}</span></div>
          <div class="slot-placeholder-box"><span class="slot-dash" style="color:var(--forest-900);">${vcounts.nutrition_verified || 0}</span><span class="slot-status">of ${vcounts.ingredients || 0} crops verified</span></div>
        </article>
        <article class="glass-card slot-card">
          <div class="slot-card-top"><span class="slot-label">Audit Ledger</span><span class="slot-icon">${Icons.spark}</span></div>
          <div class="slot-placeholder-box"><span class="slot-dash" style="color:var(--forest-900);">${data.total_audit || 0}</span><span class="slot-status">recorded lab events</span></div>
        </article>
      </section>

      <div id="admin-tab-body" class="tab-panel-host">${window.SmartCrop.Views.renderAdminTabBody(state)}</div>
    </div>`;
};
