/**
 * SmartCrop.AI — Ingredient Database, Data Verification & Regional Detail View
 */
window.SmartCrop = window.SmartCrop || {};
window.SmartCrop.Views = window.SmartCrop.Views || {};

const INGREDIENT_DETAILS_META = {
  'ING-001': {
    belt: 'Western & Arid India — Rajasthan (Barmer, Jodhpur, Nagaur), Gujarat, and Haryana',
    description: 'Stone-milled whole-grain pearl millet flour rich in iron, zinc, and insoluble dietary fibre. Imparts a warm, nutty roasted aroma and crispness to extruded snacks and baked biscuits.'
  },
  'ING-002': {
    belt: 'Southern & Himalayan Foothills — Karnataka, Tamil Nadu, and Uttarakhand',
    description: 'Nutrient-dense finger millet (Ragi) flour prized for its exceptionally high calcium content, slow-release complex carbohydrates, and deep earthy color in clean-label baked goods.'
  },
  'ING-003': {
    belt: 'Deccan & Central India — Maharashtra (Solapur, Marathwada), Karnataka, and Telangana',
    description: 'Gluten-free sorghum (Jowar) flour with neutral flavor, light crumb color, and good water absorption. Serves as an economical, drought-resilient base grain in puffed snacks and flatbreads.'
  },
  'ING-004': {
    belt: 'Deccan Plateau & Eastern Ghats — Andhra Pradesh, Telangana, and Karnataka',
    description: 'Small-seeded foxtail millet (Kangni) offering higher protein and balanced amino-acid density than polished cereals, ideal for savory extruded nuggets and multi-millet mixes.'
  },
  'ING-005': {
    belt: 'Central India Soy Belt — Madhya Pradesh (Malwa plateau), Maharashtra, and Rajasthan',
    description: 'High-protein defatted soy flour (~47% protein) used to boost protein density and water binding. Requires clean-label supplier verification for hexane-extraction residue.'
  },
  'ING-006': {
    belt: 'Central India — Madhya Pradesh (Indore, Ujjain), Maharashtra, and Rajasthan',
    description: 'Whole heat-treated soybean rich in both protein (36.5%) and natural lipids (19.9%), contributing high caloric density and emulsifying properties without synthetic additives.'
  },
  'ING-007': {
    belt: 'Central & Northern India — Madhya Pradesh, Rajasthan, and Uttar Pradesh',
    description: 'Stone-milled Bengal gram flour (Besan) delivering clean-label protein, golden color, and natural binding structure in extruded savory snacks, crisps, and batters.'
  },
  'ING-008': {
    belt: 'Central & Eastern Indo-Gangetic Plain — Madhya Pradesh, Uttar Pradesh, and Bihar',
    description: 'Split, hulled red lentil (Masoor dal) milled for high-digestibility plant protein (25%) and smooth texture, pairing well with millets for complete cereal-pulse amino balance.'
  },
  'ING-009': {
    belt: 'Arid & Semi-Arid India — Rajasthan, Maharashtra, and Andhra Pradesh',
    description: 'Finely milled green gram (Moong atta) prized for light digestibility, mild beany-free flavor, and crisp bite in kids nutrition snacks and extruded puffs.'
  },
  'ING-010': {
    belt: 'Eastern & Southern River Deltas — West Bengal, Punjab, Andhra Pradesh, and Tamil Nadu',
    description: 'Clean, neutral-tasting milled rice flour providing crisp expansion, light texture, and low-allergen bulk in gluten-free extruded snacks and crackers.'
  },
  'ING-011': {
    belt: 'Indo-Gangetic Wheat Belt — Punjab, Haryana, and Uttar Pradesh',
    description: 'Whole-wheat stone-milled atta containing natural gluten viscoelasticity for dough extensibility and reference baseline cost benchmarking.'
  },
  'ING-012': {
    belt: 'Sugarcane Belt — Maharashtra (Kolhapur), Uttar Pradesh, and Karnataka',
    description: 'Unrefined cane jaggery (Gud) free from sulphur bleaching. Provides natural caramel sweetness, trace minerals (iron, potassium), and Maillard browning in baked snacks.'
  },
  'ING-013': {
    belt: 'North-Western Arid Belt — Rajasthan (Bikaner, Jaisalmer, Churu) and Haryana',
    description: 'Natural seed galactomannan hydrocolloid extracted from guar beans. Used at low inclusion (<2%) as a clean-label thickener, moisture retainer, and dough binder.'
  },
  'ING-014': {
    belt: 'Coastal Salt Pans — Gujarat (Kutch, Bhavnagar), Tamil Nadu, and Rajasthan',
    description: 'Food-grade iodised table salt used at micro-dosing levels (0.5–2%) for flavor balance, dough strengthening, and shelf stability.'
  },
  'ING-015': {
    belt: 'Western Dairy Cooperative Belt — Gujarat (Anand), Punjab, and Maharashtra',
    description: 'Spray-dried skim milk powder supplying concentrated dairy protein (34%), lactose browning, and creamy mouthfeel in non-vegan fortification blends.'
  },
  'ING-016': {
    belt: 'Western Groundnut Belt — Gujarat (Saurashtra), Andhra Pradesh, and Tamil Nadu',
    description: 'Pressed peanut cake flour offering 45% clean-label plant protein and roasted nutty aroma, suitable for high-protein energy bars and savory biscuits.'
  },
  'ING-017': {
    belt: 'Western & Central India — Rajasthan, Gujarat, and Madhya Pradesh',
    description: 'Whole hulled sesame seeds (Til) providing concentrated energy (573 kcal/100g), healthy lipids, calcium, and visual/textural crunch on baked surfaces.'
  }
};

