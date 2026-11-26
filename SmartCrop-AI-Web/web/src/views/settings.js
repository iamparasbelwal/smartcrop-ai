/**
 * SmartCrop.AI — Settings View (Live Researcher Profile & Scientific Units)
 */
window.SmartCrop = window.SmartCrop || {};
window.SmartCrop.Views = window.SmartCrop.Views || {};

window.SmartCrop.Views.settings = function renderSettings(state) {
  const { Utils, Prefs } = window.SmartCrop;
  const esc = Utils.esc;
  const prefs = Prefs.load();
  const activeSection = state.settingsTab === 'units' ? 'units' : 'profile';
  const boot = state.bootstrap || {};
  const user = boot.user || {};

  const sections = [
    { id: 'profile', label: 'Researcher Profile' },
    { id: 'units', label: 'Scientific Units' }
  ];

  const renderPanel = () => {
    if (activeSection === 'units') {
      return `
        <div class="card-section-header">
          <h2 class="card-section-title">Scientific Units &amp; Measurement Standards</h2>
          <span class="badge-pill ok">Saved locally</span>
        </div>
        <div class="module-list">
          <div class="toggle-row">
            <div><div class="toggle-title">Metric / SI Mass Units (g, kg, mg)</div><div class="toggle-desc">Use standardized SI laboratory mass units across formulation tables.</div></div>
            <button class="switch-btn" type="button" role="switch" aria-checked="${prefs.metricUnits}" data-pref-switch="metricUnits"><span class="switch-knob"></span></button>
          </div>
          <div class="toggle-row">
            <div><div class="toggle-title">Celsius Thermal Scale (°C)</div><div class="toggle-desc">Use °C across lab specification sheets.</div></div>
            <button class="switch-btn" type="button" role="switch" aria-checked="${prefs.useCelsius}" data-pref-switch="useCelsius"><span class="switch-knob"></span></button>
          </div>
          <div class="toggle-row">
            <div><div class="toggle-title">Dry-Matter Basis Normalization</div><div class="toggle-desc">Display Studio Nutrition metrics adjusted for blend moisture content.</div></div>
            <button class="switch-btn" type="button" role="switch" aria-checked="${prefs.dryMatter}" data-pref-switch="dryMatter"><span class="switch-knob"></span></button>
          </div>
        </div>`;
    }

    return `
      <div class="card-section-header">
        <h2 class="card-section-title">Researcher Profile</h2>
        <span class="badge-pill ok">${esc(user.role === 'lab_admin' ? 'Lab Administrator' : 'Lab Worker')}</span>
      </div>
      <div class="form-grid" style="margin-bottom:16px;">
        <div class="field-group"><label class="field-label">Name</label><input class="field-input" readonly value="${esc(user.name || '')}" /></div>
        <div class="field-group"><label class="field-label">Email</label><input class="field-input" readonly value="${esc(user.email || '')}" /></div>
        <div class="field-group"><label class="field-label">Lab Organization</label><input class="field-input" readonly value="${esc(boot.lab_name || '')} (${esc(user.lab_id || '')})" /></div>
        <div class="field-group"><label class="field-label">Account ID</label><input class="field-input" readonly value="${esc(user.user_id || '')}" /></div>
      </div>
      <div class="page-actions">
        <button class="btn btn-glass btn-sm" type="button" id="settings-signout-btn"><span>Sign out of Lab</span></button>
      </div>`;
  };

  return `
    <div class="view-container">
      <div class="page-header">
        <div>
          <div class="page-eyebrow"><span class="page-eyebrow-dot"></span><span>Workspace Configuration</span></div>
          <h1 class="page-title">Settings</h1>
          <p class="page-subtitle">Manage your lab profile and scientific unit standards.</p>
        </div>
      </div>
      <section class="settings-layout">
        <nav class="glass-card settings-nav" aria-label="Settings categories">
          ${sections.map((sec) => `<button class="settings-nav-btn ${activeSection === sec.id ? 'is-active' : ''}" type="button" data-settings-tab="${sec.id}"><span>${sec.label}</span></button>`).join('')}
        </nav>
        <article class="glass-card card-section">${renderPanel()}</article>
      </section>
    </div>`;
};
