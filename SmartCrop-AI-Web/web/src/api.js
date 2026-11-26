/**
 * SmartCrop.AI — Shared Frontend API Client & Persistent UI Preferences
 */
window.SmartCrop = window.SmartCrop || {};

window.SmartCrop.Utils = {
  esc(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
};

window.SmartCrop.Prefs = {
  KEY: 'smartcrop_web_prefs_v1',
  defaults: {
    metricUnits: true,
    useCelsius: true,
    dryMatter: false,
    prioritizeLocal: true,
    showReasoning: true,
    defaultModel: ''
  },
  load() {
    try {
      const raw = localStorage.getItem(this.KEY);
      return Object.assign({}, this.defaults, raw ? JSON.parse(raw) : {});
    } catch (_) {
      return Object.assign({}, this.defaults);
    }
  },
  save(patch) {
    const next = Object.assign(this.load(), patch || {});
    try {
      localStorage.setItem(this.KEY, JSON.stringify(next));
    } catch (_) {}
    return next;
  }
};

window.SmartCrop.Api = {
  async request(url, options = {}) {
    const opts = Object.assign({ credentials: 'same-origin' }, options);
    opts.headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
    const res = await fetch(url, opts);
    const text = await res.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch (_) {
      data = { error: text || `HTTP ${res.status}` };
    }
    if (!res.ok) {
      const err = new Error(data.error || `Request failed (${res.status})`);
      err.status = res.status;
      err.payload = data;
      throw err;
    }
    return data;
  },

  bootstrap() {
    return this.request('/api/bootstrap');
  },
  health() {
    return this.request('/api/health');
  },
  login(email, password) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },
  logout() {
    return this.request('/api/auth/logout', { method: 'POST', body: '{}' });
  },
  createProject(name, description, targetRegion = 'Pan-India') {
    return this.request('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ name, description, target_region: targetRegion })
    });
  },
  updateProjectRegion(projectId, targetRegion, items = []) {
    return this.request(`/api/projects/${encodeURIComponent(projectId)}/region`, {
      method: 'POST',
      body: JSON.stringify({ target_region: targetRegion, items })
    });
  },
  clearProjectChats(projectId) {
    return this.request(`/api/projects/${encodeURIComponent(projectId)}/chats/clear`, {
      method: 'POST',
      body: '{}'
    });
  },
  getWorkspace(projectId, params = {}) {
    const q = new URLSearchParams();
    if (params.version) q.set('version', params.version);
    if (params.cmp_a) q.set('cmp_a', params.cmp_a);
    if (params.cmp_b) q.set('cmp_b', params.cmp_b);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return this.request(`/api/projects/${encodeURIComponent(projectId)}/workspace${qs}`);
  },
  computeStudio(items, validate = true, targetRegion = 'Pan-India') {
    return this.request('/api/studio/compute', {
      method: 'POST',
      body: JSON.stringify({ items, validate, target_region: targetRegion })
    });
  },
  chatStudio(payload) {
    return this.request('/api/studio/chat', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  draftStudio(payload) {
    return this.request('/api/studio/draft', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  explainStudio(payload) {
    return this.request('/api/studio/explain', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  saveStudio(payload) {
    return this.request('/api/studio/save', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  exportStudio(payload) {
    return this.request('/api/studio/export', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  listIngredients() {
    return this.request('/api/ingredients');
  },
  createIngredient(payload) {
    return this.request('/api/ingredients', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  verifyIngredient(ingredientId, payload) {
    return this.request(`/api/ingredients/${encodeURIComponent(ingredientId)}/verify`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  uploadIngredientPhoto(ingredientId, payload) {
    return this.request(`/api/ingredients/${encodeURIComponent(ingredientId)}/photo`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  getAdminOverview() {
    return this.request('/api/admin/overview');
  },
  createWorker(payload) {
    return this.request('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  toggleUser(userId, active) {
    return this.request(`/api/admin/users/${encodeURIComponent(userId)}/toggle`, {
      method: 'POST',
      body: JSON.stringify({ active })
    });
  },
  updateAccess(projectId, userId, grant) {
    return this.request('/api/admin/access', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, user_id: userId, grant })
    });
  }
};