function getIngredientCostLevel(costPerKg) {
  const c = Number(costPerKg || 0);
  if (c <= 60) return { label: 'Budget-Friendly (Low Cost)', short: 'Low Cost', cls: 'ok' };
  if (c <= 140) return { label: 'Moderate Cost', short: 'Moderate', cls: 'warn' };
  return { label: 'Specialty / Premium Cost', short: 'Premium', cls: 'flag' };
}

window.SmartCrop.Views.renderIngredientsRows = function renderIngredientsRows(state) {
  const { Utils } = window.SmartCrop;
  const esc = Utils.esc;
  const boot = state.bootstrap || {};
  const isAdmin = boot.user && boot.user.role === 'lab_admin';
  const all = (state.ingredientsData && state.ingredientsData.ingredients) || [];
  const q = (state.ingQuery || '').trim().toLowerCase();
  const cat = state.ingCategory || 'All Classes';

  const visible = all.filter((r) => {
    const matchCat = cat === 'All Classes' || r.category === cat;
    const matchQ = !q || `${r.ingredient_id} ${r.name} ${r.local_name} ${r.region} ${r.category}`.toLowerCase().includes(q);
    return matchCat && matchQ;
  });

  if (!visible.length) {
    return `<div class="table-empty-body"><div class="empty-panel" style="border:none;background:transparent;"><h2 class="empty-title">No matching ingredients</h2><p class="empty-desc">Try clearing the filter or search terms.</p></div></div>`;
  }

  return visible.map((r) => {
    const nutCls = r.nutrition_confidence === 'verified' ? 'ok' : (r.nutrition_confidence === 'unknown' ? 'flag' : 'warn');
    const costCls = r.cost_confidence === 'verified' ? 'ok' : (r.cost_confidence === 'unknown' ? 'flag' : 'warn');
    return `
      <div class="data-row-grid-ings">
        <div>
          <strong style="color:var(--forest-950);">${esc(r.name)}</strong>
          <div style="font-size:11px;color:var(--text-muted);">${esc(r.local_name || r.region)} · <code>${esc(r.ingredient_id)}</code></div>
        </div>
        <div><span class="badge-pill">${esc(r.category)}</span></div>
        <div style="font-family:var(--font-mono);">${Math.round(r.energy_kcal)} kcal · ${r.protein_g}g P</div>
        <div style="font-family:var(--font-mono);">₹${r.cost_per_kg}/kg · cap ${r.max_practical_pct}%</div>
        <div style="display:flex;gap:4px;flex-wrap:wrap;">
          <span class="badge-pill ${nutCls}">N: ${esc(r.nutrition_confidence)}</span>
          <span class="badge-pill ${costCls}">C: ${esc(r.cost_confidence)}</span>
        </div>
        <div style="display:flex;gap:6px;align-items:center;justify-content:flex-end;flex-wrap:wrap;">
          <button class="btn btn-glass btn-sm" type="button" data-open-crop="${esc(r.ingredient_id)}">More info</button>
          ${isAdmin
            ? `<button class="btn btn-glass btn-sm" type="button" data-verify-ing="${esc(r.ingredient_id)}">${r.nutrition_confidence === 'verified' && r.cost_confidence === 'verified' ? 'Review' : 'Verify'}</button>`
            : ''}
        </div>
      </div>`;
  }).join('');
};

