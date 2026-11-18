/* ==========================================================================
   MOD MANAGER FS25 — logica dashboard
   Dati generati da scan_mods.py (window.MODS_DATA)
   ========================================================================== */
(() => {
  'use strict';

  const DATA = window.MODS_DATA;
  if (!DATA || !Array.isArray(DATA.mods)) {
    document.body.innerHTML = '<div style="padding:40px;color:#fff;font-family:sans-serif">' +
      '<h1>Dati non trovati</h1><p>Esegui <code>python3 MOD_MANAGER/scan_mods.py</code> per generare <code>data/mods.js</code>.</p></div>';
    return;
  }

  const mods = DATA.mods;
  const meta = DATA.meta || {};
  const stats = meta.stats || {};
  const byId = new Map(mods.map(m => [m.id, m]));
  const colorMap = meta.category_colors || {};
  const typeLabels = meta.type_labels || {};

  const TIER_RANK = { S: 0, A: 1, B: 2, C: 3, D: 4, E: 5, F: 6, G: 7, H: 8 };
  const TYPE_GLYPH = {
    mappa: '🗺️', veicolo: '🚜', attrezzo: '🛠️', piazzabile: '🏗️',
    script: '⚙️', pacchetto: '📦', altro: '❓'
  };
  const CATEGORY_DESC = {
    'Mappe': 'Ambientazioni di gioco. In un salvataggio va attiva una sola mappa.',
    'Trattori e mezzi': 'Trattori, camion, sollevatori e veicoli per il lavoro quotidiano.',
    'Mietitrebbie e raccolta': 'Mietitrebbie, barre, raccoglitori e macchine da raccolta.',
    'Semina e colture': 'Seminatrici, concimazione, irrorazione e cura delle colture.',
    'Lavorazione del suolo': 'Aratri, coltivatori, erpici, rulli e attrezzi da terra.',
    'Falci e fienagione': 'Falciatrici, presse, andanatori e avvolgitori per foraggio.',
    'Rimorchi e zavorre': 'Rimorchi, pianali, zavorre e trasporti pesanti.',
    'Acqua, letame e stalle': 'Cisterne, pompe, letame, abbeveratoi e ricoveri animali.',
    'Silos e stoccaggio': 'Silos, bunker, magazzini, pallet e depositi.',
    'Produzioni': 'Filiere che trasformano materie prime in prodotti più redditizi.',
    'Costruzioni e decorazioni': 'Capannoni, tettoie, case, luci e arredo della fattoria.',
    'Terraforming e strade': 'Modellazione del terreno, pittura, strade e piazzali.',
    'Script e utility': 'Mod che aggiungono funzioni, HUD, comandi e qualità della vita.',
    'Strumenti vari': 'Attrezzi manuali e oggetti di uso quotidiano.',
    'Copie mod attive': 'Copie di sicurezza delle mod presenti in mods/. Utili per ripristinare.',
    'Altro': 'Mod non classificate automaticamente: apri la scheda per i dettagli.'
  };
  const ISSUE_META = {
    zip_non_valido: { title: 'ZIP non valido', level: 'error', desc: 'Il file non è un archivio ZIP leggibile: download incompleto o corrotto.' },
    moddesc_mancante: { title: 'modDesc.xml mancante', level: 'error', desc: 'Senza modDesc il gioco non può caricare la mod.' },
    versione_mancante: { title: 'Versione non dichiarata', level: 'warning', desc: 'La mod non indica la versione: difficile capire se è aggiornata.' },
    descrizione_mancante: { title: 'Descrizione troppo breve', level: 'warning', desc: 'Manca una descrizione utile (sotto i 30 caratteri): la scheda si basa sui dati tecnici.' },
    icona_mancante: { title: 'Icona mancante', level: 'warning', desc: 'Nessuna icona o preview trovata nello ZIP: in dashboard appare un segnaposto.' },
    file_molto_piccolo: { title: 'File molto piccolo', level: 'warning', desc: 'Dimensione sospetta: potrebbe essere un download incompleto o un file di errore.' },
    duplicato_esatto: { title: 'Copia esatta', level: 'info', desc: 'File identico presente più volte. Di solito è la copia di sicurezza in 15_COPIE_MOD_ATTIVE.' },
    conflitto_versione: { title: 'Conflitto di versione', level: 'warning', desc: 'La stessa mod esiste in più versioni o con contenuti diversi: scegli quale tenere.' }
  };

  const state = {
    view: 'inventory',
    q: '',
    source: 'all',
    category: 'all',
    type: 'all',
    sort: 'relevance',
    density: 'comfortable',
    dupTab: 'exact',
    catalogType: 'all',
    catalogSort: 'type',
    selectedId: null,
    expandedIssues: new Set()
  };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function setHash(value) {
    try { history.replaceState(null, '', value); } catch (error) { /* file:// in alcuni browser */ }
  }

  // --------------------------------------------------------------- helpers

  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[ch]));

  const norm = (value) => String(value ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

  function formatSize(bytes) {
    const n = Number(bytes) || 0;
    if (n < 1024) return n + ' B';
    const units = ['KB', 'MB', 'GB'];
    let value = n;
    let i = -1;
    do { value /= 1024; i++; } while (value >= 1024 && i < units.length - 1);
    return value.toLocaleString('it-IT', { maximumFractionDigits: 1 }) + ' ' + units[i];
  }

  function formatPrice(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
    return new Intl.NumberFormat('it-IT').format(Number(value)) + ' $';
  }

  function formatDate(timestamp) {
    if (!timestamp) return '—';
    return new Date(timestamp * 1000).toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  function formatVersion(value) {
    if (!value) return '—';
    return /^v/i.test(value) ? value : 'v' + value;
  }

  function formatNumber(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
    return new Intl.NumberFormat('it-IT').format(Number(value));
  }

  function priceValues(m) {
    return (m.store_items || [])
      .map(item => item.price)
      .filter(value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value)))
      .map(Number);
  }

  function priceFrom(m) {
    const values = priceValues(m);
    if (!values.length) return '';
    const positive = values.filter(value => value > 0);
    return 'da ' + formatPrice(Math.min(...(positive.length ? positive : values)));
  }

  function itemPowerLabel(item) {
    if (item.power !== null && item.power !== undefined) return formatNumber(item.power) + ' CV';
    if (item.needed_power !== null && item.needed_power !== undefined) return 'min ' + formatNumber(item.needed_power) + ' CV';
    return '—';
  }

  function itemNumber(value, unit) {
    if (value === null || value === undefined || value === '') return '—';
    const number = Number(value);
    if (!Number.isFinite(number)) return '—';
    return number.toLocaleString('it-IT', { maximumFractionDigits: 1 }) + ' ' + unit;
  }

  function officialVotes(m) {
    return m.official && Number.isFinite(Number(m.official.votes)) ? Number(m.official.votes) : null;
  }

  function uniqueMods() {
    const map = new Map();
    mods.forEach(m => {
      const current = map.get(m.key);
      if (!current || (m.source === 'attiva' && current.source !== 'attiva')) map.set(m.key, m);
    });
    return Array.from(map.values());
  }

  function sourceInfo(m) {
    if (m.source === 'attiva') return { label: 'Attiva', cls: 'badge-active', full: 'Attiva in mods/' };
    if (m.folder === '15_COPIE_MOD_ATTIVE') return { label: 'Copia', cls: 'badge-copy', full: 'Copia di sicurezza in BACKUP_MODS/15_COPIE_MOD_ATTIVE' };
    const folder = m.folder || '';
    if (folder.startsWith('mods-bck')) {
      return { label: 'Backup (bck)', cls: 'badge-backup', full: 'Archivio in ' + (m.path || folder) };
    }
    return { label: 'Backup', cls: 'badge-backup', full: 'Archivio in BACKUP_MODS/' + folder };
  }

  function categoryColor(category) {
    return colorMap[category] || '#8ea08b';
  }

  function tierRank(m) {
    const tier = m.curated && m.curated.tier;
    return tier && Object.prototype.hasOwnProperty.call(TIER_RANK, tier) ? TIER_RANK[tier] : 9;
  }

  function healthInfo(m) {
    const list = m.health || [];
    const errors = list.filter(h => h.level === 'error');
    const warnings = list.filter(h => h.level === 'warning');
    const infos = list.filter(h => h.level === 'info');
    return { errors, warnings, infos, hasIssues: errors.length + warnings.length > 0 };
  }

  function categoryGlyph(m) {
    return TYPE_GLYPH[m.type] || '❓';
  }

  function iconMarkup(m, sizeClass) {
    const color = categoryColor(m.category);
    const glyph = categoryGlyph(m);
    const fallbackStyle = `--fallback:${esc(color)}`;
    if (m.icon) {
      return `<span class="${sizeClass}-wrap">` +
        `<img class="${sizeClass}" src="${esc(m.icon)}" alt="" loading="lazy" ` +
        `onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">` +
        `<span class="${sizeClass}-fallback" style="${fallbackStyle};display:none">${glyph}</span>` +
        `</span>`;
    }
    return `<span class="${sizeClass}-wrap"><span class="${sizeClass}-fallback" style="${fallbackStyle}">${glyph}</span></span>`;
  }

  function linkify(text) {
    return esc(text).replace(/(https?:\/\/[^\s<]+)/g, url =>
      `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);
  }

  function shortText(m) {
    return (m.curated && m.curated.short) || m.desc_short || 'Nessuna descrizione disponibile.';
  }

  function typeLabel(m) {
    return typeLabels[m.type] || m.type || 'Altro';
  }

  // --------------------------------------------------------------- filtri

  function matches(m) {
    if (state.source === 'active' && m.source !== 'attiva') return false;
    if (state.source === 'backup' && m.source !== 'backup') return false;
    if (state.source === 'bck' && !(m.folder && m.folder.startsWith('mods-bck'))) return false;
    if (state.source === 'copies' && m.folder !== '15_COPIE_MOD_ATTIVE') return false;
    if (state.source === 'issues' && !healthInfo(m).hasIssues) return false;
    if (state.category !== 'all' && m.category !== state.category) return false;
    if (state.type !== 'all' && m.type !== state.type) return false;

    if (state.q) {
      const needle = norm(state.q);
      const official = m.official || {};
      const hay = norm([
        m.title, m.file, m.author, m.category, m.shop_category, m.type,
        (m.tags || []).join(' '),
        (m.curated && m.curated.short) || '',
        (m.curated && m.curated.details) || '',
        m.desc_short || '', (m.desc || '').slice(0, 3000),
        official.title, official.author, official.category, official.description,
        (m.store_items || []).map(i => [
          i.name, i.brand, (i.category_labels || []).join(' '), (i.functions || []).join(' '),
          (i.fill_types || []).join(' ')
        ].join(' ')).join(' ')
      ].join(' '));
      if (!hay.includes(needle)) return false;
    }
    return true;
  }

  function sortMods(list) {
    const sorted = list.slice();
    sorted.sort((a, b) => {
      switch (state.sort) {
        case 'name':
          return a.title.localeCompare(b.title, 'it', { sensitivity: 'base' });
        case 'size':
          return b.size - a.size;
        case 'date':
          return b.mtime - a.mtime;
        case 'category':
          return a.category.localeCompare(b.category, 'it') || a.title.localeCompare(b.title, 'it');
        case 'version':
          return String(a.version).localeCompare(String(b.version), 'it', { numeric: true });
        default: {
          const activeDelta = (a.source === 'attiva' ? 0 : 1) - (b.source === 'attiva' ? 0 : 1);
          if (activeDelta) return activeDelta;
          const tierDelta = tierRank(a) - tierRank(b);
          if (tierDelta) return tierDelta;
          return a.title.localeCompare(b.title, 'it', { sensitivity: 'base' });
        }
      }
    });
    return sorted;
  }

  function filteredMods() {
    return sortMods(mods.filter(matches));
  }

  // --------------------------------------------------------------- stats

  function renderStats() {
    const total = stats.total_files || mods.length;
    const issues = stats.issues || mods.filter(m => healthInfo(m).hasIssues).length;
    const errors = stats.errors || mods.filter(m => healthInfo(m).errors.length).length;
    const cards = [
      { stat: 'active', cls: 'accent-green', label: 'Mod attive', value: stats.active ?? '—', sub: 'caricate da mods/' },
      { stat: 'backup', cls: 'accent-amber', label: 'In archivio', value: stats.backup ?? '—', sub: 'BACKUP_MODS, 15 categorie' },
      { stat: 'unique', cls: 'accent-cyan', label: 'Mod uniche', value: stats.unique_mods ?? '—', sub: 'dopo aver unito le copie' },
      { stat: 'size', cls: 'accent-blue', label: 'Spazio occupato', value: formatSize(stats.size_total || 0), sub: 'attive ' + formatSize(stats.size_active || 0) },
      { stat: 'duplicates', cls: 'accent-violet', label: 'Copie esatte', value: stats.exact_duplicate_files ?? 0, sub: (stats.duplicate_groups || 0) + ' gruppi di file identici' },
      { stat: 'health', cls: errors ? 'accent-red' : 'accent-green', label: 'Criticità', value: issues, sub: errors ? errors + ' errori da controllare' : 'nessun errore bloccante' }
    ];
    $('#stats').innerHTML = cards.map(card =>
      `<button class="stat-card ${card.cls}" data-stat="${card.stat}">
        <span class="stat-label">${esc(card.label)}</span>
        <span class="stat-value">${esc(card.value)}</span>
        <span class="stat-sub">${esc(card.sub)}</span>
      </button>`
    ).join('');
    $('#tab-count-inventory').textContent = total;
    $('#tab-count-duplicates').textContent = stats.duplicate_groups || 0;
    $('#tab-count-health').textContent = issues;
    $('#tab-count-categories').textContent = Object.keys(stats.categories || {}).length;
    $('#tab-count-catalog').textContent = formatNumber(catalogItems().length);
    $('#game-version').textContent = meta.game_version ? 'FS25 v' + meta.game_version : 'FS25';
    $('#generated-at').textContent = meta.generated_label || '—';
    $('#footer-paths').textContent = `${stats.active || 0} attive · ${stats.backup || 0} archivio · ${formatSize(stats.size_total || 0)}`;
  }

  // --------------------------------------------------------------- filtri UI

  function sourceCounts() {
    return {
      all: mods.length,
      active: mods.filter(m => m.source === 'attiva').length,
      backup: mods.filter(m => m.source === 'backup').length,
      bck: mods.filter(m => m.folder && m.folder.startsWith('mods-bck')).length,
      copies: mods.filter(m => m.folder === '15_COPIE_MOD_ATTIVE').length,
      issues: mods.filter(m => healthInfo(m).hasIssues).length
    };
  }

  function syncQuickChips() {
    $$('[data-quick]').forEach(chip => chip.classList.toggle('is-active', chip.dataset.quick === state.source));
  }

  function renderFilters() {
    syncQuickChips();
    const counts = sourceCounts();
    const sources = [
      { id: 'all', label: 'Tutte le mod', count: counts.all },
      { id: 'active', label: 'Attive (mods/)', count: counts.active },
      { id: 'backup', label: 'Tutto l\'archivio', count: counts.backup },
    ];
    if (counts.bck > 0) {
      sources.push({ id: 'bck', label: 'Backup (mods-bck/)', count: counts.bck });
    }
    sources.push(
      { id: 'copies', label: 'Copie di sicurezza', count: counts.copies },
      { id: 'issues', label: 'Con avvisi', count: counts.issues }
    );
    $('#filter-source').innerHTML = sources.map(s =>
      `<button class="filter-item ${state.source === s.id ? 'is-active' : ''}" data-source="${s.id}">
        <span class="f-label">${esc(s.label)}</span><span class="f-count">${s.count}</span>
      </button>`
    ).join('');

    const types = Object.entries(stats.types || {}).sort((a, b) => b[1] - a[1]);
    $('#filter-type').innerHTML =
      `<button class="filter-item ${state.type === 'all' ? 'is-active' : ''}" data-type="all">
        <span class="type-glyph">▦</span><span class="f-label">Tutti i tipi</span><span class="f-count">${mods.length}</span>
      </button>` +
      types.map(([type, count]) =>
        `<button class="filter-item ${state.type === type ? 'is-active' : ''}" data-type="${esc(type)}">
          <span class="type-glyph">${TYPE_GLYPH[type] || '•'}</span>
          <span class="f-label">${esc(typeLabels[type] || type)}</span><span class="f-count">${count}</span>
        </button>`
      ).join('');

    const categories = Object.entries(stats.categories || {}).sort((a, b) => b[1] - a[1]);
    $('#filter-category').innerHTML =
      `<button class="filter-item ${state.category === 'all' ? 'is-active' : ''}" data-category="all">
        <span class="dot" style="--dot:#8ea08b"></span><span class="f-label">Tutte le categorie</span><span class="f-count">${mods.length}</span>
      </button>` +
      categories.map(([category, count]) =>
        `<button class="filter-item ${state.category === category ? 'is-active' : ''}" data-category="${esc(category)}">
          <span class="dot" style="--dot:${esc(categoryColor(category))}"></span>
          <span class="f-label" title="${esc(category)}">${esc(category)}</span><span class="f-count">${count}</span>
        </button>`
      ).join('');
  }

  // --------------------------------------------------------------- inventario

  function renderInventory() {
    const list = filteredMods();
    const tbody = $('#mod-rows');
    tbody.innerHTML = list.map(m => {
      const src = sourceInfo(m);
      const health = healthInfo(m);
      const tier = m.curated && m.curated.tier
        ? `<span class="tier tier-${esc(m.curated.tier)}" title="Importanza ${esc(m.curated.tier)}">${esc(m.curated.tier)}</span>` : '';
      let flag = '<span class="flag ok" title="Nessuna criticità">✓</span>';
      if (health.errors.length) {
        flag = `<span class="flag has-errors" title="${health.errors.length} errore/i">!</span>`;
      } else if (health.warnings.length) {
        flag = `<span class="flag has-issues" title="${health.warnings.length} avviso/i">!</span>`;
      } else if (health.infos.length) {
        flag = `<span class="flag has-info" title="Copia esatta / duplicato">⧉</span>`;
      }
      const path = m.path || '';
      const price = priceFrom(m);
      const off = m.official;
      const extra = (price || off)
        ? `<div class="mod-extra">${price ? `<span class="mini-price">${esc(price)}</span>` : ''}${off ? `<span class="mini-mh" title="Valutazione ModHub ufficiale">★ ${esc(off.rating ?? '—')}${off.votes ? ` · ${esc(formatNumber(off.votes))}` : ''}</span>` : ''}</div>`
        : '';
      const isChecked = profileState ? profileState.activeSet.has(m.file) : false;
      return `<tr data-id="${esc(m.id)}" tabindex="0" class="${state.selectedId === m.id ? 'is-selected' : ''}" title="${esc(path)}">
        <td style="text-align:center; padding:10px;">
          <input type="checkbox" class="inv-toggle" data-file="${esc(m.file)}" ${isChecked ? 'checked' : ''} style="width:19px; height:19px; cursor:pointer; accent-color:#2ecc71;">
        </td>
        <td class="col-mod">
          <div class="mod-cell">
            ${iconMarkup(m, 'mod-icon')}
            <div class="mod-meta">
              <div class="mod-title"><strong>${esc(m.title)}</strong>${tier}</div>
              <div class="mod-file">${esc(m.file)}</div>
              ${extra}
            </div>
          </div>
        </td>
        <td class="col-what"><div class="what-text">${esc(shortText(m))}</div></td>
        <td class="col-cat">
          <span class="cat-chip"><span class="cat-dot" style="--dot:${esc(categoryColor(m.category))}"></span>${esc(m.category)}</span>
          ${m.shop_category && m.shop_category !== m.category && !norm(m.category).includes(norm(m.shop_category)) ? `<span class="shop-sub">${esc(m.shop_category)}</span>` : ''}
        </td>
        <td class="col-type"><span class="badge badge-type">${esc(typeLabel(m))}</span></td>
        <td class="col-ver"><span class="cell-mono">${esc(formatVersion(m.version))}</span></td>
        <td class="col-author"><span class="cell-soft" title="${esc(m.author || '')}">${esc(m.author || '—')}</span></td>
        <td class="col-source"><span class="badge ${src.cls}" title="${esc(src.full)}">${esc(src.label)}</span></td>
        <td class="col-size"><span class="cell-size">${esc(formatSize(m.size))}</span></td>
        <td class="col-date"><span class="cell-date">${esc(formatDate(m.mtime))}</span></td>
        <td class="col-flags">${flag}</td>
      </tr>`;
    }).join('');

    // Bind checkboxes nella tabella inventario principale
    $$('.inv-toggle', tbody).forEach(chk => {
      chk.addEventListener('change', (e) => {
        e.stopPropagation();
        const file = chk.dataset.file;
        if (chk.checked) {
          profileState.activeSet.add(file);
        } else {
          profileState.activeSet.delete(file);
        }
        updateProfileUI();
      });
      chk.addEventListener('click', (e) => e.stopPropagation());
    });

    $('#empty-inventory').hidden = list.length > 0;
    $('.mod-table').style.display = list.length ? '' : 'none';
    $('#result-count').textContent = `${list.length} di ${mods.length} mod`;
    $('#tab-count-inventory').textContent = mods.length;
  }

  // --------------------------------------------------------------- drawer

  function detailStoreItems(m) {
    const items = (m.store_items || []).filter(Boolean);
    if (!items.length) return '';
    const sorted = items.slice().sort((a, b) => (a.price || 0) - (b.price || 0));
    return `<section class="drawer-section">
      <h3>Oggetti nello shop <span style="color:var(--muted-2);font-weight:400;letter-spacing:0;text-transform:none">(${items.length})</span></h3>
      <div class="store-scroll">
        <table class="store-table">
          <thead><tr><th>Nome</th><th>Categoria</th><th class="price">Prezzo</th><th>Potenza</th><th>Larghezza</th><th>Velocità</th><th>Upkeep</th></tr></thead>
          <tbody>${sorted.map(item => {
            const extra = [
              item.brand,
              item.capacity ? 'cap. ' + itemNumber(item.capacity, 'L') : '',
              item.weight ? itemNumber(item.weight, 'kg') : '',
              (item.fill_types || []).length ? 'riempimento: ' + item.fill_types.join(', ') : ''
            ].filter(Boolean).join(' · ');
            return `<tr title="${esc(extra)}">
              <td>${esc(item.name || '—')}${extra ? `<span class="store-extra">${esc(extra)}</span>` : ''}</td>
              <td class="cat">${esc((item.category_labels && item.category_labels.join(', ')) || (item.categories || []).join(', ') || '—')}</td>
              <td class="price">${esc(formatPrice(item.price))}</td>
              <td>${esc(itemPowerLabel(item))}</td>
              <td>${esc(itemNumber(item.working_width, 'm'))}</td>
              <td>${esc(itemNumber(item.maxSpeed, 'km/h'))}</td>
              <td>${item.daily_upkeep !== null && item.daily_upkeep !== undefined ? esc(formatPrice(item.daily_upkeep)) : '—'}</td>
            </tr>`;
          }).join('')}</tbody>
        </table>
      </div>
    </section>`;
  }

  function detailOfficial(m) {
    const o = m.official;
    if (!o) {
      if (m.official_status === 'not_found') {
        return `<section class="drawer-section">
          <h3>ModHub ufficiale</h3>
          <p class="drawer-text muted-line">Questa mod non è stata trovata sul ModHub ufficiale: probabilmente arriva da un sito esterno. Prezzo e specifiche sono quelli dichiarati nel suo <code>modDesc.xml</code>.</p>
        </section>`;
      }
      return '';
    }
    const rating = Number.isFinite(Number(o.rating)) ? Number(o.rating).toFixed(1) : '—';
    const votes = Number.isFinite(Number(o.votes)) ? formatNumber(o.votes) : '—';
    return `<section class="drawer-section official-section">
      <h3>ModHub ufficiale</h3>
      <div class="official-head">
        <span class="official-rating">★ ${esc(rating)}</span>
        <span class="official-votes">${esc(votes)} voti</span>
        <span class="official-badge">scheda verificata</span>
      </div>
      <div class="meta-grid official-grid">
        <div class="meta-cell"><span>Data di uscita</span><strong>${esc(o.released || '—')}</strong></div>
        <div class="meta-cell"><span>Categoria ModHub</span><strong>${esc(o.category || '—')}</strong></div>
        <div class="meta-cell"><span>Piattaforme</span><strong>${esc(o.platform || '—')}</strong></div>
        <div class="meta-cell"><span>Autore ufficiale</span><strong>${esc(o.author || '—')}</strong></div>
        <div class="meta-cell"><span>Versione ModHub</span><strong>${esc(formatVersion(o.version))}</strong></div>
        <div class="meta-cell"><span>Dimensione ModHub</span><strong>${esc(o.size || '—')}</strong></div>
      </div>
      <a class="btn btn-primary official-link" href="${esc(o.url)}" target="_blank" rel="noopener">Apri la pagina ModHub</a>
      <p class="official-note">Il ModHub non rende pubblici i download per singola mod: i voti sono il dato ufficiale di popolarità disponibile.</p>
      ${o.description ? `<details class="official-desc">
        <summary>Descrizione ufficiale ModHub</summary>
        <div>${esc(o.description).replace(/\n/g, '<br>')}</div>
      </details>` : ''}
    </section>`;
  }

  function detailRelated(m) {
    const byId = new Map(mods.map(x => [x.id, x]));
    const ids = Array.from(new Set([...(m.copies || []), ...(m.same_key || [])]))
      .filter(id => id !== m.id && byId.has(id));
    if (!ids.length) return '';
    return `<section class="drawer-section">
      <h3>Copie e stessa mod</h3>
      <div class="related-list">${ids.map(id => {
        const rel = byId.get(id);
        const src = sourceInfo(rel);
        return `<button class="related-item" data-goto="${esc(id)}">
          <span class="badge ${src.cls}">${esc(src.label)}</span>
          <span class="rel-path" title="${esc(rel.path)}">${esc(rel.path)}</span>
          <span style="color:var(--muted-2);font-size:9.5px;white-space:nowrap">${esc(formatVersion(rel.version))} · ${esc(formatSize(rel.size))}</span>
        </button>`;
      }).join('')}</div>
    </section>`;
  }

  function detailHealth(m) {
    const list = m.health || [];
    if (!list.length) {
      return `<section class="drawer-section"><h3>Controlli</h3>
        <div class="health-list"><div class="health-line ok"><span class="hdot"></span><span>Nessuna criticità rilevata: ZIP, modDesc, icona e descrizione sono a posto.</span></div></div>
      </section>`;
    }
    return `<section class="drawer-section"><h3>Controlli automatici</h3>
      <div class="health-list">${list.map(h => `<div class="health-line ${esc(h.level)}">
        <span class="hdot"></span><span>${esc(h.msg || h.code)}</span>
      </div>`).join('')}</div>
    </section>`;
  }

  function renderDetail(m) {
    const cur = m.curated || {};
    const src = sourceInfo(m);
    const health = healthInfo(m);
    const tier = cur.tier ? `<span class="badge tier-${esc(cur.tier)}">Tier ${esc(cur.tier)}</span>` : '';
    const dates = formatDate(m.mtime);
    const descText = m.desc || 'Nessuna descrizione presente nel modDesc.';
    const longDesc = descText.length > 850;
    const validNumber = v => v !== null && v !== undefined && v !== '' && Number.isFinite(Number(v));
    const priceItems = (m.store_items || []).map(i => i.price).filter(validNumber);
    const priceRange = priceItems.length
      ? (Math.min(...priceItems) === Math.max(...priceItems)
        ? formatPrice(priceItems[0])
        : formatPrice(Math.min(...priceItems)) + ' – ' + formatPrice(Math.max(...priceItems)))
      : '—';
    const powerItems = (m.store_items || []).map(i => i.power).filter(validNumber);
    const powerRange = powerItems.length
      ? (Math.min(...powerItems) === Math.max(...powerItems)
        ? Math.min(...powerItems) + ' CV'
        : Math.min(...powerItems) + '–' + Math.max(...powerItems) + ' CV')
      : '—';
    const deps = (m.deps || []).length
      ? m.deps.map(d => `<span class="tag">${esc(d)}</span>`).join('')
      : '<span style="color:var(--muted-2);font-size:11px">Nessuna dipendenza dichiarata</span>';
    const tags = (m.tags || []).length
      ? m.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')
      : '<span style="color:var(--muted-2);font-size:11px">Nessun tag automatico</span>';
    const tech = m.tech || {};

    const activation = m.source === 'attiva'
      ? ''
      : (m.folder === '15_COPIE_MOD_ATTIVE'
        ? `<div class="drawer-callout" style="border-color:rgba(106,169,255,.25);background:rgba(106,169,255,.06)">
            <span class="k" style="color:var(--blue)">Copia di sicurezza</span>
            <p>Questa copia serve solo a ripristinare la mod attiva. Non va caricata direttamente in <code>mods/</code>.</p>
          </div>`
        : `<div class="drawer-callout" style="border-color:rgba(245,196,81,.25);background:rgba(245,196,81,.055)">
            <span class="k" style="color:var(--amber)">Come attivarla</span>
            <p>Copia lo ZIP da <code>${esc(m.path)}</code> nella cartella <code>mods/</code>, poi avvia il gioco e spunta la mod nella schermata MOD del salvataggio.</p>
          </div>`);

    const descHtml = longDesc
      ? `<div class="drawer-desc desc-fade" id="desc-box">${linkify(descText)}</div>
         <button class="btn btn-ghost desc-toggle" id="desc-toggle" type="button">Mostra tutta la descrizione</button>`
      : `<div class="drawer-desc">${linkify(descText)}</div>`;
    const showDesc = descText.trim().length > 0 && !/^category:\s/i.test(descText.trim());
    const shopName = (m.shop_category || '').trim();
    const showShop = shopName && shopName.toLowerCase() !== (m.category || '').trim().toLowerCase();

    return `${activation}
      <div class="drawer-hero">
        ${iconMarkup(m, 'drawer-icon')}
        <div class="drawer-title-wrap">
          <h2>${esc(m.title)}</h2>
          <div class="drawer-file">${esc(m.file)}</div>
          <div class="drawer-badges">
            <span class="badge ${src.cls}">${esc(src.label)}</span>
            ${tier}
            <span class="badge badge-type">${esc(typeLabel(m))}</span>
            <span class="badge badge-soft">${esc(m.category)}</span>
          </div>
        </div>
      </div>

      <div class="drawer-callout">
        <span class="k">In breve</span>
        <p>${esc(shortText(m))}</p>
        ${cur.tip ? `<div class="tip"><strong>Consiglio:</strong> ${esc(cur.tip)}</div>` : ''}
      </div>

      ${cur.details ? `<section class="drawer-section"><h3>Cosa aggiunge</h3><p class="drawer-text">${esc(cur.details)}</p></section>` : ''}

      ${showDesc ? `<section class="drawer-section">
        <h3>Descrizione ufficiale</h3>
        ${descHtml}
      </section>` : ''}

      ${detailOfficial(m)}

      <section class="drawer-section">
        <h3>Dati della mod</h3>
        <div class="meta-grid">
          <div class="meta-cell"><span>Versione</span><strong>${esc(formatVersion(m.version))}</strong></div>
          <div class="meta-cell"><span>Autore</span><strong>${esc(m.author || '—')}</strong></div>
          <div class="meta-cell"><span>Categoria</span><strong>${esc(m.category)}</strong></div>
          ${showShop ? `<div class="meta-cell"><span>Categoria shop</span><strong>${esc(shopName)}</strong></div>` : ''}
          <div class="meta-cell"><span>Prezzo</span><strong>${esc(priceRange)}</strong></div>
          <div class="meta-cell"><span>Potenza</span><strong>${esc(powerRange)}</strong></div>
          <div class="meta-cell"><span>Multiplayer</span><strong>${m.multiplayer === true ? 'Sì' : m.multiplayer === false ? 'No' : 'Non dichiarato'}</strong></div>
          <div class="meta-cell"><span>modDesc</span><strong>${m.moddesc_version ? 'versione ' + esc(m.moddesc_version) : '—'}</strong></div>
          <div class="meta-cell"><span>Dimensione</span><strong>${esc(formatSize(m.size))}</strong></div>
          <div class="meta-cell"><span>Aggiornata</span><strong>${esc(dates)}</strong></div>
        </div>
      </section>

      ${detailStoreItems(m)}

      <section class="drawer-section">
        <h3>Contenuto tecnico</h3>
        <div class="tech-grid">
          <div class="tech-item"><strong>${tech.files ?? 0}</strong><span>File</span></div>
          <div class="tech-item"><strong>${tech.xml ?? 0}</strong><span>XML</span></div>
          <div class="tech-item"><strong>${tech.lua ?? 0}</strong><span>Lua</span></div>
          <div class="tech-item"><strong>${tech.i3d ?? 0}</strong><span>Modelli 3D</span></div>
          <div class="tech-item"><strong>${tech.dds ?? 0}</strong><span>Texture</span></div>
          <div class="tech-item"><strong>${tech.sounds ?? 0}</strong><span>Suoni</span></div>
          <div class="tech-item"><strong>${m.l10n_count ?? 0}</strong><span>Traduzioni</span></div>
          <div class="tech-item"><strong>${esc(formatSize(tech.uncompressed || 0))}</strong><span>Decompresso</span></div>
        </div>
      </section>

      <section class="drawer-section">
        <h3>Tag funzionali</h3>
        <div class="tag-row">${tags}</div>
      </section>

      <section class="drawer-section">
        <h3>Dipendenze</h3>
        <div class="tag-row">${deps}</div>
      </section>

      ${detailHealth(m)}
      ${detailRelated(m)}

      <section class="drawer-section">
        <h3>Percorso</h3>
        <div class="path-box">${esc(m.path)}</div>
        <button class="btn btn-ghost copy-btn" id="copy-path" type="button">Copia percorso</button>
      </section>

      <section class="drawer-section">
        <h3>Stato</h3>
        <div class="health-line ${health.errors.length ? 'error' : health.warnings.length ? '' : health.infos.length ? 'info' : 'ok'}">
          <span class="hdot"></span>
          <span>${health.errors.length ? 'Ci sono errori da correggere.' : health.warnings.length ? 'Ci sono avvisi non bloccanti.' : health.infos.length ? 'Nessun errore: è presente come copia/duplicato.' : 'Tutto regolare.'}</span>
        </div>
      </section>`;
  }

  function openMod(id, updateHash = true) {
    const m = byId.get(id);
    if (!m) return;
    state.selectedId = id;
    $$('#mod-rows tr').forEach(tr => tr.classList.toggle('is-selected', tr.dataset.id === id));
    const drawer = $('#drawer');
    const backdrop = $('#drawer-backdrop');
    $('#drawer-body').innerHTML = renderDetail(m);
    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    backdrop.hidden = false;
    requestAnimationFrame(() => backdrop.classList.add('is-open'));
    document.body.style.overflow = 'hidden';
    $('#drawer-body').scrollTop = 0;
    if (updateHash) setHash('#mod=' + encodeURIComponent(id));
  }

  function closeMod(updateHash = true) {
    state.selectedId = null;
    const drawer = $('#drawer');
    const backdrop = $('#drawer-backdrop');
    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    backdrop.classList.remove('is-open');
    document.body.style.overflow = '';
    setTimeout(() => { if (!drawer.classList.contains('is-open')) backdrop.hidden = true; }, 280);
    $$('#mod-rows tr').forEach(tr => tr.classList.remove('is-selected'));
    if (updateHash) setHash('#view=' + state.view);
  }

  // --------------------------------------------------------------- duplicati

  function groupBy(items, keyFn) {
    const map = new Map();
    items.forEach(item => {
      const key = keyFn(item);
      if (!key) return;
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(item);
    });
    return Array.from(map.values()).filter(group => group.length > 1);
  }

  function exactGroups() {
    return groupBy(mods, m => m.duplicate_group);
  }

  function sameKeyGroups() {
    return groupBy(mods, m => m.key);
  }

  function conflictGroups() {
    return sameKeyGroups().filter(group =>
      new Set(group.map(m => m.version || '?')).size > 1 ||
      new Set(group.map(m => m.sha256)).size > 1
    );
  }

  function groupTitle(group) {
    const active = group.find(m => m.source === 'attiva');
    return (active || group[0]).title;
  }

  function groupHint(group) {
    const hasActive = group.some(m => m.source === 'attiva');
    const hasCopy = group.some(m => m.folder === '15_COPIE_MOD_ATTIVE');
    const versions = new Set(group.map(m => m.version || '?'));
    if (versions.size > 1 || new Set(group.map(m => m.sha256)).size > 1) {
      return 'Stessa mod con versioni o contenuti diversi: scegli quale tenere.';
    }
    if (hasActive && hasCopy) return 'Copia di sicurezza della mod attiva: situazione regolare.';
    if (group.every(m => m.source === 'backup')) return 'Doppione nell\'archivio: puoi tenerne una sola copia.';
    return 'File identico presente in più posizioni.';
  }

  function dupItem(m) {
    const src = sourceInfo(m);
    return `<div class="dup-item" data-open-mod="${esc(m.id)}" tabindex="0" role="button">
      <span class="badge ${src.cls}">${esc(src.label)}</span>
      <span class="dup-path" title="${esc(m.path)}"><strong>${esc(m.path)}</strong></span>
      <span class="dup-version">${esc(formatVersion(m.version))}</span>
      <span class="dup-size">${esc(formatSize(m.size))}</span>
    </div>`;
  }

  function groupCard(group, badgeText, badgeClass) {
    const versions = Array.from(new Set(group.map(m => m.version || '?'))).join(' / ');
    const totalSize = group.reduce((sum, m) => sum + m.size, 0);
    const sorted = group.slice().sort((a, b) => {
      const rank = m => m.source === 'attiva' ? 0 : m.folder === '15_COPIE_MOD_ATTIVE' ? 1 : 2;
      return rank(a) - rank(b) || a.path.localeCompare(b.path);
    });
    return `<article class="dup-group">
      <div class="dup-group-head">
        <div class="dup-group-title"><span class="badge ${badgeClass}">${esc(badgeText)}</span><strong>${esc(groupTitle(group))}</strong></div>
        <div class="dup-group-meta">${esc(versions)} · ${group.length} file · ${esc(formatSize(totalSize))}</div>
      </div>
      <div class="dup-items">${sorted.map(dupItem).join('')}</div>
      <div class="dup-group-head" style="border-top:1px solid var(--line-soft);border-bottom:0;background:transparent">
        <span class="dup-hint">${esc(groupHint(group))}</span>
      </div>
    </article>`;
  }

  function renderDuplicates() {
    const exact = exactGroups();
    const same = sameKeyGroups();
    const conflicts = conflictGroups();
    const exactFiles = exact.reduce((sum, g) => sum + g.length, 0);
    $('#duplicate-stats').innerHTML = `
      <div class="mini-stat"><span>Gruppi identici</span><strong>${exact.length}</strong><small>${exactFiles} file coinvolti</small></div>
      <div class="mini-stat"><span>Copia attesa</span><strong>${exact.filter(g => g.some(m => m.source === 'attiva') && g.some(m => m.folder === '15_COPIE_MOD_ATTIVE')).length}</strong><small>attiva + copia di sicurezza</small></div>
      <div class="mini-stat"><span>Stessa mod</span><strong>${same.length}</strong><small>presente in più cartelle</small></div>
      <div class="mini-stat"><span>Conflitti</span><strong style="color:${conflicts.length ? 'var(--red)' : 'var(--green)'}">${conflicts.length}</strong><small>versioni da scegliere</small></div>`;

    let html = '';
    if (state.dupTab === 'conflicts') {
      html = conflicts.length
        ? `<div class="dup-callout"><span class="ico">⚠</span><span>Queste mod hanno versioni o contenuti diversi. Tieni una sola versione per evitare conflitti in gioco.</span></div>` +
          conflicts.map(g => groupCard(g, 'CONFLITTO', 'badge-backup')).join('')
        : `<div class="empty-panel"><strong>Nessun conflitto di versione</strong><p>Le mod duplicate sono copie esatte: non ci sono versioni diverse della stessa mod.</p></div>`;
    } else if (state.dupTab === 'same') {
      html = same.length
        ? `<div class="dup-callout"><span class="ico">⧉</span><span>Per ogni gruppo vedi tutte le posizioni della stessa mod. Le copie in <code>15_COPIE_MOD_ATTIVE</code> sono backup volontari.</span></div>` +
          same.map(g => groupCard(g, g.some(m => m.version_conflict) ? 'VERSIONI DIVERSE' : 'STESSA MOD', g.some(m => m.version_conflict) ? 'badge-backup' : 'badge-copy')).join('')
        : `<div class="empty-panel"><strong>Nessuna mod ripetuta</strong><p>Ogni mod compare una sola volta.</p></div>`;
    } else {
      html = exact.length
        ? `<div class="dup-callout"><span class="ico">⧉</span><span>Questi file sono byte-per-byte identici. È normale trovare la mod attiva in <code>mods/</code> e la sua copia in <code>15_COPIE_MOD_ATTIVE/</code>: serve per ripristinarla se si rompe.</span></div>` +
          exact.map(g => groupCard(g, 'IDENTICO', 'badge-copy')).join('')
        : `<div class="empty-panel"><strong>Nessun file identico</strong><p>Non ci sono copie esatte nell'archivio.</p></div>`;
    }
    $('#duplicate-content').innerHTML = html;
    $$('#duplicate-tabs button').forEach(btn => btn.classList.toggle('is-active', btn.dataset.duptab === state.dupTab));
    if (state.view === 'duplicates') {
      $('#result-count').textContent = `${exact.length} gruppi · ${conflicts.length} conflitti`;
    }
  }

  // --------------------------------------------------------------- criticità

  function renderHealth() {
    const allIssues = [];
    mods.forEach(m => (m.health || []).forEach(h => allIssues.push({ mod: m, issue: h })));
    const errors = allIssues.filter(x => x.issue.level === 'error');
    const warnings = allIssues.filter(x => x.issue.level === 'warning');
    const infos = allIssues.filter(x => x.issue.level === 'info');
    const clean = mods.filter(m => !healthInfo(m).hasIssues).length;

    $('#health-summary').innerHTML = `
      <div class="health-card is-error"><div class="h-label">Errori</div><div class="h-value">${errors.length}</div><div class="h-sub">mod da sistemare subito</div></div>
      <div class="health-card is-warning"><div class="h-label">Avvisi</div><div class="h-value">${warnings.length}</div><div class="h-sub">non bloccanti</div></div>
      <div class="health-card is-info"><div class="h-label">Info</div><div class="h-value">${infos.length}</div><div class="h-sub">copie e duplicati</div></div>
      <div class="health-card is-ok"><div class="h-label">Mod pulite</div><div class="h-value">${clean}</div><div class="h-sub">su ${mods.length} file</div></div>`;

    const byCode = new Map();
    allIssues.forEach(entry => {
      if (!byCode.has(entry.issue.code)) byCode.set(entry.issue.code, []);
      byCode.get(entry.issue.code).push(entry);
    });
    const ordered = Array.from(byCode.entries()).sort((a, b) => {
      const severity = code => ISSUE_META[code]?.level === 'error' ? 0 : ISSUE_META[code]?.level === 'warning' ? 1 : 2;
      return severity(a[0]) - severity(b[0]) || b[1].length - a[1].length;
    });

    if (!ordered.length) {
      $('#health-issues').innerHTML = `<div class="empty-panel"><strong>Archivio in ordine</strong><p>Nessun problema rilevato da controlli automatici.</p></div>`;
    } else {
      $('#health-issues').innerHTML = ordered.map(([code, entries]) => {
        const info = ISSUE_META[code] || { title: code, level: 'warning', desc: '' };
        const expanded = state.expandedIssues.has(code);
        const visible = expanded ? entries : entries.slice(0, 16);
        return `<article class="issue-card ${esc(info.level)}">
          <div class="issue-head"><strong>${esc(info.title)}</strong><span class="count">${entries.length} mod</span></div>
          <div class="issue-desc">${esc(info.desc)}</div>
          <div class="issue-mods">
            ${visible.map(e => `<button class="issue-mod" data-open-mod="${esc(e.mod.id)}" title="${esc(e.mod.path)}"><span class="sev-dot"></span>${esc(e.mod.title)}</button>`).join('')}
            ${entries.length > 16 && !expanded ? `<button class="issue-mod" data-expand-issue="${esc(code)}">+ ${entries.length - 16} altre…</button>` : ''}
          </div>
        </article>`;
      }).join('');
    }

    const exact = exactGroups();
    const conflicts = conflictGroups();
    const cleanup = [];
    if (conflicts.length) {
      cleanup.push(`<strong>${conflicts.length} conflitti di versione</strong>: apri la scheda Duplicati e tieni una sola versione per mod.`);
    }
    const archiveDupes = exact.filter(g => !g.some(m => m.source === 'attiva') && !g.some(m => m.folder === '15_COPIE_MOD_ATTIVE'));
    if (archiveDupes.length) {
      cleanup.push(`<strong>${archiveDupes.length} doppioni interni all'archivio</strong>: tieni una sola copia per gruppo.`);
    }
    const activeCopies = exact.filter(g => g.some(m => m.source === 'attiva') && g.some(m => m.folder === '15_COPIE_MOD_ATTIVE'));
    if (activeCopies.length) {
      cleanup.push(`${activeCopies.length} copie di sicurezza in <code>15_COPIE_MOD_ATTIVE</code>: sono volute, non cancellarle.`);
    }
    const missingIcons = mods.filter(m => (m.health || []).some(h => h.code === 'icona_mancante')).length;
    if (missingIcons) cleanup.push(`${missingIcons} mod senza icona: esegui una scansione completa (senza <code>--no-icons</code>) per generare le anteprime.`);
    const tiny = mods.filter(m => (m.health || []).some(h => h.code === 'file_molto_piccolo'));
    if (tiny.length) cleanup.push(`${tiny.length} file molto piccoli: controlla che il download non sia incompleto.`);
    const broken = mods.filter(m => (m.health || []).some(h => h.code === 'zip_non_valido' || h.code === 'moddesc_mancante'));
    if (broken.length) cleanup.push(`${broken.length} ZIP non validi o senza modDesc: riscarica o elimina il file.`);

    $('#cleanup-box').innerHTML = `<h3>Pulizia consigliata</h3>
      <div class="sub">Controlli automatici, nessun file modificato</div>
      <div class="cleanup-list">${cleanup.length
        ? cleanup.map((text, i) => `<div class="cleanup-item"><span class="n">${i + 1}</span><span>${text}</span></div>`).join('')
        : `<div class="cleanup-empty"><strong>Nessuna azione urgente.</strong><br>L'archivio è coerente: le uniche copie sono quelle di sicurezza.</div>`}</div>
      <div class="cleanup-item" style="margin-top:12px;color:var(--muted-2);font-size:10px"><span>ℹ</span><span>La dashboard è in sola lettura: per modificare l'archivio usa il file manager.</span></div>`;
    $('#tab-count-health').textContent = errors.length + warnings.length;
    if (state.view === 'health') {
      $('#result-count').textContent = `${mods.filter(m => healthInfo(m).hasIssues).length} mod con avvisi`;
    }
  }

  // --------------------------------------------------------------- categorie

  function renderCategories() {
    const entries = Object.entries(stats.categories || {}).sort((a, b) => b[1] - a[1]);
    $('#category-grid').innerHTML = entries.map(([category, count]) => {
      const list = mods.filter(m => m.category === category);
      const active = list.filter(m => m.source === 'attiva').length;
      const backup = list.length - active;
      const size = list.reduce((sum, m) => sum + m.size, 0);
      const seen = new Set();
      const examples = list.slice()
        .sort((a, b) => tierRank(a) - tierRank(b) || a.title.localeCompare(b.title, 'it'))
        .filter(m => {
          const key = m.title.trim().toLowerCase();
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        })
        .slice(0, 4);
      return `<button class="category-card" data-cat="${esc(category)}" style="--cat:${esc(categoryColor(category))}">
        <div class="category-card-head">
          <div>
            <div class="eyebrow" style="color:${esc(categoryColor(category))};margin-bottom:2px">${esc(TYPE_GLYPH[(examples[0] || {}).type] || '•')} categoria</div>
            <h3>${esc(category)}</h3>
          </div>
          <span class="category-count">${count}</span>
        </div>
        <p>${esc(CATEGORY_DESC[category] || 'Mod classificate in questa categoria.')}</p>
        <div class="category-examples">${examples.map(m => `<span class="cat-example" title="${esc(m.title)}">${esc(m.title)}</span>`).join('')}</div>
        <div class="category-foot"><span>${active} attive · ${backup} archivio</span><span>${esc(formatSize(size))}</span></div>
      </button>`;
    }).join('');
    if (state.view === 'categories') {
      $('#result-count').textContent = `${entries.length} categorie`;
    }
  }

  // --------------------------------------------------------------- catalogo shop

  let catalogCache = null;

  function validNumber(value) {
    return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
  }

  function catalogItems() {
    if (catalogCache) return catalogCache;
    const rows = [];
    const byKey = new Map();
    const placeableCats = /decoration|buildings?|floodlighting|production|placeable|silos?|sheds?|storages?|sellingpoints?|farmhouses?|constructible|trees?|landscaping|objectmisc|animalpens?|animals?|watertanks?|pallet|bigbag|misc/i;
    const toolCats = /mowers?|cultivators?|plows?|ploughs?|trailers?|discharges?|harrows?|weeders?|sprayers?|rollers?|fertilizerspreaders?|planters?|lowloaders?|windrowers?|seeders?|subsoilers?|potatoplanting|riceplanters?|grasslandcare|slurrytanks?|frontloadertools?|balers?|wrappers?|tedders?|rakes?|cutters?|weights?|shovels?|axes?|saws?|handtools?|barrels?|grapetools?|mulchers?|stonepickers?|pruning|prepruner|transporter/i;
    const vehicleCats = /tractors?|harvesters?|trucks?|cars?|telehandlers?|forklifts?|loaders?|locomotives?|trains?/i;
    const kindOf = (m, item) => {
      const cats = (item.categories || []).join(' ');
      if (placeableCats.test(cats)) return 'piazzabile';
      if (toolCats.test(cats)) return 'attrezzo';
      if (vehicleCats.test(cats)) return 'veicolo';
      if (m.type === 'mappa') return 'piazzabile';
      if (m.type === 'pacchetto') return 'attrezzo';
      return m.type || 'altro';
    };
    uniqueMods().forEach(m => {
      (m.store_items || []).forEach((item, index) => {
        const price = validNumber(item.price) ? Number(item.price) : null;
        const power = validNumber(item.power) ? Number(item.power) : null;
        const neededPower = validNumber(item.needed_power) ? Number(item.needed_power) : null;
        const name = (item.name || '').replace(/\s+/g, ' ').trim() || (item.file || 'Oggetto senza nome');
        const shopCategory = ((item.category_labels || []).join(', ') || (item.categories || []).join(', ')).trim();
        const kind = kindOf(m, item);
        const key = [m.id, name.toLowerCase(), price ?? '', shopCategory.toLowerCase()].join('|');
        const existing = byKey.get(key);
        if (existing) {
          existing.variants += 1;
          (item.fill_types || []).forEach(t => { if (!existing.fillTypes.includes(t)) existing.fillTypes.push(t); });
          (item.functions || []).forEach(f => { if (!existing.functions.includes(f)) existing.functions.push(f); });
          return;
        }
        const row = {
          key: m.id + '::' + (item.file || index),
          mod: m,
          item,
          name,
          kind,
          brand: (item.brand || '').trim(),
          shopCategory,
          price,
          power,
          neededPower,
          powerSort: Math.max(power || 0, neededPower || 0),
          variants: 1,
          fillTypes: (item.fill_types || []).slice(),
          functions: (item.functions || []).slice()
        };
        byKey.set(key, row);
        rows.push(row);
      });
    });
    catalogCache = rows;
    return rows;
  }

  function filteredCatalog() {
    const all = catalogItems();
    const needle = state.q ? norm(state.q) : '';
    const list = all.filter(row => {
      if (state.catalogType !== 'all' && row.kind !== state.catalogType) return false;
      if (!needle) return true;
      const item = row.item;
      return norm([
        row.name, row.brand, row.shopCategory, row.mod.title, row.mod.file, row.mod.author,
        row.mod.category, row.mod.shop_category, typeLabels[row.kind] || row.kind,
        (row.mod.curated && row.mod.curated.short) || '',
        (row.mod.curated && row.mod.curated.details) || '',
        row.functions.join(' '), row.fillTypes.join(' '),
        (item.categories || []).join(' ')
      ].join(' ')).includes(needle);
    });

    const compareName = (a, b) => a.name.localeCompare(b.name, 'it', { numeric: true });
    const byPrice = (a, b, dir) => {
      if (a.price === null && b.price === null) return compareName(a, b);
      if (a.price === null) return 1;
      if (b.price === null) return -1;
      return dir * (a.price - b.price) || compareName(a, b);
    };

    switch (state.catalogSort) {
      case 'type': {
        const rank = { attrezzo: 0, veicolo: 1, piazzabile: 2, pacchetto: 3 };
        list.sort((a, b) => (rank[a.kind] ?? 4) - (rank[b.kind] ?? 4) || byPrice(a, b, -1));
        break;
      }
      case 'price-asc': list.sort((a, b) => byPrice(a, b, 1)); break;
      case 'name': list.sort(compareName); break;
      case 'power-desc':
        list.sort((a, b) => b.powerSort - a.powerSort || byPrice(a, b, -1));
        break;
      case 'votes-desc':
        list.sort((a, b) => ((b.mod.official && b.mod.official.votes) || 0) - ((a.mod.official && a.mod.official.votes) || 0) || byPrice(a, b, -1));
        break;
      case 'mod':
        list.sort((a, b) => a.mod.title.localeCompare(b.mod.title, 'it', { numeric: true }) || compareName(a, b));
        break;
      default: list.sort((a, b) => byPrice(a, b, -1));
    }
    return list;
  }

  function renderCatalog() {
    const all = catalogItems();
    const list = filteredCatalog();
    const priced = all.filter(row => row.price !== null);
    const prices = priced.map(row => row.price).sort((a, b) => a - b);
    const median = prices.length
      ? (prices.length % 2
        ? prices[(prices.length - 1) / 2]
        : (prices[prices.length / 2 - 1] + prices[prices.length / 2]) / 2)
      : null;
    const modsInCatalog = uniqueMods().filter(m => (m.store_items || []).length);
    const modsWithOfficial = modsInCatalog.filter(m => m.official);

    $('#catalog-stats').innerHTML = `
      <div class="mini-stat"><span>Oggetti in catalogo</span><strong>${formatNumber(all.length)}</strong><small>da ${formatNumber(modsInCatalog.length)} mod</small></div>
      <div class="mini-stat"><span>Con prezzo</span><strong>${formatNumber(priced.length)}</strong><small>${formatNumber(all.length - priced.length)} senza prezzo dichiarato</small></div>
      <div class="mini-stat"><span>Prezzo mediano</span><strong>${median === null ? '—' : esc(formatPrice(Math.round(median)))}</strong><small>${prices.length ? 'da ' + esc(formatPrice(Math.min(...prices))) + ' a ' + esc(formatPrice(Math.max(...prices))) : 'nessun prezzo'}</small></div>
      <div class="mini-stat"><span>Schede ModHub</span><strong>${formatNumber(modsWithOfficial.length)} / ${formatNumber(modsInCatalog.length)}</strong><small>voti ufficiali disponibili</small></div>`;

    $('#catalog-rows').innerHTML = list.map(row => {
      const item = row.item;
      const extra = [
        item.capacity !== null && item.capacity !== undefined ? 'capacità ' + itemNumber(item.capacity, 'L') : '',
        item.weight !== null && item.weight !== undefined ? itemNumber(item.weight, 'kg') : '',
        row.fillTypes.length ? 'riempimento: ' + row.fillTypes.join(', ') : ''
      ].filter(Boolean).join(' · ');
      const o = row.mod.official;
      const mh = o
        ? `<span class="cat-mh">★ ${esc(Number(o.rating).toFixed(1))}</span><span class="cat-votes">${esc(formatNumber(o.votes))} voti</span>`
        : '<span class="cat-none">—</span>';
      return `<tr data-open-mod="${esc(row.mod.id)}" tabindex="0" title="${esc(row.mod.path)}">
        <td class="col-item">
          <div class="cat-item-head"><strong>${esc(row.name)}</strong>${row.brand ? `<span class="cat-brand">${esc(row.brand)}</span>` : ''}${row.variants > 1 ? `<span class="cat-variant">×${row.variants}</span>` : ''}</div>
          ${extra ? `<div class="cat-item-extra">${esc(extra)}</div>` : ''}
        </td>
        <td class="col-mod-name"><span class="cat-mod">${esc(row.mod.title)}</span></td>
        <td class="col-shop-cat">
          <span class="cat-type">${esc(typeLabels[row.kind] || row.kind)}</span>
          <span class="cat-pill">${esc(row.shopCategory || '—')}</span>
        </td>
        <td class="col-price"><strong>${row.price === null ? '—' : esc(formatPrice(row.price))}</strong></td>
        <td class="col-power">${esc(itemPowerLabel(item))}</td>
        <td class="col-width">${esc(itemNumber(item.working_width, 'm'))}</td>
        <td class="col-speed">${esc(itemNumber(item.maxSpeed, 'km/h'))}</td>
        <td class="col-upkeep">${item.daily_upkeep !== null && item.daily_upkeep !== undefined ? esc(formatPrice(item.daily_upkeep)) : '—'}</td>
        <td class="col-mh">${mh}</td>
      </tr>`;
    }).join('');

    $('#empty-catalog').hidden = list.length > 0;
    $('#view-catalog .catalog-table').style.display = list.length ? '' : 'none';
    $$('[data-catalog-type]').forEach(btn => btn.classList.toggle('is-active', btn.dataset.catalogType === state.catalogType));
    $('#tab-count-catalog').textContent = formatNumber(all.length);
    if (state.view === 'catalog') {
      $('#result-count').textContent = `${formatNumber(list.length)} di ${formatNumber(all.length)} oggetti`;
    }
  }

  // --------------------------------------------------------------- viste

  function setView(view, updateHash = true) {
    state.view = view;
    $$('.viewtab').forEach(tab => tab.classList.toggle('is-active', tab.dataset.view === view));
    $$('.view').forEach(section => section.classList.toggle('is-active', section.id === 'view-' + view));
    document.body.classList.remove('view-mode-inventory', 'view-mode-duplicates', 'view-mode-health', 'view-mode-categories', 'view-mode-catalog', 'view-mode-profiles', 'view-mode-recommended');
    document.body.classList.add('view-mode-' + view);
    if (view === 'inventory') renderInventory();
    if (view === 'duplicates') renderDuplicates();
    if (view === 'health') renderHealth();
    if (view === 'categories') renderCategories();
    if (view === 'catalog') renderCatalog();
    if (view === 'profiles') renderProfiles();
    if (view === 'recommended') renderRecommended();
    if (updateHash) setHash('#view=' + view);
  }

  // --------------------------------------------------------------- profili & mappe attive

  const DEFAULT_ITALIAN_MODS = [
    "FS25_Mediterranean_Italy.zip",
    "FS25_Fiat_480.zip",
    "FS25_Fiatagri_110_90.zip",
    "FS25_Fiatagri_160180_90.zip",
    "FS25_fiatagriSeriesPack.zip",
    "FS25_fiatSeries180_90JT.zip",
    "FS25_lamborghiniMachVRT.zip",
    "FS25_DucatoFiat19tdi.zip",
    "FS25_DucatoFiatPickupTruck.zip",
    "FS25_Fiat682_N4.zip",
    "FS25_Fiat190_48_TurboStar.zip",
    "FS25_Alpego_JetM.zip",
    "FS25_Dondi800Series.zip",
    "FS25_DoubleWeightFiat.zip",
    "FS25_Trincia_Fiat_Hesston.zip",
    "FS25_two_wheel_trailer.zip",
    "FS25_Flatbed_Trailer.zip",
    "FS25_UniaGrudziadzUPlows.zip",
    "FS25_UsedEquipmentYards.zip",
    "FS25_orchardsAndGreenhouses_crossplay.zip",
    "FS25_smallFarmProduction.zip",
    "FS25_Raisinproductionpack.zip",
    "FS25_FloorWeightStation.zip",
    "FS25_additionalFieldInfo.zip",
    "FS25_interactiveControl.zip",
    "FS25_RealisticFirstPerson.zip",
    "FS25_GPSPlus.zip",
    "FS25_AutoDrive.zip",
    "FS25_Courseplay.zip",
    "FS25_AnimalFoodCalculator.zip",
    "FS25_AutomaticWater_Animals_Greenhouses.zip"
  ];

  const profileState = {
    activeSet: new Set(DEFAULT_ITALIAN_MODS),
    q: '',
    isServerActive: false
  };

  async function syncProfileStatus() {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        profileState.isServerActive = true;
        if (Array.isArray(data.active_mods) && data.active_mods.length > 0) {
          profileState.activeSet = new Set(data.active_mods);
        }
        updateProfileUI();
        if (state.view === 'profiles') renderProfiles();
        markBusySlots();
        loadMaps();
        loadSavedLinks();
        loadPartite();
        loadBackupState();
      }
    } catch (e) {
      profileState.isServerActive = false;
      updateProfileUI();
    }
  }

  // Segna gli slot già usati, così nessuno sovrascrive per sbaglio una partita vera.
  async function markBusySlots() {
    const sel = $('#game-slot');
    if (!sel) return;
    let firstFree = null;
    for (const opt of Array.from(sel.options)) {
      try {
        const res = await fetch(`/api/slot?n=${encodeURIComponent(opt.value)}`);
        if (!res.ok) continue;
        const data = await res.json();
        const busy = (data.occupato_in || []).length > 0;
        opt.textContent = `Slot ${opt.value}${busy ? ' (già usato: chiede conferma)' : ' (libero)'}`;
        if (!busy && firstFree === null) firstFree = opt.value;
      } catch (e) { /* server spento: lascio com'è */ }
    }
    if (firstFree !== null) sel.value = firstFree;
  }

  // Mappe trovate nell'archivio (lette dal server dai modDesc.xml).
  async function loadMaps() {
    const sel = $('#game-map');
    if (!sel) return;
    try {
      const res = await fetch('/api/maps');
      if (!res.ok) return;
      const data = await res.json();
      const mappe = data.mappe || [];
      if (!mappe.length) return;
      const prima = sel.value || data.predefinita;
      sel.innerHTML = mappe.map(m => `<option value="${esc(m.file)}">${esc(m.titolo)} (${esc(m.file)})</option>`).join('');
      sel.value = mappe.some(m => m.file === prima) ? prima : mappe[0].file;
    } catch (e) { /* server spento */ }
  }

  // Elenchi dei link tolti dalla cartella del gioco (data/link_salvati/).
  async function loadSavedLinks() {
    const sel = $('#link-salvati');
    const btn = $('#btn-rimetti-link');
    if (!sel) return;
    try {
      const res = await fetch('/api/link_salvati');
      if (!res.ok) return;
      const data = await res.json();
      const elenchi = data.elenchi || [];
      if (!elenchi.length) {
        sel.innerHTML = '<option value="">Nessun elenco salvato</option>';
        if (btn) btn.disabled = true;
        return;
      }
      sel.innerHTML = elenchi.map(e => {
        const m = /^link_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/.exec(e.file);
        const quando = m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}:${m[6]}` : e.file;
        return `<option value="${esc(e.file)}">${esc(quando)}: ${e.quanti} link</option>`;
      }).join('');
      if (btn) btn.disabled = false;
    } catch (e) { /* server spento */ }
  }

  async function restoreSavedLinks() {
    const sel = $('#link-salvati');
    const file = sel?.value;
    if (!file) return;
    const label = sel.options[sel.selectedIndex]?.textContent || file;
    if (!window.confirm(
      `Rimetto nella cartella del gioco i link salvati il ${label}.\n\n` +
      `• Tolgo solo i link di adesso (il loro elenco viene salvato, così puoi tornare indietro).\n` +
      `• I file veri non vengono toccati.\n• Fallo a gioco chiuso.\n\nProcedo?`)) return;
    try {
      const res = await fetch('/api/rimetti_link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        const saltati = data.saltati || [];
        showToast(`↩ ${data.rimessi.length} link rimessi` + (saltati.length ? `, ${saltati.length} saltati` : ''));
        if (saltati.length) {
          alert(`Link non rimessi (${saltati.length}):\n\n` +
                saltati.slice(0, 15).map(x => `${x.nome}: ${x.motivo}`).join('\n') +
                (saltati.length > 15 ? `\n… e altri ${saltati.length - 15}` : ''));
        }
        syncProfileStatus();
      } else {
        showToast(`Errore: ${data.error || 'link non rimessi'}`);
      }
    } catch (e) {
      showToast('Server locale non raggiungibile. Avvia ./apri.sh');
    }
  }

  // ------------------------------------------------ mod di una partita (set di run.sh)
  const partiteState = { partite: [], set: [] };

  async function loadPartite() {
    const selSlot = $('#partita-slot');
    const selSet = $('#partita-set');
    if (!selSlot || !selSet) return;
    try {
      const res = await fetch('/api/partite');
      if (!res.ok) return;
      const data = await res.json();
      partiteState.partite = data.partite || [];
      partiteState.set = data.set || [];
      const gameSet = $('#game-set');
      if (gameSet) gameSet.innerHTML = partiteState.set.map(v =>
        `<option value="${esc(v.cartella)}">${esc(v.cartella)} (${esc(v.comando)})</option>`).join('');
      selSlot.innerHTML = partiteState.partite.map(p =>
        `<option value="${esc(p.slot)}">${esc(p.slot)} · ${esc(p.nome)} · ${esc(p.mappa)} · ${p.quante_mod} mod</option>`).join('');
      selSet.innerHTML = partiteState.set.map(v =>
        `<option value="${esc(v.cartella)}">${esc(v.cartella)} (${esc(v.comando)})${v.esiste ? '' : ' - cartella mancante'}</option>`).join('');
      const scegliSet = () => {
        const p = partiteState.partite.find(x => x.slot === selSlot.value);
        if (p) selSet.value = p.set || p.set_suggerito || selSet.value;
      };
      selSlot.onchange = () => { scegliSet(); $('#partita-esito').innerHTML = ''; };
      scegliSet();
      if (data.gioco_aperto) {
        $('#partita-esito').innerHTML = '<strong style="color:#f39c12;">Il gioco è aperto: puoi controllare, ma per cambiare le mod chiudilo.</strong>';
      }
    } catch (e) { /* server spento */ }
  }

  function renderPiano(pl) {
    const box = $('#partita-esito');
    if (!box) return;
    const riga = (t, n, colore) => `<li><strong style="color:${colore};">${n}</strong> ${t}</li>`;
    let html = `<p style="margin:0 0 6px 0;"><strong>${esc(pl.salvataggio.nome)}</strong> (${esc(pl.slot)}, ${esc(pl.salvataggio.mappa)}) con il set <code>${esc(pl.set)}</code>:</p><ul style="margin:0 0 8px 18px; padding:0;">`;
    html += riga('mod già pronte', pl.ok.length, '#2ecc71');
    html += riga('da collegare dall\'archivio', pl.da_collegare.length, '#3498db');
    html += riga('mancanti (da riscaricare)', pl.mancanti.length, pl.mancanti.length ? '#e74c3c' : '#2ecc71');
    html += riga('link in più nel set (restano, a meno che spunti la casella)', pl.link_in_piu.length, '#aaa');
    html += riga('file veri in più nel set (restano sempre)', pl.file_veri_in_piu.length, '#aaa');
    if (pl.link_rotti.length) html += riga('link rotti di mod non usate (verranno tolti)', pl.link_rotti.length, '#f39c12');
    html += '</ul>';
    if (pl.mancanti.length) {
      html += '<p style="margin:6px 0;">Mod mancanti: senza queste, aprire il salvataggio farebbe sparire i loro oggetti.</p><ul style="margin:0 0 8px 18px; padding:0;">';
      html += pl.mancanti.map(m => {
        const pagina = m.pagina ? `<a href="${esc(m.pagina)}" target="_blank" rel="noopener">pagina ModHub</a>` : `<a href="${esc(m.cerca)}" target="_blank" rel="noopener">cerca su ModHub</a>`;
        const scarica = m.mod_id ? ` · <button class="chip btn-scarica-mod" type="button" data-nome="${esc(m.nome)}" data-id="${esc(m.mod_id)}" style="cursor:pointer;">⬇ Scarica nell'archivio</button>` : '';
        return `<li><code>${esc(m.nome)}</code> ${esc(m.titolo !== m.nome ? m.titolo : '')} ${m.versione ? 'v' + esc(m.versione) : ''} · ${pagina}${scarica}</li>`;
      }).join('');
      html += '</ul>';
    }
    html += `<label style="display:flex; gap:6px; align-items:center; margin:6px 0;"><input type="checkbox" id="chk-togli-altre" style="accent-color:#2ecc71;"> Togli anche i link delle mod che questo salvataggio non usa (le mod restano nell'archivio)</label>`;
    html += `<button class="btn-launch-primary" id="btn-partita-attiva" type="button">✅ Attiva le mod di questa partita</button>`;
    box.innerHTML = html;
    $('#btn-partita-attiva')?.addEventListener('click', () => attivaPartita(pl));
    $$('.btn-scarica-mod', box).forEach(b => b.addEventListener('click', () => scaricaMod(b)));
  }

  async function controllaPartita() {
    const slot = $('#partita-slot')?.value;
    const set = $('#partita-set')?.value;
    if (!slot || !set) return;
    try {
      const res = await fetch(`/api/piano?slot=${encodeURIComponent(slot)}&set=${encodeURIComponent(set)}`);
      const data = await res.json();
      if (res.ok) renderPiano(data); else showToast(`Errore: ${data.error || 'controllo non riuscito'}`);
    } catch (e) { showToast('Server locale non raggiungibile. Avvia ./apri.sh'); }
  }

  async function attivaPartita(pl) {
    const togli = $('#chk-togli-altre')?.checked || false;
    if (!window.confirm(
      `Set ${pl.set} per ${pl.salvataggio.nome}:\n\n` +
      `• collego ${pl.da_collegare.length} mod dall'archivio\n` +
      (togli ? `• tolgo ${pl.link_in_piu.length} link di mod non usate (restano nell'archivio)\n` : '') +
      (pl.link_rotti.length ? `• tolgo ${pl.link_rotti.length} link rotti di mod non usate\n` : '') +
      `• i file veri non vengono toccati; l'elenco dei link di adesso viene salvato\n` +
      (pl.mancanti.length ? `\nATTENZIONE: mancano ancora ${pl.mancanti.length} mod. Non aprire il salvataggio finché non ci sono.\n` : '') +
      `\nProcedo?`)) return;
    try {
      const res = await fetch('/api/applica_partita', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot: pl.slot, set: pl.set, togli_altre: togli, conferma: true })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`✔ ${data.collegati.length} mod collegate, ${data.tolti.length} link tolti`);
        loadSavedLinks();
        controllaPartita();
      } else showToast(`Errore: ${data.error || 'non riuscito'}`);
    } catch (e) { showToast('Server locale non raggiungibile. Avvia ./apri.sh'); }
  }

  async function salvaAbbinamento() {
    const slot = $('#partita-slot')?.value;
    const set = $('#partita-set')?.value;
    if (!slot || !set) return;
    try {
      const res = await fetch('/api/profilo', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot, set })
      });
      const data = await res.json();
      if (res.ok) { showToast(`Ricordato: ${slot} si gioca con ${set}`); loadPartite(); }
      else showToast(`Errore: ${data.error || 'non salvato'}`);
    } catch (e) { showToast('Server locale non raggiungibile. Avvia ./apri.sh'); }
  }

  async function scaricaMod(btn) {
    const nome = btn.dataset.nome;
    if (!window.confirm(`Scarico ${nome}.zip dalla pagina ModHub ufficiale (id ${btn.dataset.id}) nell'archivio delle mod?\nNon sovrascrive niente.`)) return;
    btn.disabled = true;
    btn.textContent = '⏳ Scarico…';
    try {
      const res = await fetch('/api/scarica_mod', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome, mod_id: btn.dataset.id })
      });
      const data = await res.json();
      if (res.ok && data.success) { showToast(`✔ ${nome} scaricata (${formatSize(data.byte)})`); controllaPartita(); }
      else { showToast(`Errore: ${data.error || 'download non riuscito'}`); btn.disabled = false; btn.textContent = '⬇ Riprova'; }
    } catch (e) { showToast('Server locale non raggiungibile.'); btn.disabled = false; }
  }

  async function loadBackupState() {
    const st = $('#backup-stato');
    const btn = $('#btn-backup');
    if (!st) return;
    try {
      const res = await fetch('/api/backup');
      if (!res.ok) return;
      const d = await res.json();
      if (!d.montato) {
        st.innerHTML = `<span style="color:#f39c12;">⚠ Disco di backup non collegato o non configurato (FS25_BACKUP_DIR): nessuna copia di sicurezza possibile adesso.</span>`;
        if (btn) btn.disabled = true;
      } else {
        const u = d.ultima ? `ultima copia ${esc(d.ultima.quando)} (${d.ultima.copiati} file)` : 'nessuna copia fatta finora';
        st.textContent = d.in_corso ? 'Copia di sicurezza in corso…' : `Copia di sicurezza su ${d.destinazione}: ${u}`;
        if (btn) btn.disabled = d.in_corso;
      }
    } catch (e) { /* server spento */ }
  }

  async function avviaBackup() {
    if (!window.confirm('Copio tutte le mod (archivio, BACKUP_MODS e file veri dei set) sul disco di backup.\nNon cancella niente. Può durare a lungo la prima volta. Procedo?')) return;
    try {
      const res = await fetch('/api/backup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      const data = await res.json();
      if (res.ok) { showToast('Copia di sicurezza avviata'); loadBackupState(); }
      else showToast(`Errore: ${data.error || 'copia non avviata'}`);
    } catch (e) { showToast('Server locale non raggiungibile.'); }
  }

  function updateProfileUI() {
    const count = profileState.activeSet.size;
    const counter = $('#profile-active-counter');
    if (counter) counter.textContent = count;
    const tabCount = $('#tab-count-profiles');
    if (tabCount) tabCount.textContent = count;
    const invCounter = $('#inv-active-count');
    if (invCounter) invCounter.textContent = count;
    const topCounter = $('#top-active-count');
    if (topCounter) topCounter.textContent = count;
    const status = $('#profile-sync-status');
    if (status) {
      if (profileState.isServerActive) {
        status.innerHTML = `<span style="color:#2ecc71; font-weight:700;">🟢 Server Attivo (${count} mod attivate)</span>`;
      } else {
        status.innerHTML = `<span style="color:#f39c12; font-weight:600;">🟡 Standalone (Avvia ./apri.sh per sincronizzare)</span>`;
      }
    }
  }

  function renderProfiles() {
    updateProfileUI();
    const tbody = $('#profile-rows');
    if (!tbody) return;

    const q = norm(profileState.q || '');
    // Group all mods: first the ones in activeSet, then the rest
    const allMods = mods.slice().sort((a, b) => {
      const aIn = profileState.activeSet.has(a.file) ? 1 : 0;
      const bIn = profileState.activeSet.has(b.file) ? 1 : 0;
      if (aIn !== bIn) return bIn - aIn;
      return a.file.localeCompare(b.file);
    });

    const filtered = allMods.filter(m => {
      if (!q) return true;
      return norm(m.title).includes(q) || norm(m.file).includes(q) || norm(m.category).includes(q);
    });

    tbody.innerHTML = filtered.map(m => {
      const isChecked = profileState.activeSet.has(m.file);
      return `<tr class="${isChecked ? 'is-selected' : ''}" style="${isChecked ? 'background:rgba(46,204,113,0.06);' : ''}">
        <td style="text-align:center; padding:12px;">
          <input type="checkbox" class="profile-toggle" data-file="${esc(m.file)}" ${isChecked ? 'checked' : ''} style="width:20px; height:20px; cursor:pointer; accent-color:#2ecc71;">
        </td>
        <td class="col-mod">
          <div class="mod-cell">
            ${iconMarkup(m, 'mod-icon')}
            <div class="mod-meta">
              <div class="mod-title"><strong>${esc(m.title)}</strong></div>
              <div class="mod-file">${esc(m.file)}</div>
            </div>
          </div>
        </td>
        <td class="col-what"><div class="what-text">${esc(shortText(m))}</div></td>
        <td class="col-cat">
          <span class="cat-chip"><span class="cat-dot" style="--dot:${esc(categoryColor(m.category))}"></span>${esc(m.category)}</span>
        </td>
        <td class="col-type"><span class="badge badge-type">${esc(typeLabel(m))}</span></td>
        <td class="col-size"><span class="cell-size">${esc(formatSize(m.size))}</span></td>
        <td class="col-source"><span class="cell-mono" style="font-size:12px; color:#888;">${esc(m.file)}</span></td>
      </tr>`;
    }).join('');

    // Bind checkboxes
    $$('.profile-toggle', tbody).forEach(chk => {
      chk.addEventListener('change', () => {
        const file = chk.dataset.file;
        if (chk.checked) {
          profileState.activeSet.add(file);
        } else {
          profileState.activeSet.delete(file);
        }
        updateProfileUI();
        chk.closest('tr').classList.toggle('is-selected', chk.checked);
        chk.closest('tr').style.background = chk.checked ? 'rgba(46,204,113,0.06)' : '';
      });
    });
  }

  async function applyProfileToGame() {
    const list = Array.from(profileState.activeSet);
    const btn = $('#btn-apply-mods');
    if (!window.confirm(
      `Attivo ${list.length} mod nella cartella del gioco.\n\n` +
      `• Tolgo solo i link delle mod attive adesso (l'elenco viene salvato in data/link_salvati/).\n` +
      `• I file veri nella cartella del gioco non vengono toccati.\n` +
      `• Fallo a gioco chiuso.\n\nProcedo?`)) {
      return;
    }
    if (btn) btn.disabled = true;

    try {
      let res = await fetch('/api/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mods: list })
      });
      let data = await res.json();
      if (res.status === 409 && data.mod_del_salvataggio_tolte) {
        const t = data.mod_del_salvataggio_tolte;
        if (!window.confirm(`Attenzione: ${t.length} mod usate da un salvataggio di questo set verrebbero tolte:\n\n` +
            t.slice(0, 15).join('\n') + (t.length > 15 ? `\n… e altre ${t.length - 15}` : '') +
            `\n\nSe apri quel salvataggio senza queste mod, i loro oggetti spariscono.\nVuoi toglierle lo stesso?`)) {
          showToast('Annullato: niente cambiato');
          return;
        }
        res = await fetch('/api/activate', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mods: list, forza: true })
        });
        data = await res.json();
      }
      if (res.ok && data.success) {
        let msg = `✔ ${data.enabled_count} mod attivate nel gioco`;
        if (data.missing_count) msg += `, ${data.missing_count} non trovate`;
        showToast(msg);
        const veri = data.file_veri_lasciati || [];
        if (veri.length) {
          alert(`Attenzione: nella cartella del gioco ci sono ${veri.length} file veri che non hai scelto.\n` +
                `Non li cancello: restano attivi nel gioco.\n\n` + veri.slice(0, 15).join('\n') +
                (veri.length > 15 ? `\n… e altri ${veri.length - 15}` : ''));
        }
        updateProfileUI();
        loadSavedLinks();
      } else {
        showToast(`Errore: ${data.error || 'sincronizzazione non riuscita'}`);
      }
    } catch (e) {
      showToast('Server locale non raggiungibile. Avvia ./apri.sh');
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  // --------------------------------------------------------------- mod consigliate (kingmods & modhub)

  let recommendedLoaded = false;
  async function renderRecommended() {
    const container = $('#rec-categories-container');
    if (!container) return;

    if (!recommendedLoaded) {
      container.innerHTML = '<div style="padding:20px; color:#888;">Caricamento categorie consigliate...</div>';
      try {
        const res = await fetch('/api/recommended');
        if (res.ok) {
          const data = await res.json();
          recommendedLoaded = true;
          displayRecommendedCategories(data.categories || {});
        }
      } catch (e) {
        container.innerHTML = '<div style="padding:20px; color:#f39c12;">Server locale non raggiungibile per il database KingMods.</div>';
      }
    }
  }

  function displayRecommendedCategories(categories) {
    const container = $('#rec-categories-container');
    if (!container) return;

    container.innerHTML = Object.values(categories).map(cat => {
      const itemsHtml = (cat.items || []).map(item => `
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); padding:10px 12px; border-radius:8px; margin-top:8px; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:700; color:#fff; font-size:13px;">${esc(item.name)}</div>
            <div style="font-size:11px; color:#aaa;">${esc(item.category)} · ⭐ ${esc(item.rating)} · ⬇️ ${esc(formatNumber(item.downloads))}</div>
          </div>
          <a href="${esc(item.url)}" target="_blank" rel="noopener" class="btn btn-ghost" style="font-size:11px; padding:4px 8px; border-radius:4px; border:1px solid rgba(255,255,255,0.15); color:#e67e22; text-decoration:none;">Apri Scheda ↗</a>
        </div>
      `).join('');

      return `
        <div style="background:linear-gradient(135deg, rgba(230,126,34,0.06), rgba(22,29,24,0.6)); border:1px solid rgba(230,126,34,0.25); border-radius:10px; padding:16px;">
          <h3 style="color:#e67e22; font-size:15px; margin:0 0 10px 0; font-weight:700;">${esc(cat.title)}</h3>
          <div>${itemsHtml || '<div style="color:#666; font-size:12px;">Nessuna mod trovata</div>'}</div>
        </div>
      `;
    }).join('');
  }

  let extSearchTimer = null;
  async function searchExternalMods(q) {
    const wrap = $('#ext-search-results-wrap');
    const resultsContainer = $('#ext-search-results');
    const countSpan = $('#ext-count');
    if (!wrap || !resultsContainer) return;

    if (!q) {
      wrap.hidden = true;
      return;
    }

    wrap.hidden = false;
    resultsContainer.innerHTML = '<div style="color:#888;">Ricerca in corso tra 22.645 mod...</div>';

    try {
      const res = await fetch(`/api/search_external?q=${encodeURIComponent(q)}`);
      if (res.ok) {
        const data = await res.json();
        const list = data.results || [];
        countSpan.textContent = `${list.length} trovate`;

        if (list.length === 0) {
          resultsContainer.innerHTML = '<div style="color:#888;">Nessuna mod trovata per questa ricerca.</div>';
          return;
        }

        resultsContainer.innerHTML = list.map(item => `
          <div style="background:#161d18; border:1px solid #2a3a2e; border-radius:8px; padding:12px 14px; display:flex; flex-direction:column; justify-content:space-between;">
            <div>
              <div style="font-weight:700; color:#fff; font-size:14px;">${esc(item.name)}</div>
              <div style="font-size:12px; color:#2ecc71; margin-top:2px;">⭐ ${esc(item.rating)} · ⬇️ ${esc(formatNumber(item.downloads))} download</div>
              <div style="font-size:11px; color:#888; margin-top:1px;">${esc(item.category)} ${item.author ? `· Autore: ${esc(item.author)}` : ''}</div>
              <p style="font-size:12px; color:#aaa; margin:6px 0 0 0; line-height:1.4;">${esc(item.description)}</p>
            </div>
            <div style="margin-top:10px; display:flex; justify-content:flex-end;">
              <a href="${esc(item.url)}" target="_blank" rel="noopener" class="btn" style="background:#e67e22; color:#fff; font-size:12px; padding:6px 12px; border-radius:6px; text-decoration:none; font-weight:700;">
                📥 Scheda / Download ↗
              </a>
            </div>
          </div>
        `).join('');
      }
    } catch (e) {
      resultsContainer.innerHTML = '<div style="color:#f39c12;">Errore durante la ricerca.</div>';
    }
  }

  // --------------------------------------------------------------- CSV

  function downloadCsv(header, rows, filename) {
    const escapeCell = value => {
      let s = String(value ?? '');
      if (/^[=+\-@\t\r\n]/.test(s)) s = "'" + s;  // niente formule eseguite da Excel/LibreOffice
      return '"' + s.replace(/"/g, '""') + '"';
    };
    const csv = '\uFEFF' + [header, ...rows].map(row => row.map(escapeCell).join(';')).join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function exportCsv() {
    const list = filteredMods();
    const header = ['Stato', 'Categoria', 'Tipo', 'Titolo', 'File', 'Versione', 'Autore', 'Prezzo min', 'Prezzo max', 'Oggetti shop', 'Rating ModHub', 'Voti ModHub', 'URL ModHub', 'Dimensione', 'Aggiornata', 'Percorso', 'Cosa fa', 'Tier', 'Criticità'];
    const rows = list.map(m => {
      const prices = priceValues(m);
      const price = prices.length ? Math.min(...prices) : '';
      const priceMax = prices.length ? Math.max(...prices) : '';
      const o = m.official || {};
      const issues = (m.health || []).filter(h => h.level !== 'info').map(h => h.msg).join(' | ');
      return [
        sourceInfo(m).label, m.category, typeLabel(m), m.title, m.file, m.version,
        m.author, price, priceMax, (m.store_items || []).length,
        o.rating ?? '', o.votes ?? '', o.url ?? '',
        m.size, new Date(m.mtime * 1000).toISOString().slice(0, 10),
        m.path, shortText(m), (m.curated && m.curated.tier) || '', issues
      ];
    });
    downloadCsv(header, rows, `FS25_mods_${new Date().toISOString().slice(0, 10)}.csv`);
    showToast(`Esportate ${list.length} mod in CSV`);
  }

  function exportCatalogCsv() {
    const list = filteredCatalog();
    const header = ['Mod', 'File mod', 'Tipo', 'Oggetto', 'Marca', 'Categoria shop', 'Categoria mod', 'Prezzo', 'Potenza CV', 'Potenza richiesta CV', 'Larghezza m', 'Velocità km/h', 'Upkeep', 'Capacità L', 'Peso kg', 'Fill types', 'Varianti', 'Rating ModHub', 'Voti ModHub', 'URL ModHub'];
    const rows = list.map(row => {
      const item = row.item;
      const o = row.mod.official || {};
      return [
        row.mod.title, row.mod.file, typeLabels[row.kind] || row.kind, row.name, row.brand, row.shopCategory,
        row.mod.category, row.price ?? '', row.power ?? '', row.neededPower ?? '',
        item.working_width ?? '', item.maxSpeed ?? '', item.daily_upkeep ?? '',
        item.capacity ?? '', item.weight ?? '', row.fillTypes.join(', '), row.variants,
        o.rating ?? '', o.votes ?? '', o.url ?? ''
      ];
    });
    downloadCsv(header, rows, `FS25_catalogo_${new Date().toISOString().slice(0, 10)}.csv`);
    showToast(`Esportati ${list.length} oggetti in CSV`);
  }

  // --------------------------------------------------------------- toast/copy

  let toastTimer = null;
  function showToast(message) {
    const toast = $('#toast');
    toast.textContent = message;
    toast.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 2600);
  }

  function copyText(text) {
    const done = () => showToast('Percorso copiato negli appunti');
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
    } else {
      fallbackCopy(text, done);
    }
  }

  function fallbackCopy(text, done) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try { document.execCommand('copy'); done(); } catch { showToast('Copia non disponibile: seleziona il percorso a mano'); }
    textarea.remove();
  }

  // --------------------------------------------------------------- eventi

  function bind() {
    // tabs
    $$('.viewtab').forEach(tab => tab.addEventListener('click', () => {
      if ($('#drawer').classList.contains('is-open')) closeMod();
      setView(tab.dataset.view);
    }));

    // ricerca
    const search = $('#search');
    search.addEventListener('input', () => {
      state.q = search.value.trim();
      if (state.view === 'catalog') renderCatalog();
      else if (state.view !== 'inventory') setView('inventory');
      else renderInventory();
    });

    document.addEventListener('keydown', event => {
      const target = event.target;
      const typing = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT');
      if (event.key === '/' && !typing) {
        event.preventDefault();
        search.focus();
      }
      if (event.key === 'Escape') {
        if ($('#drawer').classList.contains('is-open')) closeMod();
        else if (document.activeElement === search && search.value) {
          search.value = '';
          state.q = '';
          if (state.view === 'catalog') renderCatalog();
          else renderInventory();
        }
      }
      if (event.key === 'Enter' && target && (target.matches('tr[data-id]') || target.matches('tr[data-open-mod]'))) {
        openMod(target.dataset.id || target.dataset.openMod);
      }
    });

    // chip rapidi
    $$('[data-quick]').forEach(chip => chip.addEventListener('click', () => {
      state.source = chip.dataset.quick;
      renderFilters();
      renderInventory();
    }));

    // sidebar
    $('#filter-source').addEventListener('click', event => {
      const btn = event.target.closest('[data-source]');
      if (!btn) return;
      state.source = btn.dataset.source;
      renderFilters(); renderInventory();
    });
    $('#filter-type').addEventListener('click', event => {
      const btn = event.target.closest('[data-type]');
      if (!btn) return;
      state.type = btn.dataset.type;
      renderFilters(); renderInventory();
    });
    $('#filter-category').addEventListener('click', event => {
      const btn = event.target.closest('[data-category]');
      if (!btn) return;
      state.category = btn.dataset.category;
      renderFilters(); renderInventory();
    });

    // ordinamento/densità
    $('#sort').addEventListener('change', event => {
      state.sort = event.target.value;
      renderInventory();
    });
    $$('[data-density]').forEach(btn => btn.addEventListener('click', () => {
      state.density = btn.dataset.density;
      $$('[data-density]').forEach(b => b.classList.toggle('is-active', b === btn));
      document.body.classList.toggle('density-compact', state.density === 'compact');
    }));

    // catalogo shop
    $$('[data-catalog-type]').forEach(btn => btn.addEventListener('click', () => {
      state.catalogType = btn.dataset.catalogType;
      renderCatalog();
    }));
    $('#catalog-sort').addEventListener('change', event => {
      state.catalogSort = event.target.value;
      renderCatalog();
    });

    // reset
    $('#btn-reset-filters').addEventListener('click', () => {
      state.q = ''; state.source = 'all'; state.category = 'all'; state.type = 'all'; state.sort = 'relevance';
      $('#search').value = ''; $('#sort').value = 'relevance';
      renderFilters(); renderInventory();
    });

    // statistiche cliccabili
    $('#stats').addEventListener('click', event => {
      const card = event.target.closest('[data-stat]');
      if (!card) return;
      const stat = card.dataset.stat;
      if (stat === 'duplicates') setView('duplicates');
      else if (stat === 'health') setView('health');
      else if (stat === 'active') { state.source = 'active'; setView('inventory'); renderFilters(); renderInventory(); }
      else if (stat === 'backup') { state.source = 'backup'; setView('inventory'); renderFilters(); renderInventory(); }
      else { state.source = 'all'; setView('inventory'); renderFilters(); renderInventory(); }
    });

    // esporta
    $('#btn-export').addEventListener('click', exportCsv);
    $('#btn-export-catalog').addEventListener('click', exportCatalogCsv);

    // drawer
    $('#drawer-close').addEventListener('click', closeMod);
    $('#drawer-backdrop').addEventListener('click', closeMod);
    document.addEventListener('click', event => {
      const expand = event.target.closest('[data-expand-issue]');
      if (expand) {
        state.expandedIssues.add(expand.dataset.expandIssue);
        renderHealth();
        return;
      }
      const cat = event.target.closest('[data-cat]');
      if (cat) {
        state.category = cat.dataset.cat;
        state.source = 'all'; state.type = 'all';
        setView('inventory'); renderFilters(); renderInventory();
        window.scrollTo({ top: 0, behavior: 'smooth' });
        return;
      }
      const goto = event.target.closest('[data-goto]');
      if (goto) {
        openMod(goto.dataset.goto);
        return;
      }
      const open = event.target.closest('[data-open-mod]');
      if (open) {
        openMod(open.dataset.openMod);
        return;
      }
      const row = event.target.closest('#mod-rows tr[data-id]');
      if (row) openMod(row.dataset.id);
    });

    // drawer: toggle descrizione, copia percorso, navigazione interna
    $('#drawer-body').addEventListener('click', event => {
      if (event.target.id === 'desc-toggle') {
        const box = $('#desc-box');
        if (!box) return;
        const open = box.classList.toggle('is-open');
        box.classList.toggle('desc-fade', !open);
        event.target.textContent = open ? 'Riduci descrizione' : 'Mostra tutta la descrizione';
      }
      if (event.target.id === 'copy-path') {
        const m = byId.get(state.selectedId);
        if (m) copyText(m.path);
      }
    });

    // tabs duplicati
    $('#duplicate-tabs').addEventListener('click', event => {
      const btn = event.target.closest('[data-duptab]');
      if (!btn) return;
      state.dupTab = btn.dataset.duptab;
      renderDuplicates();
    });

    // profili & mappe attive
    const btnApply = $('#btn-apply-mods');
    if (btnApply) btnApply.addEventListener('click', applyProfileToGame);

    const btnPresetItaly = $('#btn-preset-italy');
    if (btnPresetItaly) btnPresetItaly.addEventListener('click', () => {
      profileState.activeSet = new Set(DEFAULT_ITALIAN_MODS);
      $('#btn-preset-italy')?.classList.add('is-active');
      $('#btn-preset-all')?.classList.remove('is-active');
      $('#btn-preset-clear')?.classList.remove('is-active');
      renderProfiles();
      showToast('Caricato preset: 🇮🇹 Italia Mediterranea (31 mod)');
    });

    const btnPresetAll = $('#btn-preset-all');
    if (btnPresetAll) btnPresetAll.addEventListener('click', () => {
      profileState.activeSet = new Set(mods.map(m => m.file));
      $('#btn-preset-italy')?.classList.remove('is-active');
      $('#btn-preset-all')?.classList.add('is-active');
      $('#btn-preset-clear')?.classList.remove('is-active');
      renderProfiles();
      showToast(`Selezionate tutte le ${mods.length} mod dell'archivio`);
    });

    const btnPresetClear = $('#btn-preset-clear');
    if (btnPresetClear) btnPresetClear.addEventListener('click', () => {
      profileState.activeSet.clear();
      $('#btn-preset-italy')?.classList.remove('is-active');
      $('#btn-preset-all')?.classList.remove('is-active');
      $('#btn-preset-clear')?.classList.add('is-active');
      renderProfiles();
      showToast('Deselezionate tutte le mod');
    });

    const profileSearch = $('#profile-search');
    if (profileSearch) profileSearch.addEventListener('input', () => {
      profileState.q = profileSearch.value.trim();
      renderProfiles();
    });

    // preset economici
    const btnEcoSurvival = $('#btn-eco-survival');
    if (btnEcoSurvival) btnEcoSurvival.addEventListener('click', () => {
      $('#custom-money').value = 0;
      $('#custom-loan').value = 0;
      $('#game-diff').value = 'HARD';
      $('#chk-destr').checked = true;
      $('#chk-plow').checked = true;
      $('#chk-stones').checked = true;
      $('#chk-weeds').checked = true;
      $('#chk-lime').checked = true;
      $('#chk-snow').checked = true;
      btnEcoSurvival.classList.add('is-active');
      $('#btn-eco-standard')?.classList.remove('is-active');
      $('#btn-eco-sandbox')?.classList.remove('is-active');
      showToast('Impostato preset: 💀 Survival Hardcore 0€');
    });

    const btnEcoStandard = $('#btn-eco-standard');
    if (btnEcoStandard) btnEcoStandard.addEventListener('click', () => {
      $('#custom-money').value = 100000;
      $('#custom-loan').value = 0;
      $('#game-diff').value = 'NORMAL';
      $('#chk-destr').checked = false;
      $('#chk-plow').checked = false;
      $('#chk-stones').checked = false;
      btnEcoStandard.classList.add('is-active');
      $('#btn-eco-survival')?.classList.remove('is-active');
      $('#btn-eco-sandbox')?.classList.remove('is-active');
      showToast('Impostato preset: 🚜 Azienda Standard (100k€)');
    });

    const btnEcoSandbox = $('#btn-eco-sandbox');
    if (btnEcoSandbox) btnEcoSandbox.addEventListener('click', () => {
      $('#custom-money').value = 1000000;
      $('#custom-loan').value = 0;
      $('#game-diff').value = 'EASY';
      $('#chk-destr').checked = false;
      $('#chk-plow').checked = false;
      $('#chk-stones').checked = false;
      $('#chk-weeds').checked = false;
      btnEcoSandbox.classList.add('is-active');
      $('#btn-eco-survival')?.classList.remove('is-active');
      $('#btn-eco-standard')?.classList.remove('is-active');
      showToast('Impostato preset: 🎨 Sandbox Libero (1M€)');
    });

    // ricerca esterna KingMods
    const extSearch = $('#ext-search');
    if (extSearch) {
      extSearch.addEventListener('input', () => {
        clearTimeout(extSearchTimer);
        const q = extSearch.value.trim();
        extSearchTimer = setTimeout(() => searchExternalMods(q), 300);
      });
    }

    // bottone launch & game architect
    const btnLaunch = $('#btn-create-and-launch');
    if (btnLaunch) {
      btnLaunch.addEventListener('click', async () => {
        const slot = parseInt($('#game-slot')?.value || '1', 10);
        const name = $('#game-name')?.value || 'Survival Italia Mediterranea - Giorno 1';
        const money = parseInt($('#custom-money')?.value || '0', 10);
        const loan = parseInt($('#custom-loan')?.value || '0', 10);
        const diff = $('#game-diff')?.value || 'HARD';
        const days = parseInt($('#custom-days')?.value || '1', 10);
        const timeScale = parseFloat($('#custom-timescale')?.value || '5.0');
        const launchObs = $('#chk-launch-obs')?.checked ?? true;
        const list = Array.from(profileState.activeSet);

        btnLaunch.disabled = true;
        btnLaunch.textContent = '⏳ Preparo la partita…';

        const invia = (conferma) => fetch('/api/create_game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              conferma_sovrascrittura: conferma,
              map: $('#game-map')?.value || 'FS25_Mediterranean_Italy.zip',
              set: $('#game-set')?.value || '',
              slot: slot,
              name: name,
              money: money,
              loan: loan,
              difficulty: diff,
              days_per_period: days,
              time_scale: timeScale,
              fruit_destruction: $('#chk-destr')?.checked ?? true,
              plowing_required: $('#chk-plow')?.checked ?? true,
              stones: $('#chk-stones')?.checked ?? true,
              weeds: $('#chk-weeds')?.checked ?? true,
              lime: $('#chk-lime')?.checked ?? true,
              snow: $('#chk-snow')?.checked ?? true,
              mods: list,
              launch_game: true,
              launch_obs: launchObs
            })
          });

        try {
          let res = await invia(null);
          let data = await res.json();
          if (res.status === 409 && data.serve_conferma) {
            const ok = window.confirm(
              `Lo slot ${slot} contiene già un salvataggio:\n\n${(data.occupato_in || []).join('\n')}\n\n` +
              `Se continui, quel salvataggio viene SPOSTATO (non cancellato) nella cartella BACKUP_SAVEGAMES ` +
              `accanto, e al suo posto nasce una partita nuova.\n\n` +
              `Per sicurezza scrivi il numero dello slot nella prossima finestra.`);
            if (!ok) { showToast('Annullato: nessun salvataggio toccato'); return; }
            const scritto = window.prompt(`Scrivi ${slot} per confermare:`);
            if (String(scritto || '').trim() !== String(slot)) {
              showToast('Annullato: numero diverso, nessun salvataggio toccato');
              return;
            }
            res = await invia(slot);
            data = await res.json();
          }
          if (res.ok && data.success) {
            showToast(`🚀 Partita preparata nello Slot ${slot}! Farming Simulator 25 in avvio...`);
            updateProfileUI();
            const backups = data.backups || [];
            alert(`Partita pronta nello slot ${slot}\n\n` +
                  `• Mappa: ${data.mappa ? data.mappa.titolo : '?'}\n` +
                  `• Soldi: ${money} €\n` +
                  `• Prestito: ${loan} €\n` +
                  `• Difficoltà: ${diff}\n` +
                  `• Mod nel set ${data.set}: ${data.enabled_mods_count} (aggiunte, nessuna tolta)\n` +
                  `• Avvio: ${(partiteState.set.find(v => v.cartella === data.set) || {}).comando || 'run.sh'}\n` +
                  (backups.length ? `• Salvataggio di prima spostato in:\n  ${backups.join('\n  ')}\n` : '') +
                  (data.game_launched ? `• Gioco: in avvio\n` : `• Gioco: non avviato${data.launch_error ? ' (' + data.launch_error + ')' : ''}\n`) +
                  (launchObs ? `• OBS: ${data.obs_launched ? 'avviato' : 'non avviato'}\n` : '') +
                  `\nNel gioco: Carriera → Carica → slot ${slot}.`);
          } else {
            showToast(`Errore: ${data.error || 'preparazione del salvataggio non riuscita'}`);
          }
        } catch (e) {
          showToast('Server locale non raggiungibile. Avvia ./apri.sh');
        } finally {
          btnLaunch.disabled = false;
          btnLaunch.textContent = '🚀 Prepara la partita e avvia FS25';
        }
      });
    }

    // bottone rapido topbar per aprire il Game Launcher
    $('#btn-top-launcher')?.addEventListener('click', () => {
      if ($('#drawer').classList.contains('is-open')) closeMod();
      setView('profiles');
    });

    // pulsanti selezione rapida inventario principale
    $('#btn-inv-italy')?.addEventListener('click', () => {
      profileState.activeSet = new Set(DEFAULT_ITALIAN_MODS);
      updateProfileUI();
      renderInventory();
      showToast('Spuntate le 31 mod italiane per FS25!');
    });

    $('#btn-inv-apply')?.addEventListener('click', applyProfileToGame);
    $('#btn-rimetti-link')?.addEventListener('click', restoreSavedLinks);
    $('#btn-partita-controlla')?.addEventListener('click', controllaPartita);
    $('#btn-partita-salva')?.addEventListener('click', salvaAbbinamento);
    $('#btn-backup')?.addEventListener('click', avviaBackup);

    // hash iniziale e navigazione tramite URL
    function applyHash() {
      if (location.hash.startsWith('#mod=')) {
        const id = decodeURIComponent(location.hash.slice(5));
        if (byId.has(id)) {
          setView('inventory', false);
          openMod(id, false);
          return;
        }
      }
      if (location.hash.startsWith('#view=')) {
        const view = location.hash.slice(6);
        if (['inventory', 'duplicates', 'health', 'categories', 'catalog', 'profiles', 'recommended'].includes(view)) {
          if (state.selectedId) closeMod(false);
          setView(view, false);
        }
      }
    }
    applyHash();
    window.addEventListener('hashchange', applyHash);
  }

  // --------------------------------------------------------------- init

  renderStats();
  renderFilters();
  renderInventory();
  renderDuplicates();
  renderHealth();
  renderCategories();
  renderCatalog();
  bind();
  setView(state.view, false);
  syncProfileStatus();
})();