window.SmartCrop.Views.ingredients = function renderIngredients(state) {
  const { Icons, Utils } = window.SmartCrop;
  const esc = Utils.esc;
  const data = state.ingredientsData || {};
  const all = data.ingredients || [];
  const counts = data.counts || {};
  const categories = ['All Classes', ...Array.from(new Set(all.map((r) => r.category)))];
  const activeCat = state.ingCategory || 'All Classes';

  return `
    <div class="view-container">
      <div class="page-header">
        <div>
          <div class="page-eyebrow"><span class="page-eyebrow-dot"></span><span>Functional Library · Data Verification</span></div>
          <h1 class="page-title">Ingredient Database</h1>
          <p class="page-subtitle">
            ${all.length} local ingredients (${counts.nutrition_verified || 0} nutrition verified, ${counts.cost_verified || 0} cost verified). Click <strong>More info</strong> for regional popularity, description, energy, and cost details.
          </p>
        </div>
        <div class="page-actions">
          <button class="btn btn-primary" type="button" id="ing-new-btn">${Icons.plus}<span>New Ingredient</span></button>
        </div>
      </div>

      <section class="glass-card filter-toolbar">
        <div class="search-field">
          ${Icons.search}
          <input id="ing-search-input" class="search-input" type="search" value="${esc(state.ingQuery || '')}" placeholder="Search ingredient name, ID, local name, or region…" aria-label="Search ingredients" />
        </div>
        <div class="pill-tabs" role="tablist" aria-label="Ingredient classes">
          ${categories.map((cat) => `<button class="pill-tab ${activeCat === cat ? 'is-active' : ''}" type="button" data-ing-cat="${esc(cat)}">${esc(cat)}</button>`).join('')}
        </div>
      </section>

      <section class="glass-card table-shell">
        <div class="data-row-grid-ings data-row-header" role="row">
          <span>Ingredient</span><span>Category</span><span>Nutrition / 100 g</span><span>Mandi Cost &amp; Cap</span><span>Confidence</span><span style="text-align:right;">Actions</span>
        </div>
        <div id="ingredients-table-host">${window.SmartCrop.Views.renderIngredientsRows(state)}</div>
      </section>
    </div>`;
};

window.SmartCrop.Views['crop-detail'] = function renderIngredientDetail(state) {
  const { Icons, Utils } = window.SmartCrop;
  const esc = Utils.esc;
  const all = (state.ingredientsData && state.ingredientsData.ingredients) || [];
  const crop = all.find((r) => r.ingredient_id === state.activeCropId) || all[0] || null;

  if (!crop) {
    return `
      <div class="view-container">
        <div class="empty-panel">
          <h2 class="empty-title">Ingredient not found</h2>
          <p class="empty-desc">The requested ingredient record could not be loaded.</p>
          <button class="btn btn-primary btn-sm" type="button" data-route="ingredients">Back to Ingredient Database</button>
        </div>
      </div>`;
  }

  const meta = INGREDIENT_DETAILS_META[crop.ingredient_id] || {
    belt: `Regional Indian cultivation — primarily ${crop.region || 'regional mandi networks'}`,
    description: `${crop.name} (${crop.local_name || crop.category}) is a ${String(crop.category || '').toLowerCase()} ingredient sourced from ${crop.region || 'local Indian markets'}. ${crop.clean_label_note || ''}`
  };
  const costTier = getIngredientCostLevel(crop.cost_per_kg);
  const cleanCls = crop.is_clean_label === 'yes' ? 'ok' : (crop.is_clean_label === 'check' ? 'warn' : 'flag');
  const nutCls = crop.nutrition_confidence === 'verified' ? 'ok' : (crop.nutrition_confidence === 'unknown' ? 'flag' : 'warn');
  const costConfCls = crop.cost_confidence === 'verified' ? 'ok' : 'warn';

  const nutBreakdown = [
    { label: 'Energy', val: `${Math.round(crop.energy_kcal)} kcal`, pct: Math.min(100, (crop.energy_kcal / 600) * 100) },
    { label: 'Protein', val: `${crop.protein_g} g`, pct: Math.min(100, (crop.protein_g / 50) * 100) },
    { label: 'Carbohydrate', val: `${crop.carbs_g} g`, pct: Math.min(100, crop.carbs_g) },
    { label: 'Dietary Fibre', val: `${crop.fibre_g} g`, pct: Math.min(100, (crop.fibre_g / 25) * 100) },
    { label: 'Total Fat', val: `${crop.fat_g} g`, pct: Math.min(100, (crop.fat_g / 50) * 100) },
    { label: 'Moisture', val: `${crop.moisture_g} g`, pct: Math.min(100, (crop.moisture_g / 20) * 100) }
  ];

  return `
    <div class="view-container crop-detail-view">
      <div class="crop-detail-topbar">
        <button class="btn btn-glass btn-sm" type="button" data-route="ingredients">← Back to Ingredient Database</button>
        <button class="btn btn-primary btn-sm" type="button" data-formulate-crop="${esc(crop.name)}">${Icons.studio}<span>Use in Formulation Studio</span></button>
      </div>

      <section class="glass-card crop-detail-hero crop-detail-hero-grid">
        <div class="crop-detail-hero-main">
          <div class="crop-detail-hero-top">
            <div>
              <div class="page-eyebrow"><span class="page-eyebrow-dot"></span><span>${esc(crop.ingredient_id)} · ${esc(crop.category)} · Source ${esc(crop.source_id || 'S-001')}</span></div>
              <h1 class="page-title" style="margin-top:4px;">${esc(crop.name)}</h1>
              <div style="font-size:14px;color:var(--text-muted);margin-top:2px;">Local / Regional Name: <strong style="color:var(--forest-950);">${esc(crop.local_name || 'Standard')}</strong></div>
            </div>
            <div class="crop-detail-badges">
              <span class="badge-pill ${cleanCls}">${crop.is_clean_label === 'yes' ? 'Clean Label' : `Watchlist: ${esc(crop.is_clean_label)}`}</span>
              <span class="badge-pill ${costTier.cls}">${esc(costTier.short)}</span>
              <span class="badge-pill ${nutCls}">Nutrition: ${esc(crop.nutrition_confidence)}</span>
            </div>
          </div>
          <p class="crop-detail-desc">${esc(meta.description)}</p>
        </div>

        <div class="crop-photo-card" data-photo-iid="${esc(crop.ingredient_id)}">
          ${crop.photo_url ? `
            <img src="${esc(crop.photo_url)}" alt="${esc(crop.name)}" class="crop-photo-img" />
            <div class="crop-photo-actions">
              <label class="btn btn-glass btn-sm" for="crop-photo-input" style="cursor:pointer;">Change Photo</label>
              <button class="btn btn-glass btn-sm" type="button" data-remove-crop-photo="${esc(crop.ingredient_id)}">Remove</button>
            </div>
          ` : `
            <label class="crop-photo-empty" for="crop-photo-input">
              <span class="crop-photo-empty-icon" aria-hidden="true">${Icons.crops}</span>
              <span class="crop-photo-empty-title">+ Add Ingredient Photo</span>
              <span class="crop-photo-empty-hint">PNG, JPG, WEBP · up to 5 MB</span>
            </label>
          `}
          <input id="crop-photo-input" type="file" accept=".png,.jpg,.jpeg,.webp,image/*" data-photo-target="${esc(crop.ingredient_id)}" hidden />
        </div>
      </section>

      <section class="grid-4" aria-label="Ingredient summary metrics">
        <article class="glass-card slot-card">
          <div class="slot-card-top"><span class="slot-label">Energy (per 100g)</span></div>
          <div class="slot-placeholder-box">
            <span class="slot-dash" style="color:var(--forest-950);font-size:22px;">${Math.round(crop.energy_kcal)} kcal</span>
            <span class="slot-status">${esc(crop.nutrition_basis || 'as-is per 100 g')}</span>
          </div>
        </article>
        <article class="glass-card slot-card">
          <div class="slot-card-top"><span class="slot-label">Protein Density</span></div>
          <div class="slot-placeholder-box">
            <span class="slot-dash" style="color:var(--forest-950);font-size:22px;">${crop.protein_g} g</span>
            <span class="slot-status">Fibre ${crop.fibre_g}g · Fat ${crop.fat_g}g</span>
          </div>
        </article>
        <article class="glass-card slot-card">
          <div class="slot-card-top"><span class="slot-label">Cost Level</span></div>
          <div class="slot-placeholder-box">
            <span class="slot-dash" style="color:var(--forest-950);font-size:22px;">₹${Number(crop.cost_per_kg).toFixed(2)}/kg</span>
            <span class="slot-status">${esc(costTier.label)} · ₹${(Number(crop.cost_per_kg) / 10).toFixed(2)}/100g</span>
          </div>
        </article>
        <article class="glass-card slot-card">
          <div class="slot-card-top"><span class="slot-label">Max Practical Cap</span></div>
          <div class="slot-placeholder-box">
            <span class="slot-dash" style="color:var(--forest-950);font-size:22px;">${crop.max_practical_pct}%</span>
            <span class="slot-status">Recommended max blend share</span>
          </div>
        </article>
      </section>

      <section class="grid-2">
        <article class="glass-card card-section">
          <div class="card-section-header">
            <h2 class="card-section-title">Indian Regional Popularity &amp; Sourcing</h2>
            <span class="badge-pill ok">${esc(crop.region)}</span>
          </div>
          <div class="crop-info-list">
            <div class="crop-info-row">
              <span class="crop-info-key">Primary Indian State / Region</span>
              <span class="crop-info-val"><strong>${esc(crop.region)}</strong></span>
            </div>
            <div class="crop-info-row">
              <span class="crop-info-key">High Popularity Belt</span>
              <span class="crop-info-val">${esc(meta.belt)}</span>
            </div>
            <div class="crop-info-row">
              <span class="crop-info-key">Cost Level &amp; Spot Pricing</span>
              <span class="crop-info-val"><strong>${esc(costTier.label)}</strong> — ₹${Number(crop.cost_per_kg).toFixed(2)}/kg (${esc(crop.cost_basis || 'local mandi spot price')})</span>
            </div>
            <div class="crop-info-row">
              <span class="crop-info-key">Price Survey Date &amp; Status</span>
              <span class="crop-info-val">${esc(crop.cost_date || '—')} · <span class="badge-pill ${costConfCls}">${esc(crop.cost_confidence)}</span></span>
            </div>
            <div class="crop-info-row">
              <span class="crop-info-key">Clean-Label Assessment</span>
              <span class="crop-info-val">${esc(crop.clean_label_note || 'No synthetic additives')}</span>
            </div>
          </div>
        </article>

        <article class="glass-card card-section">
          <div class="card-section-header">
            <h2 class="card-section-title">Proximate Nutrition Breakdown</h2>
            <span class="card-section-meta">Per 100 g (${esc(crop.nutrition_basis || 'as-is')})</span>
          </div>
          <div class="crop-nutrient-bars">
            ${nutBreakdown.map((n) => `
              <div class="crop-nut-row">
                <div class="crop-nut-head">
                  <span>${esc(n.label)}</span>
                  <strong style="font-family:var(--font-mono);">${esc(n.val)}</strong>
                </div>
                <div class="share-meter-track" style="width:100%;height:7px;">
                  <div class="share-meter-fill" style="width:${Math.max(2, n.pct)}%;"></div>
                </div>
              </div>`).join('')}
          </div>
        </article>
      </section>
    </div>`;
};
